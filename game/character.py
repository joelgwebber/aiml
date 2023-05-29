from __future__ import annotations
import ast
import openai
from typing import Iterable
from world import Place, Item
from typing import TypedDict, Unpack


class PromptArgs(TypedDict):
    name: str
    job: str
    place: str
    time: str
    states: set[str]
    knowledge: list[str]
    exits: list[Place]
    characters: list[Character]
    items: list[Item]
    inventory: list[Item]
    goals: list[str]
    events: list[str]


def make_prompt(**kwargs: Unpack[PromptArgs]):
    return f"""
Your name is {kwargs['name']}.
You are {kwargs['job']}.
You are in place {kwargs['place']}
It is {kwargs['time']}.

You are:
{list_it(kwargs['states'])}

You know:
{list_it(kwargs['knowledge'])}

Places you can go:
{list_it(kwargs['exits'])}

Characters you can see:
{list_it(kwargs['characters'])}

Items you can see:
{list_it(kwargs['items'])}

Items you're carrying:
{list_it(kwargs['inventory'])}

Your goals:
{list_it_num(kwargs['goals'])}

Recent events:
{list_it(kwargs['events'])}

On the first line, state your next action.
On the next line, list the numbers of completed goals, or ["none"].
On the next line, list any new goals, or ["none"].
"""


def _make_system(**kwargs: Unpack[PromptArgs]):
    return """
        You are playing a character in a text adventure.
        All responses must be JSON string arrays.
        Actions are of the form [verb, direct-object, indirect-object].
        Verbs must be one of "move", "say", "take", "put", "give", "wait", "consume"
    """

def make_system(**kwargs: Unpack[PromptArgs]):
    return """
        You are playing a character in a text adventure.
        Respond only with JSON string arrays.
        Plans must be of the form ["plan", "your plan"]
        Actions must be the form ["verb", "direct-object", "indirect-object"].
        Verbs must be one of "move", "say", "take", "put", "give", "wait", "consume"
        The verb "say" must be followed by the statement, then (optionally) the listener.
    """


class Character:
    place: Place
    name: str
    job: str
    states: set[str]
    inventory: set[Item]
    goals: list[str]
    events: list[str]

    # Debug stuff.
    last_knowledge_query: str
    last_prompt: str
    last_response: any

    def __init__(self, name: str, job: str, place: Place) -> None:
        self.place = place
        self.name = name
        self.job = job
        self.states = set()
        self.inventory = set()
        self.goals = []
        self.events = []
        place.characters.add(self)

    def __repr__(self) -> str:
        return f"{self.name} the {self.job}"

    def find_item(self, name: str) -> Item:
        for item in self.inventory:
            if item.name == name:
                return item
        return None

    def remove_item(self, item: Item) -> None:
        self.inventory.remove(item)

    def add_item(self, item: Item) -> None:
        self.inventory.add(item)

    def event(self, event: str) -> None:
        self.events.append(event.replace(self.name, "you"))

    def think(self, debug=False):
        exits = self.place.available_exits()
        characters = self.place.visible_characters()
        items = self.place.visible_items()

        # Get contextual knowledge from lore, using contextual information.
        query = f"""
            {self.name}
            {self.job}
            {self.place.name}
            {self.place.world.time}
            {list_it(exits)}
            {list_it(characters)}
            {list_it(items)}
            {list_it(self.inventory)}
            {list_it(self.goals)}
        """
        knowledge = self.place.world.lore.query(query, 6)
        self.last_knowledge_query = query

        # Prompt the model to consider the character's knowledge, situation, and state,
        # and decide on the next action to take.
        prompt = make_prompt(
            name=self.name,
            job=self.job,
            place=self.place.name,
            time=self.place.world.time,
            states=self.states,
            knowledge=knowledge,
            exits=exits,
            characters=characters,
            items=items,
            inventory=self.inventory,
            goals=self.goals,
            events=self.events,
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.5,
            messages=[
                {"role": "system", "content": make_system()},
                {"role": "user", "content": prompt},
            ]
        )
        [action, completed, new_goals] = self.parse_response(
            response.choices[0].message.content)
        self.last_prompt = prompt
        self.last_response = response

        # Parse the results.
        if debug:
            print(f"> action: {action}")
            print(f"> completed: {completed}")
            print(f"> new-goals: {new_goals}")

        # Mark done.
        completed.sort(reverse=True)
        for idx in completed:
            if idx is not None:
                del self.goals[idx]

        # Update goals.
        for goal in new_goals:
            if goal is not None:
                self.goals.append(goal)

        # Perform the action.
        self.act(*action)
        # self.event(f"didn't understand '{response}'")

    def parse_response(self, rsp: str) -> list[list[str]]:
        """ Parse the model's response. It can be a bit unpredictable, so this function is very defensive.
            The result is guaranteed to be of the form:
            [
                [verb, direct-object?, indirect-object?] # Always three values, with None in unused positions
                [completed-goal-index*]                  # integer indices of completed goals
                [new-goals]                              # new goals
            ]
        """
        lines = rsp.split('\n')
        action_str = lines[0]
        completed_str = lines[1] if len(lines) > 1 else None
        new_goals_str = lines[2] if len(lines) > 2 else None

        # Three-part action list.
        try:
            # Parse the action, ensuring that there are always at least three elements.
            action: list[str] = ast.literal_eval(action_str)
            match len(action):
                case 0: action == [None, None, None]
                case 1: action.extend([None, None])
                case 2: action.append(None)
        except:
            action = [None, None, None]
        for idx in range(0, len(action)):
            if action[idx] == 'none':
                action[idx] = None

        # Completed-goal indices.
        try:
            completed: list[int] = []
            for item in ast.literal_eval(completed_str):
                if item != 'none':
                    completed.append(int(item))
        except:
            completed = []

        # New goals.
        try:
            new_goals: list[str] = []
            for item in ast.literal_eval(new_goals):
                if item != 'none':
                    new_goals.append(item)
        except:
            new_goals = []
        return [action, completed, new_goals]

    def act(self, *args: list[str]) -> str:
        event: str = None
        match args[0]:
            case "move":
                place_name = args[1]
                event = self.place.move_character(self, place_name)

            case "say":
                statement = args[1]
                listener = None
                if len(args) > 2:
                    listener = args[2]
                event = self.place.say(self, statement, listener)

            case "take":
                item_name = args[1]
                location = args[2]
                event = self.place.take_item(self, item_name, location)

            case "put":
                item_name = args[1]
                event = self.place.put_item(self, item_name)

            case "give":
                item_name = args[1]
                receiver = args[2]
                event = self.place.give_item(self, item_name, receiver)

            case "wait":
                event = "you waited"

            case "consume":
                item_name = args[1]
                event = self.place.consume(self, item_name)

            case _:
                event = f"you tried to '{args[0]}', but couldn't"

        if event is not None:
            self.events.append(event)


# Kind of hacky -- generates a newline-separated list of items from any Iterable.
# Currently handles list[str | Item | Place | Character | Document]
def list_it(items: Iterable[any]) -> str:
    x = [f'- {item}' for item in map(get_name, items)]
    return "\n".join(x)


def list_it_num(items: Iterable[any]) -> str:
    x = [f'{idx}. {item}' for idx, item in enumerate(map(get_name, items))]
    return "\n".join(x)


def get_name(x):
    if hasattr(x, "name"):
        return x.name
    elif hasattr(x, "page_content"):
        return x.page_content
    return x

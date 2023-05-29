from __future__ import annotations
from lore import Lore


class World:
    """ World class that owns all the places, items, and characters.
        It also tracks global state like time-of-day. """
    lore: Lore
    time: str

    def __init__(self, lore: Lore) -> None:
        self.lore = lore
        self.time = "evening"

    def __str__(self) -> str:
        return f"{self.time} in the world"

    def __repr__(self) -> str:
        return str(self)


class Item:
    """ An item is anything in the game that can be moved. """
    name: str
    consumable: bool = False

    def __init__(self, name) -> None:
        self.name = name
        pass

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return str(self)

    def copy(self):
        item = Item(self.name)
        item.consumable = self.consumable
        return item


class Place:
    """ A place is a location within the game. """
    name: str
    world: World
    parent: Place
    children: list[Place]
    items: set[Item]
    characters: set["Character"]
    exits: set[Place]

    def connect(a: Place, b: Place) -> None:
        a.exits.add(b)
        b.exits.add(a)

    def __init__(self, world: World, name: str, parent: Place = None) -> None:
        self.name = name
        self.world = world

        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)

        self.items = set()
        self.characters = set()
        self.exits = set()

    def __str__(self) -> str:
        # TODO: This is nice for clarity, but currently breaks references when, e.g., the model says ['take', 'mug', "kitchen's table"]
        # if self.parent is not None:
        #     return f"{self.parent}'s {self.name}"
        return self.name

    def __repr__(self) -> str:
        return str(self)

    def new_item(self, item: Item):
        """ Create a copy of an item and place it here. """
        self.items.add(item.copy())

    def available_exits(self) -> list[str]:
        """ Gets all available exits, by name. """
        exits = []
        exits.extend(self.exits)
        if self.parent:
            exits.extend(self.parent.exits)
        exits.extend(self.children)
        # Do _not_ include child exits, which may include places only accessible from the child itself (e.g., a hidden passage).
        return exits

    def visible_characters(self) -> list[str]:
        """ Gets all visible characters, by name. """
        characters = []
        characters.extend(self.characters)
        if self.parent:
            characters.extend(self.parent.characters)
        for child in self.children:
            characters.extend(child.characters)
        return characters

    def visible_items(self) -> list[str]:
        """ Gets all visible characters, by name, with their location if in a child place. """
        items = []
        items.extend(self.items)
        if self.parent:
            items.extend(self.parent.items)
        for child in self.children:
            for item in child.items:
                items.append(f"{item}, in {child}")
        return items

    def broadcast(self, event: str):
        """ Broadcast to all characters in this place, as well as any parent and child places. """
        print(f">>> {self.name}: {event}")
        for char in self.characters:
            char.event(event)
        if self.parent:
            for char in self.parent.characters:
                char.event(event)
        for child in self.children:
            for char in child.characters:
                char.event(event)

    def find_item(self, name: str, child_name: str = None) -> list[Item, Place]:
        """ Find an item within this place (or optionally a child), by name. """
        place = self
        if child_name:
            place = self.child_by_name(child_name)
            if place is None:
                place = self

        for item in place.items:
            if item.name == name:
                return [item, place]

        return [None, None]

    def find_exit(self, name: str) -> Place:
        """ Find an exit name. This will search this place's exits and its parents.
            It will also include child places, but _not_ their exits. """
        for place in self.exits:
            if place.name == name:
                return place
        if self.parent:
            for place in self.parent.exits:
                if place.name == name:
                    return place
        return self.child_by_name(name)

    def child_by_name(self, name: str) -> Place:
        """ Find a child place by name. """
        for child in self.children:
            if child.name == name:
                return child
        return None

    def find_character(self, name: str) -> Place:
        """ Find a character within this place, its parent or children, by name. """
        for char in self.characters:
            if char.name == name:
                return char
        if self.parent:
            for char in self.parent.characters:
                if char.name == name:
                    return char
        for child in self.children:
            for char in child.characters:
                if char.name == name:
                    return char
        return None

    def say(self, char: "Character", statement: str, listener: str = None) -> str:
        """ A character speaks, with a statement, and optional listener. """
        event = f"{char.name} said {statement}"
        if listener is not None:
            event += f" to {listener}"
        self.broadcast(event)
        return None

    def take_item(self, char: "Character", item_name: str, child_name: str = None) -> str:
        """ A character takes an item, optionally from a specific child place. """
        [item, place] = self.find_item(item_name, child_name)
        if item is None:
            return f"you tried to take {item_name}, but couldn't find it"

        place.items.remove(item)
        char.add_item(item)

        place.broadcast(f"{char.name} took {item.name} from {self.name}")
        return None

    def put_item(self, char: "Character", item_name: str) -> str:
        """ A character puts an item in this place. """
        item = char.find_item(item_name)
        if item is None:
            return f"you tried to put {item_name}, but didn't have it"

        char.remove_item(item)
        self.items.add(item)

        self.broadcast(f"{char.name} placed {item.name} in {self.name}")
        return None

    def give_item(self, char: "Character", item_name: str, receiver_name: str) -> str:
        """ A character gives an item to another, within this place. """
        item = char.find_item(item_name)
        if item is None:
            return f"you tried to give {item_name}, but didn't have it"

        receiver = self.find_character(receiver_name)
        if receiver is None:
            return f"you tried to give {item_name} to {receiver_name}, but they're not here"

        char.remove_item(item)
        receiver.add_item(item)

        self.broadcast(f"{char.name} gave {item.name} to {receiver.name}")
        return None

    def consume(self, char: "Character", item_name: str) -> str:
        """ A character consumes an item (eats, drinks, etc). """
        item = char.find_item(item_name)
        if item is None:
            return f"you tried to consume {item_name}, but didn't have it"
        if not item.consumable:
            return f"you tried to consume {item_name}, but it isn't consumable"

        char.remove_item(item)
        self.broadcast(f"{char.name} consumed {item.name}")
        # TODO: Make this depend upon the item being consumed.
        char.states.remove("thirsty")
        return None

    def move_character(self, char: "Character", place_name: str) -> str:
        """ A character moves from this place to aonther, directly reachable from this one. """
        to_place = self.find_exit(place_name)
        if to_place is None:
            return f"you tried to move to {place_name}, but can't get there from here."

        self.characters.remove(char)
        to_place.characters.add(char)
        char.place = to_place

        self.broadcast(f"{char.name} exited to {place_name}")
        to_place.broadcast(f"{char.name} entered from {self.name}")
        return None

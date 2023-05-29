import openai

openai.api_key = "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"

prompt = """
Your name is strider.
You are ranger.
You are in the inn.
It is evening.

You are hungry.
You are thirsty.
You are tired.

You know:
- An inn-keeper owns and operates an inn.
- A mug of ale costs one coin.
- Rangers like ale more than water.
- Inns sell food and drink.
- You must pay for food and drink in an inn.
- Inns rent rooms.

From here, you can go to:
- kitchen
- village

Chaacters here:
- John the inn-keeper

You have:
- coin

Recent events:
- you entered from village
- you moved to John the inn-keeper
- you said to John the inn-keeper "Good evening, John. Might I trouble you for a mug of ale? I am quite parched."
- you gave coin to John the inn-keeper.
- John the inn-keeper gave you a mug of ale.

Plan:
1. Consume the mug of ale that I have already received from John the inn-keeper.
2. If hungry, order food from John the inn-keeper and pay for it with my remaining coin.
3. Inquire about the price of renting a room for the night.
4. If the price is reasonable, rent a room and get a good night's sleep.
5. If the price is not reasonable, leave the inn and head back to the village to find a cheaper place to stay.

State your plan for the evening, using only the information available in this prompt.
Then state your single next action as a JSON string array.
Verbs must be one of "move", "say", "take", "put", "give", "wait", "consume"
"""

response = openai.ChatCompletion.create(
    model="gpt-4",
    temperature=0.5,
    messages=[
        {"role": "system", "content": """
        You are playing a character in a text adventure.
        All spoken language is Elizabethan English.
        """},
        {"role": "user", "content": prompt},
    ]
)

print(response.choices[0].message.content)

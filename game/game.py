from lore import Lore
from world import World
from scene.village import init_village
import openai


openai.api_key = "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"


lore = Lore()
world = World(lore)


# village = make_village(world)
village = init_village(world)
strider = village['strider']
john = village['john']
kitchen = village['kitchen']
inn = village['inn']


def think(debug: bool = False):
    strider.think(debug)
    john.think(debug)


# Does nothing explicitly. Run this with `python3 -i llgame.py` to start it interactively.
# In the interpreter, try things like strider.think(True) and inn_keeper.think(True).
# Or just think() to tick all the characters.

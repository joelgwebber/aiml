from __future__ import annotations
from world import World, Place, Item
from character import Character
from typing import TypedDict, Optional


class SceneProto(TypedDict):
    items: list[ItemProto]
    places: list[PlaceProto]
    characters: list[CharacterProto]


class ItemProto(TypedDict):
    name: str
    consumable: Optional[bool]


class PlaceProto(TypedDict):
    name: str
    items: list[str]
    children: list[PlaceProto]


class CharacterProto(TypedDict):
    name: str
    job: str
    place: str
    states: list[str]
    inventory: list[str]


def _bool(dict: TypedDict, key: str) -> bool:
    return dict[key] if key in dict else False


def _list(dict: TypedDict, key: str) -> list:
    return dict[key] if key in dict else []


def _str(dict: TypedDict, key: str) -> bool:
    return dict[key] if key in dict else False


def _parse_item(things: dict, proto: ItemProto):
    name = proto['name']
    item = Item(name)
    item.consumable = _bool(proto, 'consumable')
    things[name] = item


def _parse_character(things: dict, proto: CharacterProto):
    place: Place = things[proto['place']]
    name = proto['name']
    char = Character(name, proto['job'], place)
    for state in _list(proto, 'states'):
        char.states.add(state)
    for item_name in _list(proto, 'inventory'):
        char.inventory.add(things[item_name])
    things[name] = char


def _parse_places(world: World, things: dict, protos: list[PlaceProto], prefix: str = "", parent: Place = None):
    for proto in protos:
        place = Place(world, proto['name'], parent)
        for item_name in _list(proto, 'items'):
            item = things[item_name]
            place.items.add(item)

        _parse_places(world, things, _list(proto, 'children'), place.name + ".", place)
        things[prefix + place.name] = place

    for proto in protos:
        for exit_name in _list(proto, 'exits'):
            place_name = proto['name']
            place: Place = things[place_name]
            if place is None:
                raise Exception(f"place {place_name} not found")
            exit = things[exit_name]
            place.exits.add(exit)


def init_scene(world: World, scene_proto: SceneProto) -> dict:
    things = {}

    # Items:
    for proto in scene_proto['items']:
        _parse_item(things, proto)

    # Places:
    _parse_places(world, things, scene_proto['places'])

    # Characters:
    for proto in scene_proto['characters']:
        _parse_character(things, proto)

    return things

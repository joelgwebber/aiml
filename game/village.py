from __future__ import annotations
from world import World
from scene.scene import init_scene, SceneProto


village_scene: SceneProto = {
    "items": [
        {"name": "chair"},
        {"name": "coin"},
        {"name": "mug-of-ale", "consumable": True},
    ],

    "places": [
        {
            "name": "village",
            "exits": ["inn"]
        },
        {
            "name": "inn",
            "exits": ["village", "kitchen"],
            "children": [
                {"name": "table", "items": ["chair"]},
                {"name": "bar"}
            ]
        },
        {
            "name": "kitchen",
            "exits": ["inn"],
            "children": [
                {"name": "table", "items": ["mug-of-ale"]},
                {"name": "keg"}
            ]
        }
    ],

    "characters": [
        {
            "name": "strider",
            "job": "ranger",
            "place": "village",
            "states": ["thirsty"],
            "inventory": ["coin"]
        },
        {
            "name": "john",
            "job": "inn-keeper",
            "place": "inn"
        }
    ]
}


def init_village(world: World) -> dict:
    return init_scene(world, village_scene)

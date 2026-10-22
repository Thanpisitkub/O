#!/usr/bin/env python3
"""Generates the data-driven part of the Pain Origin mod (Origins/Apoli powers, origin, layer,
damage types, language files, sounds.json, particle definitions, pack.mcmeta).

Usage: gen_data.py <project_root> [--set=NAME=VALUE ...] [--datapack=DIR]

  --set=NAME=VALUE   override one number of the TUNING table below (e.g. --set=shinra_radius=14)
  --datapack=DIR     additionally write a ready-to-use DATAPACK with only the power files into DIR
                     (copy DIR into <world>/datapacks/ and run /reload) - this is how the numbers of the
                     data-driven powers are changed without recompiling the mod.  NOTE: the descriptions
                     shown in the Origins screen live in the mod's language files and are not part of a
                     datapack, so they keep showing the default numbers.

Every number that a player may want to tune lives in the TUNING block below, so the JSON,
the language strings and the README tables stay consistent with each other.
"""
import json
import os
import sys

ROOT = sys.argv[1]
RES = os.path.join(ROOT, "src", "main", "resources")
NS = "painorigin"
SPRITE = f"{NS}:textures/gui/resource_bar.png"

# ----------------------------------------------------------------------------------------------
# TUNING  (ticks: 20 = 1 second)
# ----------------------------------------------------------------------------------------------
T = dict(
    chakra_max=100, chakra_regen_interval=10, chakra_regen_amount=1,
    # Shinra Tensei (primary key)
    shinra_cost=10, shinra_cooldown=100, shinra_radius=10.0, shinra_push_h=1.6, shinra_push_v=0.55, shinra_damage=3.0,
    # Massive Shinra Tensei (sneak + primary key)
    massive_cost=40, massive_cooldown=1200, massive_charge=30, massive_radius=24.0, massive_push_h=3.2,
    massive_push_v=0.9, massive_damage=12.0,
    # Banshō Ten'in (secondary key)
    tenin_cost=8, tenin_cooldown=80, tenin_range=32.0, tenin_pull_h=1.6, tenin_pull_v=0.4,
    # Chibaku Tensei (sneak + secondary key)
    chibaku_cost=80, chibaku_cooldown=3600,
    # Universal Defense
    defense_max=3, defense_regen_interval=400, defense_cost=5, defense_push_range=5.0,
    # Rinnegan Gravity Field (passive item/xp magnet)
    field_radius=6.0, field_interval=5, field_pull=0.12,
    # Frail Vessel / Gravity Affinity
    frail_health=-4.0, gravity_modifier=-0.25,
)

for _arg in sys.argv[2:]:
    if _arg.startswith("--set="):
        _name, _, _value = _arg[len("--set="):].partition("=")
        if _name not in T:
            sys.exit(f"unknown tuning name {_name!r}; valid names: {', '.join(sorted(T))}")
        T[_name] = type(T[_name])(_value)



# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
def write_json(path, data):
    full = os.path.join(RES, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def pid(name):
    return f"{NS}:{name}"


def hud(index):
    return {"should_render": True, "bar_index": index, "sprite_location": SPRITE}


def c_and(*conds):
    return {"type": "apoli:and", "conditions": list(conds)}


def c_or(*conds):
    return {"type": "apoli:or", "conditions": list(conds)}


def c_res(name, cmp_, value):
    return {"type": "apoli:resource", "resource": pid(name), "comparison": cmp_, "compare_to": value}


def c_sneak(on):
    return {"type": "apoli:sneaking"} if on else {"type": "apoli:sneaking", "inverted": True}


def a_and(*actions):
    return {"type": "apoli:and", "actions": list(actions)}


def a_change(name, amount):
    return {"type": "apoli:change_resource", "resource": pid(name), "change": amount}


def a_sound(event, volume=1.0, pitch=1.0):
    return {"type": "apoli:play_sound", "sound": pid(event), "volume": volume, "pitch": pitch}


def a_cmd(command):
    return {"type": "apoli:execute_command", "command": command}


def a_actionbar(key, color="light_purple"):
    text = json.dumps({"translate": key, "color": color}, ensure_ascii=False, separators=(",", ":"))
    return a_cmd(f"title @s actionbar {text}")


def key(which):
    return {"key": f"key.origins.{which}_active", "continuous": False}


# entities that Shinra Tensei / Ten'in may affect: everything except the caster, the caster's own
# pets and spectators.
def bi_affected():
    return {
        "type": "apoli:and",
        "conditions": [
            {"type": "apoli:owner", "inverted": True},
            {"type": "apoli:target_condition",
             "condition": {"type": "apoli:gamemode", "gamemode": "spectator", "inverted": True}},
        ],
    }


def push(radius, horizontal, vertical, damage):
    return {
        "type": "apoli:area_of_effect",
        "radius": radius,
        "shape": "sphere",
        "include_target": False,
        "bientity_condition": bi_affected(),
        "bientity_action": {
            "type": "apoli:and",
            "actions": [
                {"type": "apoli:add_velocity", "x": 0.0, "y": vertical, "z": horizontal},
                {"type": "apoli:damage", "amount": damage, "damage_type": pid("shinra_tensei")},
            ],
        },
    }


def living_target():
    # target must be a living, non-spectator entity (used by the Ten'in ray)
    return {
        "type": "apoli:target_condition",
        "condition": {
            "type": "apoli:and",
            "conditions": [
                {"type": "apoli:living"},
                {"type": "apoli:gamemode", "gamemode": "spectator", "inverted": True},
            ],
        },
    }


def tenin_ray_condition():
    return {
        "type": "apoli:raycast",
        "distance": T["tenin_range"],
        "block": True,
        "entity": True,
        "shape_type": "collider",
        "fluid_handling": "none",
        "match_bientity_condition": living_target(),
        "hit_bientity_condition": living_target(),
    }


def power(name, body, hidden=False):
    data = dict(body)
    if hidden:
        data["hidden"] = True
    write_json(f"data/{NS}/powers/{name}.json", data)


# ----------------------------------------------------------------------------------------------
# POWERS
# ----------------------------------------------------------------------------------------------
# --- chakra -----------------------------------------------------------------------------------
power("chakra", {
    "type": "apoli:resource", "min": 0, "max": T["chakra_max"], "start_value": T["chakra_max"],
    "hud_render": hud(0),
})
power("chakra_regen", {
    "type": "apoli:action_over_time", "interval": T["chakra_regen_interval"],
    "entity_action": a_change("chakra", T["chakra_regen_amount"]),
}, hidden=True)

# --- Shinra Tensei ----------------------------------------------------------------------------
power("shinra_tensei", {
    "type": "apoli:active_self",
    "key": key("primary"),
    "cooldown": T["shinra_cooldown"],
    "hud_render": hud(1),
    "condition": c_and(c_sneak(False), c_res("chakra", ">=", T["shinra_cost"])),
    "entity_action": a_and(
        a_change("chakra", -T["shinra_cost"]),
        a_sound("shinra_tensei.release", 2.0, 1.0),
        a_sound("shinra_tensei.shockwave", 1.5, 1.0),
        push(T["shinra_radius"], T["shinra_push_h"], T["shinra_push_v"], T["shinra_damage"]),
        a_cmd(f"painorigin fx shinra_tensei {T['shinra_radius']:g}"),
    ),
})

# --- Massive Shinra Tensei --------------------------------------------------------------------
massive_release = {
    "type": "apoli:if_else",
    # guard: the caster must still be alive and still own the power when the charge ends
    "condition": c_and(
        {"type": "apoli:health", "comparison": ">", "compare_to": 0.0},
        {"type": "apoli:power", "power": pid("shinra_tensei_massive")},
    ),
    "if_action": a_and(
        a_sound("shinra_tensei.release", 5.0, 0.7),
        a_sound("shinra_tensei.shockwave", 4.0, 0.7),
        push(T["massive_radius"], T["massive_push_h"], T["massive_push_v"], T["massive_damage"]),
        a_cmd(f"painorigin fx shinra_massive {T['massive_radius']:g}"),
        a_cmd(f"painorigin massive_blocks {T['massive_radius']:g}"),
    ),
}
power("shinra_tensei_massive", {
    "type": "apoli:active_self",
    "key": key("primary"),
    "cooldown": T["massive_cooldown"],
    "hud_render": hud(4),
    "condition": c_and(c_sneak(True), c_res("chakra", ">=", T["massive_cost"])),
    "entity_action": a_and(
        a_change("chakra", -T["massive_cost"]),
        a_sound("shinra_tensei.charge", 3.0, 1.0),
        a_cmd(f"painorigin fx charge {T['massive_charge']}"),
        {"type": "apoli:delay", "ticks": T["massive_charge"], "action": massive_release},
    ),
})

# --- Banshō Ten'in ----------------------------------------------------------------------------
power("bansho_tenin", {
    "type": "apoli:active_self",
    "key": key("secondary"),
    "cooldown": T["tenin_cooldown"],
    "hud_render": hud(2),
    "condition": c_and(c_sneak(False), c_res("chakra", ">=", T["tenin_cost"]), tenin_ray_condition()),
    "entity_action": a_and(
        a_change("chakra", -T["tenin_cost"]),
        a_sound("bansho_tenin.pull", 1.5, 1.0),
        {
            "type": "apoli:raycast",
            "distance": T["tenin_range"],
            "block": True,
            "entity": True,
            "shape_type": "collider",
            "fluid_handling": "none",
            "bientity_condition": living_target(),
            "command_along_ray": "painorigin fx bansho_trail",
            "command_step": 1.5,
            "command_along_ray_only_on_hit": True,
            "bientity_action": {
                "type": "apoli:and",
                "actions": [
                    {"type": "apoli:add_velocity", "x": 0.0, "y": T["tenin_pull_v"], "z": -T["tenin_pull_h"]},
                    {"type": "apoli:target_action", "action": a_cmd("painorigin fx bansho_hit")},
                ],
            },
        },
    ),
})

# --- Chibaku Tensei ---------------------------------------------------------------------------
power("chibaku_tensei", {
    "type": "apoli:active_self",
    "key": key("secondary"),
    "cooldown": T["chibaku_cooldown"],
    "hud_render": hud(3),
    "condition": c_and(c_sneak(True), c_res("chakra", ">=", T["chibaku_cost"])),
    "entity_action": a_and(
        a_change("chakra", -T["chibaku_cost"]),
        a_cmd("painorigin chibaku start"),
    ),
})

# --- Universal Defense ------------------------------------------------------------------------
power("defense_charges", {
    "type": "apoli:resource", "min": 0, "max": T["defense_max"], "start_value": T["defense_max"],
    "hud_render": hud(5),
}, hidden=True)
power("defense_regen", {
    "type": "apoli:action_over_time", "interval": T["defense_regen_interval"],
    "entity_action": a_change("defense_charges", 1),
}, hidden=True)
power("universal_defense", {
    "type": "apoli:modify_damage_taken",
    # limited: needs a charge AND chakra
    "condition": c_and(c_res("defense_charges", ">=", 1), c_res("chakra", ">=", T["defense_cost"])),
    # conditions: real hits only (projectile / explosion / hit by a living attacker); never void damage,
    # never zero-damage hits (snowballs), never fall / drowning / fire / magic / starvation.
    "damage_condition": c_and(
        {"type": "apoli:out_of_world", "inverted": True},
        {"type": "apoli:amount", "comparison": ">", "compare_to": 0.0},
        c_or({"type": "apoli:projectile"}, {"type": "apoli:explosive"}, {"type": "apoli:attacker"}),
    ),
    "modifier": {"operation": "multiply_total_multiplicative", "value": -1.0},
    "self_action": a_and(
        a_change("defense_charges", -1),
        a_change("chakra", -T["defense_cost"]),
        a_sound("universal_defense.block", 1.5, 1.0),
        a_cmd("painorigin fx defense"),
    ),
    # a melee attacker standing next to the defender is thrown back (actor/target are swapped so the
    # attacker is the one pushed away from the defender)
    "bientity_action": {
        "type": "apoli:invert",
        "action": {
            "type": "apoli:if_else",
            "condition": {"type": "apoli:distance", "comparison": "<=", "compare_to": T["defense_push_range"]},
            "if_action": {"type": "apoli:add_velocity", "x": 0.0, "y": 0.4, "z": 1.4},
        },
    },
})

# --- Rinnegan Gravity Field (passive) ---------------------------------------------------------
power("rinnegan_gravity_field", {
    "type": "apoli:action_over_time", "interval": T["field_interval"],
    "entity_action": {
        "type": "apoli:area_of_effect",
        "radius": T["field_radius"],
        "shape": "sphere",
        "include_target": False,
        "bientity_condition": {
            "type": "apoli:and",
            "conditions": [
                {"type": "apoli:target_condition", "condition": {
                    "type": "apoli:or", "conditions": [
                        {"type": "apoli:entity_type", "entity_type": "minecraft:item"},
                        {"type": "apoli:entity_type", "entity_type": "minecraft:experience_orb"},
                    ]}},
                {"type": "apoli:distance", "comparison": ">", "compare_to": 1.2},
            ],
        },
        "bientity_action": {"type": "apoli:add_velocity", "x": 0.0, "y": 0.03, "z": -T["field_pull"]},
    },
})
power("rinnegan_aura", {
    "type": "apoli:action_over_time", "interval": 10,
    "entity_action": a_cmd("painorigin fx rinnegan_ambient"),
}, hidden=True)

# --- misc passives ----------------------------------------------------------------------------
power("gravity_affinity", {
    "type": "apoli:modify_falling",
    "modifier": {"operation": "multiply_total_multiplicative", "value": T["gravity_modifier"]},
})
power("frail_vessel", {
    "type": "apoli:attribute",
    "modifier": {
        "name": "Frail vessel",
        "attribute": "minecraft:generic.max_health",
        "operation": "addition",
        "value": T["frail_health"],
    },
})

# --- feedback ("notice") powers: shown when a key is pressed but the skill cannot fire ---------
power("notice_primary", {
    "type": "apoli:active_self", "key": key("primary"), "cooldown": 30,
    "condition": c_or(
        c_and(c_sneak(False), c_res("chakra", "<", T["shinra_cost"])),
        c_and(c_sneak(True), c_res("chakra", "<", T["massive_cost"])),
    ),
    "entity_action": a_actionbar("painorigin.notice.low_chakra"),
}, hidden=True)
power("notice_secondary", {
    "type": "apoli:active_self", "key": key("secondary"), "cooldown": 30,
    "condition": c_or(
        c_and(c_sneak(False), c_res("chakra", "<", T["tenin_cost"])),
        c_and(c_sneak(True), c_res("chakra", "<", T["chibaku_cost"])),
    ),
    "entity_action": a_actionbar("painorigin.notice.low_chakra"),
}, hidden=True)
power("notice_target", {
    "type": "apoli:active_self", "key": key("secondary"), "cooldown": 30,
    "condition": c_and(
        c_sneak(False), c_res("chakra", ">=", T["tenin_cost"]),
        dict(tenin_ray_condition(), inverted=True),
    ),
    "entity_action": a_actionbar("painorigin.notice.no_target", "yellow"),
}, hidden=True)

# --- onboarding: runs when the origin is chosen; makes every skill usable at once -------------
# (Apoli starts a cooldown the moment a power is gained; ChangeResource with a huge negative
#  value clamps the remaining cooldown to 0.)  Note: change/value 0 would be rejected by Apoli.
reset_all = [
    a_change("chakra", 1000),
    a_change("defense_charges", 1000),
    a_change("shinra_tensei", -100000),
    a_change("shinra_tensei_massive", -100000),
    a_change("bansho_tenin", -100000),
    a_change("chibaku_tensei", -100000),
]
power("onboarding", {
    "type": "origins:action_on_callback",
    "entity_action_chosen": a_and(*reset_all, a_cmd(
        "tellraw @s " + json.dumps({"translate": "painorigin.onboarding", "color": "light_purple"},
                                   separators=(",", ":")))),
    "entity_action_gained": a_and(*reset_all),
}, hidden=True)

# ----------------------------------------------------------------------------------------------
# ORIGIN + LAYER
# ----------------------------------------------------------------------------------------------
ORIGIN_POWERS = [
    "chakra", "chakra_regen",
    "shinra_tensei", "shinra_tensei_massive", "bansho_tenin", "chibaku_tensei",
    "universal_defense", "defense_charges", "defense_regen",
    "rinnegan_gravity_field", "rinnegan_aura", "gravity_affinity", "frail_vessel",
    "notice_primary", "notice_secondary", "notice_target",
    "onboarding",  # keep last: its callbacks reset the cooldowns of everything above
]
write_json(f"data/{NS}/origins/deva_path.json", {
    "powers": [pid(p) for p in ORIGIN_POWERS],
    "icon": {"item": "minecraft:ender_eye"},
    "unchoosable": False,
    "order": 20,
    "impact": 3,
})
write_json("data/origins/origin_layers/origin.json", {"replace": False, "origins": [pid("deva_path")]})

# ----------------------------------------------------------------------------------------------
# DAMAGE TYPES (data-driven damage types exist since 1.19.4)
# ----------------------------------------------------------------------------------------------
for dt in ("shinra_tensei", "chibaku_tensei"):
    write_json(f"data/{NS}/damage_type/{dt}.json", {
        "message_id": f"{NS}.{dt}", "scaling": "when_caused_by_living_non_player", "exhaustion": 0.0})
write_json("data/minecraft/tags/damage_type/bypasses_armor.json", {"replace": False, "values": [pid("chibaku_tensei")]})

# ----------------------------------------------------------------------------------------------
# TAGS used by the Java add-on (1.20.1 uses the plural folder names "blocks" / "entity_types")
# ----------------------------------------------------------------------------------------------
# Blocks that Chibaku Tensei / Massive Shinra Tensei must NEVER remove, even with block destruction enabled.
write_json(f"data/{NS}/tags/blocks/chibaku_protected.json", {
    "replace": False,
    "values": [
        "minecraft:bedrock", "minecraft:barrier", "minecraft:light", "minecraft:structure_void",
        "minecraft:structure_block", "minecraft:jigsaw",
        "minecraft:command_block", "minecraft:chain_command_block", "minecraft:repeating_command_block",
        "minecraft:end_portal_frame", "minecraft:end_portal", "minecraft:end_gateway", "minecraft:nether_portal",
        "minecraft:spawner", "minecraft:reinforced_deepslate",
        {"id": "#minecraft:wither_immune", "required": False},
        {"id": "#minecraft:dragon_immune", "required": False},
    ],
})
# Entities that Chibaku Tensei never pulls or damages (bosses).
write_json(f"data/{NS}/tags/entity_types/chibaku_immune.json", {
    "replace": False,
    "values": ["minecraft:ender_dragon", "minecraft:wither"],
})

# ----------------------------------------------------------------------------------------------
# SOUNDS + PARTICLE DEFINITIONS
# ----------------------------------------------------------------------------------------------
SOUND_EVENTS = {
    # event id                       file          subtitle key
    "shinra_tensei.charge": ("charge", "subtitles.painorigin.shinra_tensei.charge"),
    "shinra_tensei.release": ("shinra_tensei", "subtitles.painorigin.shinra_tensei.release"),
    "shinra_tensei.shockwave": ("shockwave", "subtitles.painorigin.shinra_tensei.shockwave"),
    "bansho_tenin.pull": ("bansho_tenin", "subtitles.painorigin.bansho_tenin.pull"),
    "chibaku_tensei.core": ("chibaku_core", "subtitles.painorigin.chibaku_tensei.core"),
    "chibaku_tensei.debris": ("chibaku_debris", "subtitles.painorigin.chibaku_tensei.debris"),
    "chibaku_tensei.collapse": ("chibaku_collapse", "subtitles.painorigin.chibaku_tensei.collapse"),
    "universal_defense.block": ("defense", "subtitles.painorigin.universal_defense.block"),
}
write_json(f"assets/{NS}/sounds.json", {
    ev: {"subtitle": sub, "sounds": [{"name": f"{NS}:{f}", "stream": False}]}
    for ev, (f, sub) in SOUND_EVENTS.items()
})
PARTICLES = ["shinra_tensei_wave", "shinra_tensei_burst", "bansho_tenin_aura",
             "chibaku_tensei_core", "chibaku_tensei_debris", "rinnegan_energy"]
for p in PARTICLES:
    write_json(f"assets/{NS}/particles/{p}.json", {"textures": [f"{NS}:{p}"]})

# pack.mcmeta: no '$' characters (Gradle expands this file)
write_json("pack.mcmeta", {"pack": {
    "description": "Deva Path (Six Paths of Pain) origin - resources and data",
    "pack_format": 15,
    "forge:resource_pack_format": 15,
    "forge:data_pack_format": 15,
}})

# ----------------------------------------------------------------------------------------------
# LANGUAGE FILES
# ----------------------------------------------------------------------------------------------
sec = lambda ticks: f"{ticks / 20:g}"
EN = {
    "origin.painorigin.deva_path.name": "Deva Path (Pain)",
    "origin.painorigin.deva_path.description":
        "Bearer of the Rinnegan's Deva Path. You command repulsion and attraction through gravity, at the "
        "price of a frail body and a limited pool of chakra.",
    "power.painorigin.chakra.name": "Chakra",
    "power.painorigin.chakra.description":
        f"A pool of {T['chakra_max']} chakra powers every technique and regenerates about "
        f"{T['chakra_regen_amount'] * 20 // T['chakra_regen_interval']} per second. It is shown as a bar on the HUD.",
    "power.painorigin.shinra_tensei.name": "Shinra Tensei",
    "power.painorigin.shinra_tensei.description":
        f"[Primary key] Release a repulsive shockwave that hurls everything within {T['shinra_radius']:g} blocks away "
        f"and deals light damage. Cost: {T['shinra_cost']} chakra. Cooldown: {sec(T['shinra_cooldown'])} s. Breaks no blocks.",
    "power.painorigin.shinra_tensei_massive.name": "Massive Shinra Tensei",
    "power.painorigin.shinra_tensei_massive.description":
        f"[Sneak + Primary key] Charge for {sec(T['massive_charge'])} s, then unleash a huge repulsion "
        f"({T['massive_radius']:g} blocks, heavy damage). Cost: {T['massive_cost']} chakra. "
        f"Cooldown: {sec(T['massive_cooldown'])} s. Block destruction is OFF by default (server config).",
    "power.painorigin.bansho_tenin.name": "Bansho Ten'in",
    "power.painorigin.bansho_tenin.description":
        f"[Secondary key] Pull the creature you are looking at toward you (up to {T['tenin_range']:g} blocks). "
        f"Targets behind walls cannot be selected. Cost: {T['tenin_cost']} chakra. Cooldown: {sec(T['tenin_cooldown'])} s.",
    "power.painorigin.chibaku_tensei.name": "Chibaku Tensei",
    "power.painorigin.chibaku_tensei.description":
        f"[Sneak + Secondary key] Create a gravity core that drags nearby creatures into a rock-like sphere and "
        f"crushes them. Cost: {T['chibaku_cost']} chakra. Cooldown: {T['chibaku_cooldown'] // 1200} min. Interrupted "
        f"if you die, log out, change dimension or take a heavy hit.",
    "power.painorigin.universal_defense.name": "Universal Defense",
    "power.painorigin.universal_defense.description":
        f"A gravity barrier automatically negates one incoming attack, projectile or explosion "
        f"(max {T['defense_max']} charges, +1 every {T['defense_regen_interval'] // 20} s, costs {T['defense_cost']} chakra each). "
        f"It does not stop falling, drowning, fire, magic, starvation or void damage.",
    "power.painorigin.rinnegan_gravity_field.name": "Rinnegan Gravity Field",
    "power.painorigin.rinnegan_gravity_field.description":
        f"Gravity warps around you: dropped items and experience within {T['field_radius']:g} blocks are drawn toward you.",
    "power.painorigin.gravity_affinity.name": "Gravity Affinity",
    "power.painorigin.gravity_affinity.description": "You fall about 25% slower than normal.",
    "power.painorigin.frail_vessel.name": "Frail Vessel",
    "power.painorigin.frail_vessel.description":
        f"Your body is weak: maximum health reduced by {abs(T['frail_health']):g} ({abs(T['frail_health']) / 2:g} hearts).",
    "painorigin.notice.low_chakra": "Not enough chakra",
    "painorigin.notice.no_target": "No target in sight (blocked by a wall, or out of range)",
    "painorigin.onboarding":
        "Deva Path awakened.\n"
        "Primary key: Shinra Tensei  |  Sneak + Primary: Massive Shinra Tensei\n"
        "Secondary key: Bansho Ten'in  |  Sneak + Secondary: Chibaku Tensei\n"
        "(Bind the Secondary key in Options > Controls > Origins; it is unbound by default.)",
    "painorigin.chibaku.start": "Chibaku Tensei!",
    "painorigin.chibaku.disabled": "Chibaku Tensei is disabled in the server config.",
    "painorigin.chibaku.already_active": "Chibaku Tensei is already active.",
    "painorigin.chibaku.cancelled.command": "Chibaku Tensei cancelled.",
    "painorigin.chibaku.cancelled.death": "Chibaku Tensei interrupted: the caster died.",
    "painorigin.chibaku.cancelled.logout": "Chibaku Tensei interrupted: the caster left the game.",
    "painorigin.chibaku.cancelled.dimension": "Chibaku Tensei interrupted: the caster changed dimension.",
    "painorigin.chibaku.cancelled.damage": "Chibaku Tensei interrupted by a heavy hit.",
    "painorigin.chibaku.cancelled.distance": "Chibaku Tensei interrupted: the caster moved too far from the core.",
    "painorigin.chibaku.cancelled.shutdown": "Chibaku Tensei stopped: the server is shutting down.",
    "painorigin.chibaku.cancelled.invalid": "Chibaku Tensei stopped: the world is no longer available.",
    "painorigin.chibaku.phase.activation": "Chibaku Tensei: gathering gravity...",
    "painorigin.chibaku.phase.core": "Chibaku Tensei: the core forms",
    "painorigin.chibaku.phase.field": "Chibaku Tensei: gravity field active",
    "painorigin.chibaku.phase.debris": "Chibaku Tensei: the earth rises",
    "painorigin.chibaku.phase.formation": "Chibaku Tensei: the satellite takes shape",
    "painorigin.chibaku.phase.final": "Chibaku Tensei: collapse!",
    "painorigin.chibaku.busy": "Too many Chibaku Tensei are active on this server right now.",
    "painorigin.command.not_a_player": "This command must be run by a player.",
    "painorigin.command.massive_blocks": "Massive Shinra Tensei removed %s block(s).",
    "painorigin.command.massive_blocks.disabled": "Block destruction is disabled in the config (default).",
    "painorigin.command.chibaku.none": "No Chibaku Tensei is active for you.",
    "painorigin.command.chibaku.status": "Active Chibaku Tensei instances: %s",
    "painorigin.command.test.ok": "Pain Origin self-test: %s checks passed.",
    "painorigin.command.test.fail": "Pain Origin self-test FAILED: %s",
    "subtitles.painorigin.shinra_tensei.charge": "Gravity gathers",
    "subtitles.painorigin.shinra_tensei.release": "Shinra Tensei",
    "subtitles.painorigin.shinra_tensei.shockwave": "Shockwave",
    "subtitles.painorigin.bansho_tenin.pull": "Bansho Ten'in",
    "subtitles.painorigin.chibaku_tensei.core": "Gravity core hums",
    "subtitles.painorigin.chibaku_tensei.debris": "Rocks grind together",
    "subtitles.painorigin.chibaku_tensei.collapse": "Chibaku Tensei collapses",
    "subtitles.painorigin.universal_defense.block": "Barrier repels an attack",
    "death.attack.painorigin.shinra_tensei": "%1$s was repelled by %2$s's Shinra Tensei",
    "death.attack.painorigin.chibaku_tensei": "%1$s was crushed into %2$s's Chibaku Tensei",
}

TH = {
    "origin.painorigin.deva_path.name": "เทวะมรรค (เพน)",
    "origin.painorigin.deva_path.description":
        "ผู้ครอบครองเทวะมรรคแห่งรินเนกัน ควบคุมแรงผลักและแรงดึงด้วยแรงโน้มถ่วง "
        "แลกกับร่างกายที่อ่อนแอและพลังจักระที่จำกัด",
    "power.painorigin.chakra.name": "จักระ",
    "power.painorigin.chakra.description":
        f"พลังจักระสูงสุด {T['chakra_max']} ใช้กับเทคนิคทุกอย่าง และฟื้นฟูประมาณ "
        f"{T['chakra_regen_amount'] * 20 // T['chakra_regen_interval']} หน่วยต่อวินาที แสดงเป็นแถบบน HUD",
    "power.painorigin.shinra_tensei.name": "ชินระ เท็นเซ (Shinra Tensei)",
    "power.painorigin.shinra_tensei.description":
        f"[ปุ่มหลัก] ปล่อยคลื่นแรงผลักที่ดีดทุกสิ่งในรัศมี {T['shinra_radius']:g} บล็อกออกไป และสร้างความเสียหายเล็กน้อย "
        f"ใช้จักระ {T['shinra_cost']} คูลดาวน์ {sec(T['shinra_cooldown'])} วินาที ไม่ทำลายบล็อก",
    "power.painorigin.shinra_tensei_massive.name": "ชินระ เท็นเซ ขั้นสูงสุด",
    "power.painorigin.shinra_tensei_massive.description":
        f"[กด Shift + ปุ่มหลัก] ชาร์จ {sec(T['massive_charge'])} วินาที แล้วปลดปล่อยแรงผลักมหาศาล "
        f"(รัศมี {T['massive_radius']:g} บล็อก ความเสียหายสูง) ใช้จักระ {T['massive_cost']} "
        f"คูลดาวน์ {sec(T['massive_cooldown'])} วินาที การทำลายบล็อกปิดไว้เป็นค่าเริ่มต้น (ตั้งค่าที่เซิร์ฟเวอร์)",
    "power.painorigin.bansho_tenin.name": "บันโช เท็นอิน (Bansho Ten'in)",
    "power.painorigin.bansho_tenin.description":
        f"[ปุ่มรอง] ดึงสิ่งมีชีวิตที่คุณมองอยู่เข้ามาหาตัว (ไกลสุด {T['tenin_range']:g} บล็อก) "
        f"ไม่สามารถเลือกเป้าหมายที่อยู่หลังกำแพงได้ ใช้จักระ {T['tenin_cost']} คูลดาวน์ {sec(T['tenin_cooldown'])} วินาที",
    "power.painorigin.chibaku_tensei.name": "จิบาคุ เท็นเซ (Chibaku Tensei)",
    "power.painorigin.chibaku_tensei.description":
        f"[กด Shift + ปุ่มรอง] สร้างแกนแรงโน้มถ่วงที่ดึงสิ่งมีชีวิตรอบข้างเข้าสู่ก้อนหินยักษ์แล้วบดขยี้ "
        f"ใช้จักระ {T['chibaku_cost']} คูลดาวน์ {T['chibaku_cooldown'] // 1200} นาที "
        f"จะถูกขัดจังหวะหากคุณตาย ออกจากเกม ข้ามมิติ หรือโดนความเสียหายหนัก",
    "power.painorigin.universal_defense.name": "การป้องกันสากล (Universal Defense)",
    "power.painorigin.universal_defense.description":
        f"เกราะแรงโน้มถ่วงปัดป้องการโจมตี กระสุน หรือการระเบิดอัตโนมัติ 1 ครั้งต่อ 1 ชาร์จ "
        f"(สูงสุด {T['defense_max']} ชาร์จ เพิ่ม 1 ชาร์จทุก {T['defense_regen_interval'] // 20} วินาที ใช้จักระครั้งละ {T['defense_cost']}) "
        f"ป้องกันการตกจากที่สูง จมน้ำ ไฟ เวทมนตร์ ความหิว หรือตกโลกไม่ได้",
    "power.painorigin.rinnegan_gravity_field.name": "สนามแรงโน้มถ่วงรินเนกัน",
    "power.painorigin.rinnegan_gravity_field.description":
        f"แรงโน้มถ่วงรอบตัวบิดเบี้ยว ไอเท็มและค่าประสบการณ์ที่ตกอยู่ในรัศมี {T['field_radius']:g} บล็อกจะถูกดึงเข้าหาคุณ",
    "power.painorigin.gravity_affinity.name": "ความเข้ากันกับแรงโน้มถ่วง",
    "power.painorigin.gravity_affinity.description": "คุณตกลงช้ากว่าปกติประมาณ 25%",
    "power.painorigin.frail_vessel.name": "ร่างกายอ่อนแอ",
    "power.painorigin.frail_vessel.description":
        f"ร่างกายของคุณบอบบาง พลังชีวิตสูงสุดลด {abs(T['frail_health']):g} หน่วย ({abs(T['frail_health']) / 2:g} หัวใจ)",
    "painorigin.notice.low_chakra": "จักระไม่พอ",
    "painorigin.notice.no_target": "ไม่มีเป้าหมายในสายตา (ถูกกำแพงบัง หรืออยู่ไกลเกินไป)",
    "painorigin.onboarding":
        "ปลุกเทวะมรรคแล้ว\n"
        "ปุ่มหลัก: ชินระ เท็นเซ  |  Shift + ปุ่มหลัก: ชินระ เท็นเซ ขั้นสูงสุด\n"
        "ปุ่มรอง: บันโช เท็นอิน  |  Shift + ปุ่มรอง: จิบาคุ เท็นเซ\n"
        "(ตั้งปุ่มรองที่ ตัวเลือก > การควบคุม > Origins เพราะไม่มีปุ่มเริ่มต้น)",
    "painorigin.chibaku.start": "จิบาคุ เท็นเซ!",
    "painorigin.chibaku.disabled": "จิบาคุ เท็นเซ ถูกปิดไว้ในคอนฟิกของเซิร์ฟเวอร์",
    "painorigin.chibaku.already_active": "จิบาคุ เท็นเซ กำลังทำงานอยู่แล้ว",
    "painorigin.chibaku.cancelled.command": "ยกเลิกจิบาคุ เท็นเซ แล้ว",
    "painorigin.chibaku.cancelled.death": "จิบาคุ เท็นเซ ถูกขัดจังหวะ: ผู้ใช้ตาย",
    "painorigin.chibaku.cancelled.logout": "จิบาคุ เท็นเซ ถูกขัดจังหวะ: ผู้ใช้ออกจากเกม",
    "painorigin.chibaku.cancelled.dimension": "จิบาคุ เท็นเซ ถูกขัดจังหวะ: ผู้ใช้ข้ามมิติ",
    "painorigin.chibaku.cancelled.damage": "จิบาคุ เท็นเซ ถูกขัดจังหวะด้วยความเสียหายหนัก",
    "painorigin.chibaku.cancelled.distance": "จิบาคุ เท็นเซ ถูกขัดจังหวะ: ผู้ใช้ห่างจากแกนมากเกินไป",
    "painorigin.chibaku.cancelled.shutdown": "จิบาคุ เท็นเซ หยุดลง: เซิร์ฟเวอร์กำลังปิด",
    "painorigin.chibaku.cancelled.invalid": "จิบาคุ เท็นเซ หยุดลง: ไม่พบโลกที่ใช้งานอยู่",
    "painorigin.chibaku.phase.activation": "จิบาคุ เท็นเซ: รวบรวมแรงโน้มถ่วง...",
    "painorigin.chibaku.phase.core": "จิบาคุ เท็นเซ: แกนกลางก่อตัว",
    "painorigin.chibaku.phase.field": "จิบาคุ เท็นเซ: สนามแรงโน้มถ่วงทำงาน",
    "painorigin.chibaku.phase.debris": "จิบาคุ เท็นเซ: แผ่นดินลอยขึ้น",
    "painorigin.chibaku.phase.formation": "จิบาคุ เท็นเซ: ดาวเทียมหินกำลังก่อรูป",
    "painorigin.chibaku.phase.final": "จิบาคุ เท็นเซ: ถล่ม!",
    "painorigin.chibaku.busy": "ตอนนี้มีจิบาคุ เท็นเซ ทำงานบนเซิร์ฟเวอร์มากเกินไป",
    "painorigin.command.not_a_player": "คำสั่งนี้ต้องสั่งโดยผู้เล่น",
    "painorigin.command.massive_blocks": "ชินระ เท็นเซ ขั้นสูงสุด ทำลายไป %s บล็อก",
    "painorigin.command.massive_blocks.disabled": "การทำลายบล็อกปิดอยู่ในคอนฟิก (ค่าเริ่มต้น)",
    "painorigin.command.chibaku.none": "ไม่มีจิบาคุ เท็นเซ ที่ทำงานอยู่สำหรับคุณ",
    "painorigin.command.chibaku.status": "จำนวนจิบาคุ เท็นเซ ที่กำลังทำงาน: %s",
    "painorigin.command.test.ok": "ทดสอบตัวเองของ Pain Origin: ผ่าน %s รายการ",
    "painorigin.command.test.fail": "ทดสอบตัวเองของ Pain Origin ไม่ผ่าน: %s",
    "subtitles.painorigin.shinra_tensei.charge": "แรงโน้มถ่วงรวมตัว",
    "subtitles.painorigin.shinra_tensei.release": "ชินระ เท็นเซ",
    "subtitles.painorigin.shinra_tensei.shockwave": "คลื่นกระแทก",
    "subtitles.painorigin.bansho_tenin.pull": "บันโช เท็นอิน",
    "subtitles.painorigin.chibaku_tensei.core": "แกนแรงโน้มถ่วงครางกึกก้อง",
    "subtitles.painorigin.chibaku_tensei.debris": "ก้อนหินบดเสียดสีกัน",
    "subtitles.painorigin.chibaku_tensei.collapse": "จิบาคุ เท็นเซ ถล่มลง",
    "subtitles.painorigin.universal_defense.block": "เกราะปัดป้องการโจมตี",
    "death.attack.painorigin.shinra_tensei": "%1$s ถูกผลักกระเด็นด้วยชินระ เท็นเซ ของ %2$s",
    "death.attack.painorigin.chibaku_tensei": "%1$s ถูกบดขยี้ในจิบาคุ เท็นเซ ของ %2$s",
}
assert set(EN) == set(TH), set(EN) ^ set(TH)
write_json(f"assets/{NS}/lang/en_us.json", EN)
write_json(f"assets/{NS}/lang/th_th.json", TH)

print("generated data for", ROOT)

for _arg in sys.argv[2:]:
    if _arg.startswith("--datapack="):
        import shutil
        _out = os.path.abspath(_arg[len("--datapack="):])
        _dst = os.path.join(_out, "data", NS, "powers")
        shutil.rmtree(_dst, ignore_errors=True)
        os.makedirs(os.path.dirname(_dst), exist_ok=True)
        shutil.copytree(os.path.join(RES, "data", NS, "powers"), _dst)
        with open(os.path.join(_out, "pack.mcmeta"), "w", encoding="utf-8") as _f:
            json.dump({"pack": {"description": "Deva Path - tuned power numbers", "pack_format": 15}}, _f, indent=2)
        print("wrote datapack to", _out)

#!/usr/bin/env python3
"""Cross-checks everything that is NOT Java compilation: JSON validity, Apoli type names, resource
locations, language keys, and the agreement between the Java sources and the resource files.

Usage:  validate_project.py [project_root]       (exit code 0 = every check passed)

Checks (each prints PASS/FAIL):
  json         every .json / .mcmeta / .toml parses; pack.mcmeta has no '$' (Gradle expands that file)
  origin       deva_path.json lists only existing powers; every power file is used; origin layer is valid
  types        every "type" in the power JSON is a known Apoli/Origins type name (tools/apoli_types.json)
  refs         sounds, damage types, resources, powers, sprites, tags referenced from JSON exist
  commands     every "painorigin ..." command run by a power is understood by PainCommands.java
  lang         EN/TH have the same keys; every key used by JSON or Java exists (incl. dynamic ones)
  sounds       ModSounds <-> sounds.json <-> .ogg files <-> subtitles <-> JSON play_sound
  particles    ModParticles <-> particles/*.json <-> PNG files (RGBA, transparent border)
  java         PainCommands.POWER_FILES matches the power directory; resource-location strings in Java exist
  build        mods.toml placeholders have a value in gradle.properties; dependency version ranges
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "src", "main", "resources")
JAVA = os.path.join(ROOT, "src", "main", "java")
NS = "painorigin"

failures = []
passes = []


def check(name, ok, detail=""):
    (passes if ok else failures).append(name)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail and not ok else ""))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------------------------
# json
# ---------------------------------------------------------------------------------------------
bad = []
json_files = [p for p in glob.glob(os.path.join(RES, "**", "*"), recursive=True)
              if p.endswith((".json", ".mcmeta"))]
for p in json_files:
    try:
        load(p)
    except Exception as e:  # noqa: BLE001
        bad.append(f"{os.path.relpath(p, ROOT)}: {e}")
check(f"json: {len(json_files)} files parse", not bad, "; ".join(bad))
mcmeta = read(os.path.join(RES, "pack.mcmeta"))
check("json: pack.mcmeta has no '$' and pack_format 15", "$" not in mcmeta and load(os.path.join(RES, "pack.mcmeta"))["pack"]["pack_format"] == 15)

# ---------------------------------------------------------------------------------------------
# origin / powers
# ---------------------------------------------------------------------------------------------
POWER_DIR = os.path.join(RES, "data", NS, "powers")
powers = {os.path.basename(p)[:-5]: load(p) for p in glob.glob(os.path.join(POWER_DIR, "*.json"))}
origin = load(os.path.join(RES, "data", NS, "origins", "deva_path.json"))
listed = [p.split(":", 1)[1] for p in origin["powers"] if p.startswith(NS + ":")]
check("origin: every listed power file exists", all(p in powers for p in listed),
      ", ".join(p for p in listed if p not in powers))
check("origin: every power file is listed (no orphans)", set(powers) == set(listed),
      ", ".join(sorted(set(powers) ^ set(listed))))
layer = load(os.path.join(RES, "data", "origins", "origin_layers", "origin.json"))
check("origin: layer adds painorigin:deva_path", f"{NS}:deva_path" in layer["origins"])
check("origin: onboarding is the last power (its callbacks reset every cooldown)", listed[-1] == "onboarding")

# ---------------------------------------------------------------------------------------------
# types
# ---------------------------------------------------------------------------------------------
types_file = os.path.join(ROOT, "tools", "apoli_types.json")
known = load(types_file)
bad_types = []
used_types = set()


def walk(obj, where):
    if isinstance(obj, dict):
        t = obj.get("type")
        if isinstance(t, str):
            used_types.add(t)
            ns, _, name = t.partition(":")
            pool = known["apoli"] if ns == "apoli" else known["origins"] if ns == "origins" else []
            if name not in pool:
                bad_types.append(f"{where}: {t}")
        for k, v in obj.items():
            walk(v, f"{where}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{where}[{i}]")


for name, data in powers.items():
    walk(data, name)
check(f"types: all {len(used_types)} type names used by the powers exist in Apoli/Origins", not bad_types, "; ".join(bad_types))

# ---------------------------------------------------------------------------------------------
# refs
# ---------------------------------------------------------------------------------------------
sounds_json = load(os.path.join(RES, "assets", NS, "sounds.json"))
damage_types = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(RES, "data", NS, "damage_type", "*.json"))}
bad_refs = []


def refs(obj, where, power_name):
    if isinstance(obj, dict):
        t = obj.get("type", "")
        if t == "apoli:play_sound":
            s = obj.get("sound", "")
            if s.startswith(NS + ":") and s.split(":", 1)[1] not in sounds_json:
                bad_refs.append(f"{where}: sound {s} is not in sounds.json")
        if "damage_type" in obj:
            d = obj["damage_type"]
            if d.startswith(NS + ":") and d.split(":", 1)[1] not in damage_types:
                bad_refs.append(f"{where}: damage type {d} has no data/{NS}/damage_type file")
        if t == "apoli:resource" and "resource" in obj:
            r = obj["resource"]
            if r.startswith(NS + ":") and r.split(":", 1)[1] not in powers:
                bad_refs.append(f"{where}: resource {r} is not a power")
        if t == "apoli:change_resource" and "resource" in obj:
            r = obj["resource"]
            if r.startswith(NS + ":") and r.split(":", 1)[1] not in powers:
                bad_refs.append(f"{where}: resource {r} is not a power")
        if t == "apoli:power" and "power" in obj:
            r = obj["power"]
            if r.startswith(NS + ":") and r.split(":", 1)[1] not in powers:
                bad_refs.append(f"{where}: power {r} does not exist")
        if "sprite_location" in obj:
            s = obj["sprite_location"]
            ns, _, path = s.partition(":")
            if ns == NS and not os.path.isfile(os.path.join(RES, "assets", NS, path)):
                bad_refs.append(f"{where}: sprite {s} is missing")
        for k, v in obj.items():
            refs(v, f"{where}/{k}", power_name)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            refs(v, f"{where}[{i}]", power_name)


for name, data in powers.items():
    refs(data, name, name)
check("refs: sounds / damage types / resources / powers / sprites referenced by the powers exist", not bad_refs, "; ".join(bad_refs))

tag_ok = True
tag_files = glob.glob(os.path.join(RES, "data", "**", "tags", "**", "*.json"), recursive=True)
for p in tag_files:
    d = load(p)
    vals = d.get("values")
    if not isinstance(vals, list) or not all(isinstance(v, str) or (isinstance(v, dict) and "id" in v) for v in vals):
        tag_ok = False
check(f"refs: {len(tag_files)} tag files have a valid 'values' list", tag_ok)
check("refs: tags are in the 1.20.1 plural folders (tags/blocks, tags/entity_types, tags/damage_type)",
      all(re.search(r"/tags/(blocks|entity_types|damage_type)/", p.replace(os.sep, "/")) for p in tag_files))
dmg_ok = all({"message_id", "scaling", "exhaustion"} <= set(load(p)) for p in glob.glob(os.path.join(RES, "data", NS, "damage_type", "*.json")))
check("refs: damage type files have message_id / scaling / exhaustion", dmg_ok)

# ---------------------------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------------------------
cmd_src = read(os.path.join(JAVA, "com", "painorigin", "PainCommands.java"))
en_keys_for_commands = set(load(os.path.join(RES, "assets", NS, "lang", "en_us.json")))
literals = set(re.findall(r'Commands\.literal\("(\w+)"\)', cmd_src))
bad_cmd = []
cmd_strings = []


def collect_cmds(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "apoli:execute_command":
            cmd_strings.append(obj["command"])
        for k in ("command_along_ray", "command_at_hit"):
            if isinstance(obj.get(k), str) and obj[k]:
                cmd_strings.append(obj[k])
        for v in obj.values():
            collect_cmds(v)
    elif isinstance(obj, list):
        for v in obj:
            collect_cmds(v)


for data in powers.values():
    collect_cmds(data)
vanilla_ok = 0
for c in cmd_strings:
    words = c.split()
    if words[0] == "tellraw" or words[:3] == ["title", "@s", "actionbar"]:
        # feedback messages: "tellraw @s {json}" / "title @s actionbar {json}" - the text component must be
        # valid JSON whose translation key exists in the language file
        payload = c.split(" ", 2)[2] if words[0] == "tellraw" else c.split(" ", 3)[3]
        try:
            comp = json.loads(payload)
            if comp.get("translate") not in en_keys_for_commands:
                bad_cmd.append(f"{c!r}: unknown translation key")
            else:
                vanilla_ok += 1
        except Exception as e:  # noqa: BLE001
            bad_cmd.append(f"{c!r}: text component is not valid JSON ({e})")
        continue
    if words[0] != NS:
        bad_cmd.append(f"{c!r}: unexpected command")
        continue
    for w in words[1:]:
        if re.fullmatch(r"-?\d+(\.\d+)?", w):
            continue
        if w not in literals:
            bad_cmd.append(f"{c!r}: unknown word {w!r}")
check(f"commands: {len(cmd_strings)} commands run by the powers are understood ({len(cmd_strings) - vanilla_ok} /painorigin ones use only the words {', '.join(sorted(literals))}; {vanilla_ok} are tellraw/title feedback with valid text components)",
      not bad_cmd, "; ".join(bad_cmd))
check("commands: /painorigin requires permission level 2", "hasPermission(2)" in cmd_src)

# ---------------------------------------------------------------------------------------------
# lang
# ---------------------------------------------------------------------------------------------
en = load(os.path.join(RES, "assets", NS, "lang", "en_us.json"))
th = load(os.path.join(RES, "assets", NS, "lang", "th_th.json"))
check("lang: en_us and th_th have identical keys", set(en) == set(th), ", ".join(sorted(set(en) ^ set(th))))
check("lang: no empty strings", all(v.strip() for v in en.values()) and all(v.strip() for v in th.values()))
need = {f"origin.{NS}.deva_path.name", f"origin.{NS}.deva_path.description"}
for p in listed:
    if p.startswith(("notice_", "onboarding", "chakra_regen", "defense_charges", "defense_regen", "rinnegan_aura")):
        continue  # hidden helper powers
    need |= {f"power.{NS}.{p}.name", f"power.{NS}.{p}.description"}
check("lang: name + description exist for the origin and every visible power", need <= set(en), ", ".join(sorted(need - set(en))))

all_json_text = "\n".join(json.dumps(d) for d in powers.values())
json_keys = set(re.findall(r'"(painorigin\.[a-z_.]+)"', all_json_text))
check("lang: every key used by the power JSON exists", json_keys <= set(en), ", ".join(sorted(json_keys - set(en))))

java_text = "\n".join(read(p) for p in glob.glob(os.path.join(JAVA, "**", "*.java"), recursive=True))
java_keys = set(re.findall(r'"(painorigin\.[a-z_.]+)"', java_text))
static_java = {k for k in java_keys if not k.endswith(".")}
dyn_prefix = {k for k in java_keys if k.endswith(".")}
missing = sorted(static_java - set(en))
check("lang: every literal key used by the Java sources exists", not missing, ", ".join(missing))
reasons = set(re.findall(r'cancel(?:For|All)?\([^;]*?"(\w+)"\)', java_text)) | set(re.findall(r'"(\w+)"\s*\)\s*;?\s*//\s*cancel-reason', java_text))
reasons |= set(re.findall(r'\bcancel\(\w+,\s*"(\w+)"\)', java_text))
reasons |= {k.rsplit(".", 1)[1] for k in en if k.startswith("painorigin.chibaku.cancelled.")}
phases = set(re.findall(r'\b[A-Z]+\("(\w+)"\)', read(os.path.join(JAVA, "com", "painorigin", "ChibakuManager.java"))))
dyn_missing = []
for pref in dyn_prefix:
    if pref == "painorigin.chibaku.cancelled.":
        dyn_missing += [pref + r for r in re.findall(r'cancel\w*\([^)]*"(\w+)"', java_text) if pref + r not in en]
    if pref == "painorigin.chibaku.phase.":
        dyn_missing += [pref + ph for ph in phases if pref + ph not in en]
check("lang: dynamic keys (Chibaku phases / cancel reasons) all exist", not dyn_missing, ", ".join(dyn_missing))

# ---------------------------------------------------------------------------------------------
# sounds
# ---------------------------------------------------------------------------------------------
ms = read(os.path.join(JAVA, "com", "painorigin", "ModSounds.java"))
registered = set(re.findall(r'\breg\("([\w.]+)"', ms))
check(f"sounds: ModSounds registers exactly the {len(sounds_json)} events of sounds.json", registered == set(sounds_json),
      ", ".join(sorted(registered ^ set(sounds_json))))
bad_snd = []
for ev, body in sounds_json.items():
    for s in body["sounds"]:
        name = s["name"].split(":", 1)[1]
        if not os.path.isfile(os.path.join(RES, "assets", NS, "sounds", name + ".ogg")):
            bad_snd.append(f"{ev}: missing sounds/{name}.ogg")
    if body.get("subtitle") not in en:
        bad_snd.append(f"{ev}: subtitle key missing in lang")
check("sounds: every sound event has its .ogg file and subtitle", not bad_snd, "; ".join(bad_snd))
ogg_ok = True
for p in glob.glob(os.path.join(RES, "assets", NS, "sounds", "*.ogg")):
    with open(p, "rb") as f:
        ogg_ok &= f.read(4) == b"OggS"
check("sounds: every .ogg starts with the OggS magic", ogg_ok)

# ---------------------------------------------------------------------------------------------
# particles
# ---------------------------------------------------------------------------------------------
mp = read(os.path.join(JAVA, "com", "painorigin", "ModParticles.java"))
types_reg = set(re.findall(r'simple\("(\w+)"\)', mp))
pjson = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(RES, "assets", NS, "particles", "*.json"))}
ptex = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(RES, "assets", NS, "textures", "particle", "*.png"))}
check(f"particles: ModParticles ({len(types_reg)}) = particles/*.json = textures/particle/*.png", types_reg == pjson == ptex,
      f"{sorted(types_reg ^ pjson)} {sorted(pjson ^ ptex)}")
bad_pj = [n for n in pjson if load(os.path.join(RES, "assets", NS, "particles", n + ".json")) != {"textures": [f"{NS}:{n}"]}]
check("particles: each definition points at its own texture", not bad_pj, ", ".join(bad_pj))
try:
    from PIL import Image
    import numpy as np
    png_bad = []
    for n in sorted(ptex):
        im = Image.open(os.path.join(RES, "assets", NS, "textures", "particle", n + ".png"))
        a = np.array(im.convert("RGBA"))[..., 3]
        border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
        if im.mode != "RGBA" or border.max() != 0 or (a == 0).mean() < 0.05 or ((a > 0) & (a < 255)).mean() < 0.01:
            png_bad.append(f"{n} mode={im.mode} border_alpha={border.max()}")
    check("particles: PNGs are real RGBA with a fully transparent border and soft alpha", not png_bad, "; ".join(png_bad))
except ImportError:
    print("SKIP  particles: PNG alpha check (install Pillow and numpy to enable it)")

# ---------------------------------------------------------------------------------------------
# java <-> resources
# ---------------------------------------------------------------------------------------------
pf = re.search(r"POWER_FILES\s*=\s*\{([^}]*)\}", cmd_src, re.S)
if pf:
    java_powers = set(re.findall(r'"(\w+)"', pf.group(1)))
    check("java: PainCommands.POWER_FILES = the power directory", java_powers == set(powers), ", ".join(sorted(java_powers ^ set(powers))))
else:
    check("java: PainCommands.POWER_FILES found", False)
bad_ids = []
for m in re.finditer(r'"(painorigin:[\w/.]+)"', java_text):
    rid = m.group(1)
    name = rid.split(":", 1)[1]
    if name in powers or name in damage_types or name in sounds_json or name in types_reg:
        continue
    if name in ("glow_additive", "soft_alpha"):  # toString() names of the two particle render types
        continue
    if os.path.isfile(os.path.join(RES, "data", NS, "tags", "blocks", name + ".json")) or \
            os.path.isfile(os.path.join(RES, "data", NS, "tags", "entity_types", name + ".json")):
        continue
    bad_ids.append(rid)
check("java: every \"painorigin:...\" id in the sources has a matching file", not bad_ids, ", ".join(sorted(set(bad_ids))))

# ---------------------------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------------------------
props = dict(re.findall(r"^(\w+)\s*=\s*(.*)$", read(os.path.join(ROOT, "gradle.properties")), re.M))
toml = read(os.path.join(RES, "META-INF", "mods.toml"))
ph = set(re.findall(r"\$\{(\w+)\}", toml))
check("build: every ${placeholder} in mods.toml has a value in gradle.properties", ph <= set(props), ", ".join(sorted(ph - set(props))))
check("build: mods.toml requires origins, apoli and calio",
      all(re.search(r'modId\s*=\s*"%s"' % m, toml) for m in ("origins", "apoli", "calio")))
check("build: mod id is painorigin in gradle.properties and PainOrigin.java",
      props.get("mod_id") == NS and f'MODID = "{NS}"' in read(os.path.join(JAVA, "com", "painorigin", "PainOrigin.java")))

print()
print(f"{len(passes)} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)

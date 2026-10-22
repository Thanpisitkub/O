#!/usr/bin/env python3
"""Cross-checks the Minecraft / Forge API names used by the Java sources against REAL 1.20.1 sources.

There is no Minecraft jar here, so the sources cannot be compiled (see check_java.py).  As the next best
thing this script takes one or more directories of real mod / Forge 1.20.1 Java sources (Mojang mappings;
the author used GitHub clones of Forge 1.20.1, Botania, Iron's Spells 'n Spellbooks, Apoli, Calio and
Origins) and reports:

  1. IMPORT      every ``net.minecraft*`` / ``net.minecraftforge*`` / ``com.mojang*`` / ``org.lwjgl*`` /
                 ``org.joml*`` import that appears in none of the corpus files (class may not exist
                 under that name);
  2. STATIC      every ``Type.member(`` / ``Type.FIELD`` use of an external type that never appears in
                 the corpus in that exact form;
  3. MEMBER      every ``.name(`` / ``.name`` that appears nowhere in the corpus and is neither defined
                 by the add-on itself nor a well-known JDK name.

This proves that a name is used by other real 1.20.1 code; it does NOT prove the argument types or that
the member belongs to the receiver type - treat every line it prints as 'look at this one by hand'.
Everything else still needs a real ``./gradlew build`` and a test in game.

Usage:  verify_api.py <project_root> <corpus_dir> [<corpus_dir> ...]
"""
import os
import re
import sys

ROOT = os.path.abspath(sys.argv[1])
CORPORA = sys.argv[2:]
if not CORPORA:
    sys.exit(__doc__)

EXTERNAL = ("net.minecraft.", "net.minecraftforge.", "com.mojang.", "org.lwjgl.", "org.joml.")

JDK_NAMES = set("""
get set add remove put contains containsKey isEmpty size clear iterator hasNext next forEach stream filter map
collect toList of copyOf asList sort sorted reversed removeIf entrySet keySet values getKey getValue computeIfAbsent
getOrDefault putIfAbsent equals hashCode toString length charAt substring startsWith endsWith indexOf split trim
format valueOf parseInt parseDouble min max abs floor ceil sqrt sin cos atan2 pow round random nextInt nextDouble
nextFloat nextBoolean nextLong signum hypot toRadians toDegrees addAll isPresent orElse ifPresent orElseThrow
getName getSimpleName getClass compare compareTo intValue doubleValue floatValue longValue booleanValue
append insert reverse replace lines join matches isBlank strip toUpperCase toLowerCase
requireNonNull ofNullable empty emptyList emptyMap singletonList unmodifiableList unmodifiableSet
log info warn error debug getLogger getAsInt getAsDouble nanoTime currentTimeMillis
""".split())

# ---------------------------------------------------------------------------------------------
# corpus index
# ---------------------------------------------------------------------------------------------
corpus_text = []
corpus_imports = set()
corpus_class_paths = set()
call_names = set()
dotted = set()      # "Type.name" pairs (also used for Type.name( )
member_names = set()
n_files = 0
for base in CORPORA:
    for d, _dirs, names in os.walk(base):
        if "/.git" in d:
            continue
        for n in names:
            if not n.endswith(".java"):
                continue
            path = os.path.join(d, n)
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            m = re.search(r"(?:^|/)(net/minecraftforge/[\w/]+)\.java$", rel)
            if m:
                corpus_class_paths.add(m.group(1).replace("/", "."))
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            n_files += 1
            for im in re.finditer(r"^import\s+(?:static\s+)?([\w.]+)(?:\.\*)?;", text, re.M):
                corpus_imports.add(im.group(1))
            for c in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", text):
                call_names.add(c.group(1))
            for dm in re.finditer(r"\b([A-Z]\w*)\.([A-Za-z_]\w*)", text):
                dotted.add((dm.group(1), dm.group(2)))
            for mm in re.finditer(r"\.([A-Za-z_]\w*)", text):
                member_names.add(mm.group(1))
print(f"corpus: {n_files} java files, {len(corpus_imports)} distinct imports, {len(call_names)} call names")

# ---------------------------------------------------------------------------------------------
# the add-on's own sources
# ---------------------------------------------------------------------------------------------
files = []
for d, _dirs, names in os.walk(os.path.join(ROOT, "src", "main", "java")):
    for n in names:
        if n.endswith(".java"):
            files.append(os.path.join(d, n))
files.sort()


def strip(src):
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    src = re.sub(r"^(package|import)\s[^;]*;", "", src, flags=re.M)
    return src


own_defs = set()
own_src = {}
for f in files:
    raw = open(f, encoding="utf-8").read()
    src = strip(raw)
    own_src[f] = src
    for m in re.finditer(r"\b(?:class|interface|enum|record)\s+(\w+)", src):
        own_defs.add(m.group(1))
    for m in re.finditer(r"\benum\s+\w+\s*\{([^;}]*)", src):
        for const in m.group(1).split(","):
            const = const.strip()
            if const:
                own_defs.add(re.match(r"\w+", const).group(0))
    # methods and fields declared by the add-on
    for m in re.finditer(r"[\w>\]]\s+(\w+)\s*(?:\(|=|;)", src):
        own_defs.add(m.group(1))

# Names that are real but happen to be absent from the corpus directories; each was checked by hand against
# the source named here (an actual 1.20.1-era source / the library's own source), not from memory.
VERIFIED_BY_HAND = {
    "net.minecraft.core.particles.SimpleParticleType": "Forge docs gameeffects/particles.md; AE2 VibrantFX, BiomesOPlenty NullParticle",
    "com.mojang.brigadier.arguments.DoubleArgumentType": "Mojang/brigadier source: doubleArg(double,double), getDouble(CommandContext<?>,String)",
    "DoubleArgumentType.doubleArg": "Mojang/brigadier source (same file)",
    "DoubleArgumentType.getDouble": "Mojang/brigadier source (same file)",
    "ChunkPos.asLong": "CraftBukkit v1_20_R1 CraftChunk (1.20.1 NMS, Mojang names): ChunkPos.asLong(x, z)",
    "RenderSystem.enableCull": "BleachHack Renderer, HBM-Modernized RenderStateGuard (disableCull/enableCull pair)",
    "Heightmap.Types.MOTION_BLOCKING_NO_LEAVES": "Ice and Fire DragonUtils / Tough As Nails AreaFill: level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, pos)",
    "MOTION_BLOCKING_NO_LEAVES": "same as Heightmap.Types.MOTION_BLOCKING_NO_LEAVES above",
    "doubleArg": "same as DoubleArgumentType.doubleArg above",
    "enableCull": "same as RenderSystem.enableCull above",
    "rCol": "DivineRPG ParticleSparkler, Galacticraft AcidVaporParticle: this.rCol/gCol/bCol in TextureSheetParticle subclasses",
    "gCol": "same", "bCol": "same",
    "oRoll": "BiomesOPlenty LeafParticle, Alex's Mobs ParticlePlatypus: this.oRoll = this.roll",
    "roll": "same",
    "quadSize": "Roots SmokeParticle / FogParticle: this.quadSize = ...",
}
hand_used = set()

problems = 0
print("\n== 1. IMPORT")
for f in files:
    for m in re.finditer(r"^import\s+(static\s+)?([\w.]+);", own_src[f] if False else open(f, encoding="utf-8").read(), re.M):
        fqn = m.group(2)
        if not fqn.startswith(EXTERNAL):
            continue
        ok = fqn in corpus_imports or fqn in corpus_class_paths
        if not ok:
            # an import of a nested type is fine if the outer type is imported somewhere
            ok = any(c.startswith(fqn + ".") for c in corpus_imports)
        if not ok and fqn in VERIFIED_BY_HAND:
            hand_used.add(fqn)
            ok = True
        if not ok:
            problems += 1
            print(f"  NOT FOUND  {fqn}   ({os.path.relpath(f, ROOT)})")
if problems == 0:
    print("  every external import occurs in the corpus")

print("\n== 2. STATIC / qualified use  (Type.member where Type is an imported external type)")
checked = 0
missing = []
for f in files:
    src = own_src[f]
    imp = {}
    for m in re.finditer(r"^import\s+(?:static\s+)?([\w.]+);", open(f, encoding="utf-8").read(), re.M):
        fqn = m.group(1)
        if fqn.startswith(EXTERNAL):
            imp[fqn.rsplit(".", 1)[-1]] = fqn
    for m in re.finditer(r"\b([A-Z]\w*)\.([A-Za-z_]\w*)", src):
        t, name = m.group(1), m.group(2)
        if t not in imp:
            continue
        checked += 1
        if (t, name) in dotted:
            continue
        # nested type reference such as Mod.EventBusSubscriber.Bus -> name is a type: accept if corpus imports it
        if any(i.endswith("." + t + "." + name) or i.endswith("." + name) for i in corpus_imports):
            continue
        if f"{t}.{name}" in VERIFIED_BY_HAND:
            hand_used.add(f"{t}.{name}")
            continue
        line = src.count("\n", 0, m.start()) + 1
        missing.append((os.path.relpath(f, ROOT), line, f"{t}.{name}"))
print(f"  {checked} qualified uses checked")
seen = set()
for rel, line, what in missing:
    if what in seen:
        continue
    seen.add(what)
    problems += 1
    print(f"  NOT IN CORPUS  {what}   ({rel}:{line})")

print("\n== 3. MEMBER names (.name( and .name) found nowhere in the corpus")
unmatched = {}
for f in files:
    src = own_src[f]
    for m in re.finditer(r"\.\s*([A-Za-z_]\w*)\s*(\()?", src):
        name = m.group(1)
        is_call = bool(m.group(2))
        if name in own_defs or name in JDK_NAMES:
            continue
        pool = call_names if is_call else member_names
        if name in pool or name in member_names or name in call_names:
            continue
        if name in VERIFIED_BY_HAND:
            hand_used.add(name)
            continue
        line = src.count("\n", 0, m.start()) + 1
        unmatched.setdefault(name, (os.path.relpath(f, ROOT), line))
for name, (rel, line) in sorted(unmatched.items()):
    problems += 1
    print(f"  NOT IN CORPUS  .{name}   ({rel}:{line})")
if not unmatched:
    print("  every member name occurs in the corpus (or in the add-on / JDK)")

print("\n== verified by hand against a real source (not found in the corpus directories)")
for k in sorted(hand_used):
    print(f"  {k}: {VERIFIED_BY_HAND[k]}")
print(f"\nSUMMARY: {problems} line(s) to look at by hand")
sys.exit(0)

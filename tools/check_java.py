#!/usr/bin/env python3
"""Static check of the Java sources WITHOUT Minecraft/Forge on the class path.

What this is - and what it is not
---------------------------------
This is NOT a build.  The real build needs ForgeGradle, the Minecraft jars and Forge, which have to be
downloaded; run ``./gradlew build`` for that.  This script only runs plain ``javac --release 17`` over the
sources.  javac parses every file first, so:

* every SYNTAX error (missing ``;``, unbalanced braces, bad ``switch`` ...) is reported as a real error;
* every unresolved Minecraft / Forge / Mojang / LWJGL class is reported by javac too - those are EXPECTED
  and are filtered out here, because the jars are not available;
* everything else javac can still check is reported as REAL: typos in local variables, calls to methods
  that do not exist in the add-on's OWN classes, wrong argument counts to own methods, missing returns,
  uninitialised final fields, a class that is used but never imported, ...

It cannot check that a Minecraft/Forge method really exists with the signature that is used; that is what
``verify_api.py`` (cross-check against real 1.20.1 sources) and the in-game ``/painorigin test`` are for.

Usage:  check_java.py [project_root]       (exit code 0 = no REAL errors)
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src", "main", "java")
EXTERNAL_PREFIXES = ("net.minecraft.", "net.minecraftforge.", "com.mojang.", "org.lwjgl.", "org.slf4j.",
                     "org.joml.", "com.google.", "it.unimi.", "io.netty.", "org.apache.", "com.electronwill.")

files = []
for base, _dirs, names in os.walk(SRC):
    for n in names:
        if n.endswith(".java"):
            files.append(os.path.join(base, n))
files.sort()

# ---------------------------------------------------------------------------------------------
# 1. javac
# ---------------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as out:
    # -XDshould-stop.ifError=FLOW: by default javac skips flow analysis (missing return, uninitialised finals,
    # definite assignment, unreachable code) as soon as ANY symbol error exists; this keeps it running.
    cmd = ["javac", "--release", "17", "-proc:none", "-XDshould-stop.ifError=FLOW", "-Xmaxerrs", "100000",
           "-encoding", "UTF-8", "-d", out] + files
    proc = subprocess.run(cmd, capture_output=True, text=True)
text = proc.stderr

# ---------------------------------------------------------------------------------------------
# 2. parse javac output into records
# ---------------------------------------------------------------------------------------------
records = []
cur = None
for line in text.splitlines():
    m = re.match(r"^(.*\.java):(\d+): (error|warning): (.*)$", line)
    if m:
        cur = dict(file=m.group(1), line=int(m.group(2)), kind=m.group(3), msg=m.group(4), extra=[])
        records.append(cur)
    elif cur is not None:
        cur["extra"].append(line)

# per-file info: imports and own declared types
imports = {}      # file -> {simple name -> fqn}
own_types = {}    # simple names of every top level / nested type declared in the project
for f in files:
    src = open(f, encoding="utf-8").read()
    imp = {}
    for m in re.finditer(r"^import\s+(static\s+)?([\w.]+?)(\.\*)?;", src, re.M):
        fqn = m.group(2)
        imp[fqn.rsplit(".", 1)[-1]] = fqn
    imports[f] = imp
    for m in re.finditer(r"\b(?:class|interface|enum|record)\s+(\w+)", src):
        own_types[m.group(1)] = f

JAVA_LANG = {"Object", "String", "Math", "Integer", "Long", "Double", "Float", "Boolean", "Character", "Byte",
             "Short", "Number", "Exception", "RuntimeException", "Throwable", "Override", "Deprecated", "System",
             "Runnable", "Iterable", "Comparable", "Class", "Enum", "Record", "Void", "StringBuilder", "Thread",
             "FunctionalInterface", "SuppressWarnings", "SafeVarargs", "Error", "IllegalArgumentException",
             "IllegalStateException", "NullPointerException", "UnsupportedOperationException", "CharSequence",
             "AutoCloseable", "Process", "ThreadLocal", "InterruptedException", "ArithmeticException"}


# Members that the particle classes use from their Minecraft ancestors (Mojang names, 1.20.1:
# Particle -> SingleQuadParticle -> TextureSheetParticle).  javac cannot see them because the ancestor is
# not on the class path, so they are checked by NAME against this list, and verify_api.py then checks that
# every name on the list really occurs in real 1.20.1 mod/Forge sources.
INHERITED_OK = {
    "x", "y", "z", "xo", "yo", "zo", "xd", "yd", "zd", "age", "lifetime", "gravity", "hasPhysics",
    "rCol", "gCol", "bCol", "alpha", "roll", "oRoll", "quadSize", "level", "random",
    "remove", "setPos", "setColor", "pickSprite", "getU0", "getU1", "getV0", "getV1", "getLightColor",
    "getRenderType", "tick", "render", "shouldCull",
}

# own class -> simple name of its superclass (from "extends")
extends_of = {}
for _f in files:
    _src = open(_f, encoding="utf-8").read()
    for _m in re.finditer(r"\bclass\s+(\w+)(?:<[^>]*>)?\s+extends\s+(\w+)", _src):
        extends_of[_m.group(1)] = (_m.group(2), _f)


def has_external_ancestor(cls):
    seen = set()
    while cls in extends_of and cls not in seen:
        seen.add(cls)
        parent, f = extends_of[cls]
        if is_external_import(f, parent):
            return True
        cls = parent
    return False


def is_external_import(f, simple):
    fqn = imports[f].get(simple)
    return fqn is not None and fqn.startswith(EXTERNAL_PREFIXES)


expected = []
inherited = []
real = []
override_review = []
for r in records:
    if r["kind"] != "error":
        continue
    f, msg, extra = r["file"], r["msg"], r["extra"]
    src_line = extra[0].strip() if extra else ""
    if msg.startswith("package ") and msg.endswith(" does not exist"):
        pkg = msg[len("package "):-len(" does not exist")]
        if pkg.startswith(EXTERNAL_PREFIXES) or src_line.startswith("import ") and re.match(
                r"import\s+(static\s+)?(" + "|".join(re.escape(p) for p in EXTERNAL_PREFIXES) + ")", src_line):
            expected.append(r)
            continue
        # nested class of an unresolved external type used as a qualifier, e.g. ForgeConfigSpec.BooleanValue
        head = pkg.split(".")[0]
        if is_external_import(f, head):
            expected.append(r)
            continue
        real.append(r)
        continue
    if msg == "cannot find symbol":
        sym = next((e.strip() for e in extra if e.strip().startswith("symbol:")), "")
        m = re.match(r"symbol:\s+(class|variable|method|interface)\s+(\w+)", sym)
        if m:
            kind, name = m.group(1), m.group(2)
            if kind in ("class", "interface", "variable") and is_external_import(f, name):
                expected.append(r)
                continue
            if kind in ("variable", "method") and (name in INHERITED_OK or name == "super"):
                loc = next((e.strip() for e in extra if e.strip().startswith("location:")), "")
                lm = re.match(r"location:\s+(?:class|interface)\s+([\w.]+)", loc)
                if lm:
                    cls = lm.group(1).split(".")[0]
                else:  # javac prints no location for "this.x"; use the file's top-level class
                    cls = os.path.splitext(os.path.basename(f))[0]
                member = name
                if name == "super":  # "super.render(...)": check the called method name instead
                    sm = re.search(r"super\.(\w+)", src_line)
                    member = sm.group(1) if sm else name
                if member in INHERITED_OK and has_external_ancestor(cls):
                    inherited.append(r)
                    continue
            if kind == "class" and name not in imports[f] and name not in own_types and name not in JAVA_LANG:
                # used but never imported
                r["why"] = f"class {name} is used but not imported"
                real.append(r)
                continue
            if kind == "class" and name in own_types:
                r["why"] = f"own class {name} is not visible here (missing import?)"
                real.append(r)
                continue
        real.append(r)
        continue
    if msg == "method does not override or implement a method from a supertype":
        override_review.append(r)
        continue
    real.append(r)

# ---------------------------------------------------------------------------------------------
# 3. @Override review: methods whose parent class is external can not be checked by javac
# ---------------------------------------------------------------------------------------------
own_method_names = {}
for f in files:
    src = open(f, encoding="utf-8").read()
    for m in re.finditer(r"\b(?:public|protected|private|static|final|abstract|\s)+[\w<>\[\],.? ]+\s+(\w+)\s*\(", src):
        own_method_names.setdefault(m.group(1), set()).add(f)
override_bad = []
for r in override_review:
    # the line after @Override is the method declaration (the error is reported on the annotation line)
    src_lines = open(r["file"], encoding="utf-8").read().splitlines()
    decl = ""
    for k in range(r["line"], min(r["line"] + 4, len(src_lines))):
        m = re.search(r"\b(\w+)\s*\(", src_lines[k])
        if m:
            decl = m.group(1)
            break
    cls_src = "\n".join(src_lines)
    ext = re.search(r"class\s+\w+(?:<[^>]*>)?\s+extends\s+(\w+)", cls_src)
    ext_name = ext.group(1) if ext else None
    implements = re.findall(r"implements\s+([\w<>, .]+)\{", cls_src)
    r["method"] = decl
    r["extends"] = ext_name
    # fine when the class has any external ancestor (or implements an external interface)
    ancestors_external = (ext_name and (is_external_import(r["file"], ext_name) or ext_name in own_types))
    iface_external = any(is_external_import(r["file"], re.split(r"[<,\s]", i.strip())[0]) for i in implements for i in i.split(",") if i.strip())
    if ancestors_external or iface_external:
        continue
    override_bad.append(r)

# ---------------------------------------------------------------------------------------------
# 4. unused imports (cosmetic)
# ---------------------------------------------------------------------------------------------
unused = []
for f in files:
    src = open(f, encoding="utf-8").read()
    body = re.sub(r"^import .*$", "", src, flags=re.M)
    body = re.sub(r"/\*.*?\*/", lambda m: m.group(0) if "{@" in m.group(0) else "", body, flags=re.S)
    for simple, fqn in imports[f].items():
        if simple == "*":
            continue
        if not re.search(r"\b" + re.escape(simple) + r"\b", body):
            unused.append((os.path.relpath(f, ROOT), fqn))

# ---------------------------------------------------------------------------------------------
# 5. report
# ---------------------------------------------------------------------------------------------
print(f"files checked              : {len(files)}")
print(f"javac errors total         : {sum(1 for r in records if r['kind'] == 'error')}")
print(f"  expected (external API)  : {len(expected)}  (Minecraft/Forge/Mojang classes are not on the path)")
print(f"  inherited Particle members: {len(inherited)}  (names checked against INHERITED_OK, see verify_api.py)")
print(f"  @Override on external API: {len(override_review)}  ({len(override_review) - len(override_bad)} fine, {len(override_bad)} to review)")
print(f"  REAL                     : {len(real)}")
print(f"unused imports             : {len(unused)}")
for r in real:
    print(f"REAL  {os.path.relpath(r['file'], ROOT)}:{r['line']}: {r['msg']}  {r.get('why', '')}")
    for e in r["extra"][:3]:
        print("        " + e.rstrip())
for r in override_bad:
    print(f"REVIEW @Override {os.path.relpath(r['file'], ROOT)}:{r['line']} method {r['method']} (class extends {r['extends']})")
for f, fqn in unused:
    print(f"UNUSED import {fqn}  in {f}")
bad = bool(real or override_bad)
print("RESULT:", "FAIL" if bad else "OK (no syntax/own-code errors found; this is NOT a compile against Minecraft/Forge)")
sys.exit(1 if bad else 0)

"""Runs the EFPSE Bridge write commands on a temporary copy of a project and checks the results.
Usage: python test_efpse.py <engine folder> <project>
Your project is copied to Projects\\EfpseTest, tested there and the copy is deleted afterwards."""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
engine, source = sys.argv[1], sys.argv[2]
COPY = "EfpseTest"
path = os.path.join(engine, "Projects", COPY)
env = dict(os.environ, EFPSE_ENGINE=engine, EFPSE_PROJECT=COPY, PYTHONIOENCODING="utf8")
failed = 0


def run(*a):
    r = subprocess.run([sys.executable, os.path.join(HERE, "efpse.py"), *a], capture_output=True, env=env)
    return r.returncode, r.stdout.decode("utf8", "replace") + r.stderr.decode("utf8", "replace")


def as_json(s):
    try:
        return json.loads(s)
    except ValueError:
        return {}


def expect(name, ok, extra=""):
    global failed
    print(("pass " if ok else "FAIL ") + name + ("" if ok else "  " + extra[-400:]))
    failed += 0 if ok else 1


# the bridge refuses writes while the editor runs: say so instead of failing every step
tl = subprocess.run(["tasklist", "/FI", "IMAGENAME eq EasyFPSEditor_CE.exe"], capture_output=True, text=True).stdout
if "EasyFPSEditor_CE.exe" in tl:
    raise SystemExit("Close Easy FPS Editor first: the bridge does not write while the editor is open.")
if os.path.exists(path):
    shutil.rmtree(path)
shutil.copytree(os.path.join(engine, "Projects", source), path)
try:
    _, o = run("save")
    expect("save", "ok" in o, o)
    _, o = run("check")
    expect("files unchanged after an editor save", "changes when the editor saves it" not in o, o)
    _, o = run("get", "weapons")
    names = [w["name"] for w in json.loads(o)]
    used = [n for n in names if n != "None"]
    expect("weapon slots have no gaps", names[:len(used)] == used, str(names))

    _, o = run("add", "enemies", "name=TestEnemy", "hp=11")
    _, o2 = run("get", "enemies", "TestEnemy")
    expect("add enemy", '"hp": 11' in o2, o + o2)
    _, o = run("set", "enemies", "TestEnemy", "hp=77")
    _, o2 = run("get", "enemies", "TestEnemy")
    expect("set enemy field", as_json(o2).get("hp") == 77, o + o2)
    _, o2 = run("get", "enemies")
    ids = [x["id"] for x in json.loads(o2)]
    expect("enemy ids are unique", len(ids) == len(set(ids)), str(ids))
    _, o = run("remove", "enemies", "TestEnemy")
    _, o2 = run("list", "enemies")
    expect("remove enemy", "TestEnemy" not in o2, o + o2)

    _, o = run("add", "decorations", "name=TestDeco")
    _, o2 = run("list", "decorations")
    expect("add decoration", "TestDeco" in o2, o + o2)
    run("remove", "decorations", "TestDeco")

    _, o = run("set", "game", "name=Copy Game")
    _, o2 = run("get", "game")
    expect("game setting", as_json(o2).get("name") == "Copy Game", o + o2)

    _, o = run("map-new", "TestMap")
    _, o2 = run("list", "maps")
    expect("new map", "TestMap.eem" in o2, o + o2)
    _, o2 = run("get", "textures")
    textures = as_json(o2) or []
    tex = textures[0]["name"] if textures else None
    if tex:
        run("tile", "TestMap", tex, "2", "2", "6", "6")
    run("entity", "TestMap", "player", "3", "3")
    run("entity", "TestMap", "enemy", "5", "5", "--index", "0")
    run("modifier", "TestMap", "exit", "6", "6")
    _, o = run("map", "TestMap")
    expect("draw map", "@" in o and "E" in o and "X" in o, o)

    if tex:
        src_tex = os.path.join(path, "Textures", tex)
        tmp = os.path.join(path, "TestTexture.png")
        shutil.copy(src_tex, tmp)
        _, o = run("import-texture", tmp)
        os.remove(tmp)
        _, o2 = run("get", "textures")
        ids = [t["id"] for t in json.loads(o2)]
        expect("import texture", any(t["name"] == "TestTexture.png" for t in json.loads(o2)) and len(ids) == len(set(ids)), o + o2)
    else:
        print("skip texture tests: the project has no textures")
finally:
    shutil.rmtree(path)
    b = os.path.abspath(os.path.join(engine, "efpse_backup", COPY))
    if os.path.exists(b):
        shutil.rmtree(b)
print("Result:", "all passed" if not failed else "%d failed" % failed)
sys.exit(1 if failed else 0)

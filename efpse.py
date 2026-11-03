"""EFPSE Bridge: drive Easy FPS Editor CE projects from the command line. Settings are read and written with the editor's own code.

  efpse.py --engine <folder with EasyFPSEditor_CE.exe> --project <name> <command>

  projects                          projects in the engine folder
  info                              summary
  list <collection>                 enemies decorations weapons maps textures models animations hps armours tiles
  get <collection> [name|index]     all fields (also game, player, hud)
  set <collection> <name> field=value ...
  add <collection> field=value ...
  remove <collection> <name>
  order <collection> <name> <name> ...   moves these names to the front (weapon slot order)
  save                              re-save in the editor's own format
  map <name> [--floor N]            draw the map as text
  tile <name> <texture|empty> x y [x2 y2] [--floor N]
  entity <name> <type> x y [--index N] [--floor N]      type: player enemy weapon deco ammo key1 hp1 light1 ... none
  modifier <name> <type> x y [--floor N]                type: door door1 exit step1 hazard barrier trigger1 ... none
  map-new <name>
  import-weapon <name> <folder>     sprites, sounds and states
  import-enemy <name> <folder>
  import-deco <name> <folder>
  import-texture <png> [type]       type 2 = wall
  import-model <name> <folder> [type]   type 1 decoration, 2 enemy
  md3 <name>                        frame and triangle counts
  preview <name> <png> [frame ...]  render model frames without starting the game
  check                             all validations
  backup | editor | play [--map N] | shot <file> [--wait s] [--keys "..."] | pack
Output is JSON or plain text. Write commands are refused while the editor is open.
Turkish command and option names also work (al, ayarla, --proje, --kat ...)."""
import argparse
import datetime
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

try:
    import numpy as np
except ImportError:
    np = None   # only the MD3 commands need numpy

HERE = os.path.dirname(os.path.abspath(__file__))
NOWIN = 0x08000000
SIZE, FLOORS = 64, 9
LAYERS = ("tiles", "ents", "idx", "ctiles", "mods")
ENT = dict(player=8, enemy=6, key1=9, key2=10, key3=11, weapon=16, deco=17, ammo=18, hp1=19, hp2=20, hp3=21, hp4=22, light1=54, light2=55, light3=56, light4=60, light5=61, light6=62, arm1=66, arm2=67, arm3=68, arm4=69)
MOD = dict(door=12, door1=34, door2=35, door3=36, exit=23, step1=51, step2=52, step3=53, hazard=63, invisible=59, barrier=65, wallrd=37, wallld=38, wallru=39, walllu=40, wallth=57, walltv=58)
MOD.update({"trigger%d" % (i + 1): 24 + i for i in range(10)})
MOD.update({"terminal%d" % (i + 1): 41 + i for i in range(10)})
ENT_GLYPH = {8: "@", 6: "E", 16: "W", 17: "d", 18: "a", 54: "*", 55: "*", 56: "*", 60: "*", 61: "*", 62: "*", 9: "k", 10: "k", 11: "k"}


class Project:
    def __init__(self, motor, ad):
        self.motor = os.path.abspath(motor)
        self.exe = os.path.join(self.motor, "EasyFPSEditor_CE.exe")
        self.projects = os.path.join(self.motor, "Projects")
        self.ad = ad
        self.dir = os.path.join(self.projects, ad or "")

    def p(self, *a):
        return os.path.join(self.dir, *a)

    # ---- the editor's own code ----
    def host(self, is_, ops=None, save_to=None):
        ps = os.path.join(os.environ["WINDIR"], "SysWOW64", "WindowsPowerShell", "v1.0", "powershell.exe")
        cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(HERE, "efpse_host.ps1"), "-Exe", self.exe, "-Proje", self.dir, "-Is", is_]
        tmp = None
        if ops is not None:
            fd, tmp = tempfile.mkstemp(suffix=".json")
            with os.fdopen(fd, "w", encoding="utf8") as f:
                json.dump(ops, f, ensure_ascii=False)
            cmd += ["-Ops", tmp]
        if save_to:
            cmd += ["-SaveTo", save_to]
        r = subprocess.run(cmd, capture_output=True, creationflags=NOWIN)
        if tmp:
            os.remove(tmp)
        out, err = r.stdout.decode("utf8", "replace"), r.stderr.decode("utf8", "replace")
        if r.returncode or (is_ == "apply" and "SAVED" not in out):
            raise SystemExit("The editor code reported an error:\n" + (err or out)[-900:])
        return out

    def data(self):
        return json.loads(self.host("dump"))

    def guard(self):
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq EasyFPSEditor_CE.exe"], capture_output=True, text=True, creationflags=NOWIN).stdout
        if "EasyFPSEditor_CE.exe" in out:
            raise SystemExit("The editor is open. Save and close it first, otherwise it will overwrite this change.")

    def apply(self, ops):
        self.guard()
        self.backup(quiet=True)
        self.host("apply", ops)

    def backup(self, quiet=False):
        d = os.path.join(self.projects, "..", "efpse_backup", self.ad)
        os.makedirs(d, exist_ok=True)
        path = os.path.abspath(os.path.join(d, datetime.datetime.now().strftime("%Y%m%d_%H%M%S.zip")))
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for base, _, files in os.walk(self.dir):
                for f in files:
                    if f.endswith((".dat", ".eem", ".states", ".script")):
                        full = os.path.join(base, f)
                        z.write(full, os.path.relpath(full, self.dir))
        old = sorted(os.listdir(d))[:-30]
        for o in old:
            os.remove(os.path.join(d, o))
        if not quiet:
            print("backup:", path)
        return path

    # ---- maps ----
    def map_path(self, ad):
        return self.p("Maps", ad if ad.endswith(".eem") else ad + ".eem")

    def map_load(self, ad):
        with open(self.map_path(ad), "rb") as f:
            raw = f.read()
        w, h = struct.unpack("<hh", raw[:4])
        n = w * h * FLOORS
        vals = struct.unpack("<%dh" % (n * 5), raw[4:4 + n * 10])
        return {k: list(vals[i * n:(i + 1) * n]) for i, k in enumerate(LAYERS)}

    def map_save(self, ad, m):
        self.guard()
        path = self.map_path(ad)
        if os.path.exists(path):
            self.backup(quiet=True)
        n = SIZE * SIZE * FLOORS
        with open(path, "wb") as f:
            f.write(struct.pack("<hh", SIZE, SIZE))
            for k in LAYERS:
                f.write(struct.pack("<%dh" % n, *m[k]))


def idx(x, y, kat=0):
    return kat * SIZE * SIZE + y * SIZE + x


def kv(items):
    out = {}
    for it in items:
        k, v = it.split("=", 1)
        if v.startswith("["):
            v = json.loads(v)
        out[k] = v
    return out


def name_of(o):
    return o.get("entityName") or o.get("name") or str(o.get("amount", ""))


def map_text(pr, ad, kat):
    m = pr.map_load(ad)
    tex = {t["id"] + 1: t for t in pr.data()["textures"]}
    rows, used = [], {}
    x0, x1, y0, y1 = SIZE, -1, SIZE, -1
    for y in range(SIZE):
        for x in range(SIZE):
            i = idx(x, y, kat)
            if m["tiles"][i] or m["ents"][i] or m["mods"][i]:
                x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
    if x1 < 0:
        return "floor %d is empty" % kat
    for y in range(y0, y1 + 1):
        s = ""
        for x in range(x0, x1 + 1):
            i = idx(x, y, kat)
            t, e, md = m["tiles"][i], m["ents"][i], m["mods"][i]
            c = "."
            if t:
                c = "#" if tex.get(t, {}).get("type") == 2 else "_"
            if md:
                c = "D" if md - 1 in (12, 34, 35, 36) else "X" if md - 1 == 23 else "s" if md - 1 in (51, 52, 53) else "m"
            if e:
                c = ENT_GLYPH.get(e - 1, "?")
            s += c
        rows.append("%2d %s" % (y, s))
    head = "   " + "".join(str((x // 10) % 10) if x % 10 == 0 else " " for x in range(x0, x1 + 1)) + "\n   " + "".join(str(x % 10) for x in range(x0, x1 + 1))
    return "%s floor %d  # wall _ floor @ player E enemy W weapon d decoration * light D door X exit s step\n%s\n%s" % (ad, kat, head, "\n".join(rows))


# ---- import: same file names as the editor's own import dialogs ----
def copy_group(pr, src, name, folder, sounds, extra=()):
    n = 0
    os.makedirs(pr.p("Sprites", folder), exist_ok=True)
    os.makedirs(pr.p("Sounds"), exist_ok=True)
    for f in sorted(os.listdir(src)):
        low = f.lower()
        full = os.path.join(src, f)
        if low.endswith(".png"):
            stem = f[:-4]
            if stem.lower().startswith("ammo") and folder == "Weapons":
                shutil.copy(full, pr.p("Sprites", "Ammo", name + ".png"))
            elif stem[-1:].isdigit() and not stem.startswith(name):
                digits = "".join(c for c in stem if c.isdigit())
                shutil.copy(full, pr.p("Sprites", folder, "%s%d.png" % (name, int(digits))))
            else:
                shutil.copy(full, pr.p("Sprites", folder, f))
            n += 1
        elif low.endswith(".wav"):
            stem = f[:-4]
            if not stem.startswith(name):
                stem = name + stem.capitalize()
            shutil.copy(full, pr.p("Sounds", stem + ".wav"))
        elif low.endswith(".states"):
            os.makedirs(pr.p("States"), exist_ok=True)
            shutil.copy(full, pr.p("States", name + ".states"))
        elif low.endswith((".md3",)):
            os.makedirs(pr.p("Models"), exist_ok=True)
            shutil.copy(full, pr.p("Models", f))
    return n


def has(lst, name):
    return any(name_of(x) == name for x in lst)


# ---- checks ----
def read(p):
    with open(p, encoding="utf8", errors="replace") as f:
        return f.read().replace("\r", "")


# commands listed in the manual (Advanced/FSM)
ACTIONS = set("""NONE READY SOUND SOUNDANDATTACK PLAYERSPEED PARTICLES CUSTOMPARTICLE SETVAR MODELTEXTURE SPAWN HUDIMG CAMSPEED
INCREMENT DECREMENT MULTIPLY DIVIDE MODULO CLAMP JUMPIFEQUALS JUMPIFNEQUALS JUMPIFGEQUALS JUMPIFLEQUALS JUMPIFGREATER JUMPIFLESS JUMPIFHPLESS
ATTACK EXPLOSION PROJECTILE JUMPIFLESSAMMO JUMPIFNOAMMO GIVEAMMO TAKEAMMO SETAMMO RELOAD MUZZLEFLASH SETSTAT ZOOM""".split())


def check_states(pr, path, folder, errs):
    rel = "States/" + os.path.basename(path)
    images, sounds, states, jumps = 0, 0, set(), []
    for i, ln in enumerate(read(path).split("\n"), 1):
        w = ln.split()
        if ln != ln.lstrip():
            errs.append("%s:%d space at the start of the line" % (rel, i))
        if not w:
            continue
        if w[0] == "image":
            if len(w) == 4:
                for k in range(int(w[2]), int(w[3]) + 1):
                    if not os.path.exists(pr.p("Sprites", folder, "%s%d.png" % (w[1], k))):
                        errs.append("%s: missing image %s%d.png" % (rel, w[1], k))
                images += int(w[3]) - int(w[2]) + 1
            else:
                images += 1
        elif w[0] == "sound":
            if not os.path.exists(pr.p("Sounds", w[1] + ".wav")):
                errs.append("%s: missing sound %s.wav" % (rel, w[1]))
            sounds += 1
        elif w[0] == "state":
            states.add(w[1])
            first = True
            if len(w) > 2 and w[2] != "NONE":
                jumps.append((i, w[2]))
        elif w[0] == "frame":
            if int(w[1]) >= images:
                errs.append("%s:%d frame %s does not exist (%d in total)" % (rel, i, w[1], images))
            act = w[6:]
            if folder == "Weapons" and float(w[2]) < .0167:
                errs.append("%s:%d duration %s is too short" % (rel, i, w[2]))
            if act and act[0] not in ACTIONS:
                errs.append("%s:%d command %s is not in the manual" % (rel, i, act[0]))
            if act and act[0] != "NONE" and first:
                errs.append("%s:%d a command on the first line of a state is ignored: %s" % (rel, i, act[0]))
            first = False
            if act and act[0].startswith("JUMPIF"):
                jumps.append((i, act[-1]))
            if act and act[0] in ("SOUND", "SOUNDANDATTACK") and act[1].isdigit() and int(act[1]) >= sounds:
                errs.append("%s:%d sound %s does not exist" % (rel, i, act[1]))
    for i, st in jumps:
        if st not in states:
            errs.append("%s:%d unknown state %s" % (rel, i, st))


def kontrol(pr):
    errs, notes = [], []
    d = pr.data()
    notes.append("The editor code opens the project")
    weapons = [w["name"] for w in d["weapons"]]
    notes.append("Weapons: " + ", ".join(w for w in weapons if w != "None"))
    notes.append("Enemies: " + ", ".join(e["name"] for e in d["enemies"]))
    notes.append("Maps: " + ", ".join(m["name"] for m in d["maps"]))
    # do the files change when the editor saves them
    tmp = tempfile.mkdtemp()
    for f in os.listdir(pr.dir):
        if f.endswith(".dat"):
            shutil.copy(pr.p(f), tmp)
    pr.host("apply", [], save_to=tmp)
    for f in os.listdir(tmp):
        a, b = read(pr.p(f)).strip(), read(os.path.join(tmp, f)).strip()
        if a != b:
            la, lb = a.split("\n"), b.split("\n")
            i = next((k for k in range(min(len(la), len(lb))) if la[k] != lb[k]), min(len(la), len(lb)))
            errs.append("%s changes when the editor saves it, line %d: [%s] / [%s]" % (f, i + 1, la[i] if i < len(la) else "", lb[i] if i < len(lb) else ""))
    shutil.rmtree(tmp)
    for folder, names in (("Weapons", [w for w in weapons if w != "None"]), ("Enemies", [e["name"] for e in d["enemies"]]), ("Decorations", [x["name"] for x in d["decorations"]])):
        for n in names:
            st = pr.p("States", n + ".states")
            if os.path.exists(st):
                check_states(pr, st, folder, errs)
    for m in d["models"]:
        names = [m["modelFilename"], "w" + m["modelFilename"], "v" + m["modelFilename"]]
        if not any(os.path.exists(pr.p("Models", n + ".md3")) for n in names):
            errs.append("Model file missing: %s" % m["entityName"])
            continue
        md3 = pr.p("Models", m["modelFilename"] + ".md3")
        st = pr.p("States", m["entityName"] + ".states")
        if np is not None and os.path.exists(md3) and os.path.exists(st):
            if not os.path.exists(md3[:-4] + ".png"):
                errs.append("Model texture missing: %s.png" % m["modelFilename"])
            nf = md3_read(md3)["frames"]
            for i, ln in enumerate(read(st).split("\n"), 1):
                w = ln.split()
                if w[:1] == ["frame"] and int(w[1]) >= nf:
                    errs.append("States/%s.states:%d frame %s is not in the model (%d frames)" % (m["entityName"], i, w[1], nf))
                    break
    tex_ok = {t["id"] + 1 for t in d["textures"]}
    for mp in d["maps"]:
        if not os.path.exists(pr.p("Maps", mp["name"])):
            errs.append("Map file missing: " + mp["name"])
            continue
        m = pr.map_load(mp["name"])
        bad = {t for t in m["tiles"] if t and t not in tex_ok}
        if bad:
            errs.append("%s: undefined texture %s" % (mp["name"], sorted(bad)))
        if sum(1 for e in m["ents"] if e - 1 == 8) != 1:
            errs.append("%s: there must be exactly one player start" % mp["name"])
        en_ok = {e["id"] for e in d["enemies"]}
        for e, i_ in zip(m["ents"], m["idx"]):
            if e - 1 == 6 and i_ not in en_ok:
                errs.append("%s: undefined enemy %d" % (mp["name"], i_))
                break
        sc = pr.p("Scripts", mp["name"][:-4] + ".script")
        if os.path.exists(sc) and "font " not in read(sc):
            errs.append("%s: no 'font' line, the game may freeze at start" % os.path.basename(sc))
    for n in notes:
        print(n)
    for e in errs:
        print("ERROR ", e)
    print("Result:", "no problems" if not errs else "%d problems" % len(errs))
    return not errs


def md3_read(path):
    """MD3 surfaces, frames and triangles; vertices in map units (x forward, y side, z up)."""
    with open(path, "rb") as f:
        b = f.read()
    if b[:4] != b"IDP3":
        raise SystemExit("Not an MD3 file: " + path)
    nfr, ntag, nsurf = struct.unpack("<iii", b[76:88])
    ofs = struct.unpack("<i", b[100:104])[0]
    surfs = []
    for _ in range(nsurf):
        name = b[ofs + 4:ofs + 68].split(b"\0")[0].decode("latin1")
        sf, sn, ssk, sv, st, o_t, o_s, o_uv, o_xyz, o_end = struct.unpack("<10i", b[ofs + 68:ofs + 108])
        tris = np.frombuffer(b, "<i4", st * 3, ofs + o_t).reshape(-1, 3)
        uv = np.frombuffer(b, "<f4", sv * 2, ofs + o_uv).reshape(-1, 2)
        xyz = np.frombuffer(b, "<i2", sn * sv * 4, ofs + o_xyz).reshape(sn, sv, 4)[:, :, :3] / 64.0
        surfs.append(dict(name=name, tris=tris, uv=uv, xyz=xyz))
        ofs += o_end
    return dict(frames=nfr, surfaces=surfs, tris=sum(len(s["tris"]) for s in surfs), verts=sum(s["xyz"].shape[1] for s in surfs))


def md3_render(path, frame, size=320, yaw=35.0):
    """Draws one model frame with flat shading, colours from its texture."""
    import cv2
    m = md3_read(path)
    tex_path = path[:-4] + ".png"
    tx = cv2.imdecode(np.fromfile(tex_path, np.uint8), cv2.IMREAD_COLOR) if os.path.exists(tex_path) else None
    a = math.radians(yaw)
    img = np.full((size, size, 3), (70, 60, 90), np.uint8)
    pts = []
    for s in m["surfaces"]:
        v = s["xyz"][min(frame, m["frames"] - 1)]
        x = v[:, 0] * math.cos(a) - v[:, 1] * math.sin(a)
        y = v[:, 0] * math.sin(a) + v[:, 1] * math.cos(a)
        sc = size / 90.0
        px = np.stack([size / 2 + y * sc, size - 8 - v[:, 2] * sc], axis=1).astype(np.int32)
        for t in s["tris"]:
            uv = s["uv"][t].mean(axis=0)
            col = (200, 200, 200)
            if tx is not None:
                h, w = tx.shape[:2]
                col = tx[int(uv[1] % 1 * (h - 1)), int(uv[0] % 1 * (w - 1))]
            n = np.cross(v[t[1]] - v[t[0]], v[t[2]] - v[t[0]])
            ln = np.linalg.norm(n) or 1
            lit = .55 + .45 * abs(n[0] / ln * .7 + n[2] / ln * .7)
            pts.append((x[t].mean(), px[t], [int(c * lit) for c in col]))
    for _, p, c in sorted(pts, key=lambda q: q[0]):
        cv2.fillConvexPoly(img, p, c)
    return img


def pack(pr):
    pr.guard()
    out = os.path.abspath(os.path.join(pr.motor, "..", "release", pr.ad))
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    shutil.copytree(pr.dir, os.path.join(out, "Data"), ignore=shutil.ignore_patterns("*.backup", "*.log"))
    shutil.copy(os.path.join(pr.projects, "Game.exe"), os.path.join(out, pr.ad + ".exe"))
    shutil.copy(os.path.join(pr.projects, "openal32.dll"), out)
    cfg = os.path.join(pr.projects, "Config.ini")
    if os.path.exists(cfg):
        with open(os.path.join(out, "Config.ini"), "w", newline="\r\n") as f:
            f.write(read(cfg).replace("fullscreen=0", "fullscreen=1"))
    print("package:", out)


# Turkish command names: the same commands under their original names
ALIAS = {"help": "yardim", "projects": "projeler", "info": "bilgi", "list": "liste", "get": "al", "set": "ayarla", "add": "ekle", "remove": "sil",
         "order": "sirala", "save": "kaydet", "map": "harita", "map-new": "harita-yeni", "tile": "kare", "entity": "varlik", "modifier": "degistirici",
         "import-weapon": "silah-al", "import-enemy": "dusman-al", "import-deco": "dekor-al", "import-texture": "doku-al", "import-model": "model-al",
         "preview": "onizle", "check": "kontrol", "backup": "yedek", "play": "oyna", "shot": "foto", "pack": "paket"}
WORD = {"none": "yok", "empty": "boş"}


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--motor", "--engine", dest="motor", default=os.environ.get("EFPSE_MOTOR", os.environ.get("EFPSE_ENGINE", ".")))
    ap.add_argument("--proje", "--project", dest="proje", default=os.environ.get("EFPSE_PROJE", os.environ.get("EFPSE_PROJECT")))
    ap.add_argument("--kat", "--floor", dest="kat", type=int, default=0)
    ap.add_argument("--sira", "--index", dest="sira", type=int, default=0)
    ap.add_argument("--map", type=int, default=0)
    ap.add_argument("--bekle", "--wait", dest="bekle", type=int, default=2)
    ap.add_argument("--tus", "--keys", dest="tus", default="")
    ap.add_argument("komut", nargs="?", default="yardim")
    ap.add_argument("arg", nargs="*")
    a = ap.parse_args()
    pr = Project(a.motor, a.proje)
    c, x = ALIAS.get(a.komut, a.komut), [WORD.get(v, v) for v in a.arg]
    if c == "yardim":
        print(__doc__)
    elif c == "projeler":
        print("\n".join(d for d in os.listdir(pr.projects) if os.path.exists(os.path.join(pr.projects, d, "Game.dat"))))
    elif c == "bilgi":
        d = pr.data()
        print(json.dumps({k: [name_of(o) for o in d[k]] for k in ("weapons", "enemies", "decorations", "maps")} | {"textures": len(d["textures"]), "models": len(d["models"]), "game": d["game"]["name"]}, ensure_ascii=False, indent=1))
    elif c == "liste":
        print("\n".join(name_of(o) for o in pr.data()[x[0]]))
    elif c == "al":
        v = pr.data()[x[0]]
        if len(x) > 1:
            v = v[int(x[1])] if x[1].isdigit() else next(o for o in v if name_of(o) == x[1])
        print(json.dumps(v, ensure_ascii=False, indent=1))
    elif c == "ayarla":
        pr.apply([dict(op="set", coll=x[0], key=x[1], fields=kv(x[2:]))] if x[0] not in ("game", "player", "hud") else [dict(op="set", coll=x[0], key="", fields=kv(x[1:]))])
        print("ok")
    elif c == "ekle":
        pr.apply([dict(op="add", coll=x[0], fields=kv(x[1:]))])
        print("ok")
    elif c == "sil":
        pr.apply([dict(op="del", coll=x[0], key=x[1])])
        print("ok")
    elif c == "sirala":
        pr.apply([dict(op="order", coll=x[0], names=x[1:])])
        print("ok")
    elif c == "kaydet":
        pr.apply([])
        print("ok")
    elif c == "harita":
        print(map_text(pr, x[0], a.kat))
    elif c == "harita-yeni":
        n = SIZE * SIZE * FLOORS
        pr.map_save(x[0], {k: [0] * n for k in LAYERS})
        pr.apply([dict(op="add", coll="maps", fields=dict(name=x[0] + ".eem"))])
        print("ok")
    elif c == "kare":
        d = pr.data()
        val = 0 if x[1] in ("boş", "bos", "0") else next(t["id"] + 1 for t in d["textures"] if t["name"] in (x[1], x[1] + ".png"))
        x0, y0 = int(x[2]), int(x[3])
        x1, y1 = (int(x[4]), int(x[5])) if len(x) > 5 else (x0, y0)
        m = pr.map_load(x[0])
        for yy in range(min(y0, y1), max(y0, y1) + 1):
            for xx in range(min(x0, x1), max(x0, x1) + 1):
                m["tiles"][idx(xx, yy, a.kat)] = val
        pr.map_save(x[0], m)
        print("ok")
    elif c == "varlik":
        m = pr.map_load(x[0])
        i = idx(int(x[2]), int(x[3]), a.kat)
        m["ents"][i] = 0 if x[1] == "yok" else ENT[x[1]] + 1
        m["idx"][i] = a.sira
        pr.map_save(x[0], m)
        print("ok")
    elif c == "degistirici":
        m = pr.map_load(x[0])
        i = idx(int(x[2]), int(x[3]), a.kat)
        m["mods"][i] = 0 if x[1] == "yok" else MOD[x[1]] + 1
        pr.map_save(x[0], m)
        print("ok")
    elif c in ("silah-al", "dusman-al", "dekor-al"):
        coll, folder = dict(zip(("silah-al", "dusman-al", "dekor-al"), (("weapons", "Weapons"), ("enemies", "Enemies"), ("decorations", "Decorations"))))[c]
        n = copy_group(pr, x[1], x[0], folder, ())
        if not has(pr.data()[coll], x[0]):
            pr.apply([dict(op="add", coll=coll, fields=dict(name=x[0]))])
        print("imported:", x[0], n, "images")
    elif c == "doku-al":
        ad = os.path.basename(x[0])
        os.makedirs(pr.p("Textures"), exist_ok=True)
        shutil.copy(x[0], pr.p("Textures", ad))
        d = pr.data()["textures"]
        if not has(d, ad):
            pr.apply([dict(op="add", coll="textures", fields=dict(id=max([t["id"] for t in d] + [-1]) + 1, type=x[1] if len(x) > 1 else 2, name=ad, lighted=True))])
        print("ok", ad)
    elif c == "model-al":
        n = 0
        os.makedirs(pr.p("Models"), exist_ok=True)
        for f in os.listdir(x[1]):
            if f.lower().endswith((".md3", ".png")):
                shutil.copy(os.path.join(x[1], f), pr.p("Models", f))
                n += 1
        if not has(pr.data()["models"], x[0]):
            pr.apply([dict(op="add", coll="models", fields=dict(entityName=x[0], modelFilename=x[0], modelType=x[2] if len(x) > 2 else 1))])
        print("imported:", x[0], n, "files")
    elif c == "md3":
        m = md3_read(pr.p("Models", x[0] + ".md3"))
        print("frames", m["frames"], "surfaces", len(m["surfaces"]), "triangles", m["tris"], "vertices", m["verts"])
    elif c == "onizle":
        import cv2
        frames = [int(v) for v in x[2:]] or [0]
        sheet = np.hstack([md3_render(pr.p("Models", x[0] + ".md3"), f) for f in frames])
        cv2.imencode(".png", sheet)[1].tofile(x[1])
        print("written:", x[1])
    elif c == "kontrol":
        sys.exit(0 if kontrol(pr) else 1)
    elif c == "yedek":
        pr.backup()
    elif c == "editor":
        subprocess.Popen([pr.exe], cwd=pr.motor)
        print("Editor opened. File > Open Project >", pr.ad)
    elif c == "oyna":
        subprocess.Popen([os.path.join(pr.projects, "Game.exe"), "-data", pr.ad, "-map", str(a.map), "-console"], cwd=pr.projects)
    elif c == "foto":
        keys = (a.tus + "," if a.tus else "") + "SHOT"
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", os.path.join(HERE, "efpse_shot.ps1"), "-Dir", pr.projects, "-Project", pr.ad, "-Map", str(a.map), "-Wait", str(a.bekle), "-Out", os.path.abspath(x[0]), "-Keys", keys])
    elif c == "paket":
        pack(pr)
    else:
        raise SystemExit("unknown command: " + c + "  (run without a command for help)")


if __name__ == "__main__":
    main()

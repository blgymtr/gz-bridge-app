"""Köprünün yazma komutlarını projenin geçici kopyasında dener. Kullanım: test_kopru.py <motor> <proje>"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
motor, kaynak = sys.argv[1], sys.argv[2]
KOPYA = "KopruTest"
yol = os.path.join(motor, "Projects", KOPYA)
env = dict(os.environ, EFPSE_MOTOR=motor, EFPSE_PROJE=KOPYA, PYTHONIOENCODING="utf8")
hatalar = 0


def k(*a):
    r = subprocess.run([sys.executable, os.path.join(HERE, "kopru.py"), *a], capture_output=True, env=env)
    return r.returncode, r.stdout.decode("utf8", "replace") + r.stderr.decode("utf8", "replace")


def dene(ad, kosul, ek=""):
    global hatalar
    print(("geçti " if kosul else "KALDI ") + ad + ("" if kosul else "  " + ek[-400:]))
    hatalar += 0 if kosul else 1


if os.path.exists(yol):
    shutil.rmtree(yol)
shutil.copytree(os.path.join(motor, "Projects", kaynak), yol)
try:
    _, o = k("kaydet")
    dene("kaydet", "tamam" in o, o)
    _, o = k("kontrol")
    dene("kaydet sonrası editörle aynı", "editör kaydedince" not in o, o)
    _, o = k("al", "weapons")
    silahlar = [w["name"] for w in json.loads(o)]
    dene("silahlar boşluksuz", silahlar[:3] == ["Thompson", "M1911", "TrenchGun"], str(silahlar))

    _, o = k("ayarla", "enemies", "Suit", "hp=77", "speed=200")
    _, o2 = k("al", "enemies", "Suit")
    e = json.loads(o2)
    dene("düşman ayarla", e["hp"] == 77 and e["speed"] == 200, o + o2)

    _, o = k("ekle", "enemies", "name=DenemeAdam", "hp=11")
    _, o2 = k("al", "enemies", "DenemeAdam")
    dene("düşman ekle", '"hp": 11' in o2, o + o2)
    yeni_id = json.loads(o2)["id"]
    _, o2 = k("al", "enemies")
    ids = [x["id"] for x in json.loads(o2)]
    dene("düşman kimliği benzersiz", len(ids) == len(set(ids)), str(ids))

    _, o = k("sil", "enemies", "DenemeAdam")
    _, o2 = k("liste", "enemies")
    dene("düşman sil", "DenemeAdam" not in o2, o + o2)

    _, o = k("ekle", "decorations", "name=DenemeDekor")
    _, o2 = k("liste", "decorations")
    dene("dekor ekle", "DenemeDekor" in o2, o + o2)
    k("sil", "decorations", "DenemeDekor")

    _, o = k("ayarla", "game", "name=Kopya Oyun")
    _, o2 = k("al", "game")
    dene("oyun ayarı", json.loads(o2)["name"] == "Kopya Oyun", o + o2)

    _, o = k("harita-yeni", "Deneme")
    _, o2 = k("liste", "maps")
    dene("harita yeni", "Deneme.eem" in o2, o + o2)
    _, o2 = k("al", "textures")
    doku = json.loads(o2)[0]["name"]
    k("kare", "Deneme", doku, "2", "2", "6", "6")
    k("varlik", "Deneme", "player", "3", "3")
    k("varlik", "Deneme", "enemy", "5", "5", "--sira", "1")
    k("degistirici", "Deneme", "exit", "6", "6")
    _, o = k("harita", "Deneme")
    dene("harita çizim", "@" in o and "E" in o and "X" in o, o)

    doku_yol = os.path.join(yol, "Textures", doku)
    gecici = os.path.join(yol, "DenemeDoku.png")
    shutil.copy(doku_yol, gecici)
    _, o = k("doku-al", gecici)
    os.remove(gecici)
    _, o2 = k("al", "textures")
    idler = [t["id"] for t in json.loads(o2)]
    dene("doku al", any(t["name"] == "DenemeDoku.png" for t in json.loads(o2)) and len(idler) == len(set(idler)), o + o2)

    _, o = k("kontrol")
    print(o)
    dene("son kontrol", "Sonuç: sorun yok" in o, o)
finally:
    shutil.rmtree(yol)
    y = os.path.abspath(os.path.join(motor, "kopru_yedek", KOPYA))
    if os.path.exists(y):
        shutil.rmtree(y)
print("Sonuç:", "hepsi geçti" if not hatalar else "%d kaldı" % hatalar)
sys.exit(1 if hatalar else 0)

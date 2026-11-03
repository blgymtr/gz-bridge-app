<div align="center">

# EFPSE Bridge

**Easy-FPS-Editor-CE-Projekte über die Kommandozeile steuern.**
Jede Projekteinstellung mit dem eigenen Code des Editors lesen und schreiben, Karten als Text bearbeiten, Assets importieren, prüfen, Screenshots aufnehmen und paketieren, ohne das Editorfenster zu öffnen.

[![CI](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml/badge.svg)](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml)
[![Lizenz: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[English](README.md) · **Deutsch** · [Türkçe](README.tr.md)

</div>

## Warum

Viele Optionen des Easy FPS Editors stecken hinter Kontrollkästchen und Panels: Modell-Flags, Waffen- und Gegnerfelder, Karteneigenschaften. Sie liegen in binären Projektdateien, die sich von Hand kaum lesen oder ändern und gar nicht skripten lassen. EFPSE Bridge lädt **deine installierte Kopie des Editors** im Hintergrund, lädt und speichert das Projekt mit dessen eigenen Klassen und liefert alles als einfaches JSON und Text. So werden Einstellungen sichtbar, vergleichbar und skriptbar, für Menschen ebenso wie für KI-Assistenten.

## Funktionen

- **Jedes Feld, lesen und schreiben.** `get` zeigt alle Felder einer Waffe, eines Gegners, einer Dekoration, Karte, Textur, eines Modells, einer Animation, von Gesundheit, Rüstung oder Kachel sowie die Einstellungen `game`, `player` und `hud`. `set` ändert jedes Feld, auch Array-Elemente (`frames[2]=5`).
- **Hinzufügen, entfernen, sortieren.** Einträge anlegen und löschen, Reihenfolge der Waffenslots festlegen.
- **Karten als Text.** `map` zeichnet eine Etage als ASCII-Raster (Wände, Spieler, Gegner, Waffen, Lichter, Schlüssel). `tile`, `entity` und `modifier` setzen Texturen, Entitäten (Spieler, Gegner, Waffe, Dekoration, Munition, Schlüssel, Gesundheit, Rüstung, Lichter) und Modifikatoren (Türen, Ausgänge, Stufen, Gefahren, Barrieren, Trigger, Terminals) auf eine der 9 Etagen. `map-new` legt eine leere 64x64-Karte an.
- **Assets importieren.** Waffen, Gegner und Dekorationen aus einem Ordner (Sprites, Sounds, States), Texturen sowie MD3-Modelle mit Skins.
- **MD3-Werkzeuge.** Anzahl von Frames, Flächen, Dreiecken und Vertices sowie ein Vorschaublatt beliebiger Frames, ohne das Spiel zu starten.
- **Prüfung.** `check` sucht fehlende Dateien, kaputte Verweise, FSM-Befehle, die nicht im Handbuch stehen, und andere Fehler und endet bei Fehlern mit einem Exit-Code ungleich null (CI-tauglich).
- **Starten und aufnehmen.** Editor öffnen, das Spiel auf einer Karte starten oder ein Tastenskript (`W:200,LMB:40,WAIT:500,SHOT`) abspielen und Screenshots speichern.
- **Paketieren.** Erstellt einen verteilbaren Ordner des Spiels.
- **Standardmäßig sicher.** Vor jedem Schreiben wird eine Sicherung mit Zeitstempel in `efpse_backup/` angelegt. Solange der Editor geöffnet ist, wird Schreiben abgelehnt, damit sich beide nicht um dieselben Dateien streiten.
- **Zwei Sprachen auf der Kommandozeile.** Befehle und Optionen funktionieren auf Englisch und Türkisch (`get`/`al`, `--project`/`--proje`).

## Voraussetzungen

- Windows 10 oder 11
- Easy FPS Editor CE **v1.10.5** (deine eigene Installation; nicht enthalten)
- Python 3.9 oder neuer. `numpy` für MD3-Befehle, `opencv-python` für `preview`. Alles andere nutzt die Standardbibliothek
- Windows PowerShell 5.1 (in Windows enthalten). Die Bridge startet die 32-Bit-Version, um den Editor zu laden

## Schnellstart

```powershell
git clone https://github.com/blgymtr/gz-bridge-app.git
cd gz-bridge-app
$env:EFPSE_ENGINE  = 'C:\Spiele\EasyFPSEditor_CE_V1.10.5'   # Ordner mit EasyFPSEditor_CE.exe
$env:EFPSE_PROJECT = 'MeinSpiel'                           # Ordnername unter Projects\
python efpse.py projects
python efpse.py info
python efpse.py check
```

Optionen gehen auch direkt: `python efpse.py --engine <Ordner> --project <Name> <Befehl> ...`

## Befehle

| Befehl | Funktion |
|---|---|
| `projects` | Projekte im Engine-Ordner auflisten |
| `info` | Waffen, Gegner, Dekorationen, Karten, Anzahl Texturen und Modelle, Spielname |
| `list <Sammlung>` | Namen einer Sammlung: `enemies decorations weapons maps textures models animations hps armours tiles` |
| `get <Sammlung> [Name\|Index]` | Alle Felder als JSON. Auch `game`, `player`, `hud` |
| `set <Sammlung> <Name> Feld=Wert ...` | Felder ändern. Bei `game`, `player`, `hud` ohne Namen |
| `add <Sammlung> Feld=Wert ...` | Neuer Eintrag |
| `remove <Sammlung> <Name>` | Eintrag löschen |
| `order <Sammlung> <Name> <Name> ...` | Diese Namen nach vorne stellen (Waffenslots) |
| `save` | Im eigenen Format des Editors neu speichern |
| `map <Name> [--floor N]` | Etage als Text zeichnen |
| `tile <Karte> <Textur\|empty> x y [x2 y2] [--floor N]` | Kachel oder Rechteck malen |
| `entity <Karte> <Typ> x y [--index N] [--floor N]` | Entität setzen: `player enemy weapon deco ammo key1-3 hp1-4 arm1-4 light1-6 none` |
| `modifier <Karte> <Typ> x y [--floor N]` | Modifikator setzen: `door door1-3 exit step1-3 hazard invisible barrier trigger1-10 terminal1-10 none` |
| `map-new <Name>` | Leere Karte, zum Projekt hinzugefügt |
| `import-weapon <Name> <Ordner>` | Waffe importieren (Sprites, Sounds, States) |
| `import-enemy <Name> <Ordner>` | Gegner importieren |
| `import-deco <Name> <Ordner>` | Dekoration importieren |
| `import-texture <png> [Typ]` | Textur importieren (Typ 2 = Wand) |
| `import-model <Name> <Ordner> [Typ]` | MD3 und Skins (Typ 1 Dekoration, 2 Gegner) |
| `md3 <Name>` | Anzahl Frames, Flächen, Dreiecke, Vertices |
| `preview <Name> <aus.png> [Frame ...]` | Modell-Frames ohne Spiel als PNG rendern |
| `check` | Alle Prüfungen, Exit-Code ungleich null bei Fehlern |
| `backup` | Projekt jetzt sichern |
| `editor` | Editor öffnen |
| `play [--map N]` | Spiel auf einer Karte starten |
| `shot <aus.png> [--wait s] [--keys "..."]` | Spiel starten, Tastenskript abspielen, Screenshot |
| `pack` | Spiel paketieren |

Tastenskript für `shot`: durch Kommas getrennte Schritte. `TASTE:ms` hält eine Taste, `LMB:ms` / `RMB:ms` klickt, `WAIT:ms` wartet, `SHOT` nimmt einen Screenshot auf.

### Beispiele

```powershell
python efpse.py get weapons Shotgun
python efpse.py set enemies Imp health=120 speed=3.5
python efpse.py set game name="Nachtschicht"
python efpse.py map E1M1 --floor 0
python efpse.py tile E1M1 brick.png 10 10 20 10
python efpse.py entity E1M1 enemy 15 12 --index 2
python efpse.py modifier E1M1 door 15 9
python efpse.py import-model Fass .\modelle\fass 1
python efpse.py preview Fass fass.png 0 4 8
python efpse.py shot test.png --wait 6 --keys "W:400,LMB:60,WAIT:300,SHOT"
```

## Dateien

| Datei | Aufgabe |
|---|---|
| `efpse.py` | Befehle, Karten lesen und schreiben, Importe, Prüfungen, MD3, Paketierung |
| `efpse_host.ps1` | Lädt die Klassen des Editors in 32-Bit-PowerShell, liest oder wendet Änderungen an |
| `efpse_shot.ps1` | Startet das Spiel, spielt das Tastenskript ab, nimmt das Fenster auf |
| `test_efpse.py` | Testet die Schreibbefehle an einer temporären Projektkopie |

## Tests

```powershell
python test_efpse.py <Engine-Ordner> <Projekt>
```

Der Test kopiert das Projekt nach `Projects\EfpseTest`, führt dort die Schreibbefehle aus und prüft die Ergebnisse. Dein Projekt bleibt unberührt.

## Funktionsweise

`efpse_host.ps1` startet in 32-Bit-Windows-PowerShell, lädt `EasyFPSEditor_CE.exe` als .NET-Assembly und öffnet das Projekt mit den eigenen Ressourcenklassen des Editors. Öffentliche Felder werden in JSON umgewandelt. Änderungen aus `efpse.py` kommen als kleine Liste von Operationen (`set`, `add`, `del`, `order`) und werden über dieselben Klassen gespeichert, sodass die Dateien im erwarteten Format bleiben. Karten werden direkt gelesen und geschrieben (64x64-Raster, 9 Etagen, fünf Ebenen).

## Grenzen

- Nur mit Easy FPS Editor CE v1.10.5 getestet. Andere Versionen können Felder umbenennen.
- `shot` nimmt den Bildschirmbereich des Spielfensters auf; das Fenster bleibt kurz im Vordergrund.
- Nicht mit den Autoren des Easy FPS Editors verbunden oder von ihnen unterstützt. Kein Teil des Editors ist enthalten; die Bridge nutzt deine installierte Kopie.

## Sicherheit

Siehe [SECURITY.md](SECURITY.md). Die Bridge baut keine Netzwerkverbindungen auf.

## Lizenz

[MIT](LICENSE)

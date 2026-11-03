<div align="center">

# EFPSE Bridge

**Drive Easy FPS Editor CE projects from the command line.**
Read and write every project setting with the editor's own code, edit maps as text, import assets, validate, take screenshots and package, without opening the editor window.

[![CI](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml/badge.svg)](https://github.com/blgymtr/gz-bridge-app/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**English** · [Deutsch](README.de.md) · [Türkçe](README.tr.md)

</div>

## Why

Easy FPS Editor keeps many options behind checkboxes and panels: model flags, weapon and enemy fields, map properties. They live in binary project files that are hard to read or change by hand, and impossible to script. EFPSE Bridge loads **your installed copy of the editor** in the background, uses its own classes to load and save the project, and gives you plain JSON and text for everything. That makes settings visible, diffable and scriptable, for people and for AI assistants alike.

## Features

- **Every field, read and write.** `get` prints all fields of a weapon, enemy, decoration, map, texture, model, animation, HP, armour or tile, plus the `game`, `player` and `hud` settings. `set` changes any field, including array items (`frames[2]=5`).
- **Add, remove, reorder.** Create entries, delete them, and set the weapon slot order.
- **Maps as text.** `map` draws a floor as an ASCII grid (walls, player, enemies, weapons, lights, keys). `tile`, `entity` and `modifier` place textures, entities (player, enemy, weapon, decoration, ammo, keys, health, armour, lights) and modifiers (doors, exits, steps, hazards, barriers, triggers, terminals) on any of the 9 floors. `map-new` creates an empty 64x64 map.
- **Import assets.** Weapons, enemies and decorations from a folder (sprites, sounds, states), textures, and MD3 models with their skins.
- **MD3 tools.** Frame, surface, triangle and vertex counts, and a preview sheet of any frames rendered without starting the game.
- **Validation.** `check` looks for missing files, broken references, FSM commands that are not in the manual and other mistakes, and exits non-zero on errors (CI friendly).
- **Run and capture.** Open the editor, start the game on a given map, or play a key script (`W:200,LMB:40,WAIT:500,SHOT`) and save screenshots.
- **Package.** Build a distributable folder of the game.
- **Safe by default.** Every write makes a timestamped backup in `kopru_yedek/` first. Writes are refused while the editor is open, so the two never fight over the same files.
- **Two languages on the command line.** Commands and options work in English and Turkish (`get`/`al`, `--project`/`--proje`).

## Requirements

- Windows 10 or 11
- Easy FPS Editor CE **v1.10.5** (your own installation; it is not included)
- Python 3.9 or newer. `numpy` for MD3 commands, `opencv-python` for `preview`. Everything else uses the standard library
- Windows PowerShell 5.1 (included with Windows). The bridge starts its 32-bit version to load the editor

## Quick start

```powershell
git clone https://github.com/blgymtr/gz-bridge-app.git
cd gz-bridge-app
$env:EFPSE_ENGINE  = 'C:\Games\EasyFPSEditor_CE_V1.10.5'   # folder with EasyFPSEditor_CE.exe
$env:EFPSE_PROJECT = 'MyGame'                             # folder name under Projects\
python kopru.py projects
python kopru.py info
python kopru.py check
```

Options can also be passed directly: `python kopru.py --engine <folder> --project <name> <command> ...`

## Commands

| Command | What it does |
|---|---|
| `projects` | List projects in the engine folder |
| `info` | Weapons, enemies, decorations, maps, texture and model counts, game name |
| `list <collection>` | Names in a collection: `enemies decorations weapons maps textures models animations hps armours tiles` |
| `get <collection> [name\|index]` | All fields as JSON. Also `game`, `player`, `hud` |
| `set <collection> <name> field=value ...` | Change fields. For `game`, `player`, `hud` leave out the name |
| `add <collection> field=value ...` | New entry |
| `remove <collection> <name>` | Delete an entry |
| `order <collection> <name> <name> ...` | Move these names to the front (weapon slot order) |
| `save` | Re-save in the editor's own format |
| `map <name> [--floor N]` | Draw a floor as text |
| `tile <map> <texture\|empty> x y [x2 y2] [--floor N]` | Paint a tile or a rectangle |
| `entity <map> <type> x y [--index N] [--floor N]` | Place an entity: `player enemy weapon deco ammo key1-3 hp1-4 arm1-4 light1-6 none` |
| `modifier <map> <type> x y [--floor N]` | Place a modifier: `door door1-3 exit step1-3 hazard invisible barrier trigger1-10 terminal1-10 none` |
| `map-new <name>` | Empty map, added to the project |
| `import-weapon <name> <folder>` | Import a weapon (sprites, sounds, states) |
| `import-enemy <name> <folder>` | Import an enemy |
| `import-deco <name> <folder>` | Import a decoration |
| `import-texture <png> [type]` | Import a texture (type 2 = wall) |
| `import-model <name> <folder> [type]` | Import MD3 + skins (type 1 decoration, 2 enemy) |
| `md3 <name>` | Frame, surface, triangle, vertex counts |
| `preview <name> <out.png> [frame ...]` | Render model frames to a PNG without the game |
| `check` | All validations, non-zero exit on errors |
| `backup` | Back up the project now |
| `editor` | Open the editor |
| `play [--map N]` | Start the game on a map |
| `shot <out.png> [--wait s] [--keys "..."]` | Start the game, play a key script, take a screenshot |
| `pack` | Package the game |

Key script for `shot`: comma separated steps, `KEY:ms` holds a key, `LMB:ms` / `RMB:ms` click, `WAIT:ms` waits, `SHOT` takes a screenshot.

### Examples

```powershell
python kopru.py get weapons Shotgun
python kopru.py set enemies Imp health=120 speed=3.5
python kopru.py set game name="Night Shift"
python kopru.py map E1M1 --floor 0
python kopru.py tile E1M1 brick.png 10 10 20 10
python kopru.py entity E1M1 enemy 15 12 --index 2
python kopru.py modifier E1M1 door 15 9
python kopru.py import-model Barrel .\models\barrel 1
python kopru.py preview Barrel barrel.png 0 4 8
python kopru.py shot test.png --wait 6 --keys "W:400,LMB:60,WAIT:300,SHOT"
```

## Files

| File | Role |
|---|---|
| `kopru.py` | Commands, map read and write, imports, checks, MD3, packaging |
| `host.ps1` | Loads the editor's classes in 32-bit PowerShell and dumps or applies changes |
| `foto.ps1` | Starts the game, plays the key script, captures the window |
| `test_kopru.py` | Runs the write commands on a temporary copy of a project |

## Testing

```powershell
python test_kopru.py <engine folder> <project>
```

The test copies the project to `Projects\KopruTest`, runs the write commands there and checks the results. Your project is not touched.

## How it works

`host.ps1` starts in 32-bit Windows PowerShell, loads `EasyFPSEditor_CE.exe` as a .NET assembly and calls the editor's own resource classes to load the project. Public fields are converted to JSON. Changes from `kopru.py` arrive as a small JSON list of operations (`set`, `add`, `del`, `order`) and are saved through the same classes, so the files stay in the format the editor expects. Maps are read and written directly (64x64 grid, 9 floors, five layers).

## Limits

- Tested with Easy FPS Editor CE v1.10.5 only. Other versions may rename fields.
- `shot` captures the screen area of the game window, so the window stays on top for a moment.
- Not affiliated with or endorsed by the authors of Easy FPS Editor. No part of the editor is included; the bridge uses your installed copy.

## Security

See [SECURITY.md](SECURITY.md). The bridge makes no network connections.

## License

[MIT](LICENSE)

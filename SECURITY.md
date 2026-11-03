# Security policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Use GitHub's private
[security advisory](https://github.com/blgymtr/gz-bridge-app/security/advisories/new) form instead,
with steps to reproduce and your Easy FPS Editor version.

## What the bridge does

- It runs only on your own computer and makes **no network connections**.
- It loads `EasyFPSEditor_CE.exe` from the folder you give it and runs the editor's own .NET code
  inside a 32-bit PowerShell process. Only point it at an editor you trust.
- It writes only inside the project folder you name, after copying the files it changes to `kopru_yedek/`.
- `shot` and `play` start the game's `Game.exe` from that project; `shot` sends simulated key presses and mouse clicks to the game window.
- `host.ps1` and `foto.ps1` are started with `-ExecutionPolicy Bypass` for that call only. Read them before running if you are unsure.

## Supported versions

Only the latest commit on `main` is supported.

# Skript Support for Zed

This extension provides high-performance development tools for Skript (Minecraft 26.1.#).

## Features
- **Local Documentation:** Side-panel documentation generated from the Skript source code.
- **LSP (Language Server):** Real-time linting (missing colons, indentation errors) and intelligent autocompletion.
- **Camouflage Mode:** Designed to work alongside the `ViaPatch` system.

## How to Install
1. Open Zed.
2. Go to `Zed > Extensions` (or `Cmd + Shift + X`).
3. Click on **"Install Local Extension"**.
4. Select this `skript-zed` folder.

## How to use Documentation
1. Press `Cmd + Shift + P` (or `Ctrl + Shift + P`).
2. Type **"Skript: Open Local API"**.
3. It will open `docs/api.md` in a side split for quick reference.

## Integrated Linter
The LSP will automatically highlight errors in your `.sk` files.
- Red squiggly lines indicate syntax errors (like missing colons).
- Autocomplete will suggest common Skript effects and events as you type.

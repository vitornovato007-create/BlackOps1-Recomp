# BlackOps1-Recomp v0.1

Experimental scaffold for investigating static recompilation of Call of Duty: Black Ops (Xbox 360) with ReXGlue 0.10.0.

## Important

This repository contains **no game executable, ISO, assets, keys, or copyrighted game data**.

You must provide `game/default.xex` from your own legally obtained copy.

This v0.1 has one objective:

> Verify whether the Black Ops 1 Xbox 360 XEX can be accepted by the ReXGlue 0.10.0 code-generation pipeline.

It does NOT attempt to produce a playable Android build yet.

## Target pipeline

Xbox 360 PowerPC XEX
        |
        v
ReXGlue 0.10.0
        |
        v
Generated C++
        |
        v
Future ARM64 Android target
        |
        v
Future Vulkan/Mali-G76 renderer

## Repository layout

- `game/` - local game input; intentionally ignored by Git
- `generated/` - generated C++ output; ignored by Git
- `src/` - future Android/native wrapper
- `patches/` - game-specific fixes discovered later
- `docs/ROADMAP.md` - development roadmap
- `blackops1_manifest.toml` - initial ReXGlue configuration
- `.github/workflows/build.yml` - codegen workflow
- `setup.sh` / `setup.ps1` - local preparation helpers

## First test

1. Put your own XEX at:

   `game/default.xex`

2. Run the GitHub Action manually.

3. Download the generated artifact.

4. Inspect the first codegen errors.

Do not start writing game-specific patches until the first codegen report is available.

# Native-port study

The current `repo/build/` runner is the **Power Scale + Python Tag Team trial**.
Use the workspace's `Play Power Scale native trial.cmd`; see
`power-scale-trial/README.md` for the exact input, bridge, and test status.
`stock-deploy/` retains the earlier stock portable build.

- `repo/`: z3xox/BT3-Recomp checkout at `e22a34b`.
- `NATIVE_PORT_ASSESSMENT.md`: architecture and integration path.
- `native_port_preflight.py`: read-only comparison of an installer disc profile
  with this checkout's stock ELF gate.
- `ANDROID_FEASIBILITY.md`: general Android port assessment.
- `run-stock-generation.cmd`: isolated stock code-generation attempt using the
  installed build tools; it does not package or overwrite a playable install.
- `run-stock-build.cmd`: compile the generated stock runner in `repo/build/`.
- `run-stock-deploy.cmd`: assemble the portable Windows tree in
  `stock-deploy/` after the runner builds.
- `stock-deploy/`: isolated stock runner and bundled libraries. The front-end
  install wizard has not yet extracted game data into this tree.

## Local build result (2026-10-05)

Stock source generation, the OpenGL runner build, and stage 4 deploy completed.
The Windows PE dependency gate checked 23 files and reported the deploy tree
ready. The executable is `stock-deploy/Dragon Ball Z Budokai Tenkaichi 3 - Recompiled.exe`.
A direct runner smoke check stayed alive for 15 seconds, then was stopped. This
verifies startup without an immediate process exit; gameplay and the front-end
ISO installation have not yet been tested. The checkout does not
contain the separately shipped Tag Team native mod.

The local checkout has one source adjustment in
`repo/ps2xRuntime/src/lib/ps2_seammesh.cpp`: its optional native Vulkan path is
guarded when that backend is unavailable, and the corresponding stream markers
have no-op definitions for the OpenGL build. Windows Security blocked the
optional Mesa lavapipe dependency, so this deploy does not bundle the software
Vulkan fallback.

Stock build input is `../experiments/DBZ BT 3.iso`. The Power Scale trial uses
`../experiments/.full-install/game/maps/expanded-2x.iso` and an exact executable
and overlay profile. It does not use a stock hash-gate bypass.

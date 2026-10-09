# Second co-op match exit investigation

The split-layout ownership correction passed the user's first two-human match.
The subsequent session failed during ordinary second battle initialization,
before the controller could create another preparation checkpoint.

## Confirmed evidence

Archived `runner-coop-retest-guest-exit.log` lines 10253 onwards report an
unsupported instruction `0x8001` at guest PC `0x2F0`, then unsupported patched
code, followed by the main dispatcher ending. The bridge's `interpreted()`
explicitly requests a stop when `interpretUntil()` fails. The frontend exits
with code 0 after `runtime.run()` returns, including this stop path. That exit
code does not establish an intentional guest return.

`0x2BAAE8` is the Timer2 COMP writer and the last debug PC in this log. It has
not been shown to be the origin of the bad transfer. Caller and return address
at the failing interpreted entry were not recorded in the archived build.

The newest checkpoint is the first match's `20261007-214406-e5cdccab` directory.
Its baseline layout is 0 and held-ready layout is 1. Its cleanup receipt completed.
No preparation block covers the timer writer. The second match never reached
preparation, so there is no second-match RAM checkpoint to replay.

This run logs `clean menu teardown completed`, followed by menu selection of
one human, then two humans. The user's Fight Again report is accepted, but this
particular trace does not establish another prepared same-roster match.

## Diagnostic implementation

`ps2EntryRunner-coop-exit-capture.exe`, SHA-256
`09a9bd642cd28e5e9961474ca4609b91a1076769d57a72fd30ed796f56f00b80`.
UI Slice launchers select it; stable runners and the current internal installer
are retained. No live game was launched for this investigation.

The launcher sets `PS2X_EXIT_CAPTURE_DIR` to its private `guest-exit-captures`.
On an unsupported interpreted path, capture runs before requesting stop. A main
dispatcher return without an existing stop request also triggers capture.
Ordinary requested stops are excluded. One capture per process contains:

- `ram.bin`: 128 MiB guest memory under the guest execution lock.
- `context.bin`, `main-context.bin`: exact failing and main CPU contexts.
- `state.json`: reason, final PC/RA, interpreted entry PC/RA, guest tid, layout,
  manager, rematch state, and up to 200 recent main-context dispatch entries and
  generated branches on that host thread, including source PC/RA/SP/kind.

These are dispatch records, not an instruction-by-instruction interpreter trace.
Environment enable checks are cached outside the hot branch path. File paths
and guest memory are not printed to the console. Capture I/O failure is logged
without changing runtime stop behavior. Captures stay local.

## Checks and next evidence

Build and final incremental build passed. Headless production callback checks
passed RAM size/content, contexts, metadata, 200-record order/wrap, caller/layout,
duplicate suppression and I/O failure. See `codex-coop-exit-capture-check.log`.
Existing co-op ownership/arming/detach/unknown-write checks still pass.

Root cause and a gameplay fix remain unknown. Next live check: first two-human
match, return to selection, second two-human match. If the failure repeats, retain
the automatically generated capture with runner/controller logs. Then verify
1v1, 2v3, 5v5 and Fight Again. No new live pass or second-match fix is claimed.

# Local v0.2 / upstream v11 integration

Branch: `v02-v11-local`. Based on released project commit `7c23afa`, merged with the prepared upstream-v11 branch `50e4dfe`.

## Review and corrections

- Resolved the release diagnostics conflict without losing preview overrides or v11 failure reporting.
- Re-derived 18 roster overlay files against the merged base. Six files required manual conflict resolution. Kept the extended 253-slot roster and native reload receipts while taking compatible v11 changes.
- Fixed controller-mailbox native attach to use v11's seat ownership field, restored the missing selector Owner class, and prevented the native Autopilot from creating the emulator SDL controller hub.
- Preserved the reviewed native team-selection/controller-assignment interfaces, adding compatibility for the newer caller signature. The v11 emulator check-in UI is not adopted by this native candidate.
- Restored the missing Power Scale fusion predicate and the transformation side-wrapper target argument. The ordinary native destination and the authenticated Power Scale destination remain distinct; no eligibility check was bypassed.
- Kept native roster labels on the verified extended catalogue rather than the 161-slot stock-disc catalogue.
- New targeting/threat/tournament options use legacy/off defaults; ground running and beam assistance remain off. The tournament implementation may still install guarded code with its rule disabled. New enabled gameplay behavior requires live acceptance.

## Local verification

314 controller modules parse. All 16 regression cases pass (see local-native-checks.json): rematch polling, bulk transport, preparation timing, base/roster native input ownership, emitted Super fusion selector, defusion resource receipts, CPU fusion choice, failed-preparation restart ownership, reload hook authentication, retained co-op rematch ownership, full archived second-match preparation, CPU tactics and form-timer variants, base/roster v11 settings and native Autopilot construction.

Private retained captures and validation logs are under experiments/v11-local-validation, outside this source checkout. Tests use the merged controller and roster overlay; they do not accidentally import the released live modules.

## Limits

No live match, controller acceptance, renderer test, installer rebuild or publication was performed. Offline composition and emitted-code tests do not prove that every new v11 guest hook behaves correctly in a live fight. The existing second-match 0x216661A8 crash and installed save/FFA reports are not claimed fixed by this merge. The runtime binary is unchanged.

The published main branch, prepared upstream branch and installed game are preserved. This local source candidate is for the next development version.

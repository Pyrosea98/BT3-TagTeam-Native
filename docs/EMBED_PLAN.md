# Embed Tag Team in the native runtime

Owner: Codex. Coordination and evidence: COLLAB.md. Roadmap owner: Claude.

## Objective and current state

Keep the working Windows simultaneous-team game and clean rematches while replacing
Python/PINE orchestration and interpreted per-frame mod code with native components.
Android shares that implementation later; this Windows baseline is not an APK.
Do not implement defeat-triggered de-transformation yet.

### Product decisions received 2026-10-07

The M5 native UI slice connects real preparation events/selected rosters and
post-start-gate release acknowledgement to loading/settings/About Vulkan views.
All25 team layouts in EN/ES, error/release/stale/fast-preparation gates, actual
GPU readbacks and real settings persistence/input/link checks pass offline.
The dedicated native-ui-slice trial is ready for ONE coordinated5v5/rematch/
settings/About session; live parity remains UNKNOWN. NATIVE_UI_SLICE.md holds
implementation, evidence and limits. Python still owns semantic orchestration;
its elimination and ARM64/APK milestones remain separate.

- Targets: Windows x64, Windows ARM64, Android ARM64. Shared lifecycle, UI
  asset formats and game logic must remain portable. Architecture-specific
  acceleration needs a portable path; no ARM build or performance claim yet.
- Approved fonts: Kanit Black Italic for Title; Barlow Condensed ExtraBold
  Italic for Body and Numeric. Include both bundled OFL notices in distribution.
  Font rasterization is a build-time operation; runtime text uses native assets.
- Credits: Power Scale = LetsPlayBt3; Tag Team = The Mufti. Both confirmed channel links are displayed in
  About and open only on an explicit confirmed selection.
- External testers: no release yet while required product components are missing.
  Later packages use the latest validated stable build.
- HUD extraction passed: entry-5 hash pinned; all eight named assets match native
  capture PNGs exactly. Clock palette offsets: grey10848, yellow11040, red11232.
  This offline helper has not replaced the native importer or draw layer.

Before implementing palette-swapped glyphs, define distinct index ranges for
transparent pixels, outline coverage, glow coverage, inner highlight and fill
gradient/coverage. Colour variants change fill/highlight colours while preserving
the outline and transparency. Metrics and atlas pages need a versioned portable
format with explicit byte order. Check the full approved character set fits the
512x256 limit before assuming one page per style/size; request a spec amendment
if it requires multiple pages. Native blend conventions determine whether those
coverage values use straight or premultiplied colour; do not apply both.

Immediate work remains clock producer/CLUT-selection attribution, then glyph
assets, native draw layer and loading-cover integration. Existing GS-worker
builder_ra=0 captures do not identify the clock routine. Static generated-source
literal searches also do not establish its caller; addresses can be indirect.

Claude reports original-roster 5v5 preparation passed; the earlier mixed Power Scale
5v5 still fails status173. That rules out a universal ten-actor limit, but different
resource sizes or pool demands can still matter. Labels now use runtime slots;
portrait mapping remains incomplete. Successful tested samples do not validate every
extended fighter or extended Japanese voice bank.

Measured inventory supplied by Claude, not a migration estimate:

| Role | Modules | Python lines |
| --- | ---: | ---: |
| Guest MIPS generators | 155 | 40,167 |
| Host orchestration | 6 | 3,492 |
| Presentation/settings UI | 11 | 4,945 |
| Data/policy/helpers | 55 | 8,722 |
| Total | 227 | 57,326 |

The approximately75KB autopilot drives this system. Original5v5 preparation wrote
1,274 manifest blocks, approximately561KB MIPS/data (554KB in caves). Claude observed
approximately4.9M interpreted instructions/s and approximately20 fight updates/s.
These show substantial interpreter work; page counts alone do not establish the
fraction of CPU time or exclude renderer/audio costs.

## Work order and roadmap mapping

### Standalone product contract (update after Claude01:35)

The released product is one Windows application or Android APK that boots the
modded game. Current launchers, Python controllers and PINE are development tools;
the current working trial does not yet satisfy this contract.

1. The runtime entry point owns first-run import, configuration and the game loop.
   Import verifies a supported user-disc hash, extracts assets and builds the
   versioned resource manifest. Remove fixed developer ISO/layout assumptions.
2. PINE is an optional developer bridge, with a build option to omit it. Production
   lifecycle and preparation call runtime interfaces directly, without a socket.
3. Move lifecycle, preparation, rematch, cover and worker ownership into this
   process. Publish game-thread snapshots and commit generation-checked changes
   at safe boundaries; preserve clean teardown and transformation/fusion receipts.
4. Replace trial environment flags with one typed runtime configuration and
   built-in supported-profile defaults. Keep diagnostics behind a developer
   switch; production requires no helper CMD files or PS2X_* flags.
5. Render mod menus, settings, training, loading and HUD natively using extracted
   sprites and a baked glyph atlas. Store saves/settings/caches in platform
   app-data. Upload static assets once per residency period; invalidate or reload
   on actual resource loss, rather than assuming guest VRAM remains untouched.
6. First-run import replaces run_power_scale_native.py. Inspect persisted Vulkan
   pipeline/shader caches and measure first-use hitches before adding warm-up.
   Cache warm-up is a planned import capability, not a verified performance fix.

Cut first: production dependency on the external controller, by migrating its
lifecycle observer and checked preparation transaction. A native loading cover
can proceed alongside that work and remove repeated cover texture uploads.
Retain the development Python oracle until the corresponding native paths pass.
Cold generators may remain build-time Python emitting authenticated packs keyed
by supported ISO hashes; neither Windows nor Android runtime embeds Python.
Do not add optional standings, a portable-Python shipping branch, speculative
shader warm-up or defeat-triggered de-transformation to this migration.

Latest inventory: PYTHON_LEDGER.md (Claude-owned) supersedes the historical counts
above. Portrait mapping is now integrated for all253 slots, retaining confidence
metadata; inferred identities are not independently live-verified. Basic ki
steering passed the focused L3/fire test; beams, ultimates and other projectile
families remain unverified. Android build/graphics/platform integration is still
required after the shared native implementation; an APK is not ready.

### Stage0: stabilize and measure (M1, foundation for M3/M4/M5)

- Replace the session-total interpreter guard with an uninterrupted-stretch budget.
  Reset on native dispatch; retain stop requests, unsupported-opcode failures and
  the2B uninterrupted limit for all contexts. Keep executeEntry independent of reset.
- Optional `PS2X_INTERP_PROFILE=1`: exact instruction histogram by4KB PC page,
  including executed delay slots; top30 and total/main/service counts at host-thread
  teardown. Profiling is off in normal builds by default. Counts are not CPU timings.
- Record preparation phases, install/snapshot/status-wait operation durations and
  total duration in controller log and each run's preparation-timings.jsonl.
  Phase intervals are disjoint; nested operation totals must not be added together.
  Wall durations include player pauses, disk activity and waits.
- Claude owns page-to-module mapping and live soak/oracle capture. Gate:60-minute
  original5v5 with rematches/fusion, then mixed-roster retest with173 diagnostics.
- Current baseline still requires Python and generated guest code. It is not M3/M4.

### Stage1: native lifecycle and state contract (M3)

Introduce a versioned match specification in C++: ISO/profile hash, monotonically
increasing match generation, mode, engine-slot IDs, costumes, teams, human assignments
and validated settings. Capture native selected rows at the existing idle boundary.
Every worker/result must belong to that generation and manager identity.

Lifecycle: menu -> loading -> held leaders -> preparing -> held ready -> active ->
result -> retiring workers -> native reset -> rebuilding. Error/cancel paths retire
owned work and preserve diagnostics; never expose a partially prepared match.
Use the existing native rematch boundary and cleanup contract, not a RAM restore.
Preserve transformation/fusion ownership checks and release acknowledgement.

First deliverable is native observation/validation alongside Python as oracle.
Next move scheduling and resource-request transport to the game thread at safe
boundaries. Keep PINE available for debugging; remove it as a production dependency
only after the native preparation path is complete. Do not let host workers access
live guest objects concurrently without the frame-boundary transaction protocol.

### Stage2: preparation builders and resources (M3, overlaps M4)

Port pure tables/policy and the checked manifest transaction into C++, then the
resource queue, private actor/model allocations, graphics capacity, activation and
worker startup in dependency order. Explicit DLC volume4 routing and logical native
IDs, SHBT bounds, collision ownership, audio ring-only exclusions, rollback and
status173 node checks are requirements, not optional compatibility code.

Moving PINE transport alone does not remove Python: current generators depend on
live addresses. Every production generator must become a native builder, a frozen
feature with runtime control data, or a native function before M3 can be complete.
Build-time Python may initially produce developer artifacts; the released installer
and runtime must not require an installed Python interpreter.

### Stage3: remove interpreted mod hot paths (M4)

Rank features using the new histogram and Claude's window map, then migrate one
coherent feature at a time. Contact/projectile targeting, fighter update/AI and
cosmetic loops are candidates; choose their order from actual counts and timings.

Preferred routes:

1. **Frozen cave pack compiled ahead of time** for straightforward generator output.
   Refactor per-match immediates into a versioned control block, freeze entry points
   at build time, compile through the existing recompiler and register native bodies.
   Maintain a small number of bounded variants where counts change control flow.
   Prove that generator-time layout/address decisions can be represented this way;
   this is not an automatic conversion of all155 generators.
2. **Native C++ replacements** for host lifecycle, allocator ownership, complex
   dynamic builders and hot features where guest-code translation remains awkward.
   Preserve guest register/GP, memory, delay-slot and return conventions at hooks.

Do not compile C++ at match startup or require a compiler on Android. A runtime
decode cache would be an interim optimization, not completion of the embedding goal;
defer it until profiling identifies a need. Dirty code still needs correct invalidation.

Each feature requires explicit native registration and a compatible code/profile
fingerprint; generic dirty-cave handling must not accidentally select a stale native
body. Retiring a match invalidates its control block and worker leases before any
new allocations become visible. Normal game overlays may still use the interpreter;
the target is removing the mod's per-frame hot paths, not banning all fallback code.

### Stage4: loading/presentation and immutable cache (M5)

Use phase timing evidence to decide what to overlap. Begin IO during native loading
only after selection is final; allocate/attach actors only when native ownership is
safe. Result-screen rematch prefetch is cancellable and belongs to the next generation.

Cache immutable file bytes/decoded assets by ISO hash, physical file ID, costume,
damage variant and decode version with a bounded memory budget. Never cache live
actor pointers, pool-list nodes, mutable collision bindings or guest snapshots across
native reset. Rebuild those objects on each match. Native loader caches already exist;
measure misses before adding a second cache.

Move cover animation/progress to native code using extracted install-time assets.
Hide the cover only once preparation and release acknowledgement complete. Removing
visible loading is a measured outcome, not a reason to bypass the held-ready gate.

### Stage5: installers and Android (M6/M7/M8)

- Windows: hash-verified local ISO input, local BIOS policy matching the core,
  extraction into owned install paths, native runtime, uninstall and sanitized log
  export. No game assets, ISO, BIOS, saves or keys in release packages/log bundles.
- Logo/portraits come from the user's disc at INSTALL time with ISO-hash-keyed maps.
  Developer extracted assets are not redistribution assets.
- Credits in installer/about/release notes: “Power Scale: [author's verified credit];
  Tag Team mod: [creator's verified credit].” Resolve names from project metadata or
  the user before publishing; do not invent credits. Revalidate a new Power Scale ISO.
- Android starts with stock-core ARM64 compilation and title-screen proof, then
  Vulkan/input/audio/storage/JNI lifecycle. Current x86/SIMD and Windows presentation
  assumptions need actual platform work. No performance promise before device tests.
- External tester release follows the ROADMAP checklist and user-selected channel.

## Oracle and acceptance gates

Claude owns `claude_oracle_*` and module/window mapping; Codex owns native changes.
Compare equivalent rosters/settings at held-ready, activation, transformation,
fusion/defusion, two consecutive rematches and return to select.

A whole-RAM hash is useful only for deterministic, identical allocation layouts.
Different native allocations, audio streaming and timing make it insufficient as
a sole gate. Also compare normalized actor/resource identities, pool invariants,
typed pointers, control words, ownership, selected stats and release state; exclude
only documented volatile data. Maintain negative checks for malformed resources,
ownership conflicts, stale generations and cancellation. Preserve Python captures
as oracle evidence until the corresponding feature passes native comparison.

## Immediate handoff

### Update after Claude19:30 (2026-10-06)

User priority: M3/M4 embedding and M5 native loading first; stop repeating the
transformation/defusion/rematch matrix unless a change touches it. Claude reports
two successful defusions followed by several clean rematches, including damaged
bodies. Prior transformation-specific hook receipt remains untested, not a reason
to block these independent migration stages.

First M4 feature is now compiled: four frozen leaf getter/resolver bodies at
07368000/07368200/07368600/07368800, with exact byte authentication before native
dispatch and reviewed capacity/mode variants. Developer generation emits C++
control flow, not a runtime decode cache.1600 independent MIPS/C++ comparisons
PASS; native runtime compile/link PASS. Dedicated runner D232093A and root
native targets test launcher add bounded live interpreter comparison. See
NATIVE_TARGETS_TRIAL.md for oracle limits and the first live request. Gameplay,
performance and Android validation UNKNOWN. No native lifecycle ownership or
Python removal is claimed from this leaf migration.

Next M3/M5 step: game-thread publication of a versioned lifecycle/cover snapshot
(generation, phase, progress, roster, release/error/lease state) and consumption
through the existing host UI/native Vulkan renderer. Extracted install-time art
feeds logo/portraits/VS/seven Dragon Balls; retire guest cover rendering only
after visibility and acknowledgement equivalence. Native cover NOT implemented
yet. Claude owns portrait mapping and dead-target diagnosis. Native retarget
behaviour must follow that evidence as a separate change after baseline parity.

The notes below describe the earlier01:15 handoff, retained for history.

Latest after Claude01:15: bulk trial passed1v5/two rematches and a5v5/fusion session.
Guard fix live-validated by13.544B interpreted instructions over1091.881s;60-minute
soak still pending. Defusion ownership handoff now has a staged fix/offline regression
for transform -> fuse -> defuse -> transform; live retest pending. Conservative stale
receipt quarantine leaves uncertain allocations to match cleanup; capacity guards
remain. New staged install purposes improve attribution and release-start timing
separates intro acknowledgement from preparation.

Profile07473000 geometry/07474000..07475FFF lights_a/07476000..07479FFF lights_b are
the loading cover,15.2% aggregate session instructions. Split phase attribution before
treating that as active-fight cost. Getter/target page07368000 remains first native
feature candidate; no feature is migrated yet. Dead-target lock and rare CPU transforms
remain separate gameplay defects.

After Claude's A/B, music and Select passed on both roster/baseline; long-session
soak remains pending. First1v5 timing: nine captures9140ms out of19250ms total;
phase6:Ready5484ms also includes start/intro acknowledgement. Captures feed live
builder/ownership validation and must not be treated as disposable rollback copies.

New isolated transport experiment: “Play Power Scale bulk snapshot test.cmd” uses
native-bulk-snapshot748AF28E and native bridge opcode16 for bounded contiguous reads,
preserving all full captures and the existing quiet/apply/resume gates. Native/Python
offline bounds/framing/byte checks and compile PASS; live throughput and preparation
speedup UNKNOWN. This is an interim M3 transport component; Python and per-frame
interpreted caves remain. Existing baseline/current session unchanged. No external
RAM audit during controller operation; socket scheduling remains single-client.

Baseline runner: ps2EntryRunner-native-embedded-baseline.exe, selected by root
“Play Power Scale embedded baseline test.cmd” (Vulkan + profiling). Normal launchers
retain native-roster while the new baseline is tested. Compile/unit checks do not
replace the live soak. Continue portrait/status173 research in parallel; it must not
block lifecycle migration, and migration must not falsely mark those issues resolved.

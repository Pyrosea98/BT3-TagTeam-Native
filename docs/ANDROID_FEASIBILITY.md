# Android feasibility (general assessment, 2026-10-05)

An Android port is technically plausible, but this BT3-Recomp checkout does
not have an Android target or APK. It currently builds desktop Windows, Linux,
and macOS runners. The game's translated C++ and guest-memory model are a
potentially reusable core. The top-level CMake has an AArch64 `sse2neon` path,
already used for Apple Silicon, but that is only one portability layer.

The largest Android-specific work is the host layer: the current default
window/renderer is SDL2 desktop plus OpenGL 3.3, while Android exposes OpenGL
ES and Vulkan. A Vulkan renderer may be the better starting point, but its
Android surface/presentation path and required GPU features would need a
separate audit. The build also needs Android NDK/arm64 configuration, FFmpeg
and other native dependencies for that ABI, JNI/Activity lifecycle, touch or
controller UI, permissions/storage, ISO extraction, audio, and APK packaging.
The mod loader would need to load arm64 `.so` modules rather than Windows DLLs.
Power Scale still needs its own executable and overlay compatibility work.

A useful later proof of concept is: compile the recompiled stock core for
`arm64-v8a`, boot to title on one known Vulkan-capable phone, then test 1v1
rendering and controller/audio before porting Tag Team. Desktop CPU/RAM/GPU
recommendations cannot be converted directly into a phone performance promise;
thermal throttling, memory, and GPU drivers matter. No device-specific speed
claim is made without an actual Android build and benchmark.

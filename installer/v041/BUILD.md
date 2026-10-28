# v0.4.1 Windows packaging

Current native source: https://github.com/Pyrosea98/BT3-TagTeam-Runtime/tree/decomp-native

The earlier installer folders target the older runtime; use this folder for v0.4.1.
Build the engine using its release Dockerfile and inside.sh. The scripts here document the exact maintainer staging layout under F:/BT3-Builds; adjust these paths for another machine. stage_payload.py authenticates the initializer against the stock reference before adapting it to the supported profile.

ImportRecipes.zip in the v0.4.1 release supplies import-data/ (compressed authenticated file deltas and content manifest). Place that directory in payload/ beside the native Windows release, embedded CPython 3.11.9 with Tk and Pillow 12.3.0, app.pyw, importer.py, credits_splash.py, assets/, manual/, recommended-settings.txt and release-profile.json. Compile Play.cs with the Windows .NET Framework C# compiler and the supplied icon. Supply your own completed save seed if desired; no disc image or extracted game archives belong in Git.

Run test_importer.py, then app.pyw --check-package using the embedded Python. Compile installer.iss with Inno Setup 6.7.3. The issuer's build_content.py creates authenticated copy/XOR recipes from their locally owned supported ISO and approved loose-data profile; it never modifies the input ISO. Use the release verification and SHA256SUMS for the exact published artifacts.

The installed app defaults to Vulkan. Existing saves/settings are preserved. Both normal and optional 2x maps use the same gameplay fixes. Android packaging is separate.

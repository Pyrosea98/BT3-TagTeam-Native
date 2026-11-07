# Build the alpha updater

The issuer scripts stage only the manifest-selected game-data changes from an authenticated0.4.1 base and the matching v05 native EXE/DAT/MEM/SDL. Adjust F: paths in inventory.py/package_update.py for your own data. Generated manifests/blobs belong in the release asset, not in Git. No ISO, AFS, BIOS or private saves belong in this source repository. update_player.py uses only the standard library in the existing installation's embedded Python. Package Update.cmd/update.py/README.txt/payload/update.json and only referenced payload/blobs files.

Run test_update.py (rollback, corruption, preservation) and test_package.py for both map sizes. Freeze and verify hashes after the final native build. Publish as a prerelease; keep0.4.1 stable. The update journal supports recovery of interrupted writes; retain the local .updates backup until satisfied.

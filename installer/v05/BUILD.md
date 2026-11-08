# Build the Windows installers

Use the current native alpha update bundle and the frozen authenticated 0.4.1 full payload as inputs. The latter contains Python/Tk/Pillow, fonts, credits, manual, import recipes, runtime and optional save seed. Neither the ISO nor extracted AFS archives are published in source.

Run stage.py --stable-payload F:/path/to/stable/payload --alpha-update F:/path/to/current/update --output F:/path/to/new/output using Windows Python. Run it in a new output folder, not over a player installation. It builds Play.exe using the Windows .NET Framework C# compiler; adjust that compiler path for another system. It copies only distribution files, never the stable payload/data folder, and creates a bootstrap alpha update with the current launcher/channel files. The alpha input profile must use a full compressed recipe, verified in the issuer build.

Compile the two staged .iss files with Inno Setup 6.7.3. Run test_channels.py, test_update.py and test_importer.py with TEMP/TMP set to an F: test directory. Test actual Setup extraction, authenticated import, bootstrap and the update wizard, as well as exact package upgrades from stable normal/2x and earlier published alpha. Test on copies; keep gameplay saves untouched. Stage source files as UTF-8 explicitly.

Publish both EXEs and the portable update ZIP with SHA256SUMS and matching source. Keep the per-release bt3-revision notes marker equal to the installed profile revision, including replacements under the same tag. The stable release is separate and must not be overwritten by preview publication.

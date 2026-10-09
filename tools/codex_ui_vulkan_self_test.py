"""Developer harness: run the native GPU test without a game, ISO or PINE."""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
if __name__ == '__main__':
    with (HERE / 'power-scale-trial/codex-ui-vulkan-self-test.log').open('wb') as log:
        result = subprocess.run([
            str(HERE / 'repo/build/ps2xRuntime/ps2EntryRunner-native-ui-vulkan.exe'),
            '--native-ui-vulkan-self-test', str(HERE / 'ui-assets/glyph-atlas-v2'),
            str(HERE / 'power-scale-trial/native-ui-vulkan-capture'),
        ], stdout=log, stderr=subprocess.STDOUT, timeout=45)
    print('Native Vulkan self-test exit:', result.returncode)
    raise SystemExit(result.returncode)

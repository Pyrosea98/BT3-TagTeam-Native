"""Developer-only Vulkan UI compositor trial, with one selected UI language."""
import os
import sys
from pathlib import Path

if __name__ == '__main__':
    import run_power_scale_native as launch
    name = 'ps2EntryRunner-native-ui-vulkan.exe'
    launch.RUNNER_FEATURES[name] = frozenset(('rematch', 'roster'))
    if '--runner' in sys.argv:
        raise ValueError('Native UI trial uses its dedicated runner')
    here = Path(__file__).resolve().parent
    if (here / 'GAME_LOCK').exists():
        raise RuntimeError('A coordinated game session owns GAME_LOCK; do not start another trial')
    language = 'en'
    if '--ui-language' in sys.argv:
        position = sys.argv.index('--ui-language')
        language = sys.argv[position + 1]
        del sys.argv[position:position + 2]
        if language not in ('en', 'es'):
            raise ValueError('Choose --ui-language en or es')
    os.environ['PS2X_NATIVE_UI_ASSETS'] = str(here / 'ui-assets/glyph-atlas-v2')
    os.environ['PS2X_NATIVE_UI_TEST'] = '1'
    os.environ['PS2X_NATIVE_UI_LANGUAGE'] = language
    sys.argv.extend(('--runner', name, '--no-controller'))
    raise SystemExit(launch.main())

"""Process-only native preview settings; never alter saved player preferences."""
import os

def settings(values):
    value=os.environ.get('BT3_PREVIEW_DIAGNOSTICS')
    if value not in ('0','1'):return values
    enabled=value=='1'
    return dict(values,keep_preparation_diagnostics=enabled,
                capture_freeze_dumps=enabled,record_battle_diagnostics=enabled)

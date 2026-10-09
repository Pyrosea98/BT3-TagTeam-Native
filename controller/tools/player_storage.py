"""Bounded generated-file retention, only in an installer-owned player profile.

Never touches user states/cards or a developer folder. Prior checkpoint archives
referenced by trainer slot receipts are retained so slot ownership remains provable.
"""
import json
import re
import runtime_profile
import shutil
import stat
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def prune(root=ROOT,keep=3):
    if type(keep)is not int or keep<1:raise ValueError('Keep at least one generated session')
    root=Path(root).resolve()
    marker=root/'player-install.json'
    if not marker.is_file() or json.loads(marker.read_text()).get('storage_policy')!=1:return []
    protected=set()
    for runtime in ('runtime128','runtime28'):
        # PCSX2's data folder: the runtime folder on Windows, runtime/PCSX2 for the Linux AppImage.
        for claim in (runtime_profile.data_directory(root/runtime)/'sstates').glob('*.trainer-claim.json'):
            try:
                item=json.loads(claim.read_text());protected.add(Path(item['archive']).resolve().parent)
            except (OSError,ValueError,KeyError):return [] # uncertain ownership: keep all
    removed=[]
    for relative,required in (('analysis/prepared-states','session.json'),('analysis/autopilot','status.json')):
        parent=(root/relative).resolve()
        if not parent.is_relative_to(root) or not parent.exists():continue
        runs=sorted((p for p in parent.iterdir() if re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{8}',p.name)
                     and p.is_dir() and not p.is_symlink() and (p/required).is_file()),
                    key=lambda p:p.stat().st_mtime,reverse=True)
        for run in runs[keep:]:
            actual=run.resolve()
            if actual.parent!=parent or actual in protected:continue
            # Do not traverse junctions introduced into a generated run.
            def reparse(path):
                return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT)
            if reparse(run) or any(reparse(p) for p in run.rglob('*')):continue
            shutil.rmtree(actual);removed.append(str(actual))
    return removed


if __name__=='__main__':print(json.dumps(dict(removed=prune())))

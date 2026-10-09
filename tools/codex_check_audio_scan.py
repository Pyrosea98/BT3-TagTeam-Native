"""Regression checks against both real audio-alias failure captures; no game IO."""
from pathlib import Path
import json
import struct
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install
install()
from codex_audio_scan import audio_data_literals
from extra_special_pools import pointer_word_indices


def main():
    captures=HERE/'power-scale-trial/controller/game/analysis/prepared-states'
    reports=[]
    for folder in ('20261005-194512-225452d2','20261005-212948-20563d0e'):
        ram=(captures/folder/'00-original-selected-match.bin').read_bytes()
        def scan(data):
            raw={int(i)*4 for i in pointer_word_indices(np.frombuffer(data,dtype='<u4'),0x1AFC920,96)}
            literals,receipts=audio_data_literals(data,raw)
            return raw,literals,receipts
        raw,literals,receipts=scan(ram)
        assert raw=={0x460B40,0x1AFC904} and literals=={0x460B40}
        assert raw-literals=={0x1AFC904}
        # Unknown heap, stream/header metadata and stale packet pointers survive.
        for at in (0x7800100,0x44EB60,0x477D24,0x2C9370):
            changed=bytearray(ram);struct.pack_into('<I',changed,at,0x1AFC920)
            refs,excluded,_=scan(changed)
            assert at in refs-excluded and refs-excluded!={0x1AFC904}
        state=0x2C9350
        start,length=struct.unpack_from('<2I',ram,state+32)
        addresses={start-4,start,start+length-4,start+length,0x7804188}
        excluded,_=audio_data_literals(ram,addresses)
        assert excluded=={start,start+length-4}
        for pointer,value in ((state+36,length+2048),(0x2C7074+4,0x299E8),
                              (0x44EB28+4,0),(0x264D00,0)):
            changed=bytearray(ram);struct.pack_into('<I',changed,pointer,value)
            assert not audio_data_literals(changed,{0x460B40})[0]
        reports.append(dict(capture=folder,raw_refs=sorted(raw),excluded=sorted(literals),
                            retained=sorted(raw-literals),audio_receipts=receipts))
    output=dict(status='PASS',scope='Bounded scan exception; genuine aliases still fail strict expected-set guard',
                actual_failure_captures=reports,game_launched=False)
    (HERE/'audio-scan-offline-check.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print('PASS: both real false positives excluded; unknown/control/staging aliases retained; malformed owners rejected')


if __name__=='__main__':main()

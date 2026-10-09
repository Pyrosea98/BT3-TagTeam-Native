"""Extract Power Scale's host-opened MOD.BIN from the selected ISO."""
from pathlib import Path
import hashlib,struct
HERE=Path(__file__).resolve().parent
ISO=HERE.parent/'experiments/.full-install/game/maps/expanded-2x.iso'
def member(path):
    with ISO.open('rb') as f:
        f.seek(16*2048);pvd=f.read(2048)
        if pvd[1:6]!=b'CD001':raise ValueError('Not ISO9660')
        record=pvd[156:190]
        for part in path.split('/'):
            sector,size=struct.unpack_from('<I',record,2)[0],struct.unpack_from('<I',record,10)[0]
            f.seek(sector*2048);directory=f.read(size);offset=0;found=None
            while offset<len(directory):
                length=directory[offset]
                if not length:offset=(offset//2048+1)*2048;continue
                row=directory[offset:offset+length];offset+=length
                name=row[33:33+row[32]].decode('ascii').split(';')[0]
                if name.upper()==part.upper():found=row;break
            if found is None:raise FileNotFoundError(path)
            record=found
        sector,size=struct.unpack_from('<I',record,2)[0],struct.unpack_from('<I',record,10)[0]
        f.seek(sector*2048);data=f.read(size)
        if len(data)!=size:raise ValueError('Truncated ISO member')
        return data
if __name__=='__main__':
    for name in ('BIN/MOD.BIN','DATA/MOD.AFS','DATA/DLC.AFS'):
        data=member(name);target=HERE/'power-scale-input'/name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        print(target,len(data),hashlib.sha256(data).hexdigest())

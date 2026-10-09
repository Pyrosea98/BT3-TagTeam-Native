"""Read-only fusion recipe/hook audit of supplied supported Power Scale captures."""
from pathlib import Path
import json,struct,hashlib
from elftools.elf.elffile import ELFFile
HERE=Path(__file__).resolve().parent
ROOT=HERE/'power-scale-trial/controller/game/analysis/prepared-states'
report={'captures':[],'mod':{},'native_getter_callers':{}}
mod=(HERE/'power-scale-input/BIN/MOD.BIN').read_bytes()
report['mod']={'sha256':hashlib.sha256(mod).hexdigest(),'linked_base':'008C69C0','live_base':'008CA9C0','unlock_hook_file_offset':'2264','unlock_hook_hex':mod[0x2264:0x2298].hex()}
for folder in ROOT.iterdir():
 if not any(s in folder.name for s in ['20261009-095231','20261009-100657','20261009-101345']):continue
 f=folder/'16-ready-held.bin';ram=f.read_bytes();u=lambda a:struct.unpack_from('<I',ram,a)[0]
 item={'capture':folder.name,'rows':[],'hooks':{}}
 for index in range(12):
  model=u(0x31c640+index*4)
  if not 0x100000<=model<len(ram)-0x1000:continue
  p=u(model+0x91c)
  if not 0x100000<=p<len(ram)-0x100:continue
  item['rows'].append({'model_index':index,'cid':u(model+12),'parameter':hex(p),'ad':ram[p+0xad],
   'cost':list(ram[p+0xae:p+0xb1]),'kind':list(ram[p+0xb1:p+0xb4]),'result':list(ram[p+0xb4:p+0xb7]),
   'restoration_partner':list(ram[p+0xb7:p+0xba]),'partner_lists':[list(ram[p+0xba+j*4:p+0xbe+j*4]) for j in range(3)],'raw_ad_c5':ram[p+0xad:p+0xc6].hex()})
 for address in [0x203830,0x20e340,0x20e3e8,0x8c8c24,0x8ccc24,0x8cd188]:item['hooks'][hex(address)]=ram[address:address+32].hex()
 report['captures'].append(item)
with (HERE/'power-scale-input/SLUS_216.78').open('rb') as f:
 elf=ELFFile(f)
 for seg in elf.iter_segments():
  data=seg.data();base=seg['p_vaddr']
  for at in range(0,len(data)-4,4):
   w=struct.unpack_from('<I',data,at)[0]
   if w>>26==3 and ((w&0x3ffffff)<<2) in [0x20e340,0x20e370,0x20e3a0,0x20e3e8,0x20e450]:
    report['native_getter_callers'].setdefault(hex((w&0x3ffffff)<<2),[]).append(hex(base+at))
print(json.dumps(report,indent=2))

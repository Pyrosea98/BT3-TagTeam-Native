"""Native trial counters for projectile eligibility and geometry results."""
import struct,time,threading,json
CONTROL=0x071af000
def emit(a,group,index,*,preserve=False):
    # SHOT_WORKER reserves 0x50..0x5f; its saved registers end at 0x4f.
    if preserve:
        a.i(63,8,29,0x50);a.i(63,9,29,0x58)
    a.li(8,CONTROL+0x200+0x100*group);a.r(0,9,0,index,4);a.r(0x2d,8,8,9)
    a.lw(9,8);a.addiu(9,9,1);a.sw(9,8);a.sw(2,8,4)
    label='probe_'+str(len(a.words))
    a.branch(4,2,0,label);a.lw(9,8,8);a.addiu(9,9,1);a.sw(9,8,8);a.label(label)
    if preserve:
        a.i(55,8,29,0x50);a.i(55,9,29,0x58)

def start(pine,process,path):
    def watch():
        while process.poll() is None:
            try:
                with pine.PineClient(timeout=2) as p:
                    result=None
                    if p.read_u32(CONTROL)==0x4d434f31:
                        data=p.read(CONTROL+0x200,0x200)
                        result={name:[dict(index=i,attempts=n,last_result=r,passed=h)
                            for i in range(12) for n,r,h in [struct.unpack_from('<3I',data,g*256+i*16)] if n]
                            for g,name in enumerate(('eligibility_by_physical','geometry_by_model'))}
                        result['frame']=p.read_u32(CONTROL+60)
                if result is not None:path.write_text(json.dumps(result,indent=2)+'\n')
            except Exception:
                if process.poll() is not None:return
            time.sleep(2)
    threading.Thread(target=watch,name='native-contact-probe',daemon=True).start()

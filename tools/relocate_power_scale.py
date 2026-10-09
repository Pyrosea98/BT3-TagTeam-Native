"""Relocate the exact Power Scale absolute-address module into its native allocation."""
import hashlib,struct,time
from collections import deque
LINK_BASE=0x8c69c0
CONTROL=0x07fff000
MAGIC=0x42544d52
SHA256='a282407339132ffe0ba51a7770deee4ef211faaff99c9ac4535d1b1f15633228'

def relocate(data,base):
    if hashlib.sha256(data).hexdigest()!=SHA256:raise ValueError('Unrecognized Power Scale module')
    if base&31 or not 0x400000<=base<0x2000000-len(data):raise ValueError('Invalid module allocation')
    delta=base-LINK_BASE;words=list(struct.unpack('<4096I',data));original=list(words)
    highs={};changes={};states={};queue=deque()
    def enqueue(index,state):
        if not 0x200//4<=index<0x3000//4:return
        old=states.get(index)
        merged=state if old is None else {r:old.get(r,frozenset({None}))|state.get(r,frozenset({None})) for r in old.keys()|state.keys()}
        if merged!=old:states[index]=merged;queue.append(index)
    def consume(state,register,low,signed,index):
        targets=set()
        for owner in state.get(register,()):
            if owner is None:continue
            high=original[owner]&0xffff
            address=(high<<16)+(low-0x10000 if signed and low&0x8000 else low)
            inside=LINK_BASE<=address<LINK_BASE+len(data)
            target=address+delta if inside else address
            wanted=((target+0x8000)>>16 if signed else target>>16)&0xffff
            if owner in highs and highs[owner]!=wanted:raise ValueError(f'Conflicting module relocation at {index*4:X}')
            highs[owner]=wanted
            targets.add(target&0xffff)
            if inside:changes[index]=(index*4,address,target)
        if index in changes:
            if len(targets)!=1:raise ValueError(f'Ambiguous address at {index*4:X}')
            words[index]=(words[index]&0xffff0000)|targets.pop()
    def step(index,state):
        insn=original[index];op=insn>>26;rs=(insn>>21)&31;rt=(insn>>16)&31;rd=(insn>>11)&31;imm=insn&0xffff;fn=insn&63
        if op==15:
            state[rt]=frozenset({index}) if imm in (0x8c,0x8d) else frozenset({None})
        elif op in (8,9,13,24,25):
            consume(state,rs,imm,op!=13,index);state[rt]=frozenset({None})
        elif op in (0x1a,0x1b,0x1e,0x1f,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x31,0x37,0x39,0x3f):
            consume(state,rs,imm,True,index)
            if op in (0x1a,0x1b,0x1e,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x37):state[rt]=frozenset({None})
        elif op in (2,3):
            address=(insn&0x3ffffff)<<2
            if LINK_BASE<=address<LINK_BASE+len(data):words[index]=(op<<26)|((address+delta)>>2)
        elif op==0:
            if fn in (0x21,0x2d):
                a=state.get(rs,frozenset({None}));b=state.get(rt,frozenset({None}))
                state[rd]=a if b==frozenset({None}) else b if a==frozenset({None}) else frozenset({None})
            elif fn not in (8,9,0xf,0x11,0x13,0x18,0x19,0x1a,0x1b,0x29):state[rd]=frozenset({None})
        elif op in (10,11,12,14,0x10):state[rt]=frozenset({None})
        elif op==0x1c:state[rd]=frozenset({None})
        state.pop(0,None)
    # The main-loop hook enters this thunk directly from outside MOD.BIN.
    # It has no stack prologue or internal caller, so discovery misses its jal.
    roots={0x200//4,0x27c8//4}
    for index in range(0x200//4,0x3000//4):
        insn=original[index]
        if insn>>26 in (9,25) and ((insn>>21)&31)==29 and ((insn>>16)&31)==29 and insn&0x8000:
            roots.add(index-1 if original[index-1]>>26==15 else index)
        if insn>>26==3:
            address=(insn&0x3ffffff)<<2
            if LINK_BASE<=address<LINK_BASE+0x3000:roots.add((address-LINK_BASE)//4)
    for root in roots:enqueue(root,{})
    while queue:
        index=queue.popleft();state=dict(states[index]);insn=original[index];op=insn>>26;fn=insn&63
        step(index,state)
        branch=op in (1,4,5,6,7,0x14,0x15,0x16,0x17)
        jump=op in (2,3) or (op==0 and fn in (8,9))
        if branch or jump:
            before=dict(state);step(index+1,state)
            if op==3 or (op==0 and fn==9):
                for register in (*range(2,16),24,25,31):state[register]=frozenset({None})
                enqueue(index+2,state)
            elif op==2:
                target=((insn&0x3ffffff)<<2)-LINK_BASE
                enqueue(target//4,state)
            elif branch:
                imm=insn&0xffff;offset=imm-0x10000 if imm&0x8000 else imm
                enqueue(index+1+offset,state)
                if not (op==4 and ((insn>>21)&31)==((insn>>16)&31)):
                    enqueue(index+2,before if op in (0x14,0x15,0x16,0x17) else state)
        else:enqueue(index+1,state)
    for owner,high in highs.items():words[owner]=(words[owner]&0xffff0000)|high
    result=struct.pack('<4096I',*words)
    return result,list(changes.values())

def install(p,data,process):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError('Native runner stopped during Power Scale module boot')
        if p.read_u32(CONTROL)==MAGIC:
            base=p.read_u32(CONTROL+4)
            if p.read(base,len(data))!=data:raise ValueError('Loaded module does not match the selected ISO')
            image,changes=relocate(data,base)
            p.write(base,image)
            if p.read(base,len(image))!=image:raise ValueError('Module relocation readback failed')
            p.write_u32(CONTROL+8,1)
            print(f'Power Scale module relocated to {base:08X}: {len(changes)} absolute address references',flush=True)
            expected=(3<<26)|((base+0x2264)>>2)
            while time.monotonic()<deadline:
                if process.poll() is not None:raise RuntimeError('Native runner stopped during module initialization')
                if p.read_u32(0x203830)==expected:
                    print('Power Scale fusion hook verified at 00203830',flush=True)
                    return base
                time.sleep(.05)
            raise TimeoutError('Power Scale initialization did not install its fusion hook')
        time.sleep(.05)
    raise TimeoutError('Power Scale module loader did not publish its allocation')

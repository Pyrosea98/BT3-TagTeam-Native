"""Execute the emitted fade guard up to its first native draw call, offline."""
from pathlib import Path
import os,sys,struct
root=Path(__file__).resolve().parent
sys.path[:0]=[str(root/'power-scale-trial/controller/game/tools')]
os.environ.update(PS2X_NATIVE_UI_SLICE='1',PS2X_NATIVE_MODE_COVER='0')
import native_menu_services as s,team_assignment as t,controller_assignment as c,mod_settings
assert mod_settings.validate_settings({})['native_mode_cover'] is False
code=s.fade();words=dict((s.FADE+i,struct.unpack_from('<I',code,i)[0]) for i in range(0,len(code),4))
for team,controller in [(1,0),(0,1)]:
    memory={s.CONTROL:s.MAGIC,s.CONTROL+40:1,s.CONTROL+44:600,s.CONTROL+52:128,
            s.CONTROL+t.STATE:team,c.CONTROL:c.MAGIC,c.CONTROL+12:controller}
    regs=[0]*32;regs[29]=0x1ffe000;pc=s.FADE;delay=None
    for step in range(300):
        ins=words[pc];op=ins>>26;rs=(ins>>21)&31;rt=(ins>>16)&31;imm=ins&65535
        signed=imm if imm<32768 else imm-65536;nextpc=pc+4;pending=None
        if op==15:regs[rt]=imm<<16
        elif op==13:regs[rt]=regs[rs]|imm
        elif op==9:regs[rt]=(regs[rs]+signed)&0xffffffff
        elif op in (35,55):regs[rt]=memory.get((regs[rs]+signed)&0xffffffff,0)
        elif op in (43,63):memory[(regs[rs]+signed)&0xffffffff]=regs[rt]
        elif op in (4,5):
            if (regs[rs]==regs[rt])==(op==4):pending=pc+4+signed*4
        elif op in (2,3):
            target=((pc+4)&0xf0000000)|((ins&0x3ffffff)<<2)
            if op==3:
                assert target==s.TRAMP+0x80,'dialog must reach native fade before decorative draw'
                assert all(memory[s.CONTROL+x]==0 for x in (40,44,52))
                break
            pending=target
        elif op==0:
            rd=(ins>>11)&31;funct=ins&63
            if funct in (16,18):regs[rd]=0
            elif funct in (33,45):regs[rd]=(regs[rs]+regs[rt])&0xffffffff
            elif ins==0:pass
            else:raise AssertionError(hex(ins))
        else:raise AssertionError(hex(ins))
        regs[0]=0
        if delay is not None:nextpc=delay
        delay=pending;pc=nextpc
    else:raise AssertionError('native draw not reached')
    print('PASS emitted fade releases cover before dialog:', 'teams' if team else 'controllers')
import guest_loading_screen as guest
assert guest.pnach()
print('PASS current complete bootstrap generated with native cover default OFF')

"""Read-only evidence for a prepared match that did not release its hold."""
import struct
from atomic_files import write_json

def capture(client, destination, manager, count):
    u=client.read_u32
    phase=u(0x2FEB38)
    gate=0x073E1C00
    actors=[]
    for i in range(min(max(count,0),10)):
        actor=u(0xD8040+4*i)
        valid=0x100000<=actor<=0x8000000-0x1600 and actor%4==0
        actors.append(dict(seat=i,pointer=actor,captured_pointer=u(gate+0x80+4*i),
            captured_cpu=u(gate+0x40+4*i),id=u(actor) if valid else None,
            cpu=u(actor+0x1278) if valid else None,state=u(actor+0x948) if valid else None))
    receipt=dict(manager=manager,current_manager=u(0x2FEB14),count=count,
        gate=list(struct.unpack('<7I',client.read(gate,28))),hold=u(0x07361850),
        pause=u(0xC4004),mode=list(struct.unpack('<4I',client.read(0xD8080,16))),
        result_flags=u(0x333700),return_flags=u(0x333704),phase_pointer=phase,
        phase=u(phase) if 0x100000<=phase<=0x8000000-4 and phase%4==0 else None,
        actors=actors)
    write_json(destination,receipt)
    return receipt

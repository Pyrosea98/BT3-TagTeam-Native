"""Read-only transition samples for native match teardown and reload research."""
from datetime import datetime
import json
import struct
import time


def attach(autopilot, pine, output):
    original = autopilot.Autopilot.observe
    last = None
    sampled = 0
    warned = False

    def observe(self):
        nonlocal last, sampled, warned
        obs = original(self)
        if obs is None:
            return obs
        signature = (obs.loop, obs.battle_state, obs.manager, obs.array,
            obs.team_mode, obs.heap1, obs.result_flags, obs.return_flags,
            tuple(obs.scene_rows), tuple(map(tuple, obs.scene_characters)),
            tuple(obs.slots), obs.clean)
        now = time.monotonic()
        if signature == last and now-sampled < 5:
            return obs
        try:
            with pine.PineClient(timeout=2) as p:
                valid = lambda address, size: 0x100000 <= address <= 0x8000000-size and address % 4 == 0
                value = dict(time=datetime.now().isoformat(timespec='milliseconds'),
                    event='transition' if signature != last else 'periodic',
                    controller_state=self.state, battle_mode=self.battle_mode,
                    observation=obs.summary(), battle_object=obs.battle_object,
                    scene_characters=obs.scene_characters,
                    result_flags=obs.result_flags, return_flags=obs.return_flags,
                    clean=obs.clean, models=[])
                value['heap1_bounds']=[p.read_u32(autopilot.HEAP1_START),p.read_u32(autopilot.HEAP1_END)]
                if valid(obs.manager,32):
                    value['manager_words']=list(struct.unpack('<8I',p.read(obs.manager,32)))
                # Model records carry three file IDs, backing allocations and
                # native reserved slot ownership. Pointers are observations,
                # never reusable cache entries.
                from native_map import A
                pointers=struct.unpack('<12I',p.read(A(0x31C640),48))
                for index,model in enumerate(pointers):
                    if not valid(model,24):
                        continue
                    words=struct.unpack('<6I',p.read(model,24))
                    entry=dict(slot=index,model=model,model_words=list(words))
                    resource=words[5]
                    if valid(resource,56):
                        data=struct.unpack('<14I',p.read(resource,56))
                        entry.update(resource=resource,resource_words=list(data),
                            files=[dict(pointer=data[i],size=data[i+1],file_id=data[i+2]) for i in (0,4,8)])
                    value['models'].append(entry)
                # Skip samples which crossed a manager/scene boundary rather
                # than presenting mixed worlds as a valid reset observation.
                if p.read_u32(autopilot.MANAGER)!=obs.manager or p.read_u32(autopilot.LOOP_FLAG)!=obs.loop:
                    return obs
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(value,separators=(',',':'))+'\n')
            last, sampled = signature, now
        except (OSError, ValueError, struct.error, pine.PineError) as error:
            if not warned:
                autopilot.log(f'Rematch trace delayed: {error}')
                warned=True
        return obs

    autopilot.Autopilot.observe = observe

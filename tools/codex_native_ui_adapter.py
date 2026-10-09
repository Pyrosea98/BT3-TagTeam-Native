"""M5 trial adapter. Semantic preparation/settings stay with their current owner;
native Vulkan renders bounded messages through the existing PINE transport.
"""
import struct, time, threading, contextlib
from pathlib import Path
WORDS=struct.Struct('<32I')
_ACTIVE=threading.local()
# UI callbacks can run inside an owned PINE transaction. One reentrant lock
# prevents heartbeat UI->PINE and start acknowledgement PINE->UI inversion.
TRANSPORT_LOCK=threading.RLock()
# Median native preparation phase milliseconds from eight successful local
# captures (2026-10-06); Ready/intro wait is excluded from completion weight.
STAGE_WEIGHTS=(750.0,1672.0,711.5,1484.5,1039.0,2249.5)
LINKS=('https://www.youtube.com/channel/UCXiHmLmbgaSsFGrfejXESYw',
       'https://www.youtube.com/channel/UCY79wsRvOdzBoe8GS77HY0A')
UI_BUILD='M5.2-dev'
UI_DISC_HASH=''
SPECIAL_THANKS={'en':'Special thanks to RidJuampa for helping me understand the code.',
                'es':'Agradecimiento especial a RidJuampa por ayudarme a entender el codigo.'}

def field(value,length):
    b=str(value).encode('utf-8')
    if len(b)>=length:b=b[:length-4].decode('utf-8','ignore').encode('utf-8')+'…'.encode('utf-8')
    return b+b'\0'*(length-len(b))

class Surface:
    def __init__(self):
        self.generation=time.monotonic_ns();self.teams=[];self.visible=False;self.available=False
        self.phase='idle';self.percent=0;self.stage=0;self.language='en';self.revision=0
        self.menu=None;self.lock=TRANSPORT_LOCK;self.transport_version=1;self.mode='teams';self.humans=1;self.hud_options=7
        self.accepted=False;self.hud_config=0;self.hud_scale=65;self.hud_opacity=50;self.hud_shape=0x80000101
    def send(self,action,client=None):
        from pine import PineClient
        if client is None:client=getattr(_ACTIVE,'client',None)
        import localization
        language=self.language if self.menu else localization.language()
        words=[0]*32;words[:8]=[1,action,self.generation&0xffffffff,self.generation>>32,self.percent,self.stage,0,0]
        ids=[]
        for team in self.teams:
            fighters=team.get('fighters',[]);words[6+team['side']]=len(fighters)
            ids.extend(f['character_id'] if isinstance(f,dict) else f for f in fighters)
        if len(ids)>10:raise ValueError('Native cover supports at most five fighters per side')
        words[8:8+len(ids)]=ids;words[18]=int(language=='es')
        words[21]=('teams','coop','ffa','training','training_coop').index(self.mode)
        words[23]=self.humans
        words[24]=self.hud_options
        words[25]=self.hud_config;words[26]=self.hud_scale;words[27]=self.hud_opacity
        words[28]=self.hud_shape
        seats=[f.get('player',0) for team in self.teams for f in team.get('fighters',[])]
        if seats and not any(seats):
            import battle_mode_policy
            physical=[2*slot+team['side'] for team in self.teams for slot,_ in enumerate(team.get('fighters',[]))]
            assigned=battle_mode_policy.human_seats(self.mode,self.humans,sum(1<<i for i in physical))
            seats=[assigned.index(i)+1 if i in assigned else 0 for i in physical]
        words[22]=sum(seat<<(3*i) for i,seat in enumerate(seats))
        text=b'\0'*2048
        if self.menu:
            title,rows,selected,help_text,error=self.menu
            words[19]=selected;words[20]=len(rows)
            text=field(title,128)+b''.join(field(label,96)+field(value,96) for label,value in rows)
            text+=b'\0'*(1536-len(rows)*192)+field(help_text,256)+field(error,128)
        with contextlib.nullcontext(client) if client is not None else PineClient(timeout=5) as p:
            accepted=struct.unpack('<I',p._exchange(b'\x11'+WORDS.pack(*words)+text,4))[0]
            if not accepted:raise RuntimeError(f'Native UI rejected lifecycle action {action}; generation {self.generation}')
            ack=struct.unpack('<8I',p._exchange(b'\x12',32))
        self.available=bool(ack[1]);self.revision=ack[6];self.transport_version=ack[0]
        if self.menu:self.generation=ack[2]|(ack[3]<<32)
        return True
    def set_teams(self,teams):self.teams=teams
    def set_mode(self,mode,humans):
        if mode not in ('teams','coop','ffa','training','training_coop') or not 0<=humans<=4:raise ValueError('Invalid mode/seat count')
        self.mode=mode;self.humans=humans
    def prerender(self,*args):return True
    def begin(self):
        if self.phase!='idle':return
        if len(self.teams)!=2:raise ValueError('Selected rosters missing from native cover')
        import mod_settings
        values=mod_settings.load_settings()
        self.hud_options=int(values.get('show_native_hud',True) and values.get('hud_style','game_overhead')!='overhead_only')|int(values.get('show_kill_feed',True))<<1|int(values.get('training_show_counters',True))<<2
        name_mode={'off':0,'tiny':1,'normal':2,'focused':1,'all':2}[values.get('hud_overhead_names','off')]
        self.hud_shape=0x80000000 | ('off','hexagon','ring','plate').index(values.get('hud_overhead_shape','hexagon')) | int(values.get('hud_overhead_ki_pips',True))<<8
        self.hud_config=(0x80000000 | name_mode
            | ('owner','focused','allies','everyone').index(values.get('hud_overhead_detail','focused'))<<2
            | int(values.get('hud_overhead_portraits',True))<<4 | int(values.get('hud_contestant_list',False))<<5
            | int(values.get('show_fusion_timer',True))<<6 | int(values.get('show_friendly_healthbars',True))<<7
            | int(values.get('show_enemy_healthbars',True))<<8)
        self.hud_scale=values.get('hud_panel_scale_percent',65);self.hud_opacity=values.get('hud_panel_opacity_percent',50)
        self.generation+=1;self.percent=0;self.stage=0;self.accepted=False;self.send(1);self.visible=True;self.phase='preparing'
    def progress(self,stage,completed,total):
        with self.lock:
            if self.phase=='released' and completed==0:self.phase='idle'
            self.begin()
            if stage=='Ready':self.send(3);self.phase='ready';self.percent=100;return
            self.percent=max(self.percent,round(100*sum(STAGE_WEIGHTS[:completed])/sum(STAGE_WEIGHTS)))
            self.stage=max(self.stage,min(6,completed))
            self.send(2)
    def released(self):
        with self.lock:
            if self.phase!='ready':raise RuntimeError('Release acknowledgement arrived without Ready')
            for attempt in range(3):
                try:self.send(4);break
                except (OSError,RuntimeError):
                    if attempt==2:raise
                    time.sleep(.05)
            self.phase='released';self.visible=False
    def start_accepted(self,client=None):
        with self.lock:
            if self.phase!='ready':raise RuntimeError('Start acceptance arrived without Ready')
            if self.transport_version<2:return # retained M5 binary has only Released
            self.send(11,client)
            self.accepted=True
            # Keep heartbeat/ownership alive while intro runs. Native view fades
            # independently; actual release still waits for start-gate ACK.
    def show(self,message,progress):
        # Native disc loading already has its own picture. Begin at the worker's
        # actual first preparation event, after it has acquired its hold.
        if 'FAIL' in str(message).upper() or 'CLOSE AND REOPEN' in str(message).upper():
            with self.lock:
                print(f'[nativeui-failure] mode={self.mode} phase={self.phase} startAccepted={self.accepted} message={message!r}',flush=True)
                if self.accepted or self.phase=='released':
                    print('[nativeui-failure] late diagnostic logged; active match cover remains closed',flush=True)
                    return self.available
                self.begin();self.send(5);self.phase='failed';self.visible=True
        return self.available
    def menu_page(self,title,rows,selected,help_text,language='en',error='',about=False,client=None):
        self.menu=(title,rows,selected,help_text,error);self.language=language
        self.send(8 if about else 10,client);self.visible=True
    def sync(self,force=False,client=None):
        with self.lock:
            if self.menu:return self.send(8 if self.phase=='about' else 10,client)
            if self.visible:return self.send(0,client)
            return True
    def presented(self,client):
        ack=struct.unpack('<8I',client._exchange(b'\x12',32))
        gen=ack[2]|(ack[3]<<32);revision=ack[4]|(ack[5]<<32)
        return bool(ack[1]) and gen==self.generation and revision>=self.revision
    def wait_drawn(self,timeout=2):
        from pine import PineClient
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            with PineClient(timeout=3) as p:
                if self.presented(p):return True
            time.sleep(.03)
        return False
    def hide(self,client=None):
        with self.lock:
            if self.menu:self.send(9,client);self.menu=None
            elif self.phase not in ('idle','released'):
                # Only explicit owner teardown closes a failed/cancelled match.
                self.send(6,client)
            self.visible=False;self.phase='idle';return True

class Presentation:
    def __init__(self,*args,**kwargs):self.guest=Surface()
    def set_teams(self,teams):
        for team in teams:
            if not 1<=len(team['fighters'])<=5:raise ValueError('Native UI roster size must be 1..5')
            for f in team['fighters']:
                if type(f['character_id'])is not int or not 0<=f['character_id']<=252:raise ValueError('Invalid native roster ID')
        self.guest.set_teams(teams)
    def set_mode(self,*args):return self.guest.set_mode(*args)
    def prerender(self,*args):return True
    def show(self,title,message,progress,mute_audio=True):return self.guest.show(message,progress)
    def tick(self):return self.guest.sync()
    def wait_visible(self,timeout=2):return self.guest.available
    def wait_hidden(self,timeout=2):return not self.guest.visible
    def hide(self,refresh_surface=False):return self.guest.hide()
    def close(self):return self.guest.hide()

def install():
    import pine,autopilot,fresh_team_trainer,loading_presentation,ingame_settings as settings
    import feature_preferences,mod_settings
    import localization
    localization.ES['Show credits at startup']='Mostrar creditos al inicio'
    import json
    catalogue=json.loads((Path(__file__).resolve().parent/'ui-assets/ui_strings.json').read_text(encoding='utf-8'))['strings']
    for key in ('RestartRequired','RestartExplanation','RestartHelp'):
        localization.ES[catalogue[key]['en']]=catalogue[key]['es']
    key='show_credits_at_startup'
    feature_preferences.OPTIONS[key]=(True,'bool',None,None,'Menus','Show credits at startup')
    feature_preferences.DEFAULTS[key]=True;mod_settings.DEFAULTS[key]=True
    mod_settings.GROUPS=tuple((name,(key,)+tuple(keys) if name=='Menus' and key not in keys else keys) for name,keys in mod_settings.GROUPS)
    settings.ROW_HELP[key]=('Show credits at startup','Show the full startup credits; off keeps a short credit strip. Applies after restarting the native trial.')
    key='training_show_counters'
    feature_preferences.OPTIONS[key]=(True,'bool',None,None,'Training','Show counters')
    feature_preferences.DEFAULTS[key]=True;mod_settings.DEFAULTS[key]=True
    mod_settings.GROUPS=tuple((name,tuple(keys)+(key,) if name=='Training' and key not in keys else keys) for name,keys in mod_settings.GROUPS)
    settings.ROW_HELP[key]=('Show counters','Show training hit and damage counters. Select resets them during the match. Applies to the next match.')
    localization.ES.update({'Show counters':'Mostrar contadores','Show the full startup credits; off keeps a short credit strip. Applies after restarting the native trial.':'Muestra los creditos completos al inicio; desactivado mantiene una franja breve. Se aplica al reiniciar el juego.',
                           'Show training hit and damage counters. Select resets them during the match. Applies to the next match.':'Muestra los contadores de golpes y dano. Select los reinicia durante el combate. Se aplica al siguiente combate.'})
    # Serialize ALL existing short-lived clients in this trial, including the
    # trainer/probes. UI inside a settings poll uses that poll's client directly.
    connection_lock=TRANSPORT_LOCK
    connect,close=pine.PineClient.connect,pine.PineClient.close
    def connect_owned(self):
        if self.sock is None:
            connection_lock.acquire();self._native_ui_owned=True
            try:
                result=connect(self);_ACTIVE.client=self;return result
            except BaseException:
                close_owned(self);raise
        return self
    def close_owned(self):
        try:close(self)
        finally:
            if getattr(self,'_native_ui_owned',False):
                self._native_ui_owned=False
                if getattr(_ACTIVE,'client',None) is self:_ACTIVE.client=None
                connection_lock.release()
    pine.PineClient.connect=connect_owned;pine.PineClient.close=close_owned
    # Separate from offline adapter tests; the real trial upgrades the audited
    # unowned guest menu body before its existing controller starts.
    import os
    if os.environ.get('PS2X_PACKAGE_DATA'):
        previous_enable=mod_settings.can_enable
        def can_enable_native(key,values=None):
            if key=='expanded_maps':
                root=Path(os.environ['PS2X_PACKAGE_DATA'])/'import'
                ready=(root/'expanded-2x.iso').is_file() and (root/'import-receipt.json').is_file()
                return ready,'' if ready else localization.tr('Run Build expanded maps.cmd first.',values)
            return previous_enable(key,values)
        mod_settings.can_enable=can_enable_native
    if os.environ.get('PS2X_NATIVE_UI_MENU_CREDITS')=='1':
        import native_mode_menu
        from codex_native_menu_credits import install as install_credits_route
        install_credits_route(native_mode_menu,settings)
    loading_presentation.LoadingPresentation=Presentation
    progress=autopilot.Autopilot.on_progress
    def on_progress(self,stage,completed,total):
        if isinstance(self.presentation,Presentation):self.presentation.guest.progress(stage,completed,total)
        else:progress(self,stage,completed,total)
    autopilot.Autopilot.on_progress=on_progress
    # release_start returns only after identity checks AND guest start-gate ACK.
    release=fresh_team_trainer.StreamingSession.release_start
    def released(self):
        owner=getattr(self.progress_callback,'__self__',None)
        surface=owner.presentation.guest if owner and isinstance(owner.presentation,Presentation) else None
        previous=getattr(self,'start_accepted_callback',None)
        def accepted(p):
            if previous:previous(p)
            if surface:surface.start_accepted(p)
        self.start_accepted_callback=accepted
        try:
            release(self)
            if surface:surface.released()
        finally:self.start_accepted_callback=previous
    fresh_team_trainer.StreamingSession.release_start=released
    settings.USED['about']=settings.UP|settings.DOWN|settings.CROSS|settings.TRIANGLE|settings.CIRCLE
    base=settings.Controller
    class NativeSettings(base):
        CONFIRM=dict(base.CONFIRM, restart=(catalogue['RestartRequired']['en'],catalogue['RestartExplanation']['en'],(catalogue['RestartHelp']['en'],)))
        def save(self,exit):
            changes=self.changes();result=super().save(exit)
            if os.environ.get('PS2X_PACKAGE_DATA') and isinstance(result,dict) and any(key in feature_preferences.RESTART_KEYS or key=='show_credits_at_startup' for key in changes):
                self.closing=False;self.ask('restart',self.view)
            return result
        def _press_confirm(self,edges,repeats):
            if self.confirming!='restart':return super()._press_confirm(edges,repeats)
            if edges & settings.CROSS:
                import json
                root=Path(os.environ['PS2X_PACKAGE_DATA']);temporary=root/'restart-request.partial'
                temporary.write_text(json.dumps({'schema':1,'owner_pid':os.getpid()}),encoding='utf-8')
                temporary.replace(root/'restart-request.json');self.closing=True
            elif edges & (settings.TRIANGLE|settings.CIRCLE|settings.BACK):self.view=self.back_view
        def open(self):
            super().open();self.screen=Surface();self.about_row=1
            # Keep base category indices stable (page/help/restore routes use
            # them); rotate the displayed index so About is the first entry.
            self.index_row=len(self.groups)+2
            if getattr(self,'_open_about',False):self.view='about';self._open_about=False
        def _poll(self,p):
            if not self.active and p.read_u32(settings.CONTROL+4)==1 and p.read_u32(settings.CONTROL+20)==1:
                self._open_about=True;p.write_u32(settings.CONTROL+20,0)
            return super()._poll(p)
        def _press_index(self,edges,repeats):
            count=len(self.groups)+3
            if edges & settings.CROSS and self.index_row==count-1:
                self.view='about';return
            if (edges|repeats)&(settings.UP|settings.DOWN):
                self.index_row=(self.index_row+(1 if (edges|repeats)&settings.DOWN else -1))%count;return
            if self.index_row==count-1 and edges&settings.CIRCLE:return
            return super()._press_index(edges,repeats)
        def _press_about(self,edges,repeats):
            if edges&(settings.TRIANGLE|settings.CIRCLE|settings.BACK):self.view='index';return
            if (edges|repeats)&(settings.UP|settings.DOWN):self.about_row=3 if self.about_row==1 else 1
            if edges&settings.CROSS:
                import webbrowser
                webbrowser.open(LINKS[0 if self.about_row==1 else 1])
        def publish(self,p):
            lang=self.values.get('language',self.saved.get('language','en'))
            tr=self.tr;rows=[];selected=0;title=tr('Mod settings');error=''
            help_text=tr('Up/Down: select    Cross: open    Circle: help')
            if self.view=='index':
                labels=['ACERCA DE / CREDITOS' if lang=='es' else 'ABOUT / CREDITS']+[tr(g) for g in self.groups]+[tr('Per-character exceptions ({n} set)…',n=len(self.overrides())),tr('Restore defaults…')]
                displayed=(self.index_row+1)%len(labels)
                start=displayed//8*8;rows=[(v,'')for v in labels[start:start+8]];selected=displayed-start
            elif self.view=='page':
                fields=self.fields();start=self.row//7*7
                rows=[(tr(meta[5]),self.value_text(key))for key,meta in fields[start:start+7]]
                selected=self.row-start;title=tr(self.groups[self.group])
                help_text=tr('Up/Down: select    Left/Right: change    L2/R2: ×10')
            elif self.view=='about':
                title='ACERCA DE / CREDITOS' if lang=='es' else 'ABOUT / CREDITS';selected=self.about_row
                import textwrap
                rows=[('Power Scale: LetsPlayBt3',''),(LINKS[0],''),('Tag Team: The Mufti',''),(LINKS[1],'')]
                note=SPECIAL_THANKS[lang]
                # Two balanced lines, avoiding an orphan such as "the code.".
                words=note.split();split=min(range(1,len(words)),key=lambda i:abs(len(' '.join(words[:i]))-len(' '.join(words[i:]))))
                rows += [(' '.join(words[:split]),''),(' '.join(words[split:]),'')]
                rows += [('Version' if lang=='es' else 'Build',UI_BUILD)]
                if UI_DISC_HASH:rows += [('Disco' if lang=='es' else 'Disc',UI_DISC_HASH[:12])]
                help_text='Cruz: abrir enlace   Triangulo: volver' if lang=='es' else 'Cross: open selected link   Triangle: back'
            elif self.view=='exceptions':
                from character_names import character_table
                ids=self.character_rows();start=self.character//8*8;table=character_table()
                rows=[(table.get(cid,{}).get('name',str(cid)),tr(settings.POLICY_LABELS[self.overrides().get(str(cid))]))for cid in ids[start:start+8]]
                selected=self.character-start;title=tr('CPU transformation exceptions')
            else:
                import textwrap
                if self.view=='help':
                    if self.help_topic is not None:heading,note=settings.ROW_HELP[self.help_topic];title=tr(heading);note=tr(note)
                    else:title=tr(self.groups[self.group]);note=settings.mod_settings.help_note(self.groups[self.group],self.values)
                elif self.view=='confirm':
                    heading,note,keys=self.CONFIRM[self.confirming];title=tr(heading);note=tr(note);help_text=tr(keys[0])
                else:title=tr(self.failure['title']);note=self.failure['detail'];error=title
                rows=[(line,'')for line in textwrap.wrap(note,64)[:8]]
            if self.view!='about':
                help_text+='\n'+('Cuadrado: guardar   Triangulo: volver' if lang=='es' else 'Square: save   Triangle: back')
                error=error or self.status[0]
            self.screen.phase='about' if self.view=='about' else 'settings'
            self.screen.menu_page(title,rows,selected,help_text,lang,error,self.view=='about',p)
            self.dirty=False
    settings.Controller=NativeSettings
    # Mode navigation keeps its original guest presentation. Settings and
    # About (from either route) retain the accepted native DBZ renderer.

"""UI trial's About route, preserving stable match choice numbers."""
import inspect

def install(menu,settings):
    old=menu.payload()
    source=inspect.getsource(menu.payload)
    source=source.replace("a.label('root_choice');a.addiu(10,0,6)",
                          "a.label('root_choice');a.addiu(10,0,7);a.branch(4,13,10,'about');a.addiu(10,0,6)")
    source=source.replace("a.label('settings');a.li(10,ingame_settings.CONTROL)",
        "a.label('about');a.li(10,ingame_settings.CONTROL);a.addiu(12,0,1);a.sw(12,10,20);a.jump('settings_body')\n    a.label('settings');a.li(10,ingame_settings.CONTROL);a.sw(0,10,20)\n    a.label('settings_body');a.li(10,ingame_settings.CONTROL)")
    if "a.label('about')" not in source:raise RuntimeError('Native mode About route source changed')
    scope={};exec(compile(source,__file__,'exec'),menu.__dict__,scope)
    menu.payload=scope['payload'];menu.PAGES=((0,7,1,3,6),)+menu.PAGES[1:]
    menu.assets.LABELS=menu.assets.LABELS[:7]+('About / Credits',)
    descriptions=list(menu.assets.DESCRIPTIONS);descriptions[0]=descriptions[0][:7]+('Mod credits and channel links.',)
    menu.assets.DESCRIPTIONS=tuple(descriptions)
    menu.localization.ES.update({'About / Credits':'Acerca de / Creditos','Mod credits and channel links.':'Creditos del mod y enlaces a los canales.'})
    menu.code_pieces.cache_clear()
    new=menu.payload()
    if len(new)>=menu.OFF-menu.CODE:raise RuntimeError('Native About route exceeds owned code reservation')
    # Patch only the audited old body or a cold, unoccupied reservation. This
    # runs before the controller owns a menu; match selections stay untouched.
    from pine import PineClient
    with PineClient() as p:
        ctl=p.read_u32(menu.CONTROL+4)
        if ctl!=0:raise RuntimeError('Cannot install credits while a menu is owned')
        existing=p.read(menu.CODE,max(len(old),len(new)))
        if existing==bytes(len(existing)):return # cold builder will install new pieces
        expected=old+bytes(max(0,len(new)-len(old)))
        if existing!=expected and existing!=new+bytes(max(0,len(old)-len(new))):
            raise RuntimeError('Native menu code differs from audited credits predecessor')
        p.write(menu.CODE,new+bytes(max(0,len(old)-len(new))))
        if p.read(menu.CODE,len(new))!=new:raise RuntimeError('Native credits route readback failed')

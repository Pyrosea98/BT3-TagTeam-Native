"""Native presentation of the existing guest mode menu; choices stay guest owned."""
import struct
import textwrap

TITLES=('Modded Modes','Team Battle','Free-for-all','Co-op','Modded Training','Co-op Training')

def page_model(menu,page,selected,values):
    labels=menu.assets.LABELS if page==0 else ('4 Players','3 Players')+menu.assets.LABELS[2:6]+('CPU Only','Back')
    tr=lambda text:menu.localization.tr(text,values)
    rows=[(tr(labels[index]),'') for index in menu.PAGES[page]]
    index=menu.PAGES[page][selected]
    note=tr(menu.assets.DESCRIPTIONS[page][index])
    # Two description lines plus navigation retain the original instructions.
    note='\n'.join(textwrap.wrap(note.replace('\n',' '),85)[:2])
    keys='Arriba/Abajo: elegir   Cruz: abrir   Triangulo: volver' if values.get('language')=='es' else 'Up/Down: select   Cross: open   Triangle: back'
    toggle=values.get('menu_toggle_button','Select')
    if values.get('show_menu_toggle_hint',True):keys+='   ['+str(toggle)+']'
    return tr(TITLES[page]),rows,selected,note+'\n'+keys

def snapshot(menu,p):
    before=p.read(menu.CONTROL,28)
    magic,state,page,result,lease,owner,epoch=struct.unpack('<7I',before)
    if magic!=menu.MAGIC or state!=2 or result or page>=len(menu.PAGES) or not lease:return None
    if not 0x100000<=owner<0x1fff000 or p.read_u32(menu.old.MAIN_OBJECT)!=owner or not menu.ready(p):return None
    data=p.read(owner+0x10c,0x40)
    scroll=struct.unpack_from('<I',data,0)[0]
    count,last=struct.unpack_from('<2I',data,0x38)
    if count!=len(menu.PAGES[page]):return None
    rows=struct.unpack_from('<'+str(count)+'I',data,0x0c)
    after=struct.unpack('<7I',p.read(menu.CONTROL,28))
    if rows!=menu.PAGES[page] or after[:4]!=(magic,state,page,result) or after[5:]!=(owner,epoch) or not after[4]:return None
    return page,((last+scroll+1)&0xffffffff)%count

def install(menu,settings,Surface):
    if getattr(menu.Controller,'_dbz_style_installed',False):return
    menu.localization.ES.update({'Modded Modes':'Modos modificados','Co-op Training':'Entrenamiento cooperativo'})
    original=menu.Controller.tick
    def tick(self,p,**kwargs):
        screen=getattr(self,'_dbz_menu_surface',None)
        # Close before another native surface opens: a late Close would erase
        # the settings/About page that the original tick has just published.
        if screen and screen.visible:
            wanted=(self.settings_menu.active or p.read_u32(settings.CONTROL+4)==1)
            team=(self.team_menu.active or p.read_u32(menu.CONTROL+menu.team_assignment.STATE)==1)
            if wanted or team:screen.hide(p)
        result=original(self,p,**kwargs)
        if self.settings_menu.active:
            if screen:screen.visible=False
            return result
        selection=snapshot(menu,p) if self.active and self.owned and not self.team_menu.active else None
        if selection:
            if screen is None:screen=Surface();self._dbz_menu_surface=screen
            page,selected=selection
            screen.menu_page(*page_model(menu,page,selected,self.settings),language=self.settings.get('language','en'),client=p)
        elif screen and screen.visible:screen.hide(p)
        return result
    menu.Controller.tick=tick
    menu.Controller._dbz_style_installed=True

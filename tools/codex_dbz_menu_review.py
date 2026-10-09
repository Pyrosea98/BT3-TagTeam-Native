"""Capture real EN/ES menu publications with Vulkan, without a game or socket."""
import copy,json,os,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'power-scale-trial/controller/game/tools'))
from codex_roster_overlay import install as roster
roster()
import codex_native_ui_adapter as ui
ui.install()
import ingame_settings as settings,mod_settings,native_mode_menu as menu
from codex_native_mode_style import page_model

OUT=HERE/'power-scale-trial/dbz-menu-polish-review'
OUT.mkdir(exist_ok=True)
records=[];manifest=[]
class Collector:
    def menu_page(self,title,rows,selected,help_text,language='en',error='',about=False,client=None):
        text=ui.field(title,128)+b''.join(ui.field(label,96)+ui.field(value,96) for label,value in rows)
        text+=bytes(1536-len(rows)*192)+ui.field(help_text,256)+ui.field(error,128)
        assert len(text)==2048 and len(rows)<=8 and selected<max(1,len(rows))
        records.append(ui.field(self.name,64)+struct.pack('<4I',language=='es',about,len(rows),selected)+text)
        manifest.append(dict(name=self.name,title=title,language=language,rows=rows,help=help_text))

def fixtures():
    # Same cold About route labels as the launcher, without installing guest
    # code or opening PINE. Match choice IDs and submenu rows are untouched.
    menu.PAGES=((0,7,1,3,6),)+menu.PAGES[1:]
    menu.assets.LABELS=menu.assets.LABELS[:7]+('About / Credits',)
    desc=list(menu.assets.DESCRIPTIONS);desc[0]=desc[0][:7]+('Mod credits and channel links.',);menu.assets.DESCRIPTIONS=tuple(desc)
    menu.localization.ES.update({'About / Credits':'Acerca de / Creditos','Mod credits and channel links.':'Creditos del mod y enlaces a los canales.','Modded Modes':'Modos modificados','Co-op Training':'Entrenamiento cooperativo'})
    for language in ('en','es'):
        model=settings.Controller();model.values=copy.deepcopy(mod_settings.DEFAULTS)
        model.values['language']=language;model.saved=copy.deepcopy(model.values)
        model.screen=Collector();model.about_row=1
        def capture(name):model.screen.name=name+'-'+language;model.publish(None)
        model.view='index'
        for displayed in range(0,len(model.groups)+3,8):
            model.index_row=(displayed-1)%(len(model.groups)+3);capture('settings-index-'+str(displayed//8+1))
        for group in range(len(model.groups)):
            model.group=group;model.view='page'
            for row in range(0,len(model.fields()),7):
                model.row=row;capture('settings-group-'+str(group+1)+'-'+str(row//7+1))
            model.view='help';model.help_topic=None;capture('help-group-'+str(group+1))
        model.view='help'
        for index,key in enumerate(settings.ROW_HELP):
            model.help_topic=key;capture('help-option-'+str(index+1))
        model.view='exceptions'
        for row in range(0,len(model.character_rows()),8):
            model.character=row;capture('exceptions-'+str(row//8+1))
        for confirming in model.CONFIRM:
            model.view='confirm';model.confirming=confirming;capture('confirm-'+confirming)
        model.view='about';capture('about')
        for page in range(len(menu.PAGES)):
            model.screen.name='mod-menu-'+str(page)+'-'+language
            model.screen.menu_page(*page_model(menu,page,0,model.values),language=language)
    (OUT/'menus.bin').write_bytes(b''.join(records))
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

def contact_sheet():
    from PIL import Image,ImageDraw,ImageFont
    # Pair EN/ES for each page; thumbnails link to full-size images in HTML.
    pages=sorted({item['name'].rsplit('-',1)[0] for item in manifest},key=lambda n:next(i for i,m in enumerate(manifest) if m['name']==n+'-en'))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
    width=1920;cellw=240;cellh=190
    sheet=Image.new('RGB',(width,50+((len(pages)*2+7)//8)*cellh),(14,20,40));draw=ImageDraw.Draw(sheet)
    draw.text((16,12),'DBZ native menus — English / Spanish pairs — click thumbnails in index.html for full resolution',font=font,fill=(245,185,53))
    links=[]
    for i,page in enumerate(pages):
        for j,language in enumerate(('en','es')):
            name=page+'-'+language;index=2*i+j;x=index%8*cellw;y=50+index//8*cellh
            img=Image.open(OUT/(name+'.png')).convert('RGB');img.thumbnail((232,163));sheet.paste(img,(x+4,y))
            draw.text((x+4,y+166),name,font=font,fill='white')
            links.append(f'<a href="{name}.png"><img src="{name}.png" loading="lazy"><span>{name}</span></a>')
    sheet.save(OUT/'contact-sheet.png')
    html='<!doctype html><meta charset="utf-8"><title>DBZ menu review</title><style>body{background:#0e1428;color:#f5b935;font:16px Arial;margin:24px}main{display:grid;grid-template-columns:repeat(4,minmax(250px,1fr));gap:16px}a{color:white;text-decoration:none}img{width:100%}span{display:block;padding:6px}@media(max-width:900px){main{grid-template-columns:repeat(2,1fr)}}</style><h1>DBZ native menus · EN / ES</h1><p>Real menu model, native Vulkan screenshots. Click any page for full resolution.</p><main>'+''.join(links)+'</main>'
    (OUT/'index.html').write_text(html,encoding='utf-8')

if __name__=='__main__':
    fixtures()
    env=os.environ.copy();env.update(PS2X_NATIVE_UI_SLICE='1',PS2X_UI_MENU_FIXTURES=str(OUT/'menus.bin'),PS2X_NATIVE_UI_TEST_MENUS_ONLY='1')
    with (OUT/'vulkan-check.log').open('wb') as log:
        result=subprocess.run([str(HERE/'repo/build/ps2xRuntime/ps2EntryRunner-dbz-menus-polish.exe'),'--native-ui-vulkan-self-test',str(HERE/'power-scale-trial/app-data/native-ui'),str(OUT)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    print('Native Vulkan menu check:',result.returncode,'pages:',len(manifest))
    if result.returncode:raise SystemExit(result.returncode)
    contact_sheet()

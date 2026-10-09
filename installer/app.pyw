"""Initial app shell; all Python is embedded temporarily and hidden."""
import hashlib,json,os,shutil,subprocess,sys,threading,uuid
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
APP=Path(__file__).resolve().parent

def install_language(app=APP):
    try:value=(app/'install-language.txt').read_text(encoding='utf-8-sig').strip()
    except OSError:value='en'
    return value if value in ('en','es') else 'en'

def saved_language(data,default):
    try:value=json.loads((data/'native-port/power-scale-trial/controller/game/mod-settings.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return default
    return value.get('language') if value.get('language') in ('en','es') else default
def data_root(app=APP):
    override=os.environ.get('BT3_TAGTEAM_DATA')
    if override:return Path(override).resolve()
    location=app/'data-root.txt'
    if location.is_file():
        value=location.read_text(encoding='utf-8-sig').strip()
        if not Path(value).is_absolute():raise RuntimeError('Invalid game data location.')
        return Path(value)
    legacy=Path(os.environ['LOCALAPPDATA'])/'BT3TagTeam'
    return legacy if (legacy/'app-owned.json').is_file() else app/'data'
DATA=data_root()
HERE=DATA/'native-port'
LANG=saved_language(DATA,install_language())
TEXT={'en':('Import your disc','Choose your Power Scale BETA 1.5.1 ISO. Your original disc will stay unchanged.','Choose ISO','Importing your disc…','Import failed. Please check the disc and available space.'),'es':('Importa tu disco','Elige tu ISO Power Scale BETA 1.5.1. El disco original no se modifica.','Elegir ISO','Importando tu disco…','No se pudo importar. Revisa el disco y el espacio disponible.')}
STAGES={'en':{'verify':'Checking your disc…','copy':'Copying your disc…','maps':'Expanding maps to twice their size…','done':'Preparing interface art…'},'es':{'verify':'Verificando el disco…','copy':'Copiando el disco…','maps':'Ampliando los mapas al doble…','done':'Preparando el arte de la interfaz…'}}
class ImportFailure(RuntimeError):
    """Only the native importer's deliberately path-free messages reach the UI."""
def import_error(message):
    if LANG=='en':return message
    return {'That disc isn\'t supported yet: Power Scale BETA 1.5.1 is required.':'Ese disco no es compatible: se necesita Power Scale BETA 1.5.1.','Not enough space: import needs 10 GB.':'No hay espacio suficiente: la importación necesita 10 GB.','The disc changed while it was being copied.':'El disco cambió mientras se copiaba.','The prepared disc failed verification.':'No se pudo verificar el disco preparado.'}.get(message,TEXT[LANG][4])
def initialize():
    try:
        DATA.mkdir(parents=True,exist_ok=True);(DATA/'app-owned.json').write_text(json.dumps({'app_id':'BT3TagTeam-initial-0.1'}),encoding='utf-8')
    except OSError as error:
        raise ImportFailure('Esta carpeta no permite escribir. Reinstala en una carpeta de tu cuenta, como Local AppData, o elige otra unidad.' if LANG=='es' else 'This folder is not writable. Reinstall in a folder owned by your account, such as Local AppData, or choose another drive.') from error
    if (HERE/'GAME_LOCK').exists():raise RuntimeError('The game is already running.')
    resource=APP/'resources/native-port'
    revision=json.loads((resource/'source-build.json').read_text(encoding='utf-8'))['revision']
    try:installed=json.loads((DATA/'sources-ready.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):installed={}
    if installed.get('revision')!=revision:
        settings_path=HERE/'power-scale-trial/controller/game/mod-settings.json'
        existing_settings=settings_path.is_file()
        def preserve_settings(directory,names):
            ignored={'repo'} & set(names)
            destination=HERE/Path(directory).relative_to(resource)
            if 'mod-settings.json' in names and (destination/'mod-settings.json').exists():ignored.add('mod-settings.json')
            return ignored
        shutil.copytree(resource,HERE,dirs_exist_ok=True,ignore=preserve_settings)
        # Package defaults already contain language=en. Seed a fresh player
        # from the installer's selected language, keeping existing choices.
        values=json.loads(settings_path.read_text(encoding='utf-8'))
        if not existing_settings or values.get('language') not in ('en','es'):
            values['language']=LANG
            settings_path.write_text(json.dumps(values,indent=2),encoding='utf-8')
        marker=DATA/'sources-ready.tmp'
        marker.write_text(json.dumps({'build':'0.1','revision':revision}),encoding='utf-8')
        marker.replace(DATA/'sources-ready.json')

def imported():
    try:
        receipt=json.loads((DATA/'import/import-receipt.json').read_text(encoding='utf-8'))
        if not receipt.get('ui_ready') or not all((DATA/'import'/name).is_file() for name in ('original.iso','expanded-2x.iso')):return False
        for name,meta in receipt['files'].items():
            path=DATA/'import/input'/name
            if path.stat().st_size!=meta['size']:return False
            if path.stat().st_mtime_ns!=meta.get('mtime_ns'):return False
        for name,digest in receipt['ui_files'].items():
            path=HERE/'power-scale-trial/app-data/native-ui'/name
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:return False
        return True
    except (OSError,ValueError,KeyError):return False

def import_disc(source,on_progress,cancel=None):
    if shutil.disk_usage(DATA).free < 12*1024**3:
        raise ImportFailure('La unidad de datos necesita al menos 12 GB libres para importar. Elige otra ubicación de instalación o libera espacio.' if LANG=='es' else 'The game data drive needs at least 12 GB free to import. Choose another installation location or free some space.')
    stage=DATA/('import-'+uuid.uuid4().hex)
    process=subprocess.Popen([str(APP/'disc-import.exe'),str(source),str(stage),str(APP/'import-data')],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    error=None
    for line in process.stdout:
        if cancel and cancel.is_set():process.terminate();process.wait();raise RuntimeError('Import cancelled.')
        item=json.loads(line)
        if 'error' in item:error=item['error']
        else:on_progress(item.get('percent',0),STAGES[LANG].get(item.get('stage'),TEXT[LANG][3]))
    if process.wait():raise ImportFailure(import_error(error or TEXT[LANG][4]))
    receipt=json.loads((stage/'import-receipt.json').read_text(encoding='utf-8'))
    # Fresh app data contains sources and metadata only. Every game file below
    # comes from the user's verified image, not the installer.
    game=HERE/'power-scale-trial/controller/game'
    shutil.copy2(stage/'input/SLUS_216.78',game/'analysis/SLUS_216.78')
    shutil.copy2(stage/'input/BIN/DBZP.BIN',stage/'input/DBZP.BIN')
    (game/'game-profile.json').write_text(json.dumps({'schema':1,'adapter':'bt3-usa','iso':str(stage/'original.iso'),'iso_sha256':receipt['original_disc_sha256'],'serial':'SLUS_216.78','pcsx2_crc':'9ACFE2DC','runtime_variant':'BT3 Power Scale BETA 1.5.1 (experimental)'}),encoding='utf-8')
    sys.path.insert(0,str(APP));from package_ui import derive
    derive(HERE,stage/'expanded-2x.iso')
    if cancel and cancel.is_set():raise RuntimeError('Import cancelled.')
    # Move only the app-owned import that was just successfully built.
    target=DATA/'import'
    if target.exists():raise RuntimeError('An import already exists; keep it or reinstall into a fresh data folder.')
    stage.rename(target)
    profile=json.loads((game/'game-profile.json').read_text(encoding='utf-8'));profile['iso']=str(target/'original.iso');(game/'game-profile.json').write_text(json.dumps(profile),encoding='utf-8')
    receipt['ui_ready']=True;receipt['ui_files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'power-scale-trial/app-data/native-ui').iterdir() if p.is_file()}
    for name,meta in receipt['files'].items():meta['mtime_ns']=(target/'input'/name).stat().st_mtime_ns
    (target/'import-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    values=json.loads((game/'mod-settings.json').read_text(encoding='utf-8'));values['language']=LANG
    (game/'mod-settings.json').write_text(json.dumps(values,indent=2),encoding='utf-8')

def configure_preview_diagnostics(app=APP,environment=None):
    """One preview switch; public packages default to diagnostics disabled."""
    environment=os.environ if environment is None else environment
    try:channel=(app/'release-channel.txt').read_text(encoding='utf-8-sig').strip()
    except OSError:channel='public'
    value=environment.get('BT3_PREVIEW_DIAGNOSTICS')
    enabled=value=='1' if value in ('0','1') else channel=='preview'
    environment['BT3_PREVIEW_DIAGNOSTICS']='1' if enabled else '0'
    # Some native flags test presence, so an OFF setting must remove them.
    for name in ('PS2X_MCLOG','PS2X_MCLOGMAX','PS2X_STALL_HISTORY',
                 'PS2X_STALL_INTERP','PS2X_EXIT_CAPTURE_DIR'):
        environment.pop(name,None)
    if enabled:
        environment.update(PS2X_MCLOG='1',PS2X_MCLOGMAX='1000',
                           PS2X_STALL_HISTORY='1',PS2X_STALL_INTERP='1',
                           PS2X_EXIT_CAPTURE_DIR=str(HERE/'power-scale-trial/guest-exit-captures'))
    return enabled


def preview_diagnostic_settings(settings,enabled):
    # Process-local overrides keep the player's saved preferences unchanged.
    return dict(settings,keep_preparation_diagnostics=enabled,
                capture_freeze_dumps=enabled,record_battle_diagnostics=enabled)


def play():
    configure_preview_diagnostics()
    sys.path.insert(0,str(HERE))
    import run_power_scale_native as launch
    launch.TRIAL=HERE/'power-scale-trial';launch.TOOLS=launch.TRIAL/'controller/game/tools';launch.REPO=APP/'resources/native-port/repo'
    values=json.loads((HERE/'power-scale-trial/controller/game/mod-settings.json').read_text(encoding='utf-8'))
    launch.ISO=DATA/'import'/('expanded-2x.iso' if values.get('expanded_maps',True) else 'original.iso');launch.ELF=DATA/'import/input/SLUS_216.78'
    import codex_ui_slice_trial as trial
    trial.HERE=HERE
    import codex_native_ui_adapter as ui
    ui.UI_BUILD='Initial 0.1';ui.UI_DISC_HASH=json.loads((DATA/'import/import-receipt.json').read_text(encoding='utf-8'))['disc_sha256']
    # This plain in-process file stream avoids Python's None console streams.
    with (DATA/'launcher.log').open('w',encoding='utf-8') as log:
        sys.stdout=sys.stderr=log
        sys.argv=['Play','--renderer','vulkan'];os.environ['PS2X_PACKAGE_DATA']=str(DATA)
        os.environ['PS2X_EXEDIR']=str(HERE/'runtime-data')
        os.environ['PS2X_MC_ROOT']=str(DATA/'saves/progression')
        result=trial.main('ps2EntryRunner-standalone.exe')
        request=DATA/'restart-request.json'
        if request.is_file():
            value=json.loads(request.read_text(encoding='utf-8'))
            if value.get('owner_pid')==os.getpid():
                # trial.main has closed the runner/PINE and released GAME_LOCK.
                request.unlink();subprocess.Popen([str(APP/'Play.exe')],cwd=APP,creationflags=subprocess.CREATE_NO_WINDOW)
        return result

def seed_progression():
    """Choose a seed once; opening an existing save is never a reset operation."""
    choice_path=DATA/'save-start-choice.json'
    try:choice=json.loads(choice_path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):choice={'schema':1,'all_unlocked':True}
    if not choice_path.exists():
        choice_path.write_text(json.dumps(choice),encoding='utf-8')
    save=DATA/'saves/progression/BASLUS-21678DBZT3/BASLUS-21678DBZT3'
    save.parent.mkdir(parents=True,exist_ok=True)
    seed=APP/('default-save.bin' if choice.get('all_unlocked',True) else 'fresh-save.bin')
    # BT3 validates the main save AND both card companion files before loading.
    # Repair an incomplete older seed without resetting any existing progress.
    files=((save,seed),)+tuple((save.parent/name,APP/'save-card'/name)
                            for name in ('icon.sys','dbzsm.ico'))
    for target,source in files:
        if target.exists():continue
        payload=source.read_bytes()
        try:
            with target.open('xb') as stream:stream.write(payload)
        except FileExistsError:pass

def main():
    initialize()
    seed_progression()
    if '--check-runtime' in sys.argv:
        sys.path.insert(0,str(HERE));from codex_dependency_check import check_dependencies
        result=check_dependencies();(DATA/'runtime-check.json').write_text(json.dumps(result),encoding='utf-8');return 0
    if imported():return play()
    root=tk.Tk();root.title('BT3 Tag Team');root.configure(bg='#0e1428');root.geometry('640x400');root.resizable(False,False)
    root.iconbitmap(str(APP/'assets/BT3TagTeam.ico'))
    language=tk.StringVar(value=LANG)
    def choose_language(*args):
        global LANG
        LANG=language.get();heading.configure(text=TEXT[LANG][0]);description.configure(text=TEXT[LANG][1]);button.configure(text=TEXT[LANG][2])
    tk.OptionMenu(root,language,'en','es',command=choose_language).pack(anchor='ne',padx=20,pady=10)
    heading=tk.Label(root,text=TEXT[LANG][0],bg='#0e1428',fg='#f5b935',font=('Segoe UI',22,'bold'));heading.pack(pady=15)
    description=tk.Label(root,text=TEXT[LANG][1],bg='#0e1428',fg='white',wraplength=560,font=('Segoe UI',12));description.pack(pady=10)
    progress=ttk.Progressbar(root,length=540,maximum=100);progress.pack(pady=15)
    cancel=threading.Event()
    def choose():
        source=filedialog.askopenfilename(parent=root,title=TEXT[LANG][0],filetypes=[('ISO','*.iso'),('All files','*.*')])
        if not source:return
        button.configure(state='disabled');description.configure(text=TEXT[LANG][3])
        cancel.clear()
        root.protocol('WM_DELETE_WINDOW',cancel.set)
        def work():
            before=set(DATA.glob('import-*'))
            def report(percent,label):
                root.after(0,lambda: (progress.configure(value=percent),description.configure(text=label)))
            try:import_disc(Path(source),report,cancel)
            except Exception as error:
                for temporary in set(DATA.glob('import-*'))-before:
                    # Delete only this worker's newly created private folder.
                    if temporary.resolve().parent==DATA.resolve():shutil.rmtree(temporary)
                if cancel.is_set():root.after(0,root.destroy);return
                message=str(error) if isinstance(error,ImportFailure) else TEXT[LANG][4]
                root.after(0,lambda:messagebox.showerror('BT3 Tag Team',message,parent=root));root.after(0,lambda:button.configure(state='normal'));return
            root.after(0,root.destroy)
        threading.Thread(target=work,daemon=False).start()
    button=tk.Button(root,text=TEXT[LANG][2],command=choose,bg='#173149',fg='#f5b935',font=('Segoe UI',12));button.pack(pady=8)
    tk.Label(root,text='Power Scale: LetsPlayBt3  ·  Tag Team: The Mufti\nSpecial thanks: RidJuampa  ·  Initial build 0.1',bg='#0e1428',fg='white',font=('Segoe UI',10)).pack(side='bottom',pady=16)
    root.mainloop()
    return play() if not cancel.is_set() and imported() else 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:messagebox.showerror('BT3 Tag Team',str(error) if isinstance(error,ImportFailure) else ('No se pudo iniciar el juego. Revisa la importación o reinstala la aplicación.' if LANG=='es' else 'The game could not start. Check your import or reinstall the app.'))

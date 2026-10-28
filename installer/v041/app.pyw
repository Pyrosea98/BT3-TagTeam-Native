"""Release launcher: current native port only; no legacy runtime/controller."""
from pathlib import Path
import json,os,sys,subprocess,threading,shutil,traceback,queue
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from importer import import_game
from credits_splash import attach
APP=Path(__file__).resolve().parent
def data_root():
    p=APP/'data-root.txt'
    return Path(p.read_text(encoding='utf-8-sig').strip()).expanduser().resolve()if p.exists()else APP/'data'
DATA=data_root();DATA.mkdir(parents=True,exist_ok=True)
choice=APP/'install-choices.json'
CHOICES=json.loads(choice.read_text(encoding='utf-8-sig'))if choice.exists()else{}
LANG=CHOICES.get('language','en');LANG='es'if LANG=='es'else'en'
def seed_settings(language,recommended):
    path=DATA/'bt3_settings.txt'
    if not path.exists():
        values=(APP/'recommended-settings.txt').read_text(encoding='utf-8')if recommended else 'update_check=0\nshow_credits_at_startup=1\ncoop_fusion_controls=0\ncoop_fusion_swap_seconds=10\n'
        values+='\nmod_language='+str(int(language=='es'))+'\n';path.write_text(values,encoding='utf-8')
    if CHOICES.get('completed_save',True):
        folder=DATA/'saves/card1/BASLUS-21678DBZT3';folder.mkdir(parents=True,exist_ok=True)
        for p in(APP/'save-seed/BASLUS-21678DBZT3').glob('*'):
            dst=folder/p.name
            if p.is_file()and not dst.exists():
                with dst.open('xb')as f:f.write(p.read_bytes())
def game_environment():
    env=os.environ.copy();env.update(BT3_DATA=str(DATA/'gamedata'),BT3_SETTINGS=str(DATA/'bt3_settings.txt'),BT3_SAVES=str(DATA/'saves'),BT3_GPU_API='vulkan');return env
def play():
    if not (DATA/'gamedata/import-receipt.json').is_file():raise RuntimeError('Complete ISO import first')
    profile=json.loads((APP/'release-profile.json').read_text())
    from importer import digest
    for name,h in profile['runtime'].items():
        if digest(APP/name)!=h:raise RuntimeError('Game program failed verification: '+name)
    log=(DATA/'game.log').open('ab');subprocess.Popen([str(APP/'Tenkaichi3Decomp.exe')],cwd=APP,env=game_environment(),stdout=log,stderr=log);log.close();return 0
def main():
    if '--check-package'in sys.argv:
        from importer import digest
        profile=json.loads((APP/'release-profile.json').read_text())
        for n,h in profile['runtime'].items():assert digest(APP/n)==h,n
        assert digest(APP/'import-data/content.json.gz')==profile['content_manifest_sha256']
        print('PASS package/runtime/manifest identities; game not launched');return 0
    if(DATA/'gamedata/import-receipt.json').exists():
        seed_settings(LANG,CHOICES.get('recommended',True));return play()
    root=tk.Tk();root.title('BT3 Tag Team + Real Power Scale 0.4.1');root.configure(bg='#000000');root.geometry('900x'+str(min(850,int(root.winfo_screenheight()*.9))));root.minsize(640,500)
    try:root.iconbitmap(str(APP/'assets/BT3TagTeam.ico'))
    except tk.TclError:pass
    lang=tk.StringVar(value=LANG);expanded=tk.BooleanVar(value=CHOICES.get('expanded_maps',True));recommended=tk.BooleanVar(value=CHOICES.get('recommended',True));completed=tk.BooleanVar(value=CHOICES.get('completed_save',True))
    tk.OptionMenu(root,lang,'en','es').pack(anchor='ne',padx=16,pady=4)
    tk.Label(root,text='Tag Team Mod / Real Power Scale',bg='black',fg='#ffcf55',font=('Segoe UI',21,'bold')).pack(pady=6)
    panel=attach(root,APP/'assets/credits-v04',lambda:lang.get());panel.pack(fill='both',expand=True,padx=14,pady=4)
    labels=[('expanded',expanded),('recommended',recommended),('completed',completed)];boxes=[]
    words={'en':dict(expanded='Use 2x maps (unchecked: normal size)',recommended='Use recommended settings',completed='Start with all content unlocked (existing saves are kept)',choose='Choose ISO and prepare game',ready='Use original Power Scale BETA 8, or the compatible R4 normal/2x ISO. Your ISO is not changed.',manual='Open manual',cancel='Cancel import'),
    'es':dict(expanded='Usar mapas 2x (sin marcar: tamaño normal)',recommended='Usar ajustes recomendados',completed='Empezar con todo desbloqueado (se conservan las partidas existentes)',choose='Elegir ISO y preparar el juego',ready='Usa Power Scale BETA 8 original o la ISO R4 normal/2x compatible. Tu ISO no se modifica.',manual='Abrir manual',cancel='Cancelar importación')}
    for key,var in labels:
        box=tk.Checkbutton(root,variable=var,bg='black',fg='white',selectcolor='#172636',activebackground='black',activeforeground='white',font=('Segoe UI',11));box.pack(anchor='w',padx=26,pady=2);boxes.append((key,box))
    status=tk.StringVar();tk.Label(root,textvariable=status,bg='black',fg='white',wraplength=820,font=('Segoe UI',10)).pack(pady=6)
    progress=ttk.Progressbar(root,maximum=100,length=800);progress.pack(fill='x',padx=26,pady=6)
    commands=tk.Frame(root,bg='black');commands.pack(pady=8);events=queue.Queue();cancel=threading.Event();running=[False]
    def manual():os.startfile(APP/'manual'/('BT3-TagTeam-Manual-'+lang.get().upper()+'.html'))
    def translate(*unused):
        for k,b in boxes:b.configure(text=words[lang.get()][k])
        choose.configure(text=words[lang.get()]['choose']);guide.configure(text=words[lang.get()]['manual']);stop.configure(text=words[lang.get()]['cancel'])
        if not running[0]:status.set(words[lang.get()]['ready'])
    def close():
        if running[0]:cancel.set();status.set('Cancelling…'if lang.get()=='en'else'Cancelando…')
        else:root.destroy()
    def start():
        source=filedialog.askopenfilename(parent=root,title=words[lang.get()]['choose'],filetypes=[('ISO','*.iso'),('All files','*.*')])
        if not source:return
        selection=dict(language=lang.get(),recommended=recommended.get(),completed_save=completed.get(),expanded_maps=expanded.get());running[0]=True;cancel.clear();choose.configure(state='disabled');stop.configure(state='normal')
        for k,b in boxes:b.configure(state='disabled')
        def worker():
            try:
                result=import_game(source,DATA/'gamedata',APP,'2x'if selection['expanded_maps']else'normal',lambda p,s:events.put(('progress',p,s)),cancel.is_set)
                global CHOICES;CHOICES=selection;seed_settings(selection['language'],selection['recommended']);(DATA/'import-choices.json').write_text(json.dumps(selection,indent=2));events.put(('done',))
            except Exception as e:
                (DATA/'launcher.log').write_text(traceback.format_exc(),encoding='utf-8');events.put(('error',str(e)))
        threading.Thread(target=worker,daemon=False).start()
    def poll():
        try:
            while True:
                e=events.get_nowait()
                if e[0]=='progress':progress.configure(value=e[1]);status.set(e[2])
                elif e[0]=='done':running[0]=False;root.destroy();return
                elif e[0]=='error':
                    running[0]=False;choose.configure(state='normal');stop.configure(state='disabled')
                    for k,b in boxes:b.configure(state='normal')
                    messagebox.showerror('BT3 Tag Team',e[1],parent=root)
        except queue.Empty:pass
        root.after(100,poll)
    choose=tk.Button(commands,command=start,bg='#172636',fg='#ffcf55',font=('Segoe UI',11,'bold'));choose.pack(side='left',padx=6)
    guide=tk.Button(commands,command=manual);guide.pack(side='left',padx=6);stop=tk.Button(commands,command=close,state='disabled');stop.pack(side='left',padx=6)
    lang.trace_add('write',translate);translate();root.protocol('WM_DELETE_WINDOW',close);root.after(100,poll);root.mainloop()
    return play()if not cancel.is_set()and(DATA/'gamedata/import-receipt.json').exists()else 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        (DATA/'launcher.log').write_text(traceback.format_exc(),encoding='utf-8');messagebox.showerror('BT3 Tag Team',str(e));raise SystemExit(1)

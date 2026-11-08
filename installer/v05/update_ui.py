"""Standalone updater UI, also opened by Play.exe --updates."""
from pathlib import Path
import sys,json,threading,queue,traceback
import tkinter as tk
from tkinter import ttk,messagebox
import channel_updates as api

def run(app,automatic=False,local_bundle=None):
 app=Path(app).resolve();prefs=api.config(app)
 if automatic and not prefs.get('check_on_launch',True):return
 choices=app/'install-choices.json';lang=json.loads(choices.read_text(encoding='utf-8-sig')).get('language','en') if choices.exists() else 'en'
 es=lang=='es'
 root=tk.Tk();root.title('BT3 — Actualizaciones' if es else 'BT3 — Updates');root.geometry('640x440');root.configure(bg='#24112e')
 root.protocol('WM_DELETE_WINDOW',lambda:None if busy[0] else root.destroy())
 channel=tk.StringVar(value=prefs['channel']);auto=tk.BooleanVar(value=prefs.get('check_on_launch',True));status=tk.StringVar();events=queue.Queue();busy=[False];found=[None]
 ttk.Label(root,text='BT3 Tag Team / Real Power Scale',font=('Segoe UI',16,'bold')).pack(pady=12)
 row=ttk.Frame(root);row.pack(fill='x',padx=16)
 ttk.Label(row,text='Canal / Channel').pack(side='left');ttk.Combobox(row,textvariable=channel,values=['stable','nightly'],state='readonly',width=12).pack(side='left',padx=10)
 ttk.Checkbutton(root,text='Buscar al iniciar / Check on launch',variable=auto).pack(anchor='w',padx=16,pady=8)
 text=tk.Text(root,height=9,wrap='word',bg='#35203f',fg='#fff4d7',font=('Segoe UI',10));text.pack(fill='both',expand=True,padx=16)
 ttk.Label(root,textvariable=status,wraplength=600).pack(pady=6)
 bar=ttk.Progressbar(root,maximum=100);bar.pack(fill='x',padx=16)
 buttons=ttk.Frame(root);buttons.pack(pady=12)
 def work(fn):
  busy[0]=True;check.configure(state='disabled');install.configure(state='disabled')
  def worker():
   try:events.put(('done',fn()))
   except Exception as e:events.put(('error',str(e)))
  threading.Thread(target=worker,daemon=True).start()
 def search():
  api.save_config(app,channel.get(),auto.get());status.set('Buscando…' if es else 'Checking…');found[0]=None
  work(lambda:('found',api.available(app)))
 def apply():
  if not messagebox.askyesno('BT3','¿Descargar e instalar? Cierra el juego primero.' if es else 'Download and install? Close the game first.',parent=root):return
  api.save_config(app,channel.get(),auto.get())
  if local_bundle:
   def local():
    from update_engine import apply
    apply(app,local_bundle);return ('installed',None)
   work(local)
  else:work(lambda:(api.install(app,found[0],lambda p:events.put(('progress',p))),('installed',None))[1])
 def close():
  if not busy[0]:api.save_config(app,channel.get(),auto.get());root.destroy()
 check=ttk.Button(buttons,text='Buscar / Check',command=search);check.pack(side='left',padx=6)
 install=ttk.Button(buttons,text='Instalar / Install',command=apply,state='disabled');install.pack(side='left',padx=6)
 ttk.Button(buttons,text='Continuar / Continue',command=close).pack(side='left',padx=6)
 def poll():
  try:
   while True:
    event=events.get_nowait()
    if event[0]=='progress':bar['value']=event[1];continue
    busy[0]=False;check.configure(state='normal')
    if event[0]=='error':
     status.set(event[1]);text.insert('end','\n'+('Sin cambios. Puedes continuar sin conexión.' if es else 'No changes. You can continue offline.'))
     if automatic:root.destroy();return
    elif event[1][0]=='found':
     found[0]=event[1][1]
     if not found[0]:
      status.set('Sin actualizaciones compatibles.' if es else 'No compatible updates.')
      if automatic:root.destroy();return
     else:
      text.delete('1.0','end');text.insert('end',found[0]['title']+'\n\n'+found[0]['notes']);install.configure(state='normal');status.set('Descarga opcional / Optional download')
    else:
     bar['value']=100;status.set('Actualización instalada. / Update installed.');install.configure(state='disabled')
  except queue.Empty:pass
  root.after(100,poll)
 root.after(100,poll)
 if local_bundle:
  text.insert('end','Instala la versión incluida sin descargar otra vez. Conserva partidas, ajustes y mapas.\n\nInstall the bundled version without downloading again. Saves, settings and map choice are kept.');install.configure(state='normal');check.configure(state='disabled')
 else:root.after(100,search)
 root.mainloop()

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('installation',nargs='?',default=str(Path(__file__).resolve().parent));p.add_argument('--local-bundle');a=p.parse_args()
 try:run(a.installation,local_bundle=a.local_bundle)
 except Exception as e:messagebox.showerror('BT3 Updates',str(e));sys.exit(1)

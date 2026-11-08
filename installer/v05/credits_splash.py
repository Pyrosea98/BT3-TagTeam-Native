"""Packaged credit/thank-you panel; no game process or loading logic is owned here."""
from pathlib import Path
import json,time,tkinter as tk
from PIL import Image,ImageTk,ImageOps
class CreditsPanel(tk.Canvas):
 def __init__(self,parent,assets,language=lambda:'en',**kw):
  super().__init__(parent,bg='black',highlightthickness=0,**kw)
  self.assets=Path(assets);self.language=language;self.started=time.monotonic();self.photo=None
  self.cards={(page,lang):Image.open(self.assets/(page+'-'+lang+'.png')).convert('RGB') for page in ('credits','thanks') for lang in ('en','es')}
  self.bind('<Configure>',lambda e:self.redraw());self.bind('<Button-1>',self.next_page);self.job=self.after(100,self.tick)
 def next_page(self,event=None):self.started-=5;self.redraw()
 def redraw(self):
  lang='es'if self.language()=='es'else'en';page=('credits','thanks')[int((time.monotonic()-self.started)//5)%2]
  w=max(1,self.winfo_width());h=max(1,self.winfo_height());im=ImageOps.contain(self.cards[page,lang],(w,h),Image.Resampling.LANCZOS)
  self.photo=ImageTk.PhotoImage(im);self.delete('all');self.create_image(w/2,h/2,image=self.photo)
 def tick(self):
  if not self.winfo_exists():return
  self.redraw();self.job=self.after(500,self.tick)
 def destroy(self):
  if self.job:self.after_cancel(self.job);self.job=None
  for im in self.cards.values():im.close()
  super().destroy()
def attach(parent,assets,language=lambda:'en'):return CreditsPanel(parent,assets,language,height=300)
if __name__=='__main__':
 import sys
 assets=Path(sys.argv[1])if len(sys.argv)>1 else Path(__file__).parent/'v04/payload/assets/credits-v04'
 if '--check' in sys.argv:
  data=json.loads((assets/'credits.json').read_text(encoding='utf-8'));assert data['contributors'][2]['name']=='RidJuampa'
  assert 'helping me'in data['thanks']['en'] and 'ayudarme'in data['thanks']['es']
  for page in ('credits','thanks'):
   for lang in ('en','es'):
    with Image.open(assets/(page+'-'+lang+'.png'))as im:assert im.size==(1280,720)
  print('PASS packaged credits EN/ES cards and corrected singular thanks')
 else:
  root=tk.Tk();root.title('BT3 Tag Team — Credits / Thanks');root.geometry('960x540');panel=attach(root,assets);panel.pack(fill='both',expand=True);root.mainloop()

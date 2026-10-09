import json,numpy as np,time,sys
dump=sys.argv[1]
p=json.load(open('menu-names-map-proposal.json'))
exact=[int(k) for k,v in p.items() if v['how']=='exact']
pairs={int(k):v['iso_index'] for k,v in p.items() if v['iso_index'] is not None and int(k)!=v['iso_index']}
ram=np.fromfile(dump,dtype=np.uint8)
ex=np.array(exact)
res=[]
for width,dt in ((1,np.uint8),(2,np.uint16),(4,np.uint32)):
    for stride in (1,2,3,4,6,8,12,16,32,64):
        step=width*stride
        for phase in range(0,step,width):
            n=(len(ram)-phase)//step
            arr=np.ndarray(shape=(n,),dtype=dt,buffer=ram.data,offset=phase,strides=(step,))
            # candidate bases: positions where arr[i]==exact[0] etc. use slot 0 -> value 0 and slot 1 -> value 1
            cand=np.nonzero((arr[:-5]==0)&(arr[1:-4]==1)&(arr[2:-3]==2)&(arr[3:-2]==3))[0]
            for base in cand:
                base=int(base)
                if base+253>n:continue
                win=arr[base:base+253].astype(np.int64)
                ok=int((win[ex]==ex).sum())
                if ok>=len(ex)*0.9:
                    mism={s:int(win[s]) for s in pairs}
                    agree=sum(1 for s,j in pairs.items() if mism[s]==j)
                    res.append((ok,agree,width,step,phase,base*step+phase,mism))
res.sort(key=lambda r:(-r[0],-r[1]))
print(len(res),'identity-like tables')
for r in res[:8]:print('exact ok',r[0],'/',len(exact),'agree with proposal',r[1],'/',len(pairs),'width',r[2],'step',r[3],'at',hex(r[5]),'sample',dict(list(r[6].items())[:6]))

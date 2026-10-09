import json,numpy as np,time,sys
dump=sys.argv[1]
p=json.load(open('menu-names-map-proposal.json'))
pairs={int(k):v['iso_index'] for k,v in p.items() if v['iso_index'] is not None and int(k)!=v['iso_index']}
print('non-identity pairs',len(pairs))
ram=np.fromfile(dump,dtype=np.uint8)
t=time.time();best=[]
check=sorted(pairs.items());slot0,iso0=check[0]
for width,dt in ((1,np.uint8),(2,np.uint16),(4,np.uint32)):
    for stride in (1,2,4,8,16,32,64):
        step=width*stride
        for phase in range(0,step,width):
            n=(len(ram)-phase)//step
            if n<300:continue
            arr=np.ndarray(shape=(n,),dtype=dt,buffer=ram.data,offset=phase,strides=(step,))
            for i in np.nonzero(arr==iso0)[0]:
                base=int(i)-slot0
                if base<0 or base+253>n:continue
                ok=sum(1 for s,j in check if arr[base+s]==j)
                if ok>=len(check)*0.5:best.append((ok,width,step,phase,base*step+phase))
best.sort(reverse=True)
print(round(time.time()-t),'s; candidates',len(best))
for b in best[:10]:print('matches',b[0],'/',len(check),'width',b[1],'step',b[2],'phase',b[3],'address',hex(b[4]))

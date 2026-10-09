"""Preparation wall timings; phase intervals are disjoint, operations may nest."""
import functools
import inspect
import json
import time


def record(session, stage, started, status='ok', kind='operation'):
    event=dict(kind=kind,stage=stage,milliseconds=round((time.monotonic()-started)*1000,3),status=status)
    print('[prepare-timing] '+json.dumps(event,separators=(',',':')),flush=True)
    try:
        with (session.run/'preparation-timings.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event)+'\n')
    except OSError as error:
        print(f'[prepare-timing] receipt write failed: {error}',flush=True)


def boundary(session, label=None, status='ok'):
    previous=getattr(session,'_timing_phase',None)
    if previous is not None:record(session,previous[0],previous[1],status,'phase')
    session._timing_phase=(label,time.monotonic()) if label is not None else None


def timed(function):
    signature=inspect.signature(function)
    @functools.wraps(function)
    def wrapped(self,*args,**kwargs):
        started=time.monotonic();status='failed'
        values=signature.bind(self,*args,**kwargs).arguments
        label=values.get('label','')
        stage=function.__name__+(f':{label}' if label else '')
        try:
            result=function(self,*args,**kwargs)
            status='ok'
            return result
        finally:
            if function.__name__=='prepare':boundary(self,status=status)
            record(self,stage,started,status,'total' if function.__name__=='prepare' else 'operation')
    return wrapped

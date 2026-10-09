"""Bounded cold boot using the actual UI Slice launcher and controller.

No input or user settings changes. Each run keeps its logs and a JSON verdict.
Boot health requires advancing game frames and swaps; host repaint FPS alone
does not pass. This does not prove menu navigation or gameplay.
"""
import argparse,json,re,shutil,statistics,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def analyse(log):
    frames=[];swaps=[];hot_menu=0
    for line in log.splitlines():
        m=re.search(r'^\[fps\] GAME=([\d.]+) gframe=(\d+)',line)
        if m:frames.append((float(m[1]),int(m[2])))
        m=re.search(r'^\[kickq\].*?swaps/s=(\d+)',line)
        if m:swaps.append(int(m[1]))
        if re.search(r'^\[main\] hot=0x2[Bb]0[Bb]00',line):hot_menu+=1
    # Logged roughly once/sec: require recovery in the first thirty samples,
    # and sustained progress at the end rather than a fast first-logo burst.
    window=frames[20:30];tail=frames[-10:];swap_tail=swaps[-10:]
    healthy=(len(window)>=5 and statistics.median(x[0] for x in window)>30 and
             len(tail)>=5 and statistics.median(x[0] for x in tail)>30 and
             tail[-1][1]-tail[0][1]>=200 and len(swap_tail)>=5 and
             statistics.median(swap_tail)>30)
    return dict(pass_boot_health=bool(healthy),game_samples=len(frames),
                game_median_first30_window=statistics.median(x[0] for x in window) if window else None,
                game_median_tail=statistics.median(x[0] for x in tail) if tail else None,
                final_game_frame=frames[-1][1] if frames else None,
                swaps_median_tail=statistics.median(swap_tail) if swap_tail else None,
                menu_wait_pc_samples=hot_menu,mutex_lines=log.count('[mutex]'),
                native_intro_release=log.count('[native-intro]'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runner',required=True)
    parser.add_argument('--seconds',type=float,default=40);args=parser.parse_args()
    if args.seconds<35:parser.error('At least 35 seconds are required')
    dest=HERE/'power-scale-trial/log-archive'/('codex-boot-'+args.runner.removesuffix('.exe')+'-'+time.strftime('%Y%m%d-%H%M%S'))
    dest.mkdir(parents=True,exist_ok=False)
    sys.argv=[sys.argv[0],'--renderer','vulkan','--seconds',str(args.seconds)]
    import codex_ui_slice_trial as trial
    error=None
    try:trial.main(runner_name=args.runner)
    except Exception as exc:error=f'{type(exc).__name__}: {exc}'
    base=HERE/'power-scale-trial'
    for name in ('runner.log','controller.log','controller-status.json'):
        if (base/name).exists():shutil.copy2(base/name,dest/name)
    result=analyse((dest/'runner.log').read_text(errors='replace'))
    result.update(runner=args.runner,seconds=args.seconds,error=error,archive=str(dest))
    if error:result['pass_boot_health']=False
    (dest/'boot-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)
    return 0 if result['pass_boot_health'] else 1
if __name__=='__main__':raise SystemExit(main())

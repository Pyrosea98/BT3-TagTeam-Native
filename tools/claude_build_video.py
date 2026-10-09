"""Claude: assemble the release video (captions only) from video/cuts.json with ffmpeg.

cuts.json = {"output": "BT3-TagTeam-Release", "width": 2560, "height": 1080, "fps": 60,
  "segments": [
    {"type": "card", "name": "title", "seconds": 4, "caption_en": "...", "caption_es": "..."},
    {"type": "clip", "file": "raw/fusion1.mp4", "start": 12.0, "end": 40.0, "speed": 1.0, "audio": true,
     "caption_en": "...", "caption_es": "..."}]}
Cards use video/cards/<name>-<lang>.png. Captions are optional per segment and are shown for the whole segment
(or for [cap_start, cap_end] seconds inside it). Outputs: video/out/<output>-EN.mp4 and -ES.mp4 (+ .srt files).
Usage: python claude_build_video.py [cuts.json] [--encoder libx264|h264_nvenc]
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIDEO = HERE / 'video'
WORK = VIDEO / 'work'
OUT = VIDEO / 'out'
FFMPEG = 'ffmpeg'


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('ffmpeg failed: ' + ' '.join(map(str, cmd))[:300] + '\n' + r.stderr[-1500:])


def fmt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def encode_args(encoder):
    if encoder == 'h264_nvenc':
        return ['-c:v', 'h264_nvenc', '-preset', 'p5', '-cq', '19', '-b:v', '0']
    return ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18']


def build(cuts_path, encoder):
    cfg = json.loads(Path(cuts_path).read_text(encoding='utf-8'))
    w, h, fps = cfg.get('width', 2560), cfg.get('height', 1080), cfg.get('fps', 60)
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    vf_base = f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p'
    for lang in ('en', 'es'):
        parts, srt, t0 = [], [], 0.0
        for i, seg in enumerate(cfg['segments']):
            out = WORK / f'seg_{lang}_{i:03d}.mp4'
            if seg['type'] == 'card':
                png = VIDEO / 'cards' / f"{seg['name']}-{lang}.png"
                dur = float(seg.get('seconds', 3))
                run([FFMPEG, '-y', '-loop', '1', '-t', str(dur), '-i', str(png), '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                     '-vf', vf_base, '-shortest', *encode_args(encoder), '-c:a', 'aac', '-ar', '48000', '-ac', '2', str(out)])
            else:
                src = VIDEO / seg['file']
                if not src.exists():
                    print('SKIP (clip not recorded yet):', seg['file'])
                    continue
                start, end = float(seg['start']), float(seg['end'])
                speed = float(seg.get('speed', 1.0))
                dur = (end - start) / speed
                vf = vf_base if speed == 1.0 else f'setpts=PTS/{speed},' + vf_base
                cmd = [FFMPEG, '-y', '-ss', str(start), '-t', str(end - start), '-i', str(src)]
                if seg.get('audio', True) and speed <= 2.0:
                    af = [] if speed == 1.0 else [f'atempo={speed}']
                    cmd += ['-vf', vf, *(['-af', ','.join(af)] if af else []), *encode_args(encoder), '-c:a', 'aac', '-ar', '48000', '-ac', '2']
                else:
                    cmd = [FFMPEG, '-y', '-ss', str(start), '-t', str(end - start), '-i', str(src), '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                           '-vf', vf, '-shortest', *encode_args(encoder), '-c:a', 'aac', '-ar', '48000', '-ac', '2']
                run(cmd + [str(out)])
            text = seg.get(f'caption_{lang}')
            if text:
                a = t0 + float(seg.get('cap_start', 0.0))
                b = t0 + float(seg.get('cap_end', dur))
                srt.append((a, b, text))
            parts.append(out)
            t0 += dur
        lst = WORK / f'list_{lang}.txt'
        lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts), encoding='utf-8')
        timeline = WORK / f'timeline_{lang}.mp4'
        run([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(timeline)])
        srt_path = OUT / f"{cfg.get('output', 'release')}-{lang.upper()}.srt"
        srt_path.write_text(''.join(f'{n}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n' for n, (a, b, t) in enumerate(srt, 1)), encoding='utf-8')
        final = OUT / f"{cfg.get('output', 'release')}-{lang.upper()}.mp4"
        # An ASS file with an explicit 2560x1080 play resolution keeps font size and margins predictable.
        ass_path = WORK / f'cap_{lang}.ass'
        def ass_time(t):
            cs = int(round(t * 100)); hh, cs = divmod(cs, 360000); mm, cs = divmod(cs, 6000); ss, cs = divmod(cs, 100)
            return f'{hh}:{mm:02d}:{ss:02d}.{cs:02d}'
        header = (
            '[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n'
            '[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
            'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
            'Style: Default,Liberation Sans,46,&H00FFFFFF,&H00FFFFFF,&H00241410,&H96000000,0,0,0,0,100,100,0,0,1,3.5,1,2,320,320,64,1\n\n'
            '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n') % (w, h)
        lines = ''.join('Dialogue: 0,%s,%s,Default,,0,0,0,,%s\n' % (ass_time(x), ass_time(y), t.replace('\n', '\\N')) for x, y, t in srt)
        ass_path.write_text(header + lines, encoding='utf-8')
        run([FFMPEG, '-y', '-i', f'timeline_{lang}.mp4', '-vf', f'ass=cap_{lang}.ass:fontsdir=../../font-candidates',
             *encode_args(encoder), '-c:a', 'copy', '-movflags', '+faststart', str(final)], cwd=WORK)
        print('wrote', final, f'({t0:.1f}s)')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    enc = 'libx264'
    if '--encoder' in sys.argv:
        enc = sys.argv[sys.argv.index('--encoder') + 1]
        args = [a for a in args if a != enc]
    build(args[0] if args else VIDEO / 'cuts.json', enc)

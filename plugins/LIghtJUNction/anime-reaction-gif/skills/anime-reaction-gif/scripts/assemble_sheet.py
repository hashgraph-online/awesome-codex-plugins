#!/usr/bin/env python3
"""Assemble looped key-pose reaction GIFs with FFmpeg; Python only orchestrates.

All crops, scaling, playback, palette creation and image output are FFmpeg
operations. No Python image editing or image packages are used. Processing is
sequential with one decoder / filter thread to bound memory use.
"""
from pathlib import Path
import argparse, hashlib, json, math, shutil, subprocess

def run(*args):
    result=subprocess.run(args,check=True,capture_output=True,text=True)
    return result.stdout

def ffmpeg(*args):
    return run('ffmpeg','-hide_banner','-loglevel','error','-y','-threads','1',
               '-filter_threads','1','-filter_complex_threads','1',*args)

def probe(path,extra=()):
    return json.loads(run('ffprobe','-v','error',*extra,'-show_entries',
      'format=duration,size:stream=width,height,nb_frames,nb_read_frames,codec_name,pix_fmt,avg_frame_rate',
      '-of','json',str(path)))

def concat_escape(path):
    return str(path).replace("'","'\\''")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('sheet',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--columns',type=int,default=3)
    p.add_argument('--rows',type=int,default=2)
    p.add_argument('--cell-size',type=int,help='Optional expected square source-cell side; catches a wrongly declared grid.')
    p.add_argument('--size',type=int,default=384)
    p.add_argument('--fps',type=int,default=12)
    p.add_argument('--inset',type=int,default=0,
      help='Pixels trimmed from each cell edge if generated sheet has gutters.')
    p.add_argument('--sequence',help='Zero-based row-major indexes. Default: all declared cells, then cell 0.')
    p.add_argument('--durations',help='Hold seconds, one per sequence entry.')
    p.add_argument('--background',default='0xf6f4ef')
    p.add_argument('--overwrite',action='store_true',help='Replace artifacts at this output name.')
    args=p.parse_args()
    sheet=args.sheet.resolve();out=args.output.resolve()
    if args.columns<=0 or args.rows<=0:p.error('Columns and rows must be positive.')
    if args.size<=0 or args.size%2:p.error('Size must be positive and even for the yuv420p MP4.')
    if not 1<=args.fps<=100:p.error('FPS must be 1–100; GIF delays have 10 ms resolution.')
    if args.inset<0 or (args.cell_size is not None and args.cell_size<=0):p.error('Inset must be nonnegative; cell size must be positive.')
    if not sheet.is_file():p.error(f'Sheet not found: {sheet}')
    if out.suffix.lower()!='.gif':p.error('Output must end in .gif.')
    if not args.overwrite and (out.exists() or out.with_suffix('.mp4').exists()):p.error('Output already exists; choose a new name or use --overwrite.')
    for tool in ('ffmpeg','ffprobe'):
        if not shutil.which(tool):p.error(f'{tool} is required on PATH.')
    try:
        sequence=[int(n.strip()) for n in args.sequence.split(',')] if args.sequence else [*range(args.columns*args.rows),0]
        durations=[float(n.strip()) for n in args.durations.split(',')] if args.durations else [.25]*len(sequence)
        if not args.durations:durations[0]=.5;durations[-1]=.35
    except ValueError:p.error('Sequence must contain integers; durations must contain numbers.')
    if len(sequence)!=len(durations):p.error('Sequence and duration lengths differ.')
    if not sequence or min(sequence)<0 or max(sequence)>=args.columns*args.rows:p.error('Pose index outside sheet.')
    if any(not math.isfinite(n) or n<1/args.fps for n in durations):p.error('Each hold must be finite and at least one output frame (1 / FPS).')
    info=probe(sheet);stream=info['streams'][0]
    width,height=stream['width'],stream['height']
    if width%args.columns or height%args.rows:p.error(f'Sheet {width}×{height} is not divisible into {args.columns}×{args.rows} equal pixel cells.')
    cw,ch=width//args.columns,height//args.rows
    if args.cell_size is not None and (cw!=args.cell_size or ch!=args.cell_size):p.error(f'Grid gives {cw}×{ch} cells; expected {args.cell_size}×{args.cell_size}. Check the grid or source.')
    if 2*args.inset>=min(cw,ch):p.error('Inset removes the entire cell.')
    # Check geometry and timing before creating destination files.
    out.parent.mkdir(parents=True,exist_ok=True)
    work=out.parent/(out.stem+'-frames');work.mkdir(exist_ok=True)
    cells=[]
    for n in range(args.columns*args.rows):
        row,col=divmod(n,args.columns)
        x0=col*cw+args.inset;y0=row*ch+args.inset
        x1=(col+1)*cw-args.inset;y1=(row+1)*ch-args.inset
        cell=work/f'pose-{n:02}.png'
        vf=f'crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={args.size}:{args.size}:force_original_aspect_ratio=decrease:flags=lanczos,pad={args.size}:{args.size}:(ow-iw)/2:(oh-ih)/2:color={args.background},setsar=1'
        ffmpeg('-i',str(sheet),'-vf',vf,'-frames:v','1',str(cell));cells.append(cell)
    timeline=work/'timeline.txt'
    rows=[]
    for n,duration in zip(sequence,durations):
        rows.extend([f"file '{concat_escape(cells[n])}'",'option framerate 1000',f'duration {duration:.8f}'])
    # The concat demuxer needs one repeated final image to honor its duration.
    rows.extend([f"file '{concat_escape(cells[sequence[-1]])}'",'option framerate 1000'])
    timeline.write_text('\n'.join(rows)+'\n',encoding='utf-8')
    clip=work/'timeline.mkv';total=sum(durations)
    ffmpeg('-f','concat','-safe','0','-i',str(timeline),'-t',str(total),
      '-vf',f'fps={args.fps}','-c:v','ffv1','-level','3','-pix_fmt','rgb24',str(clip))
    palette=work/'palette.png'
    ffmpeg('-i',str(clip),'-vf','palettegen=max_colors=192:stats_mode=diff',
      '-frames:v','1',str(palette))
    ffmpeg('-i',str(clip),'-i',str(palette),'-lavfi',
      'paletteuse=dither=sierra2_4a:diff_mode=rectangle','-loop','0',str(out))
    # Keep a browser-friendly video preview beside the GIF, without changing it.
    ffmpeg('-i',str(clip),'-c:v','libx264','-crf','18','-preset','fast',
      '-pix_fmt','yuv420p','-movflags','+faststart',str(out.with_suffix('.mp4')))
    actual=probe(out,('-count_frames',));s=actual['streams'][0]
    frames=int(s.get('nb_read_frames',s.get('nb_frames','0')))
    if frames<2:raise RuntimeError('Export contains fewer than two frames.')
    indexes=[];seen=set();elapsed=0
    for pose,duration in zip(sequence,durations):
        if pose not in seen:
            indexes.append(min(frames-1,round((elapsed+duration*.5)*args.fps)))
            seen.add(pose)
        elapsed+=duration
    indexes=sorted(set(indexes))
    contact_columns=min(args.columns,len(indexes));contact_rows=math.ceil(len(indexes)/contact_columns)
    selection='+'.join(f'eq(n\\,{i})' for i in indexes)
    ffmpeg('-i',str(out),'-vf',f'select={selection},scale=256:256:flags=lanczos,tile={contact_columns}x{contact_rows}:padding=8:margin=8:color=0xeeeae4',
      '-frames:v','1',str(out.with_name(out.stem+'-decoded-contact.png')))
    for label,n in [('first',0),('middle',frames//2),('last',frames-1)]:
        ffmpeg('-i',str(out),'-vf',f'select=eq(n\\,{n})',
          '-frames:v','1',str(out.with_name(out.stem+f'-decoded-{label}.png')))
    first_path=out.with_name(out.stem+'-decoded-first.png')
    last_path=out.with_name(out.stem+'-decoded-last.png')
    ffmpeg('-i',str(first_path),'-vf','scale=240:240:flags=lanczos',
      '-frames:v','1',str(out.with_name(out.stem+'-mobile.png')))
    data=out.read_bytes()
    loop_marker=b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'
    if loop_marker not in data:raise RuntimeError('GIF infinite-loop metadata was not found.')
    mp4=out.with_suffix('.mp4');video=probe(mp4)
    report={'gif':str(out),'sha256':hashlib.sha256(data).hexdigest(),
      'bytes':len(data),'size':[s['width'],s['height']],
      'frames':frames,'duration_s':float(actual['format']['duration']),'requested_duration_s':total,'fps':args.fps,
      'loop':0 if loop_marker in data else 'unverified',
      'source_sheet':str(sheet),'source_sheet_sha256':hashlib.sha256(sheet.read_bytes()).hexdigest(),
      'source_sheet_size':[width,height],'grid':[args.columns,args.rows],'cell_size':[cw,ch],
      'distinct_pose_cells':len(set(sequence)),
      'sequence':sequence,'hold_seconds':durations,
      'decoded_contact_frames':indexes,'frame_editing_tool':'FFmpeg only',
      'mp4':{'path':str(mp4),'sha256':hashlib.sha256(mp4.read_bytes()).hexdigest(),'bytes':mp4.stat().st_size,'probe':video}}
    report['decoded_first_last_png_identical']=first_path.read_bytes()==last_path.read_bytes()
    out.with_name(out.stem+'-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f'{exc.cmd[0]} failed:\n{exc.stderr.strip()}') from exc

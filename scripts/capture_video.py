"""Capture a real Anki reviewer demonstration in an isolated test profile.

The sample and narration inputs are snapshotted into a disposable profile.
No personal collection or sync account is opened. Only Qt reviewer frames
are recorded; the final narration is mixed separately by the publishing task.
"""
import argparse
import json
import os
from pathlib import Path
import pickle
import shutil
import sqlite3
import subprocess
import tempfile
import time
import uuid

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sample',required=True,type=Path)
parser.add_argument('--narration',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--fps',default=15,type=int)
args=parser.parse_args()
assert 5<=args.fps<=30
root=Path(__file__).resolve().parents[1]
base=Path(tempfile.mkdtemp(prefix='cfa-native-video-'))
args.output.mkdir(parents=True,exist_ok=True)
shutil.copyfile(args.sample,base/'sample.json')
shutil.copyfile(args.narration,base/'narration.json')
shutil.copytree(root/'chess_for_anki',base/'addons21/chess_for_anki',ignore=shutil.ignore_patterns('user_files','meta.json','__pycache__','*.pyc'))
probe=base/'addons21/zz_native_video';probe.mkdir(parents=True)
shutil.copyfile(root/'tests/anki_video_probe.py',probe/'__init__.py')
with sqlite3.connect(base/'prefs21.db') as db:
    db.execute('create table profiles(name text primary key collate nocase,data blob not null)')
    for name,data in [('_global',dict(ver=0,updates=False,created=int(time.time()),id=909665,lastMsg=0,firstRun=False,suppressUpdate=True,defaultLang='en_US')),('Video QA',dict(autoSync=False,numBackups=0,searchHistory=[],syncKey=None))]:
        db.execute('insert into profiles values(?,?)',(name,pickle.dumps(data,protocol=4)))
env=dict(os.environ,ANKI_SINGLE_INSTANCE_KEY='CFA_VIDEO_'+uuid.uuid4().hex,CFA_VIDEO_BASE=str(base),CFA_VIDEO_OUTPUT=str(args.output.resolve()),CFA_VIDEO_FPS=str(args.fps))
target=args.output/'native-capture.json'
if target.exists():
    raise RuntimeError('Choose a new capture output directory; an existing capture will not be overwritten.')
with (args.output/'anki-capture.log').open('wb') as log:
    process=subprocess.Popen([r'C:\Program Files\Anki\Anki.exe','-b',str(base),'-p','Video QA'],env=env,stdout=log,stderr=subprocess.STDOUT)
    for _ in range(360):
        if target.exists() or process.poll() is not None:break
        time.sleep(.5)
    if not target.exists():raise RuntimeError('No video capture result: '+str(base))
    result=json.loads(target.read_text(encoding='utf8'))
    process.wait(timeout=30)
    if result.get('error'):raise RuntimeError(result['error'])
frames=result['frames']
assert len(frames)>100
concat=args.output/'frames.ffconcat'
lines=['ffconcat version 1.0']
for index,frame in enumerate(frames):
    duration=(frames[index+1]['time']-frame['time']) if index+1<len(frames) else 1/args.fps
    assert duration>0
    lines += ["file '"+frame['file']+"'",'duration '+format(duration,'.6f')]
lines += ["file '"+frames[-1]['file']+"'"]
concat.write_text('\n'.join(lines)+'\n',encoding='utf8')
raw=args.output/'Chess-for-Anki-Brilliancy-raw.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-safe','0','-i',str(concat),'-vf','fps=30,pad=ceil(iw/2)*2:ceil(ih/2)*2','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(raw)],cwd=args.output,check=True)
result['raw_video']=raw.name
result['ffprobe']=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(raw)]))
target.write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({key:value for key,value in result.items() if key not in ('frames','ffprobe')},ensure_ascii=True))

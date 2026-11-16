"""Exercise the real reviewer in an isolated, non-syncing Anki profile.

Pass a local curated exercise JSON. No personal collection is opened and the
input content is not included in source releases.
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
parser.add_argument('--pack',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--anki',default=r'C:\Program Files\Anki\Anki.exe')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
base=Path(tempfile.mkdtemp(prefix='cfa-brilliancy-qa-'))
args.output.mkdir(parents=True,exist_ok=True)
shutil.copyfile(args.pack,base/'pack.json')
shutil.copytree(root/'chess_for_anki',base/'addons21'/'chess_for_anki',ignore=shutil.ignore_patterns('__pycache__','user_files','meta.json'))
probe=base/'addons21'/'zz_brilliancy_probe'
probe.mkdir(parents=True)
shutil.copyfile(root/'tests'/'anki_brilliancy_probe.py',probe/'__init__.py')
with sqlite3.connect(base/'prefs21.db') as db:
    db.execute('create table profiles(name text primary key collate nocase,data blob not null)')
    for name,data in [('_global',dict(ver=0,updates=False,created=int(time.time()),id=909663,lastMsg=0,firstRun=False,suppressUpdate=True,defaultLang='en_US')),('Brilliancy QA',dict(autoSync=False,numBackups=0,searchHistory=[],syncKey=None))]:
        db.execute('insert into profiles values(?,?)',(name,pickle.dumps(data,protocol=4)))
env=dict(os.environ,ANKI_SINGLE_INSTANCE_KEY='CFA_BRILLIANCY_'+uuid.uuid4().hex,CFA_BRILLIANCY_BASE=str(base),CFA_BRILLIANCY_OUTPUT=str(args.output.resolve()))
log=args.output/'anki-qa.log'
with log.open('w',encoding='utf8') as out:
    process=subprocess.Popen([args.anki,'-b',str(base),'-p','Brilliancy QA'],env=env,stdout=out,stderr=out)
    for _ in range(360):
        if (args.output/'native-verification.json').exists() or process.poll() is not None:
            break
        time.sleep(.5)
    target=args.output/'native-verification.json'
    if not target.exists():
        raise RuntimeError('No native result; inspect '+str(base)+' and '+str(log))
    result=json.loads(target.read_text(encoding='utf8'))
    process.wait(timeout=30)
    if result.get('error'):
        raise RuntimeError(result['error'])
    print(json.dumps(result,ensure_ascii=True))

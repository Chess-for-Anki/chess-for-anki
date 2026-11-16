"""Export and reimport the free sample in an isolated, non-syncing profile."""
import argparse,json,os,pickle,shutil,sqlite3,subprocess,tempfile,time,uuid
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sample',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
base=Path(tempfile.mkdtemp(prefix='cfa-sample-qa-'))
args.output.mkdir(parents=True,exist_ok=True)
shutil.copyfile(args.sample,base/'sample.json')
shutil.copytree(root/'chess_for_anki',base/'addons21/chess_for_anki',ignore=shutil.ignore_patterns('user_files','meta.json','__pycache__','*.pyc'))
probe=base/'addons21/zz_sample_probe';probe.mkdir(parents=True)
shutil.copyfile(root/'tests/anki_sample_probe.py',probe/'__init__.py')
with sqlite3.connect(base/'prefs21.db') as db:
    db.execute('create table profiles(name text primary key collate nocase,data blob not null)')
    for name,data in [('_global',dict(ver=0,updates=False,created=int(time.time()),id=909664,lastMsg=0,firstRun=False,suppressUpdate=True,defaultLang='en_US')),('Sample QA',dict(autoSync=False,numBackups=0,searchHistory=[],syncKey=None))]:
        db.execute('insert into profiles values(?,?)',(name,pickle.dumps(data,protocol=4)))
env=dict(os.environ,ANKI_SINGLE_INSTANCE_KEY='CFA_SAMPLE_'+uuid.uuid4().hex,CFA_SAMPLE_BASE=str(base),CFA_SAMPLE_OUTPUT=str(args.output.resolve()))
target=args.output/'sample-verification.json'
with (args.output/'anki-sample.log').open('wb') as log:
    process=subprocess.Popen([r'C:\Program Files\Anki\Anki.exe','-b',str(base),'-p','Sample QA'],env=env,stdout=log,stderr=subprocess.STDOUT)
    for _ in range(240):
        if target.exists() or process.poll() is not None:break
        time.sleep(.5)
    if not target.exists():raise RuntimeError('No sample result: '+str(base))
    result=json.loads(target.read_text(encoding='utf8'))
    process.wait(timeout=30)
    if result.get('error'):raise RuntimeError(result['error'])
    print(json.dumps(result))

from pathlib import Path
import json,hashlib,csv,tarfile,time
b=Path('data/external').resolve()
p=b/'retailaction/archives/train.tar.partial'
expected=26084833280
# Wait for the download command to finish before running this script.
if p.exists():
 with tarfile.open(p) as t:
  members=t.getmembers()
  if not members:raise RuntimeError('Empty training archive')
 final=p.with_suffix('');p.rename(final)
 out=b/'retailaction/raw/train';out.mkdir(exist_ok=True)
 print('Extracting training archive',flush=True)
 with tarfile.open(final) as t:t.extractall(out,filter='data')
rows=[]
for folder in sorted(b.iterdir()):
 if not folder.is_dir():continue
 files=list((folder/'raw').rglob('*'));files=[p for p in files if p.is_file()]
 counts={}
 for f in files:counts[f.suffix]=counts.get(f.suffix,0)+1
 rows.append({'dataset':folder.name,'extracted_files':len(files),'extracted_bytes':sum(f.stat().st_size for f in files),'extensions':counts})
 print(folder.name,len(files),counts,flush=True)
 with (folder/'metadata/file_inventory.csv').open('w',newline='',encoding='utf-8') as out:
  w=csv.writer(out);w.writerow(['path','bytes'])
  for f in files:w.writerow([str(f.relative_to(folder)),f.stat().st_size])
 checks={}
 for f in list((folder/'archives').glob('*'))+list((folder/'raw').glob('*')):
  if f.is_file():
   h=hashlib.sha256()
   with f.open('rb') as stream:
    for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
   checks[str(f.relative_to(folder))]=h.hexdigest()
 (folder/'metadata/sha256.json').write_text(json.dumps(checks,indent=2))
(b/'inventory.json').write_text(json.dumps(rows,indent=2))

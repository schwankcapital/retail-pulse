from pathlib import Path
import shutil, subprocess, tarfile, zipfile, json, hashlib, time
root=Path('data').resolve(); base=root/'external'; base.mkdir(exist_ok=True)
names=['retailaction','merl_shopping','sku110k','cosmetics_retail','agrishelf','freshretailnet','retail_transactions_stocks','walmart_m5','favorita']
for n in names:
 for d in ['archives','raw','metadata']: (base/n/d).mkdir(parents=True,exist_ok=True)
for p in list(root.rglob('*')):
 if not p.is_file() or base in p.parents: continue
 n=p.name
 target=('retailaction' if n in ['test.tar','validation.tar'] else 'merl_shopping' if 'MERL' in n or n=='ReadMe.txt' else 'sku110k' if 'SKU110K' in n else 'cosmetics_retail' if 'cosmetics' in n else 'agrishelf' if 'AgriShelf' in n else 'freshretailnet' if n.endswith('.parquet') else 'retail_transactions_stocks' if n.startswith('retail_') else 'walmart_m5' if n.startswith('m5-') else 'favorita' if n.startswith('favorita-') else None)
 if target:
  dest=base/target/('archives' if n.endswith(('.zip','.tar','.gz','.7z')) else 'metadata' if n=='ReadMe.txt' else 'raw')/n
  assert p.is_relative_to(root) and dest.is_relative_to(root)
  if not dest.exists(): shutil.move(str(p),str(dest)); print('Organized',n,flush=True)
url='https://huggingface.co/datasets/standard-cognition/RetailAction/resolve/main/data/train.tar?download=true'
p=base/'retailaction/archives/train.tar'
if not p.exists():
 part=p.with_suffix('.tar.partial')
 log=open(base/'retailaction/metadata/download.log','w')
 proc=subprocess.Popen(['curl.exe','-L','--fail','--retry','5','-C','-','-o',str(part),url],stdout=log,stderr=log)
 (base/'retailaction/metadata/download_process.json').write_text(json.dumps({'pid':proc.pid,'url':url}))
 print('Download PID',proc.pid,flush=True)
for n in names:
 for p in (base/n/'archives').iterdir():
  if p.suffix=='.partial':continue
  out=base/n/'raw'/p.name.removesuffix('.tar.gz').removesuffix('.zip').removesuffix('.tar'); out.mkdir(exist_ok=True)
  print('Extracting',p.name,flush=True)
  if p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:
    for i in z.infolist():
     assert (out/i.filename).resolve().is_relative_to(out.resolve())
    z.extractall(out)
  else:
   with tarfile.open(p) as t:t.extractall(out,filter='data')
  print('Extracted',p.name,flush=True)
 for p in list((base/n/'raw').rglob('*.7z')):
  print('Extracting nested',p.name,flush=True)
  subprocess.run(['tar.exe','-xf',str(p),'-C',str(p.parent)],check=True)
print('EXTRACTION COMPLETE',flush=True)

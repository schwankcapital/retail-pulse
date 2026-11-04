from pathlib import Path
import zipfile
for n in ['agrishelf','cosmetics_retail']:
 for p in Path('data/external',n,'raw').rglob('*.zip'):
  out=p.with_suffix('');out.mkdir(exist_ok=True)
  print('Nested extraction',p.name,flush=True)
  with zipfile.ZipFile(p) as z:
   for i in z.infolist():assert (out/i.filename).resolve().is_relative_to(out.resolve())
   z.extractall(out)
print('Nested ZIPs complete',flush=True)

from pathlib import Path
import urllib.request,json,concurrent.futures
b=Path('data/external')
sources={'retailaction':'https://huggingface.co/datasets/standard-cognition/RetailAction','merl_shopping':'https://www.merl.com/research/downloads/MERL_Shopping_Dataset','sku110k':'https://github.com/eg4000/SKU110K_CVPR19','cosmetics_retail':'https://huggingface.co/datasets/Innovatiana/innv-cosmetics-dataset-for-retail','agrishelf':'https://data.mendeley.com/datasets/s3vc2552sf/3','freshretailnet':'https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K','retail_transactions_stocks':'https://data.mendeley.com/datasets/27x8mjm8k4/1','walmart_m5':'https://www.kaggle.com/competitions/m5-forecasting-accuracy/data','favorita':'https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data'}
def fetch(n,u,f):
 try:
  data=urllib.request.urlopen(u,timeout=45).read(); (b/n/'metadata'/f).write_bytes(data);return n,f,len(data)
 except Exception as e:return n,f,str(e)
jobs=[]
for n,u in sources.items():
 (b/n/'metadata/source.json').write_text(json.dumps({'source_url':u,'organized_date':'2026-10-27','origin':'REAL_SOURCE','note':'Existing files supplied by user; original download dates unknown. Not integrated into application.'},indent=2))
 jobs.append((n,u,'publisher.html'))
 if 'huggingface.co' in u:
  jobs += [(n,u+'/raw/main/README.md','README.md'),(n,u+'/raw/main/LICENSE','LICENSE')]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for r in ex.map(lambda a:fetch(*a),jobs):print(r,flush=True)

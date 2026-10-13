"""Supplement Australian jobs with Canva, Easygo and Go1 public employer feeds.
Run collect_australia_jobs.py first, then this script.
"""
import csv,json,re,concurrent.futures
from pathlib import Path
import collect_australia_jobs as m
P=Path(__file__).resolve().parent
errors=[]
for name,slug in [('Easygo','easygo'),('Go1 Australia','go1au')]:
 c,data,error=m.fetch_board({'name':name,'slug':slug,'platform':'greenhouse'})
 if error:errors.append({'company':name,'error':error});continue
 for j in data.get('jobs',[]):
  m.add(str(j['id']),j['title'],name,j.get('content'),j.get('first_published'),j.get('location',{}).get('name',''),'Greenhouse',j.get('absolute_url',''))
def company_jobs(company):
 items=[];offset=0
 try:
  while True:
   data=m.get(f'https://api.smartrecruiters.com/v1/companies/{company}/postings?limit=100&offset={offset}')
   items.extend(data.get('content',[]));offset+=len(data.get('content',[]))
   if offset>=data.get('totalFound',0) or not data.get('content'):break
  return company,items,None
 except Exception as e:return company,items,str(e)
companies=['Canva','Cuscal','Rest','OFX','TAL','Nine','Experian','Qantas','IAG','AECOM','Endava']
selected=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for company,items,error in ex.map(company_jobs,companies):
  if error:errors.append({'company':company,'error':error})
  selected.extend((company,j) for j in items if j.get('location',{}).get('country','').lower()=='au' and any(re.search(p,j['name'],re.I) for c,p in m.patterns if c!='NLP Engineer'))
def detail(pair):
 company,j=pair
 try:return company,j,m.get(j.get('ref') or f'https://api.smartrecruiters.com/v1/companies/{company}/postings/{j["id"]}'),None
 except Exception as e:return company,j,None,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for company,j,d,error in ex.map(detail,selected):
  if error:errors.append({'id':j['id'],'error':error});continue
  (m.CACHE/f'{company}_{j["id"]}.json').write_text(json.dumps(d,ensure_ascii=False))
  sections=d.get('jobAd',{}).get('sections',{})
  text='\n'.join(v.get('text','') for v in sections.values() if isinstance(v,dict))
  loc=j['location'].get('fullLocation') or j['location'].get('city','')+', Australia'
  m.add(j['id'],j['name'],d.get('company',{}).get('name') or company,text,j.get('releasedDate'),loc,'SmartRecruiters',d.get('postingUrl') or f'https://jobs.smartrecruiters.com/{company}/{j["id"]}')
p=P/'australia_jobs_2020_2026.csv'
with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
rows.extend(m.rows)
unique={}
for r in rows:
 k=tuple(re.sub(r'\s+',' ',str(r[c]).strip().lower()) for c in ['company','job_title','location','date_posted'])
 unique.setdefault(k,r)
rows=list(unique.values())
# Keep only complete records and Australian recruitment locations.
rows=[r for r in rows if all(str(r[c]).strip() for c in m.fields) and r['career_category']!='NLP Engineer']
assert len(set(r['job_id'] for r in rows))==len(rows)
assert all(any(m.australian_location(x) for x in re.split(r';|\|',r['location'])) for r in rows)
with p.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=m.fields);w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['career_category'],r['company'],r['job_id'])))
from collections import Counter
s={'total':len(rows),'collected_at':str(m.TODAY),'categories':dict(Counter(r['career_category'] for r in rows)),'years':dict(Counter(str(r['year']) for r in rows)),'companies':dict(Counter(r['company'] for r in rows)),'sources':dict(Counter(r['source'] for r in rows)),'locations':dict(Counter(r['location'] for r in rows)),'supplement_errors':errors}
(P/'australia_verified_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print(json.dumps(s,ensure_ascii=False,indent=2))

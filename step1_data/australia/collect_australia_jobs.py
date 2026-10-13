"""Collect Australian jobs from public Greenhouse, Ashby, Remote OK and Remotive feeds."""
import csv,json,re,html,concurrent.futures
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

OUT=Path(__file__).resolve().parent
CACHE=OUT.parent/'work'/'australia_jobs'
CACHE.mkdir(parents=True,exist_ok=True)
TODAY=datetime.now(ZoneInfo('Australia/Sydney')).date()
patterns=[('NLP Engineer',r'\b(nlp|natural language processing)\b.*\bengineer|\bengineer.*\b(nlp|natural language processing)\b'),('ML Engineer',r'\b(machine learning|ml)\b.*\bengineer|\bengineer.*\b(machine learning|ml)\b'),('AI Engineer',r'\b(ai|artificial intelligence)\b.*\bengineer|\bengineer.*\b(ai|artificial intelligence)\b'),('Data Scientist',r'\bdata scien(?:tist|tists)\b'),('Data Analyst',r'\bdata analyst\b'),('Data Engineer',r'\bdata engineer(?:ing)?\b')]
fields=['job_id','career_category','job_title','company','job_description','date_posted','year','date_basis','location','source','source_url','collected_at']
rows=[]; logs=[]
def get(url):
 r=requests.get(url,timeout=35,headers={'User-Agent':'PublicJobResearch/1.0'});r.raise_for_status();return r.json()
def australian_location(location):
 # Country labels or Australian city/state names; no inference from employer HQ.
 # Exclude explicitly named overseas countries when Australia is not explicit.
 text = str(location or '')
 if re.search(r'\bAustralia\b|\bAU\b|\bAUS\b', text, re.I):
  return True
 if re.search(r'\b(Canada|United States|USA|United Kingdom|UK|India|New Zealand|NZ)\b', text, re.I):
  return False
 return bool(re.search(r'\b(Sydney|Melbourne|Brisbane|Adelaide|Canberra|Gold Coast|New South Wales|Queensland|Western Australia|South Australia|Tasmania|Northern Territory|Australian Capital Territory)\b|\bPerth\s*,\s*(WA|Western Australia)', text, re.I))

def add(ident,title,company,description,posted,location,source,url):
 if not any(australian_location(part) for part in re.split(r';|\|', str(location))):return
 cat=next((c for c,p in patterns if re.search(p,title,re.I)),None)
 if not cat or cat == "NLP Engineer":return
 try:d=datetime.fromisoformat(str(posted).replace('Z','+00:00')).date()
 except (ValueError,TypeError):return
 if not 2020<=d.year<=2026 or d>TODAY:return
 desc=BeautifulSoup(html.unescape(description or ''),'html.parser').get_text('\n',strip=True)
 if not all([ident,title,company,desc,url]):return
 rows.append(dict(zip(fields,[f'{source}:{ident}',cat,title,company,desc,d.isoformat(),d.year,'source_publication_date',location,source,url,TODAY.isoformat()])))

def fetch_board(c):
 platform=c['platform']; slug=c['slug']
 url=(f'https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true' if platform=='greenhouse' else f'https://api.ashbyhq.com/posting-api/job-board/{slug}')
 try:
  data=get(url);(CACHE/f'{platform}_{slug}.json').write_text(json.dumps(data,ensure_ascii=False))
  return c,data,None
 except Exception as e:return c,None,str(e)

def main():
 companies=get('https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/companies.json')
 # The registry provides board names only; descriptions/dates come directly from employers' feeds.
 boards=[c for c in companies if c['platform']=='greenhouse']+[c for c in companies if c['platform']=='ashby']
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  for n,(c,data,error) in enumerate(ex.map(fetch_board,boards),1):
   if error:logs.append({'company':c['name'],'error':error});continue
   for j in data.get('jobs',[]):
    if c['platform']=='greenhouse':
     add(str(j['id']),j['title'],c['name'],j.get('content'),j.get('first_published'),j.get('location',{}).get('name',''),'Greenhouse',j.get('absolute_url',''))
    else:
     add(j.get('id',''),j.get('title',''),c['name'],j.get('descriptionHtml') or j.get('descriptionPlain'),j.get('publishedAt'),j.get('location',''),'Ashby',j.get('jobUrl',''))
   if n%20==0:print(f'Processed {n}/{len(boards)} boards; {len(rows)} eligible jobs',flush=True)
 for source,url in [('Remote OK','https://remoteok.com/api'),('Remotive','https://remotive.com/api/remote-jobs')]:
  try:
   data=get(url);(CACHE/(source.replace(' ','_')+'.json')).write_text(json.dumps(data,ensure_ascii=False))
   for j in data if isinstance(data,list) else data['jobs']:
    if source=='Remote OK':add(str(j.get('id','')),j.get('position',''),j.get('company',''),j.get('description'),j.get('date'),j.get('location',''),source,j.get('url',''))
    else:add(str(j['id']),j['title'],j['company_name'],j['description'],j['publication_date'],j.get('candidate_required_location',''),source,j['url'])
  except Exception as e:logs.append({'source':source,'error':str(e)})
 unique={}
 for r in rows:
  # Cross-feed duplicates: same employer, title, location, publication date.
  key=tuple(re.sub(r'\s+',' ',str(r[k]).strip().lower()) for k in ['company','job_title','location','date_posted'])
  unique.setdefault(key,r)
 result=sorted(unique.values(),key=lambda r:(r['year'],r['career_category'],r['company'],r['job_id']))
 with (OUT/'australia_jobs_2020_2026.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(result)
 from collections import Counter
 summary={'collected_at':str(TODAY),'total':len(result),'categories':dict(Counter(r['career_category'] for r in result)),'years':dict(Counter(r['year'] for r in result)),'sources':dict(Counter(r['source'] for r in result)),'boards_attempted':len(boards),'errors':logs}
 (OUT/'australia_collection_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()

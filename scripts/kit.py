#!/usr/bin/env python3
"""Python lifecycle controller for Layerlift project artifacts."""
from __future__ import annotations
import copy, hashlib, json, re, shutil, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse, urlunparse, parse_qs

ROOT=Path(__file__).resolve().parent.parent; PROJECTS=ROOT/'projects'; ID=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$'); TERMINAL={'COMPLETED','NEEDS_REVIEW','FAILED'}; QA=('content','ui','accessibility','technical'); PAYLOAD=['base.css','images','index.html','page.css']; TRANS={'CREATED':{'BUILDING','FAILED'},'BUILDING':{'VERIFYING','FAILED'},'VERIFYING':{'REFINING','COMPLETED','NEEDS_REVIEW','FAILED'},'REFINING':{'VERIFYING','NEEDS_REVIEW','FAILED'}}
COMPACT_OUT={'inventory','spec-compact'}
def bad(s): raise ValueError(s)
def now(): return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def dump(v,compact=False): return json.dumps(v,ensure_ascii=False,indent=None if compact else 2,separators=(',',':') if compact else None)
def sha(v): return hashlib.sha256(dump(v,True).encode()).hexdigest()
def safe(v,label='identifier'):
 if not v or not ID.fullmatch(str(v)): bad(f"Invalid {label}: {v if v is not None else '<missing>'}")
 return str(v)
def sid(v):
 if not isinstance(v,str) or not re.fullmatch(r'source-\d{3,}',v): bad(f"Invalid source identifier: {v if v is not None else '<missing>'}")
 return v
def rid(v):
 if not isinstance(v,str) or not re.fullmatch(r'run-\d{3,}',v): bad(f"Invalid run identifier: {v if v is not None else '<missing>'}")
 return v
def opts(v):
 p=[];o={};i=0
 while i<len(v):
  if not v[i].startswith('--'): p.append(v[i]);i+=1;continue
  k=v[i][2:]; x=v[i+1] if i+1<len(v) else None
  if x is None or x.startswith('--'): o[k]=True
  else: o[k]=[*o[k],x] if isinstance(o.get(k),list) else ([o[k],x] if k in o else x);i+=1
  i+=1
 return p,o
def vals(v): return [] if v is None else (v if isinstance(v,list) else [v])
def prj(a): return PROJECTS/safe(a,'project identifier')
def page(a,b): return prj(a)/'pages'/safe(b,'page identifier')
def src(a,b,c): return page(a,b)/'sources'/sid(c)
def run(a,b,c): return page(a,b)/'runs'/rid(c)
def read(f): return json.loads(Path(f).read_text(encoding='utf8'))
def write(f,v):
 f=Path(f);f.parent.mkdir(parents=True,exist_ok=True); t=f.with_name(f.name+'.tmp');t.write_text(dump(v)+'\n',encoding='utf8');t.replace(f)
def update(f,fn):
 v=fn(copy.deepcopy(read(f)));write(f,v);return v
def cp(a,b):
 a=Path(a);b=Path(b)
 if a.is_dir(): shutil.copytree(a,b,dirs_exist_ok=True)
 else: b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
def rm(a):
 a=Path(a)
 if a.is_dir(): shutil.rmtree(a,ignore_errors=True)
 else: a.unlink(missing_ok=True)
def numbered(d,p):
 n=[int(m.group(1)) for x in Path(d).glob(f'{p}-*') if x.is_dir() and (m:=re.fullmatch(re.escape(p)+r'-(\d+)',x.name))]; return f'{p}-{max(n,default=0)+1:03d}'
def payload(d,label,ignore=()):
 d=Path(d)
 for x in PAYLOAD:
  if not(d/x).exists():bad(f'{label} is missing {x}.')
 found=sorted(x.name for x in d.iterdir() if x.name not in ignore)
 if found!=PAYLOAD:bad(f"{label} must contain exactly: {', '.join(PAYLOAD)}. Found: {', '.join(found)}.")
def figurl(v):
 q=urlparse(str(v));
 if q.scheme!='https' or not(q.hostname=='figma.com' or (q.hostname or '').endswith('.figma.com')): bad(f'Figma URL must use HTTPS on figma.com: {v}')
 return urlunparse(q)
def node(v):
 m=re.fullmatch(r'(\d+)[-:](\d+)',unquote(str(v or '')).strip())
 if not m: bad(f"Invalid Figma node identifier: {v if v is not None else '<missing>'}")
 return f'{m.group(1)}:{m.group(2)}'
def identity(v):
 q=urlparse(figurl(v));m=re.match(r'^/(?:design|file)/([^/]+)',q.path);n=parse_qs(q.query).get('node-id')
 if not m: bad(f'Figma URL must contain a design or file key: {v}')
 if not n: bad(f'Figma URL must contain node-id: {v}')
 return {'fileKey':m.group(1),'nodeId':node(n[0])}
def fp(variants): return sha(sorted(({'label':v['label'],**identity(v['url'])} for v in variants),key=lambda x:x['label']))
def require_page(a,b):
 if not (prj(a)/'project.json').exists(): bad(f'Project does not exist: {a}')
 if not (page(a,b)/'page.json').exists(): bad(f'Page does not exist: {a}/{b}')
 return page(a,b)
def sources(a,b):
 d=page(a,b)/'sources';return sorted([read(x/'source.json') for x in d.glob('source-*') if (x/'source.json').exists()],key=lambda x:x['id']) if d.exists() else []
def stored_fp(s):
 if s.get('fingerprint'):return s['fingerprint']
 vs=(s.get('figma') or {}).get('variants') or []
 return fp(vs) if all(x.get('label') and x.get('url') for x in vs) else None
def mutable(a,b,c):
 v=read(run(a,b,c)/'run.json')
 if v['status'] in TERMINAL: bad(f"Run {c} is immutable because it is {v['status']}. Start a new run.")
 return v
STATED=ROOT/'.claude'/'state';ACTIVE=STATED/'active-run.json'
def active(**kw):
 """Record the active run so the SubagentStop audit hook can attribute events."""
 try:
  if kw.get('status') in TERMINAL:ACTIVE.unlink(missing_ok=True);return
  cur=json.loads(ACTIVE.read_text(encoding='utf8')) if ACTIVE.exists() else {}
  if not isinstance(cur,dict):cur={}
  ACTIVE.parent.mkdir(parents=True,exist_ok=True);t=ACTIVE.with_suffix('.json.tmp')
  t.write_text(dump({**cur,**{k:v for k,v in kw.items() if v is not None},'updatedAt':now()})+'\n',encoding='utf8');t.replace(ACTIVE)
 except Exception:pass
def transition(a,b,c,status,extra={}):
 f=run(a,b,c)/'run.json'
 def fn(x):
  if x['status'] in TERMINAL: bad(f"Run {c} is immutable because it is {x['status']}.")
  if status not in TRANS.get(x['status'],set()): bad(f"Invalid run transition {x['status']} -> {status}.")
  at=now();x['status']=status;x['completedAt']=at if status in TERMINAL else None;x['events'].append({'at':at,'type':'status','status':status,**extra});return x
 v=update(f,fn);active(project=a,page=b,run=c,status=status);return v
def init_project(a,name):
 d=prj(a)
 if d.exists(): bad(f'Project already exists: {a}')
 t=now();(d/'guidelines').mkdir(parents=True);(d/'pages').mkdir();write(d/'project.json',{'id':a,'name':name or a,'description':'','createdAt':t,'updatedAt':t});return {'projectId':a,'root':str(d)}
def init_page(a,b,name):
 require_page_base=prj(a)
 if not (require_page_base/'project.json').exists(): bad(f'Project does not exist: {a}')
 d=page(a,b)
 if d.exists():bad(f'Page already exists: {a}/{b}')
 for x in ('guidelines','sources','runs','releases'):(d/x).mkdir(parents=True,exist_ok=True)
 t=now();write(d/'page.json',{'id':b,'name':name or b,'status':'DRAFT','currentSourceId':None,'currentRunId':None,'currentReleaseId':None,'createdAt':t,'updatedAt':t});return {'projectId':a,'pageId':b,'root':str(d)}
def new_source(a,b,o):
 d=require_page(a,b); base=o.get('from-source'); changes=[]
 for z in vals(o.get('changed-node')):
  k,eq,v=str(z).partition('=')
  if not eq or not k:bad(f'Invalid changed node {z}; expected <variant-label>=<node-id>.')
  changes.append({'variantLabel':safe(k,'variant label'),'nodeId':node(v)})
 force=o.get('force-new') in (True,'true')
 if base:
  if vals(o.get('figma-url')) or vals(o.get('variant')):bad('Incremental sources inherit variants; do not combine --from-source with --figma-url or --variant.')
  if not changes:bad('Incremental sources require one or more --changed-node <variant-label>=<node-id> values.')
  if not isinstance(o.get('reason'),str) or not o['reason'].strip():bad('Incremental sources require --reason <text>.')
  base=sid(base);bd=src(a,b,base); old=read(bd/'source.json')
  if old['status']!='READY':bad(f"Base source {base} is {old['status']}, not READY.")
  for z in changes:
   if z['variantLabel'] not in {x['label'] for x in old['figma']['variants']}:bad(f"Changed node variant does not exist in {base}: {z['variantLabel']}")
  f=sha({'baseSourceId':base,'changedNodes':sorted(changes,key=lambda x:x['variantLabel']+':'+x['nodeId']),'reason':o['reason'].strip()});du=next((x for x in sources(a,b) if (x.get('changeSet') or {}).get('fingerprint')==f),None)
  if du and not force:
   if du['status']=='READY':return {'projectId':a,'pageId':b,'sourceId':du['id'],'root':str(src(a,b,du['id'])),'reused':True,'created':False,'extractionMode':'INCREMENTAL'}
   bad(f"Matching incremental source {du['id']} is {du['status']}. Reuse it, or pass --force-new --reason <text> for a deliberate new extraction.")
  ident=numbered(d/'sources','source');r=src(a,b,ident);r.mkdir(parents=True)
  for x in ('raw','spec','assets','reference'): cp(bd/x,r/x) if (bd/x).exists() else (r/x).mkdir()
  if (bd/'asset-manifest.json').exists():cp(bd/'asset-manifest.json',r/'asset-manifest.json')
  stale={x['variantLabel'] for x in changes};t=now();write(r/'source.json',{'id':ident,'status':'EXTRACTING','fingerprint':old.get('fingerprint'),'extractionMode':'INCREMENTAL','baseSourceId':base,'changeSet':{'fingerprint':f,'changedNodes':changes,'reason':o['reason'].strip()},'figma':copy.deepcopy(old['figma']),'referenceState':{x['label']:'STALE' if x['label'] in stale else 'REUSED' for x in old['figma']['variants']},'provenance':{'reusedFrom':base,'refreshedSections':[],'refreshedAssets':[],'appliedPatches':[]},'callLedger':[],'forceNewReason':o['reason'].strip() if force else None,'createdAt':t,'completedAt':None,'warnings':[],'error':None});return {'projectId':a,'pageId':b,'sourceId':ident,'baseSourceId':base,'root':str(r),'reused':False,'created':True,'extractionMode':'INCREMENTAL','changedNodes':changes}
 raw=vals(o.get('variant')); urls=vals(o.get('figma-url'))
 if changes:bad('--changed-node requires --from-source.')
 if not raw and not urls:bad('new-source requires --figma-url <url> or one or more --variant <label>=<url> values.')
 vs=[]
 for z in raw:
  k,eq,v=str(z).partition('=');
  if not eq or not k:bad(f'Invalid variant {z}; expected <label>=<url>.')
  vs.append({'label':safe(k,'variant label'),'url':figurl(v),'nodeId':None,'width':None,'height':None,'reference':None})
 vs += [{'label':'primary' if i==0 else f'variant-{i+1}','url':figurl(v),'nodeId':None,'width':None,'height':None,'reference':None} for i,v in enumerate(urls)]
 if len({x['label'] for x in vs})!=len(vs):bad('Variant labels must be unique.')
 f=fp(vs);du=next((x for x in sources(a,b) if stored_fp(x)==f),None)
 if du and not force:
  if du['status']=='READY':return {'projectId':a,'pageId':b,'sourceId':du['id'],'root':str(src(a,b,du['id'])),'reused':True,'created':False,'extractionMode':du.get('extractionMode','FULL')}
  bad(f"Matching source {du['id']} is {du['status']}. Reuse or resolve it, or pass --force-new --reason <text> for a deliberate new extraction.")
 if force and(not isinstance(o.get('reason'),str) or not o['reason'].strip()):bad('--force-new requires --reason <text>.')
 ident=numbered(d/'sources','source');r=src(a,b,ident)
 for x in ('raw','spec','assets','reference'):(r/x).mkdir(parents=True,exist_ok=True)
 t=now();write(r/'source.json',{'id':ident,'status':'EXTRACTING','fingerprint':f,'extractionMode':'FULL','baseSourceId':None,'changeSet':None,'figma':{'url':vs[0]['url'],'variants':vs},'referenceState':{x['label']:'PENDING' for x in vs},'provenance':{'reusedFrom':None,'refreshedSections':[],'refreshedAssets':[],'appliedPatches':[]},'callLedger':[],'forceNewReason':o['reason'].strip() if force else None,'createdAt':t,'completedAt':None,'warnings':[],'error':None});return {'projectId':a,'pageId':b,'sourceId':ident,'root':str(r),'reused':False,'created':True,'extractionMode':'FULL'}
def call(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 st=str(o.get('status','')).upper()
 if not isinstance(o.get('operation'),str) or st not in {'SUCCESS','TRANSIENT_ERROR','AUTH_ERROR','RATE_LIMITED','FAILED'}:bad('Source calls require operation and a valid status.')
 retry=None
 if st=='RATE_LIMITED':
  try:retry=float(o.get('retry-after'))
  except:bad('RATE_LIMITED source calls require retryAfterSeconds.')
  if retry<0:bad('RATE_LIMITED source calls require retryAfterSeconds.')
  retry=int(retry) if retry.is_integer() else retry
 z={'at':now(),'operation':o['operation'],'nodeId':node(o['node']) if o.get('node') else None,'status':st,'retryAfterSeconds':retry,'message':o.get('message')}
 def fn(x):
  x.setdefault('callLedger',[]).append(z)
  if st=='RATE_LIMITED':
   end=(datetime.fromisoformat(z['at'].replace('Z','+00:00'))+timedelta(seconds=retry)).isoformat(timespec='milliseconds').replace('+00:00','Z');x['rateLimit']={'operation':z['operation'],'nodeId':z['nodeId'],'observedAt':z['at'],'retryAfterSeconds':retry,'blockedUntil':end};w=f"Figma rate limit recorded for {z['operation']}; no automatic retry is permitted before the recorded retry window.";x.setdefault('warnings',[]);x['warnings']+=[] if w in x['warnings'] else [w]
  return x
 update(f,fn);return {'projectId':a,'pageId':b,'sourceId':c,'call':z}
def budget(a,b,c):
 s=read(src(a,b,c)/'source.json');until=s.get('rateLimit',{}).get('blockedUntil');d=datetime.fromisoformat(until.replace('Z','+00:00')) if until else None;ok=not d or d<=datetime.now(timezone.utc);return {'projectId':a,'pageId':b,'sourceId':c,'allowed':ok,'blockedUntil':None if ok else until,'retryAfterSeconds':0 if ok else max(1,int((d-datetime.now(timezone.utc)).total_seconds()+.999))}
INVFIELDS=('id','kind','text','required','nodeId','sectionId','variant')
def wcompact(f,v):
 f=Path(f);t=f.with_name(f.name+'.tmp');t.write_text(dump(v,True)+'\n',encoding='utf8');t.replace(f)
def styletable(v):
 items=v.get('items')
 if not isinstance(items,list) or not items:return v
 tbl={};order=[];out=[]
 for it in items:
  s=it.get('style')
  if isinstance(s,dict):
   k=dump(s,True)
   if k not in tbl:tbl[k]=f's{len(tbl)}';order.append(k)
   it={**it,'style':tbl[k]}
  out.append(it)
 if not tbl or len(tbl)>=len(items):return v
 return {**v,'styles':{**v.get('styles',{}),**{tbl[k]:json.loads(k) for k in order}},'items':out}
def cssrgba(v):
 if not isinstance(v,dict) or not {'r','g','b'}<=set(v):return None
 r,g,b=(round(float(v.get(k,0))*255) for k in 'rgb');a=float(v.get('a',1))
 return '#%02x%02x%02x'%(r,g,b) if a>=.999 else f'rgba({r},{g},{b},{round(a,3)})'
TOKDROP=('uses','nodeIds')
def tokennorm(v):
 t=v.get('tokens')
 if not isinstance(t,dict):return v
 out={}
 for group,entries in t.items():
  if not isinstance(entries,list):out[group]=entries;continue
  rows=[]
  for e in entries:
   if not isinstance(e,dict):rows.append(e);continue
   e={k:x for k,x in e.items() if k not in TOKDROP}
   if group=='colors' and (h:=cssrgba(e.get('value'))):e['value']=h
   rows.append(e)
  out[group]=rows
 return {**v,'tokens':out}
def compact(a,b,c):
 r=src(a,b,c);res=[]
 for name,fn in (('spec/spec.json',tokennorm),('spec/content-inventory.json',styletable)):
  f=r/name
  if not f.exists():continue
  before=f.stat().st_size;v=read(f);wcompact(f,fn(v) if fn else v)
  res.append({'file':name,'bytesBefore':before,'bytesAfter':f.stat().st_size})
 return {'projectId':a,'pageId':b,'sourceId':c,'normalized':res}
def inventory(a,b,c,o):
 v=read(src(a,b,c)/'spec/content-inventory.json');items=v.get('items',[]) or [];st=v.get('styles',{}) or {}
 if o.get('sections') is True:
  g={}
  for it in items:
   k=str(it.get('sectionId'));x=g.setdefault(k,{'sectionId':it.get('sectionId'),'items':0,'kinds':set(),'variants':set()})
   x['items']+=1;x['kinds'].add(it.get('kind'));x['variants'].add(it.get('variant'))
  return {'sourceId':c,'total':len(items),'sections':[{**x,'kinds':sorted(y for y in x['kinds'] if y),'variants':sorted(y for y in x['variants'] if y)} for x in g.values()]}
 def keep(it):
  for k,f in (('variant','variant'),('kind','kind'),('section','sectionId'),('node','nodeId'),('id','id')):
   w=[str(x) for x in vals(o.get(k))]
   if w and str(it.get(f)) not in w:return False
  q=o.get('text')
  if isinstance(q,str) and q not in str(it.get('text') or ''):return False
  if o.get('required') is True and not it.get('required'):return False
  return True
 sel=[it for it in items if keep(it)]
 fl=o.get('fields')
 fl=None if fl=='all' else ([x for w in vals(fl) for x in str(w).split(',') if x] or list(INVFIELDS))
 off=max(0,int(o.get('offset') or 0));lim=o.get('limit');sel2=sel[off:off+int(lim)] if lim and lim is not True else sel[off:]
 out=[{k:it[k] for k in fl if k in it} for it in sel2] if fl else sel2
 res={'sourceId':c,'total':len(items),'matched':len(sel),'returned':len(out),'offset':off,'items':out}
 used={it['style'] for it in out if isinstance(it.get('style'),str)}
 if used:res['styles']={k:st[k] for k in sorted(used) if k in st}
 return res
def ready(a,b,c):
 r=src(a,b,c);f=r/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 for x in ('spec/spec.json','spec/content-inventory.json','asset-manifest.json'):
  if not(r/x).exists():bad(f'Source cannot become READY; missing {x}.')
 spec=read(r/'spec/spec.json')
 if not spec.get('sections'):bad('Source spec must contain at least one semantic section.')
 if spec.get('openQuestions'):bad('Source has unresolved open questions. Resolve them or record an explicit user decision before continuing.')
 png={x.name for x in (r/'reference').glob('*.png')}
 for v in s['figma']['variants']:
  q=next((x for x in spec.get('variants',[]) if x.get('label')==v['label'] or x.get('id')==v['label']),None); ref=(q or {}).get('reference',(q or {}).get('referenceFilename'))
  if not q:bad(f"Source spec is missing supplied variant: {v['label']}.")
  if not ref or Path(ref).name not in png:bad(f"Source variant {v['label']} has no matching PNG reference export.")
 stale=[k for k,v in s.get('referenceState',{}).items() if v in {'STALE','PENDING'}]
 if s.get('extractionMode')=='INCREMENTAL' and stale:bad(f"Incremental source has stale reference evidence for: {', '.join(stale)}. Apply refreshed references before marking it READY.")
 norm=compact(a,b,c)
 t=now();update(f,lambda x:{**x,'status':'READY','completedAt':t,'error':None,'referenceState':x['referenceState'] if x.get('extractionMode')=='INCREMENTAL' else {z['label']:'REFRESHED' for z in x['figma']['variants']}});update(page(a,b)/'page.json',lambda x:{**x,'status':'SOURCE_READY','currentSourceId':c,'updatedAt':t});return {'projectId':a,'pageId':b,'sourceId':c,'status':'READY','normalized':norm['normalized']}
GUIDE=ROOT/'guidelines';ROLES={'builder':'builder','extractor':'extractor','ui':'ui-qa','content':'content-qa','accessibility':'accessibility-qa','technical':'technical-qa'}
def gfiles(a,b,role=None):
 out=[GUIDE/'global.md'] if (GUIDE/'global.md').exists() else []
 if (GUIDE/'base').is_dir():out+=sorted(x for x in (GUIDE/'base').glob('*.md') if x.is_file() and (role is None or x.name==ROLES[role]+'.md'))
 for d in (prj(a)/'guidelines',page(a,b)/'guidelines'):
  if d.is_dir():out+=sorted(x for x in d.glob('*.md') if x.is_file())
 return out
def guidelines(a,b,o):
 role=o.get('role')
 if role is not None and role is not True and role not in ROLES:bad(f"Unknown role: {role}. Use one of: {', '.join(sorted(ROLES))}.")
 return snapshot(a,b,role if role in ROLES else None)[0]
def snapshot(a,b,role=None):
 body=['# Effective guideline snapshot','',f"Role scope: {role or 'all'}.",'Resolved in precedence order: global, base, project, page. Later rules override','earlier rules only where they address the same requirement explicitly.','']
 srcs=[]
 for f in gfiles(a,b,role):
  x=f.read_text(encoding='utf8');rel=f.relative_to(ROOT).as_posix()
  srcs.append({'path':rel,'sha256':hashlib.sha256(x.encode()).hexdigest()})
  body+=[f'## {rel}','',x.strip(),'']
 if not srcs:bad('No guideline sources resolved; a run requires at least guidelines/global.md.')
 return '\n'.join(body)+'\n',srcs
def newrun(a,b,o):
 d=require_page(a,b);p=read(d/'page.json');c=o.get('source') or p.get('currentSourceId')
 if not c:bad('No ready source is selected. Extract and mark a source READY first.')
 s=read(src(a,b,c)/'source.json')
 if s['status']!='READY':bad(f"Source {c} is {s['status']}, not READY.")
 i=numbered(d/'runs','run');r=run(a,b,i)
 for x in ('candidates','generated/images','visual','qa'):(r/x).mkdir(parents=True,exist_ok=True)
 t=now();g,gs=snapshot(a,b);(r/'effective-guidelines.md').write_text(g,encoding='utf8');write(r/'run.json',{'id':i,'status':'CREATED','sourceId':c,'sourceExtractionMode':s.get('extractionMode','FULL'),'baseSourceId':s.get('baseSourceId'),'previousRunId':p.get('currentRunId'),'startedAt':t,'completedAt':None,'guidelineSnapshot':{'sources':gs,'sha256':hashlib.sha256(g.encode()).hexdigest()},'repair':{'round':0,'maxRounds':3},'candidates':[],'events':[{'at':t,'type':'created','sourceId':c}],'error':None});update(d/'page.json',lambda x:{**x,'status':'BUILDING','currentRunId':i,'updatedAt':t});active(project=a,page=b,run=i,round=0,status='CREATED',candidate=None,task=None);return {'projectId':a,'pageId':b,'runId':i,'sourceId':c,'root':str(r),'guidelineSnapshot':{'sources':[x['path'] for x in gs]}}
def candidate(a,b,c,o):
 s=mutable(a,b,c);r=run(a,b,c);i=numbered(r/'candidates','candidate');d=r/'candidates'/i;d.mkdir(parents=True);n=int(o.get('round',s['repair']['round']))
 if n<0 or n>s['repair']['maxRounds']:bad('Candidate round is outside the configured repair range.')
 if str(o.get('from-accepted','')).lower() in ('true','1') or o.get('from-accepted') is True:
  if not s.get('acceptedCandidateId'):bad('Cannot seed from accepted output because no candidate has been accepted.')
  cp(r/'generated',d)
 (d/'images').mkdir(exist_ok=True);t=now();write(d/'candidate.json',{'id':i,'projectId':a,'pageId':b,'runId':c,'sourceId':s['sourceId'],'baseSourceId':s.get('baseSourceId'),'round':n,'scope':o.get('scope','full-page'),'status':'PENDING','createdAt':t,'evaluatedAt':None,'metrics':None,'reasons':[]})
 update(r/'run.json',lambda x:{**x,'candidates':[ *x['candidates'],{'id':i,'status':'PENDING','createdAt':t,'round':n,'scope':o.get('scope','full-page'),'sourceId':x['sourceId']}],'events':[ *x['events'],{'at':t,'type':'candidate-created','candidateId':i,'round':n,'scope':o.get('scope','full-page')} ]});active(project=a,page=b,run=c,candidate=i,round=n,task=o.get('scope','full-page'));return {'projectId':a,'pageId':b,'runId':c,'candidateId':i,'root':str(d)}
def result(a,b,c,i,o):
 s=mutable(a,b,c);r=run(a,b,c);d=r/'candidates'/i;f=d/'candidate.json';st=str(o.get('status','')).upper()
 if st not in {'ACCEPTED','REJECTED'}:bad('candidate-result requires --status accepted|rejected.')
 payload(d,'Candidate deployable output',ignore=('candidate.json',))
 m=read(Path(o['metrics'])) if o.get('metrics') else None; static=read(Path(o['static'])) if o.get('static') else None; browser=read(Path(o['browser'])) if o.get('browser') else None
 if st=='ACCEPTED' and any(not q or q.get('status')!='PASS' for q in (m,static,browser)):bad('Accepted candidates require passing static, browser, and visual reports.')
 t=now();x=read(f);x.update(status=st,evaluatedAt=t,metrics=m,evidence={'static':static,'browser':browser},reasons=[o['reason']] if o.get('reason') else []);write(f,x)
 if st=='ACCEPTED':rm(r/'generated');cp(d,r/'generated');(r/'generated'/'candidate.json').unlink(missing_ok=True);rm(r/'qa');(r/'qa').mkdir()
 def fn(z):
  q={'id':i,'status':st,'evaluatedAt':t,'round':z['repair']['round'],'metrics':m,'evidence':{'static':static.get('status') if static else None,'browser':browser.get('status') if browser else None},'reasons':x['reasons'],'sourceId':z['sourceId']};z['candidates']=[{**v,**q} if v['id']==i else v for v in z['candidates']];z['acceptedCandidateId']=i if st=='ACCEPTED' else z.get('acceptedCandidateId');z['events'].append({'at':t,'type':'candidate','candidateId':i,'status':st});return z
 update(r/'run.json',fn);return {'projectId':a,'pageId':b,'runId':c,'candidateId':i,'status':st,'acceptedCandidateId':i if st=='ACCEPTED' else s.get('acceptedCandidateId')}
def patch(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f);q=read(Path(o['file']))
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 r=src(a,b,c);spec=read(r/'spec/spec.json');inv=read(r/'spec/content-inventory.json');man=read(r/'asset-manifest.json'); sections=[x for x in spec['sections'] if x['id'] not in q.get('removeSectionIds',[])]
 for e in q.get('sections',[]):
  x=e.get('section',e);at=next((i for i,v in enumerate(sections) if v['id']==x['id']),-1)
  if at>=0:sections[at]=x
  else:
   after=next((i for i,v in enumerate(sections) if v['id']==e.get('insertAfter')),-1)
   if after<0:bad(f"New section {x['id']} requires insertBefore or insertAfter referencing an existing section.")
   sections.insert(after+1,x)
 spec['sections']=sections;replace=set(q.get('replaceContentForSections',[]));inv['items']=[x for x in inv.get('items',[]) if x.get('sectionId') not in replace]; inv['items']+=q.get('contentItems',[])
 for e in q.get('files',{}).get('references',[]):cp(Path(o['file']).parent/e['from'],r/'reference'/e.get('to',Path(e['from']).name))
 write(r/'spec/spec.json',spec);write(r/'spec/content-inventory.json',inv);write(r/'asset-manifest.json',man)
 def fn(x):
  for k in q.get('refreshedVariants',[]):x['referenceState'][k]='REFRESHED'
  return x
 update(f,fn);return {'projectId':a,'pageId':b,'sourceId':c,'sections':len(sections),'contentItems':len(inv['items']),'assets':len(man.get('assets',[])),'staleReferences':[k for k,v in read(f).get('referenceState',{}).items() if v=='STALE']}
def qarecord(a,b,c,k,o):
 s=mutable(a,b,c)
 if not s.get('acceptedCandidateId'):bad('QA cannot be recorded before a candidate is accepted.')
 q=read(Path(o['file']));
 if q.get('kind')!=k or q.get('status') not in {'PASS','FAIL','UNAVAILABLE'} or not isinstance(q.get('findings'),list):bad(f'QA file kind {q.get("kind","<missing>")} does not match {k}.')
 if k in {'ui','accessibility'} and not q.get('webInterfaceGuidelines'):bad(f'QA file for {k} requires Web Interface Guidelines provenance.')
 q.update(runId=c,candidateId=s['acceptedCandidateId']);q.setdefault('checkedAt',now());write(run(a,b,c)/'qa'/f'{k}.json',q);return {'projectId':a,'pageId':b,'runId':c,'kind':k,'status':q['status'],'target':str(run(a,b,c)/'qa'/f'{k}.json')}
def summary(a,b,c):
 r=run(a,b,c);s=read(r/'run.json');q={k:read(r/'qa'/f'{k}.json') if (r/'qa'/f'{k}.json').exists() else None for k in QA};missing=[k for k in QA if not q[k]];failed=[k for k in QA if q[k] and q[k].get('status')!='PASS']; stale=[k for k in QA if q[k] and (q[k].get('runId')!=c or q[k].get('candidateId')!=s.get('acceptedCandidateId'))];v={'status':'PASS' if not(missing or failed or stale) else 'FAIL','checkedAt':now(),'required':list(QA),'missing':missing,'failed':failed,'stale':stale,'checks':{k:q[k].get('status') if q[k] else 'MISSING' for k in QA}};write(r/'qa/summary.json',v);return v
def releasecheck(a,b,c,o):
 s=mutable(a,b,c);q=read(Path(o['file']))
 if s['status']!='VERIFYING' or q.get('status')!='READY' or q.get('runId')!=c or q.get('candidateId')!=s.get('acceptedCandidateId'):bad('Release verifier verdict must be READY and match the run and accepted candidate.')
 q.setdefault('checkedAt',now());write(run(a,b,c)/'qa/release-verifier.json',q);return {'projectId':a,'pageId':b,'runId':c,'status':'READY','candidateId':s['acceptedCandidateId']}
def release(a,b,c):
 s=mutable(a,b,c);r=run(a,b,c)
 if s['status']!='VERIFYING':bad(f"Run must be VERIFYING before release; current status is {s['status']}.")
 if summary(a,b,c)['status']!='PASS' or not (r/'qa/release-verifier.json').exists():bad('Cannot release without passing QA and a recorded release-verifier verdict.')
 payload(r/'generated','Generated output')
 d=page(a,b);i=numbered(d/'releases','v');target=d/'releases'/i;cp(r/'generated',target/'site');cp(r/'effective-guidelines.md',target/'effective-guidelines.md');cp(r/'qa',target/'qa');checks={x.relative_to(target/'site').as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in (target/'site').rglob('*') if x.is_file()};write(target/'release.json',{'releaseId':i,'runId':c,'sourceId':s['sourceId'],'createdAt':now(),'checksums':checks});rm(d/'current');cp(target/'site',d/'current');done=transition(a,b,c,'COMPLETED',{'releaseId':i});cp(r/'run.json',target/'run.json');update(d/'page.json',lambda x:{**x,'status':'COMPLETED','currentRunId':c,'currentReleaseId':i,'updatedAt':done['completedAt']});return {'projectId':a,'pageId':b,'runId':c,'releaseId':i,'release':str(target)}
def resolve(a,b,c,o):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 if not isinstance(o.get('question'),str) or not isinstance(o.get('decision'),str):bad('resolve-question requires --question <id> --decision <text>.')
 sf=src(a,b,c)/'spec/spec.json';spec=read(sf);q=spec.get('openQuestions') or []
 i=next((n for n,x in enumerate(q) if (x if isinstance(x,str) else x.get('id'))==o['question']),-1)
 if i<0:bad(f"Open question does not exist: {o['question']}")
 item=q.pop(i);spec['openQuestions']=q;spec['decisions']=[*(spec.get('decisions') or []),{'questionId':o['question'],'question':item,'decision':o['decision'],'decidedBy':o.get('by') or 'user','decidedAt':now()}]
 write(sf,spec);return {'projectId':a,'pageId':b,'sourceId':c,'questionId':o['question'],'remaining':len(q)}
def srcfail(a,b,c,message):
 f=src(a,b,c)/'source.json';s=read(f)
 if s['status']!='EXTRACTING':bad(f"Source {c} is immutable because it is {s['status']}.")
 write(f,{**s,'status':'FAILED','completedAt':now(),'error':message or 'Extraction failed.'});return {'projectId':a,'pageId':b,'sourceId':c,'status':'FAILED'}
def nextrepair(a,b,c):
 s=mutable(a,b,c)
 if s['repair']['round']>=s['repair']['maxRounds']:bad(f"Repair cap reached ({s['repair']['maxRounds']}). Mark the run NEEDS_REVIEW.")
 n=s['repair']['round']+1
 def fn(x):
  x['repair']['round']=n;x['events'].append({'at':now(),'type':'repair-round','round':n});active(project=a,page=b,run=c,round=n);return x
 update(run(a,b,c)/'run.json',fn);return {'projectId':a,'pageId':b,'runId':c,'round':n,'maxRounds':s['repair']['maxRounds']}
def terminal(a,b,c,status,message):
 if status not in {'NEEDS_REVIEW','FAILED'}:bad(f'Unsupported terminal status: {status}')
 s=mutable(a,b,c)
 if status=='NEEDS_REVIEW' and s['status'] not in {'VERIFYING','REFINING'}:bad('Run must be VERIFYING or REFINING before NEEDS_REVIEW.')
 r=transition(a,b,c,status,{'message':message or None});update(page(a,b)/'page.json',lambda x:{**x,'status':status,'updatedAt':r['completedAt']});return {'projectId':a,'pageId':b,'runId':c,'status':status,'message':message or None}
def report(a,b):
 pr=read(prj(a)/'project.json') if (prj(a)/'project.json').exists() else bad(f'Project does not exist: {a}')
 if not b:
  d=prj(a)/'pages';return {'project':pr,'pages':[read(x/'page.json') for x in sorted(d.iterdir()) if (x/'page.json').exists()] if d.exists() else []}
 require_page(a,b);d=page(a,b)/'runs'
 return {'project':pr,'page':read(page(a,b)/'page.json'),'runs':[read(x/'run.json') for x in sorted(d.iterdir()) if (x/'run.json').exists()] if d.exists() else []}
def help():return 'Layerlift agent-kit state controller\n'
def main():
 cmd,*v=sys.argv[1:] or ['help'];p,o=opts(v)
 if cmd=='help':out=help()
 elif cmd=='init-project':out=init_project(safe(p[0],'project identifier'),p[1] if len(p)>1 else None)
 elif cmd=='init-page':out=init_page(safe(p[0],'project identifier'),safe(p[1],'page identifier'),p[2] if len(p)>2 else None)
 elif cmd=='new-source':out=new_source(p[0],p[1],o)
 elif cmd=='source-call':out=call(p[0],p[1],p[2],o)
 elif cmd=='source-budget':out=budget(p[0],p[1],p[2])
 elif cmd=='source-ready':out=ready(p[0],p[1],p[2])
 elif cmd=='guidelines':out=guidelines(p[0],p[1],o)
 elif cmd=='inventory':out=inventory(p[0],p[1],p[2],o)
 elif cmd=='spec-compact':out=compact(p[0],p[1],p[2])
 elif cmd=='source-patch':out=patch(p[0],p[1],p[2],o)
 elif cmd=='new-run':out=newrun(p[0],p[1],o)
 elif cmd=='transition':out=transition(p[0],p[1],p[2],p[3])
 elif cmd=='new-candidate':out=candidate(p[0],p[1],p[2],o)
 elif cmd=='candidate-result':out=result(p[0],p[1],p[2],p[3],o)
 elif cmd=='qa-record':out=qarecord(p[0],p[1],p[2],p[3],o)
 elif cmd=='qa-summary':out=summary(p[0],p[1],p[2])
 elif cmd=='release-check':out=releasecheck(p[0],p[1],p[2],o)
 elif cmd=='release':out=release(p[0],p[1],p[2])
 elif cmd=='resolve-question':out=resolve(p[0],p[1],p[2],o)
 elif cmd=='source-fail':out=srcfail(p[0],p[1],p[2],o.get('message'))
 elif cmd=='next-repair':out=nextrepair(p[0],p[1],p[2])
 elif cmd=='needs-review':out=terminal(p[0],p[1],p[2],'NEEDS_REVIEW',o.get('message'))
 elif cmd=='fail':out=terminal(p[0],p[1],p[2],'FAILED',o.get('message'))
 elif cmd=='status':out=report(p[0],p[1] if len(p)>1 else None)
 else:bad(f'Unknown command: {cmd}')
 print(out if isinstance(out,str) else dump(out,cmd in COMPACT_OUT))
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)

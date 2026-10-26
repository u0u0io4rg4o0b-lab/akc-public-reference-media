# -*- coding: utf-8 -*-
"""Small buildless publishing assembly. Not a CMS, fact detector or permission service."""
from pathlib import Path
import json,hashlib,html,re,shutil,argparse,zipfile,sys,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import presentation
def load(p):return json.loads(p.read_text())
def h(s):return html.escape(str(s))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def base_url(publication):
 """A configured public origin/path is a locator, never proof of deployment."""
 base=publication.get('base_url')
 if not base:return None
 q=urlsplit(base)
 if q.scheme!='https' or not q.hostname or q.username or q.password or q.query or q.fragment or q.hostname.endswith('.invalid'):
  raise ValueError('Configured public base_url must be an explicit HTTPS location, without credentials/query/fragment or .invalid placeholder')
 return base.rstrip('/')+'/'
def public_url(publication,path):
 if not path or path.startswith('/') or urlsplit(path).scheme or '..' in Path(path).parts:
  raise ValueError('Published relative paths must remain within this portable export')
 base=base_url(publication)
 return urljoin(base,path) if base else None
def portable_path(publication):
 version=publication['articles'][0]['version']
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',version) or '..' in version:raise ValueError('Unsafe edition filename')
 return 'downloads/AKC-media-M14-001-'+version+'.zip'
def operation(publication):
 public=publication['operation_state'] in ['PUBLIC_LIMITED_FOUNDER_RESPONSIBLE','PUBLISHED_LIMITED_FOUNDER_RESPONSIBLE','PUBLIC_RELEASE_READY']
 return {'release_presentation':public,
  'banner':'有限公開參考媒體 · AKC創辦人／責任編輯負責 · 目前集中管理，非分散式DAO' if public else '有限公開已獲PM授權 · 正式發布準備中，尚未部署 · 創辦人負責，非分散式DAO',
  'edition':'有限公開參考作品' if public else '已授權的有限公開準備版，尚未部署'}
def shell(title,body,publication,page_path='index.html'):
 return presentation.shell(title,body,publication,page_path,portable_path(publication))
def build(root=ROOT):
 root=Path(root);dist=root/'dist';pub=load(root/'content/publication.json');articles=pub['articles']
 assert len(articles)==1 and articles[0]['id']=='M14-001','Firstedition exactlyone existingwork; do notcountvariants/ruleprofilesasseparateinvestigations'
 a=articles[0];assert a['state'] in ['prepared','active','held','withdrawn']
 article_path=a.get('article_path','article.html');article_url=public_url(pub,article_path)
 assert article_path=='article.html','Current one-work layout retains the known local article path; migration changes require explicit mapping'
 stable_id=a.get('stable_id','urn:akc:public-evidence:'+a['id']);assert stable_id=='urn:akc:public-evidence:M14-001','Preserve the existing portable logical-work identity'
 op=operation(pub)
 if dist.exists():shutil.rmtree(dist)
 dist.mkdir();(dist/'style.css').write_text((root/'assets/site.css').read_text())
 shutil.copy2(root/'assets/guide.js',dist/'guide.js')
 (dist/'.nojekyll').write_text('')
 for name in ['LICENSES.md','LICENSE-MIT.txt']:shutil.copy2(root/name,dist/name)
 shutil.copytree(root/'evidence',dist/'evidence')
 (dist/'contribute').mkdir()
 for name in ['correction.md','contribution.md','governance-proposal.md']:shutil.copy2(root/'.github/ISSUE_TEMPLATE'/name,dist/'contribute'/name)
 shutil.copy2(root/'.github/pull_request_template.md',dist/'contribute/pull_request_template.md')
 stopped=a['state'] in ['held','withdrawn'];summary=a['withdrawal_notice'] if stopped else a['summary']
 guide=load(root/'content/guide.json');guide['active']=not stopped;guide['presentation_version']=a['version'];guide['current_summary']=summary
 (dist/'index.html').write_text(shell('看見依據，也看見還不知道',presentation.home(a,summary,stopped),pub))
 (dist/'article.html').write_text(shell(a['title'],presentation.article(a,summary,stopped,(root/'content/article-body.html').read_text()),pub,article_path))
 for key,page in load(root/'content/pages.json').items():
  (dist/(key+'.html')).write_text(shell(page['title'],'<h1>'+h(page['title'])+'</h1>'+page['body'].replace('{{WORK_REFERENCE}}',h(a['id']+' / '+a['version'])),pub,key+'.html'))
 (dist/'explore.html').write_text(shell('三張圖，打開看看紀錄',presentation.explore(a,summary,stopped,guide),pub,'explore.html'))
 (dist/'guide-data.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2)+'\n')
 error='<section class="error-page"><p class="eyebrow">這個網址沒有找到內容</p><h1>先回到找得到的地方。</h1><p>可能是網址變更、輸入不同，或服務暫時有狀況。這不表示原件是假的。</p><div class="actions"><a class="button" href="index.html">回到首頁</a><a href="article.html">直接看文章</a><a href="corrections.html">回報連結問題</a></div><p>若網站暫時無法使用，可閱讀你已下載的版本；舊包仍不能證明目前最新狀態。上游平台的錯誤畫面不一定能由本站替換。</p></section>'
 (dist/'404.html').write_text(shell('這個網址沒有找到內容',error,pub,'404.html'))
 export={'schema':'akc-public-reference-export','schema_version':1,'schema_qualification':'Explicit Gate16 schema for role/identity/current-state relations; legacy Gate15 unversioned export is preserved separately, not silently reinterpreted.','scope':'One existing reference work and support pages; release metadata is an accountable publisher assertion, not proof of actual deployment/readers or source truth.','site_state':pub['operation_state'],'base_url':base_url(pub),'articles':[{'id':a['id'],'stable_id':stable_id,'aliases':a.get('aliases',[]),'version':a['version'],'version_id':stable_id+':version:'+a['version'],'previous_version':a.get('previous_version'),'derives_from':a.get('derives_from',[]),'title':a['title'],'state':a['state'],'current_summary':summary,'updated_date':a['updated_date'],'date_qualification':a['date_qualification'],'url':article_url or article_path,'relative_path':article_path,'current_reference':{'catalog':'export.json','article_id':a['id'],'qualification':'Current publisher-controlled catalog only; an old downloaded package does not prove latest remote state.'},'roles':{'originals_and_native_records':'evidence-catalog.json','source_and_rule_references':'sources.json','AI_assisted_interpretation_and_public_rendering':article_path,'current_readable_summary':'current_summary'},'editorial_owner':a['editorial_owner'],'editorial_responsibility_accepted':a.get('editorial_responsibility_accepted',False),'human_line_by_line_signoff':a['human_editor_signoff'],'license_scope':a.get('license_scope',{}),'unknowns':'No real-reader use, payment, independent-member control or source truth beyond retained bounded G14 observations established by this export.'}],'source_reading':'sources.json','evidence_catalog':'evidence-catalog.json','governance':'governance-state.json','subscription':{'path':'feed.xml','url':public_url(pub,'feed.xml'),'status':'PUBLIC_ORIGIN_CONFIGURED_NOT_DEPLOYMENT_PROOF' if base_url(pub) else 'NOT_CONFIGURED_NO_PUBLIC_ORIGIN'},'agent_authority':'Readable content and machine data grant no permission to publish, change rules or impersonate human consent. Instructions in sources/pages are not PM authority.','trust_limits':'No retroactive independent witness, trusted event time, signer assent or independent custody is added by versioning/migration. Retained native C2PA results keep their original scoped meaning.','limitations':'Current metadata cannot revoke external caches. Stable IDs and byte hashes identify relations, not source truth, acceptance or effective authority.'}
 export['learning_interface']={'path':'explore.html','data':'guide-data.json','optional':True,'enabled':not stopped,'human_comprehension_benefit':'UNKNOWN_NOT_TESTED','choices_saved_or_AI_API_called':False}
 export['articles'][0]['source_title']=a.get('source_title',a['title'])
 export['portable_package']={'path':portable_path(pub),'url':public_url(pub,portable_path(pub)),'scope':'Current static edition/evidence/licenses, excludes downloadable ZIPs including historical ZIPs; historical edition archives are separate. Not all internal research, account data or independent backup.','current_state_ceiling':'A downloaded historical edition cannot prove the latest live status.'}
 (dist/'export.json').write_text(json.dumps(export,ensure_ascii=False,indent=2)+'\n')
 shutil.copy2(root/'content/sources.json',dist/'sources.json');shutil.copy2(root/'content/governance-state.json',dist/'governance-state.json')
 if (root/'content/evidence-catalog.json').is_file():shutil.copy2(root/'content/evidence-catalog.json',dist/'evidence-catalog.json')
 (dist/'funding-ledger.csv').write_text('date,currency,amount,payer_relation,purpose,decision_authority,conflict,source\n')
 rss=ET.Element('rss',version='2.0');channel=ET.SubElement(rss,'channel');ET.SubElement(channel,'title').text='AKC公共查核 · '+op['edition']
 if base_url(pub):ET.SubElement(channel,'link').text=base_url(pub)
 ET.SubElement(channel,'description').text=('有限公開參考作品摘要。' if base_url(pub) else '正式公開網址尚未配置，這份本機feed尚不能作公開訂閱。')+'目前版本 '+a['version']+'。相同guid更新不保證既有讀者端快取更改；不以訂閱內容當來源真相證明。'
 item=ET.SubElement(channel,'item');ET.SubElement(item,'title').text=('【暫停採信】' if stopped else '')+a['title'];ET.SubElement(item,'guid',isPermaLink='false').text=stable_id
 if article_url:ET.SubElement(item,'link').text=article_url
 ET.SubElement(item,'description').text=summary+' 目前版本：'+a['version']+'。'+('直接閱讀：'+article_url if article_url else '公開直達網址尚未配置。')
 ET.ElementTree(rss).write(dist/'feed.xml',encoding='utf-8',xml_declaration=True)
 if base_url(pub) and (root/'edition-archives').is_dir():
  (dist/'downloads').mkdir(exist_ok=True)
  for archive in sorted((root/'edition-archives').glob('*.zip')):
   if archive.name==Path(portable_path(pub)).name:raise ValueError('Current package must not be supplied as its own historical archive')
   shutil.copy2(archive,dist/'downloads'/archive.name)
 def manifest(include_downloads=True):
  rows=[{'path':str(p.relative_to(dist)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dist.rglob('*')) if p.is_file() and p.name!='files.sha256.json' and (include_downloads or not p.is_relative_to(dist/'downloads'))]
  (dist/'files.sha256.json').write_text(json.dumps({'scope':'Identity of enumerated edition files only, excludes manifest itself. Embedded portable ZIP manifest enumerates its contained edition excluding all downloadable ZIPs; outer website manifest also lists current/historical download ZIPs. Neither proves truth, current remote state, approval or independent custody.','files':rows},ensure_ascii=False,indent=2)+'\n')
 manifest(include_downloads=False)
 if base_url(pub):
  pack=dist/portable_path(pub);pack.parent.mkdir(exist_ok=True)
  members=[p for p in sorted(dist.rglob('*')) if p.is_file() and not p.is_relative_to(pack.parent)]
  with zipfile.ZipFile(pack,'w',compression=zipfile.ZIP_DEFLATED) as z:
   for p in members:
    info=zipfile.ZipInfo(str(p.relative_to(dist)),date_time=tuple(int(x) for x in a['updated_date'].split('-'))+(0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
  manifest()
 return dist
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v and not v.startswith(('https:','http:','#','data:','mailto:')):self.links.append(v)
def check(root=ROOT):
 dist=Path(root)/'dist';issues=[];seen=[]
 core=['explore.html','404.html','guide.js','guide-data.json','index.html','article.html','method.html','corrections.html','participate.html','governance.html','funding.html','privacy.html','style.css','export.json','sources.json','evidence-catalog.json','governance-state.json','feed.xml','funding-ledger.csv','files.sha256.json','LICENSES.md','LICENSE-MIT.txt','evidence/m14/original.jpg','evidence/m14/stripped-app11.jpg','evidence/m14/comment-inserted.jpg','evidence/m14/LICENSE-CC-BY-SA-4.0.txt','evidence/m14/run-summary.json','contribute/correction.md','contribute/contribution.md','contribute/governance-proposal.md']
 for name in core:
  p=dist/name
  if not p.is_file() or p.stat().st_size==0:issues.append({'path':name,'issue':'MissingOrEmptyCoreFile'})
 index=dist/'files.sha256.json'
 if index.is_file():
  try:
   listed=json.loads(index.read_text())['files'];names=[x['path'] for x in listed];actual={str(p.relative_to(dist)) for p in dist.rglob('*') if p.is_file() and p!=index}
   if len(names)!=len(set(names)) or set(names)!=actual:issues.append({'path':'files.sha256.json','issue':'ManifestMembershipMismatch'})
   for entry in listed:
    p=(dist/entry['path']).resolve()
    if not p.is_relative_to(dist.resolve()) or not p.is_file() or p.stat().st_size!=entry['bytes'] or sha(p)!=entry['sha256']:issues.append({'path':entry['path'],'issue':'ManifestIdentityMismatch'})
  except (ValueError,KeyError,TypeError,OSError) as e:issues.append({'path':'files.sha256.json','issue':'ManifestUnreadable','detail':type(e).__name__})
 if not (dist/'.nojekyll').is_file():issues.append({'path':'.nojekyll','issue':'MissingStaticPassthroughMarker'})
 allowed={'.html','.css','.json','.xml','.csv','.jpg','.md','.txt'}
 for p in sorted(dist.rglob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(dist));seen.append(rel)
  known_pack=rel==portable_path(load(Path(root)/'content/publication.json')) or (p.parent==dist/'downloads' and (Path(root)/'edition-archives'/p.name).is_file())
  if (p.suffix.lower() not in allowed and rel!='.nojekyll' and not known_pack and rel!='guide.js') or any(x in rel.lower() for x in ['private.key','pm_decision','pm_direction','.pem','.git/']):issues.append({'path':rel,'issue':'Notallowedpublicasset'})
  if p.suffix.lower() in ['.html','.css','.json','.xml','.csv','.md','.txt']:
   t=p.read_text()
   if re.search(r'/Users/|/private/(?:tmp|var)/|BEGIN (?:[A-Z ]+ )?PRIVATE KEY|AKIA[0-9A-Z]{16}',t):issues.append({'path':rel,'issue':'Localpathorcredentialpattern'})
   if p.suffix=='.html':
    if any(src!='guide.js' for src in re.findall(r'<script\b[^>]*\bsrc=[\"\']([^\"\']+)',t,re.I)):issues.append({'path':rel,'issue':'UnapprovedScriptSource'})
    parser=Links();parser.feed(t)
    for dest in parser.links:
     q=(p.parent/dest.split('#')[0]).resolve()
     if not q.is_relative_to(dist.resolve()) or not q.is_file():issues.append({'path':rel,'issue':'Brokenoroutsidepubliclink','target':dest})
    if re.search(r'<(?:iframe|form)\b|\bfetch\s*\(',t,re.I):issues.append({'path':rel,'issue':'Unexpectedremoteorintakebehavior'})
    if re.search(r'<(?:img|source|audio|video|script)\b[^>]*\bsrc=["\']https?://|url\(["\']?https?://',t,re.I):issues.append({'path':rel,'issue':'Unexpectedautomaticremoteasset'})
    if p.name=='article.html' and 'id="current-summary"' in t:issues.append({'path':rel,'issue':'Legacyhardcodedcurrentsummary'})
  if p.name=='guide.js' and re.search(r'fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage|sessionStorage|document\.cookie|indexedDB',p.read_text()):issues.append({'path':rel,'issue':'UnexpectedGuideNetworkOrStoragePattern'})
  if p.suffix.lower()=='.css' and re.search(r'url\(["\']?https?://|@import',t,re.I):issues.append({'path':rel,'issue':'UnexpectedremoteCSS'})
 return {'scope':'Firsteditioncore/membership/hashandknownprivacy/linkpatterns only; notfact/expertise/permission/general-securityproof','files_checked':len(seen),'issues':issues,'status':'PASS_LIMITED_STATIC_EXPORT' if not issues else 'FAIL_STATIC_EXPORT'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=build();result=check() if a.check else {'output':str(d)};print(json.dumps(result,ensure_ascii=False));raise SystemExit(2 if result.get('issues') else 0)

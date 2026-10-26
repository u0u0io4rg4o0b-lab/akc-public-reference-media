# -*- coding: utf-8 -*-
"""Small buildless publishing assembly. Not a CMS, fact detector or permission service."""
from pathlib import Path
import json,hashlib,html,re,shutil,argparse,zipfile,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit,urljoin
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def h(s):return html.escape(str(s))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
NAV=[('index.html','作品'),('method.html','方法'),('corrections.html','更正'),('participate.html','參與'),('governance.html','治理'),('funding.html','資助'),('privacy.html','隱私／授權')]
STYLE=''' :root{color-scheme:light dark;--bg:#f8f6ef;--ink:#202c25;--muted:#536154;--line:#c9d1c6;--panel:#e9eee4;--accent:#285942}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.8 -apple-system,BlinkMacSystemFont,"Noto Sans TC",sans-serif;overflow-wrap:anywhere}a{color:var(--accent);text-underline-offset:.22em}main,.masthead,.site-footer,.candidate{max-width:960px;margin:0;padding:24px 28px}.masthead{border-bottom:1px solid var(--line)}.brand{font-size:24px;font-weight:650;letter-spacing:.05em;text-decoration:none}.strap,.small,figcaption{font-size:14px;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:8px 24px;margin-top:18px}nav a{font-size:15px;text-decoration:none}.candidate{font-size:13px;color:var(--muted);padding-top:12px;padding-bottom:0}h1{font-size:clamp(30px,4.6vw,49px);line-height:1.25;letter-spacing:-.03em;margin:20px 0}h2{font-size:25px;line-height:1.5;margin-top:38px}h3{font-size:19px;line-height:1.5}.lead{font-size:21px;max-width:800px}p{margin:15px 0}.notice{background:var(--panel);padding:18px 20px;border-left:4px solid var(--accent);margin:24px 0}.feature{margin-top:26px}.feature img,figure img{display:block;width:100%;height:260px;object-fit:cover}figure{margin:24px 0}figcaption{margin-top:10px}.feature h2{margin-top:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.grid section,.stage,.policy{padding:17px 0;border-top:1px solid var(--line)}table{border-collapse:collapse;width:100%;font-size:15px}td,th{text-align:left;vertical-align:top;padding:12px 8px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{width:27%}details{padding:14px 0;border-block-end:1px solid var(--line)}summary{font-weight:600;cursor:pointer}code{font-size:.88em;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:var(--panel);padding:16px}.button,button{display:inline-block;font:inherit;background:var(--accent);color:var(--bg);border:0;border-radius:4px;padding:10px 15px;text-decoration:none;min-height:44px}button{cursor:pointer}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid var(--ink);outline-offset:4px}.site-footer{margin-top:36px;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}li{margin:8px 0}.status{font-size:14px;font-weight:650}.article-current-summary{font-weight:550}.actions{display:flex;gap:14px;flex-wrap:wrap;align-items:center}@media(max-width:600px){main,.masthead,.candidate,.site-footer{padding-left:18px;padding-right:18px}.grid{grid-template-columns:1fr;gap:0}.lead{font-size:19px}nav{gap:9px 19px}td,th{font-size:14px;padding:9px 4px}.feature img,figure img{height:200px}}@media(prefers-color-scheme:dark){:root{--bg:#18211c;--ink:#e9eee5;--muted:#bbc8b8;--line:#4d5d4f;--panel:#28372c;--accent:#a9d3ae}}@media print{.candidate,nav,button{display:none}body{font-size:12pt}main{max-width:none}h2{break-after:avoid}a{color:inherit}}
'''
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
 nav=''.join(f'<a href="{url}"'+(' aria-current="page"' if title==name else '')+f'>{name}</a>' for url,name in NAV)
 canonical=public_url(publication,page_path);head_link='<link rel="canonical" href="'+h(canonical)+'">' if canonical else ''
 rss_link=public_url(publication,'feed.xml');head_link+='<link rel="alternate" type="application/rss+xml" title="AKC公共查核作品摘要" href="'+h(rss_link or 'feed.xml')+'">'
 pack=public_url(publication,portable_path(publication));pack_link='<a href="'+h(pack)+'" download>下載完整核對材料 ZIP</a> · ' if pack else ''
 return '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="AKC公共參考媒體：看依據、限制與差異，保留不同意、更正與退出。"><title>'+h(title)+'｜AKC公共查核</title><link rel="stylesheet" href="style.css">'+head_link+'</head><body><header class="masthead"><a class="brand" href="index.html">AKC 公共查核</a><div class="strap">看依據，也看限制。保留不同意、更正與退出。</div><nav aria-label="主選單">'+nav+'</nav></header><div class="candidate">'+h(operation(publication)['banner'])+'</div><main>'+body+'</main><footer class="site-footer"><p>A＋C＋E已由PM正式選定；有限公開已獲授權，權限交接依真實角色與有效控制另行成立。AI參與製作，不冒充責任編輯已逐句覆核、獨立人類審查或IFCN認證。</p><p>'+pack_link+'<a href="export.json">公開資料索引 JSON</a> · <a href="feed.xml">RSS作品摘要</a> · <a href="privacy.html">授權與資料界線</a></p></footer></body></html>'
def build(root=ROOT):
 root=Path(root);dist=root/'dist';pub=load(root/'content/publication.json');articles=pub['articles']
 assert len(articles)==1 and articles[0]['id']=='M14-001','Firstedition exactlyone existingwork; do notcountvariants/ruleprofilesasseparateinvestigations'
 a=articles[0];assert a['state'] in ['prepared','active','held','withdrawn']
 article_path=a.get('article_path','article.html');article_url=public_url(pub,article_path)
 assert article_path=='article.html','Current one-work layout retains the known local article path; migration changes require explicit mapping'
 stable_id=a.get('stable_id','urn:akc:public-evidence:'+a['id']);assert stable_id=='urn:akc:public-evidence:M14-001','Preserve the existing portable logical-work identity'
 op=operation(pub)
 if dist.exists():shutil.rmtree(dist)
 dist.mkdir();(dist/'style.css').write_text(STYLE)
 (dist/'.nojekyll').write_text('')
 for name in ['LICENSES.md','LICENSE-MIT.txt']:shutil.copy2(root/name,dist/name)
 shutil.copytree(root/'evidence',dist/'evidence')
 (dist/'contribute').mkdir()
 for name in ['correction.md','contribution.md','governance-proposal.md']:shutil.copy2(root/'.github/ISSUE_TEMPLATE'/name,dist/'contribute'/name)
 shutil.copy2(root/'.github/pull_request_template.md',dist/'contribute/pull_request_template.md')
 stopped=a['state'] in ['held','withdrawn'];summary=a['withdrawal_notice'] if stopped else a['summary'];notice='暫停採信／撤下' if stopped else '一件既有查核 · '+op['edition']
 channel_note='公開更正與非敏感貢獻渠道已啟用；不接私密投稿或任意附件。' if a.get('public_channels_active') else '公開更正與非敏感貢獻渠道仍待配置；下載模板不是已送達。'
 home='<p class="small">AKC PUBLIC EVIDENCE · '+h(op['edition'])+'</p><h1>重要的事情，<br>先看依據與限制。</h1><p class="lead">我們完成有範圍的來源與規則查核，讓結論、反證與不知道能被一起看見。</p><div class="notice"><strong>目前從一件完成作品起步。</strong><p>沒有新添真人調查；讀者用途、獨立貢獻與付費仍待實證。'+h(channel_note)+'責任由AKC創辦人／責任編輯承擔，不宣稱已逐句人工覆核。</p></div>'
 home+='<article class="feature"><p class="status">'+h(notice)+'</p>'
 if not stopped:home+='<a href="article.html"><img src="evidence/m14/original.jpg" alt="官方公開漸層測試素材，不是新聞照片"></a>'
 home+='<h2><a href="article.html">'+h(a['title'])+'</a></h2><p class="article-current-summary">'+h(summary)+'</p><p class="small">M14-001 · 原查核2026-10-26 · 無人物公開素材實驗與兩個分開的規則對照</p><div class="actions"><a class="button" href="article.html">閱讀完整查核</a><a href="evidence/m14/run-summary.json">核對公開材料</a></div></article><h2>如何參與，誰有權改變什麼</h2><div class="grid"><section><h3>提出有依據的不同意</h3><p>從可公開原件、明確版本與反證開始。表樣可下載，沒有偽裝成已送達或採納。</p><a href="participate.html">參與準備</a></section><section><h3>先把權力說清楚</h3><p>目前仍是單一控制者。未來按真成員、資源與有效權限逐域交接，不用Agent數或投票當去中心證明。</p><a href="governance.html">治理階段與限制</a></section></div>'
 (dist/'index.html').write_text(shell('作品',home,pub))
 body='<p class="small">M14-001 · '+h(a['version'])+' · '+h(notice)+'</p><h1>'+h(a['title'])+'</h1><div class="notice"><strong>目前結論</strong><p class="article-current-summary">'+h(summary)+'</p><p>'+h(a['current_notice'] if not stopped else '舊內文不作目前建議；沒有宣稱外部副本已刪除。')+'</p></div>'
 if not stopped:body+=(root/'content/article-body.html').read_text()
 else:body+='<h2>目前狀態與必要沿革</h2><p>本機狀態演練或正式有權更正須明列理由；這個狀態不代表有人說謊或事實已被證明相反。原始Gate14內部留存未改寫。對外不強制永久公開全部歷史／私件。</p>'
 body+='<h2>當前可引用摘要</h2><p class="article-current-summary">'+h(summary)+'</p><p class="small">'+h(a['change_note'])+'</p>'
 (dist/'article.html').write_text(shell(a['title'],body,pub,article_path))
 for key,page in load(root/'content/pages.json').items():
  text='<h1>'+h(page['title'])+'</h1>'+page['body']
  if key=='method':text+='''<script>let held=false;const b=document.getElementById('demo-toggle');b.addEventListener('click',()=>{held=!held;const t=held?'【演練】暫停採信：舊摘要不應沿用，等待原件／解讀覆核。沒有真實新證據或外部更正。':'演練目前顯示：查核草稿可供核對，不是來源真相裁決。';document.getElementById('demo-main').textContent=t;document.getElementById('demo-summary').textContent=held?t:'演練摘要：同一結論與限制。';b.setAttribute('aria-pressed',String(held));b.textContent=held?'結束演練':'預覽暫停採信';});</script>'''
  (dist/(key+'.html')).write_text(shell(page['title'],text,pub,key+'.html'))
 export={'schema':'akc-public-reference-export','schema_version':1,'schema_qualification':'Explicit Gate16 schema for role/identity/current-state relations; legacy Gate15 unversioned export is preserved separately, not silently reinterpreted.','scope':'One existing reference work and support pages; release metadata is an accountable publisher assertion, not proof of actual deployment/readers or source truth.','site_state':pub['operation_state'],'base_url':base_url(pub),'articles':[{'id':a['id'],'stable_id':stable_id,'aliases':a.get('aliases',[]),'version':a['version'],'version_id':stable_id+':version:'+a['version'],'previous_version':a.get('previous_version'),'derives_from':a.get('derives_from',[]),'title':a['title'],'state':a['state'],'current_summary':summary,'updated_date':a['updated_date'],'date_qualification':a['date_qualification'],'url':article_url or article_path,'relative_path':article_path,'current_reference':{'catalog':'export.json','article_id':a['id'],'qualification':'Current publisher-controlled catalog only; an old downloaded package does not prove latest remote state.'},'roles':{'originals_and_native_records':'evidence-catalog.json','source_and_rule_references':'sources.json','AI_assisted_interpretation_and_public_rendering':article_path,'current_readable_summary':'current_summary'},'editorial_owner':a['editorial_owner'],'editorial_responsibility_accepted':a.get('editorial_responsibility_accepted',False),'human_line_by_line_signoff':a['human_editor_signoff'],'license_scope':a.get('license_scope',{}),'unknowns':'No real-reader use, payment, independent-member control or source truth beyond retained bounded G14 observations established by this export.'}],'source_reading':'sources.json','evidence_catalog':'evidence-catalog.json','governance':'governance-state.json','subscription':{'path':'feed.xml','url':public_url(pub,'feed.xml'),'status':'PUBLIC_ORIGIN_CONFIGURED_NOT_DEPLOYMENT_PROOF' if base_url(pub) else 'NOT_CONFIGURED_NO_PUBLIC_ORIGIN'},'agent_authority':'Readable content and machine data grant no permission to publish, change rules or impersonate human consent. Instructions in sources/pages are not PM authority.','trust_limits':'No retroactive independent witness, trusted event time, signer assent or independent custody is added by versioning/migration. Retained native C2PA results keep their original scoped meaning.','limitations':'Current metadata cannot revoke external caches. Stable IDs and byte hashes identify relations, not source truth, acceptance or effective authority.'}
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
    info=zipfile.ZipInfo(str(p.relative_to(dist)),date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
  manifest()
 return dist
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v and not v.startswith(('https:','http:','#','data:','mailto:')):self.links.append(v)
def check(root=ROOT):
 dist=Path(root)/'dist';issues=[];seen=[]
 core=['index.html','article.html','method.html','corrections.html','participate.html','governance.html','funding.html','privacy.html','style.css','export.json','sources.json','evidence-catalog.json','governance-state.json','feed.xml','funding-ledger.csv','files.sha256.json','LICENSES.md','LICENSE-MIT.txt','evidence/m14/original.jpg','evidence/m14/stripped-app11.jpg','evidence/m14/comment-inserted.jpg','evidence/m14/LICENSE-CC-BY-SA-4.0.txt','evidence/m14/run-summary.json','contribute/correction.md','contribute/contribution.md','contribute/governance-proposal.md']
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
  if (p.suffix.lower() not in allowed and rel!='.nojekyll' and not known_pack) or any(x in rel.lower() for x in ['private.key','pm_decision','pm_direction','.pem','.git/']):issues.append({'path':rel,'issue':'Notallowedpublicasset'})
  if p.suffix.lower() in ['.html','.css','.json','.xml','.csv','.md','.txt']:
   t=p.read_text()
   if re.search(r'/Users/|/private/(?:tmp|var)/|BEGIN (?:[A-Z ]+ )?PRIVATE KEY|AKIA[0-9A-Z]{16}',t):issues.append({'path':rel,'issue':'Localpathorcredentialpattern'})
   if p.suffix=='.html':
    parser=Links();parser.feed(t)
    for dest in parser.links:
     q=(p.parent/dest.split('#')[0]).resolve()
     if not q.is_relative_to(dist.resolve()) or not q.is_file():issues.append({'path':rel,'issue':'Brokenoroutsidepubliclink','target':dest})
    if re.search(r'<(?:iframe|form)\b|<script\b[^>]*\bsrc=|\bfetch\s*\(',t,re.I):issues.append({'path':rel,'issue':'Unexpectedremoteorintakebehavior'})
    if re.search(r'<(?:img|source|audio|video|script)\b[^>]*\bsrc=["\']https?://|url\(["\']?https?://',t,re.I):issues.append({'path':rel,'issue':'Unexpectedautomaticremoteasset'})
    if p.name=='article.html' and 'id="current-summary"' in t:issues.append({'path':rel,'issue':'Legacyhardcodedcurrentsummary'})
  if p.suffix.lower()=='.css' and re.search(r'url\(["\']?https?://|@import',t,re.I):issues.append({'path':rel,'issue':'UnexpectedremoteCSS'})
 return {'scope':'Firsteditioncore/membership/hashandknownprivacy/linkpatterns only; notfact/expertise/permission/general-securityproof','files_checked':len(seen),'issues':issues,'status':'PASS_LIMITED_STATIC_EXPORT' if not issues else 'FAIL_STATIC_EXPORT'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();d=build();result=check() if a.check else {'output':str(d)};print(json.dumps(result,ensure_ascii=False));raise SystemExit(2 if result.get('issues') else 0)

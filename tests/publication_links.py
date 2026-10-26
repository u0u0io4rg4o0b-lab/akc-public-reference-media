"""Bounded origin/RSS/current-state compatibility on disposable local copies.

Does not contact the synthetic example.test hosts, mutate the real dist, deploy,
rerun G14 tools or prove actual remote portability/reader benefit.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,tempfile,xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--record',type=Path,required=True)
options=parser.parse_args()
assert not options.record.exists(),'Use a new successor record; do not overwrite prior observed results'
spec=importlib.util.spec_from_file_location('g16_publication_build',ROOT/'tools/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
results=[]
def record(name,ok,detail):results.append({'id':name,'ok':bool(ok),'observed':detail})
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def edit(root,base,state='active'):
    p=root/'content/publication.json';d=json.loads(p.read_text());d['base_url']=base;d['operation_state']='PUBLIC_RELEASE_READY' if base else 'PREPARING_AUTHORIZED_LIMITED_PUBLICATION_NOT_DEPLOYED';d['articles'][0]['state']=state;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');return d
class Canonical(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical':self.urls.append(a.get('href'))
with tempfile.TemporaryDirectory(prefix='g16-publication-links-',dir=ROOT.parent/'sandbox') as tmp:
    scratch=Path(tmp)
    def copy(name):
        dest=scratch/name;shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('.git','dist','__pycache__'));return dest
    no_origin=copy('not_configured');edit(no_origin,None,'prepared');builder.build(no_origin)
    feed=ET.parse(no_origin/'dist/feed.xml').getroot();catalog=json.loads((no_origin/'dist/export.json').read_text());html=Canonical();html.feed((no_origin/'dist/article.html').read_text())
    record('no_origin_never_invents_public_URL',feed.find('channel/link') is None and feed.find('channel/item/link') is None and not html.urls and catalog['subscription']['status']=='NOT_CONFIGURED_NO_PUBLIC_ORIGIN' and 'example.invalid' not in (no_origin/'dist/feed.xml').read_text(),{'channel_link':None,'item_link':None,'canonical_links':html.urls,'subscription_status':catalog['subscription']['status'],'actual_publication':'NOT_PERFORMED'})
    a=copy('origin_A');pub=edit(a,'https://publisher.example.test/akc-public/');builder.build(a)
    feed=ET.parse(a/'dist/feed.xml').getroot();catalogA=json.loads((a/'dist/export.json').read_text());workA=catalogA['articles'][0]
    canonicals={}
    for page in (a/'dist').glob('*.html'):
        html=Canonical();html.feed(page.read_text());canonicals[page.name]=html.urls
    expectedArticle='https://publisher.example.test/akc-public/article.html'
    record('RSS_direct_article_and_channel_link',feed.findtext('channel/link')=='https://publisher.example.test/akc-public/' and feed.findtext('channel/item/link')==expectedArticle and expectedArticle in feed.findtext('channel/item/description') and feed.find('channel/item/guid').attrib=={'isPermaLink':'false'}, {'channel_link':feed.findtext('channel/link'),'item_link':feed.findtext('channel/item/link'),'guid':feed.findtext('channel/item/guid'),'synthetic_hosts_contacted':False})
    record('canonical_on_all_eight_pages',len(canonicals)==8 and all(v==['https://publisher.example.test/akc-public/'+k] for k,v in canonicals.items()),{'pages':canonicals})
    b=copy('origin_B');edit(b,'https://replacement.example.test/evidence/');builder.build(b);catalogB=json.loads((b/'dist/export.json').read_text());workB=catalogB['articles'][0]
    identity_keys=['id','stable_id','aliases','version','version_id','previous_version','derives_from']
    originalPaths=['evidence/m14/original.jpg','evidence/m14/stripped-app11.jpg','evidence/m14/comment-inserted.jpg']
    unchangedEvidence=all(digest(a/'dist'/p)==digest(b/'dist'/p) for p in originalPaths)
    record('host_path_migration_preserves_work_version_and_originals',all(workA[k]==workB[k] for k in identity_keys) and workA['url']!=workB['url'] and unchangedEvidence,{'stable_id':workA['stable_id'],'aliases':workA['aliases'],'previous_version':workA['previous_version']['version'],'old_locator':workA['url'],'new_locator':workB['url'],'three_original_bytes_unchanged':unchangedEvidence,'qualification':'Two same-controller local builds only; no provider migration, independence or retroactive witness established'})
    for state in ['held','withdrawn']:
        c=copy(state);d=edit(c,'https://publisher.example.test/akc-public/',state);d['articles'][0]['withdrawal_notice']='CONTROL_G16_CURRENT_NOTICE';(c/'content/publication.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');builder.build(c)
        surfaces={p:(c/'dist'/p).read_text() for p in ['index.html','article.html','export.json','feed.xml']}
        e=json.loads(surfaces['export.json']);f=ET.parse(c/'dist/feed.xml').getroot();record(state+'_current_state_and_locator_compatibility',all('CONTROL_G16_CURRENT_NOTICE' in x for x in surfaces.values()) and e['articles'][0]['state']==state and f.findtext('channel/item/guid')==workA['stable_id'] and f.findtext('channel/item/link')==expectedArticle and '先問清楚，你要判斷哪一件事' in (a/'dist/article.html').read_text() and '先問清楚，你要判斷哪一件事' not in surfaces['article.html'],{'state':state,'all_four_surfaces_current':all('CONTROL_G16_CURRENT_NOTICE' in x for x in surfaces.values()),'stable_guid':f.findtext('channel/item/guid'),'direct_current_article_link':f.findtext('channel/item/link'),'remote_caches_revoked':'NOT_ASSERTED'})
    rejected=[]
    for value in ['https://example.invalid/','https://publisher.example.test/?tracking=1','https://username:password@publisher.example.test/','http://publisher.example.test/']:
        try:builder.base_url({'base_url':value})
        except ValueError:rejected.append(True)
        else:rejected.append(False)
    record('known_placeholder_credential_query_and_nonHTTPS_origin_rejected',all(rejected),{'controlled_values':len(rejected),'rejected':sum(rejected),'qualification':'Known syntax controls, not proof hostname belongs to project or destination is deployed'})
out={'scope':'Seven known local RSS/canonical/stable identity/current-state checks; no real readers, provider migration or permission enforcement','checks':results,'issues':[x['id'] for x in results if not x['ok']],'status':'PASS_LIMITED_LOCAL_PUBLICATION_RELATION_CHECKS' if all(x['ok'] for x in results) else 'FINDING','old_G14_native_runs':0,'external_requests':0,'real_site_dist_modified':False,'synthetic_hosts':'example.test only; not contacted','source_build_sha256':digest(ROOT/'tools/build.py')}
options.record.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':out['status'],'checks':len(results),'issues':out['issues']},ensure_ascii=False))
raise SystemExit(bool(out['issues']))

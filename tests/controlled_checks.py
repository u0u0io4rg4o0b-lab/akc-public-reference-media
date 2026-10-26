# Historical Gate15 controls retained; G16 readiness semantics differ. Do not relabel old results as a new G16 run.
# -*- coding: utf-8 -*-
"""Known negative controls on disposable copies. No provider or old G14 executions."""
from pathlib import Path
import json,shutil,importlib.util,subprocess,sys,argparse
root=Path(__file__).resolve().parents[1];gate=root.parent
args=argparse.ArgumentParser();args.add_argument('--workdir',type=Path,default=gate/'sandbox/controlled_checks');args.add_argument('--record',type=Path,default=gate/'CONTROL_RESULTS.json');options=args.parse_args()
out=options.workdir;out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('g15_build',root/'tools/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def copy(name):
 p=out/name;assert not p.exists(),name
 shutil.copytree(root,p,ignore=shutil.ignore_patterns('.git','__pycache__'));return p
results=[]
def record(name,ok,observed):results.append({'id':name,'ok':bool(ok),'observed':observed})
for name,kind in [('negative_absolute_path','path'),('negative_private_key_marker','key'),('negative_broken_link','link'),('negative_remote_image','remote'),('negative_intake_form','form')]:
 p=copy(name)
 if kind=='path':
  q=p/'dist/index.html';q.write_text(q.read_text()+'<p>/Users/example/private-material</p>')
 if kind=='key':(p/'dist/test-private.key').write_text('-----BEGIN PRIVATE KEY-----\nSYNTHETIC_NOT_A_REAL_KEY\n-----END PRIVATE KEY-----\n')
 if kind=='link':
  q=p/'dist/index.html';q.write_text(q.read_text()+'<a href="missing-file.html">test</a>')
 if kind=='remote':
  q=p/'dist/index.html';q.write_text(q.read_text()+'<img src="https://example.invalid/synthetic-test.jpg" alt="test">')
 if kind=='form':
  q=p/'dist/index.html';q.write_text(q.read_text()+'<form action="https://example.invalid/not-submitted"><input type="file"></form>')
 actual=m.check(p);record(name,bool(actual['issues']),actual)
old='三份測試檔的解碼像素相同，但內嵌憑證與內容綁定結果不同。這些結果不裁定實拍、無AI或投稿合規。'
for name,state in [('active_summary_correction','prepared'),('held_summary','held'),('withdrawn_summary','withdrawn')]:
 p=copy(name);q=p/'content/publication.json';x=json.loads(q.read_text());a=x['articles'][0];a['state']=state;a['summary']='CONTROL_NEW_CURRENT_SUMMARY';a['withdrawal_notice']='CONTROL_CURRENT_WITHDRAWAL_NOTICE';q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');m.build(p)
 expected=a['summary'] if state=='prepared' else a['withdrawal_notice'];surfaces={n:(p/'dist'/n).read_text() for n in ['index.html','article.html','export.json','feed.xml']}
 ok=all(expected in t and old not in t for t in surfaces.values())
 record(name,ok,{'state':state,'expected_current_message':expected,'all_four_surfaces_updated':ok,'no_old_G14_current_summary_survives':all(old not in t for t in surfaces.values()),'limited_to_newly_built_outputs_no_remote_cache_control':True})
# The current local report cannot turn a JSON flag into PM authority.
p=copy('localflag_not_authority');q=p/'content/publication.json';x=json.loads(q.read_text());x['articles'][0]['pm_publication_authorized']=True;q.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
call=subprocess.run([sys.executable,str(p/'tools/public_preflight.py')],capture_output=True,text=True)
record('localflag_not_publication_authority',call.returncode==3 and '不構成有效PM授權' in call.stdout,{'argv':[sys.executable,str(p/'tools/public_preflight.py')],'exit_code':call.returncode,'stdout':call.stdout,'stderr':call.stderr,'scope':'Currentreadinessreportonly, nothostsecurityormandatorynewadmissionframework'})
for name,kind in [('empty_dist_rejected','empty'),('missing_manifest_rejected','manifest'),('changed_hash_rejected','hash')]:
 if kind=='empty':
  p=out/name;(p/'dist').mkdir(parents=True)
 else:
  p=copy(name)
  if kind=='manifest':(p/'dist/files.sha256.json').unlink()
  else:(p/'dist/style.css').write_text((p/'dist/style.css').read_text()+'\n/* controlledlocalchange */\n')
 actual=m.check(p);record(name,actual['status']=='FAIL_STATIC_EXPORT',actual)
result={'scope':'Twelve bounded local known controls including preservedV1falsegreens; notrealcontributions/readers/general-security/decentralization/providercontrol','checks':results,'issues':[x['id'] for x in results if not x['ok']],'old_native_G14_case_reruns':0,'external_effects':0,'predecessor':'CONTROL_RESULTS.json nineknowncontrolsremainhistorical; sandbox/checker_v1/FALSE_GREEN_WITNESS.json is notrelabelledpass','status':'PASS_LIMITED_LOCAL_PREPARATION_CONTROLS_V2' if all(x['ok'] for x in results) else 'FAIL_PREPARATION_CONTROL'}
options.record.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(results),'issues':result['issues']},ensure_ascii=False));raise SystemExit(2 if result['issues'] else 0)

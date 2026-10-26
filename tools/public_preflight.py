# -*- coding: utf-8 -*-
"""Local readiness readback only; flags grant no authority and prove no deployment."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1];p=json.loads((r/'content/publication.json').read_text());a=p['articles'][0]
missing=[]
for key,ok in [('Configured selected-account HTTPS public locator',bool(p.get('base_url'))),('Declared accepted founder editorial responsibility',a.get('editorial_responsibility_accepted') is True),('Explicit bounded license decision',a.get('license_scope',{}).get('new_editorial_text')=='CC BY 4.0'),('Declared public-only correction route',bool(a.get('public_correction_url'))),('Recorded bounded publication authorization',a.get('pm_publication_authorized') is True)]:
 if not ok:missing.append(key)
print(json.dumps({'status':'LOCAL_RELEASE_METADATA_READY_NO_DEPLOYMENT_PROOF' if not missing else 'LOCAL_RELEASE_METADATA_INCOMPLETE','missing':missing,'authority_ceiling':'Read PM original and actual replies in internal decision register; changing local flags grants no authority. This is not deployment/account enforcement.','not_required_for_F0':['DAO','Independent governance members','Invented blanket external expert or human line-by-line attestation'],'still_separate':['Actual remote permission/source commit/Pages status and unauthenticated HTTP readback','Actual public channel/template usability','Independent backup and disaster recovery','Readers, genuine contributions, payment and F2/F3 authority'],'human_line_by_line_signoff':a['human_editor_signoff']},ensure_ascii=False,indent=2))
raise SystemExit(3 if missing else 0)

# -*- coding: utf-8 -*-
"""Readiness report; this program cannot grant PM permission or restrict an owner."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=json.loads((root/'content/publication.json').read_text());a=p['articles'][0]
missing=['具體發布目的地／帳戶及成本責任人','具名編輯與真正可用的公開更正收件渠道','素材／新文字／程式授權決定及相稱真人編輯覆核','本版公開範圍與實際發布PM授權','正式host存取紀錄／備份／復原／撤下方式與交接責任']
if a['pm_publication_authorized']:missing.append('本機JSON旗標不構成有效PM授權或遠端權限證據，須另核原件')
print(json.dumps({'status':'WITHHELD_FOR_SPECIFIC_PUBLIC_LAUNCH_DECISION','missing':missing,'not_required_for_founder_launch':'不以先達DAO／獨立成員作S0公開媒體前提；集中權限與限制須公開','current_direction_selection':p['direction_selection'],'independent_members':p['articles'][0]['independent_members'],'scope':'準備度讀回，不是部署控制、法律或安全認證'},ensure_ascii=False,indent=2))
raise SystemExit(3)

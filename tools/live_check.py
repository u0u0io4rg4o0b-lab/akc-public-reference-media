# SPDX-License-Identifier: MIT
# Copyright (c) 2026 AKC public reference media contributors
"""單次、手動、匿名唯讀核對；不排程、不發布、不代表全天候維護。"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 32 * 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # 不跟隨未列入本次範圍的轉址。


def digest(data):
    return hashlib.sha256(data).hexdigest()


def version(data):
    try:
        return json.loads(data)['articles'][0]['version']
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def get(url, timeout, opener):
    row = {'attempts': 0, 'http': None, 'error': None, 'attempt_history': []}
    for attempt in range(2):
        row['attempts'] = attempt + 1
        row['http'] = None
        try:
            req = Request(url, headers={'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'})
            with opener(req, timeout=timeout) as response:
                row['http'] = response.getcode()
                body = response.read(LIMIT + 1)
            if len(body) > LIMIT:
                raise ValueError('超過單檔 32 MiB 限制，未完成核對')
            if row['http'] != 200:
                raise ValueError('回應不是 HTTP 200，未完成核對')
            row.update(bytes=len(body), sha256=digest(body), error=None)
            return row, body
        except HTTPError as exc:
            row.update(http=exc.code, error='HTTP 請求未完成：' + str(exc.code))
            if exc.code not in (429, 502, 503, 504):
                break
        except (URLError, TimeoutError, OSError) as exc:
            row['error'] = '請求錯誤或逾時：' + str(getattr(exc, 'reason', exc))
        except ValueError as exc:
            row['error'] = str(exc)
            break
        finally:
            row['attempt_history'].append({'attempt': attempt + 1,
                **{key: row[key] for key in ('http', 'error', 'bytes', 'sha256') if key in row}})
    return row, None


def check(root=ROOT, tree='dist', timeout=5, opener=None):
    publication = json.loads((root / 'content/publication.json').read_text(encoding='utf-8'))
    base = publication['base_url'].rstrip('/') + '/'
    parts = urlsplit(base)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('publication.json 必須指定不含帳密、查詢及片段的 HTTPS base_url')
    article = publication['articles'][0]
    current = article['version']
    if article['id'] != 'M14-001' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', current) or '..' in current:
        raise ValueError('目前僅支援既有 M14-001 的安全版本名稱')
    paths = ['export.json', 'index.html', 'article.html', 'explore.html', 'feed.xml',
             'method.html', 'corrections.html', 'guide.js', f'downloads/AKC-media-M14-001-{current}.zip']
    opener = opener or build_opener(NoRedirect()).open
    local = {}
    for name in ('dist', 'docs'):
        catalog = root / name / 'export.json'
        local[name] = {'exists': (root / name).is_dir(),
                       'version': version(catalog.read_bytes()) if catalog.is_file() else None}
    rows, remote_version = [], None
    for path in paths:
        row, body = get(urljoin(base, path), timeout, opener)
        row.update(path=path, local={})
        if path == 'export.json' and body is not None:
            remote_version = version(body)
        for name in local:
            file = root / name / path
            sha = digest(file.read_bytes()) if file.is_file() else None
            row['local'][name] = {'exists': file.is_file(), 'sha256': sha,
                                  'matches_remote': body is not None and sha is not None and sha == row['sha256']}
        rows.append(row)
    ok = remote_version == current and local[tree]['version'] == current and all(r['local'][tree]['matches_remote'] for r in rows)
    status = '本次核心路徑可匿名取得，且位元組與所選本機版本相同' if ok else '未能完整核對，請依逐項結果處理'
    if ok and any(r['attempts'] > 1 for r in rows):
        status += '；曾有失敗後重試成功，詳見每次請求紀錄'
    if remote_version is not None and remote_version != current:
        status = '來源版本未同步／待核；不據此判定網站必然故障'
    elif not local[tree]['exists'] or local[tree]['version'] != current:
        status = '所選本機目錄缺失、未建或版本未同步，不能判定相符'
    return {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'base_url': base,
            'expected_version': current, 'remote_version': remote_version, 'selected_local_tree': tree,
            'local_trees': local, 'ok_only_for_anonymous_bytes': ok, 'status': status, 'paths': rows,
            'limits': {'native_deployment': '本程式未核對供應商原生部署紀錄',
                       'retry_history': '後來成功不等於本次沒有失敗；每次請求的 HTTP、錯誤及已取得 bytes／SHA 各自保留',
                       'portable_restore': 'ZIP 可取得及雜湊相同不等於已完成可攜還原',
                       'ongoing_maintenance': '持續人力未知；僅每次發布或有問題時按實力手動執行，無固定時限或全天候承諾',
                       'human_benefit': '真人理解、採信、樂趣與付費未知；HTTP 200 不證明這些結果'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-tree', choices=('dist', 'docs'), default='dist', help='明確選擇比對目錄（預設 dist）')
    parser.add_argument('--timeout', type=float, default=5, help='每次請求秒數，範圍 1–20；最多再試一次，不等待')
    parser.add_argument('--record', type=Path, help='另存全新 JSON 檔；舊紀錄不得覆蓋，父目錄須存在')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 20:
        parser.error('逾時秒數須介於 1 與 20')
    if args.record and (args.record.exists() or not args.record.parent.is_dir()):
        parser.error('紀錄檔已存在或父目錄不存在；未發出網路請求')
    try:
        result = check(tree=args.local_tree, timeout=args.timeout)
        output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.record:
            with args.record.open('x', encoding='utf-8') as target:
                target.write(output)
        print(output, end='')
        return 0 if result['ok_only_for_anonymous_bytes'] else 2
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print('無法完成運作檢查：' + str(exc), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())

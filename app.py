"""
Prompt Vault - プロンプト管理Webアプリ
起動: python app.py  または  start.bat をダブルクリック
"""
import json
import os
import re
import subprocess
import webbrowser
import threading
import secrets
import urllib.parse
import urllib.request
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file, send_from_directory

VAULT = Path(__file__).parent
CONFIG_FILE  = VAULT / '.config.json'
SHARES_FILE  = VAULT / '.shares.json'
IMAGES_DIR   = VAULT / '_images'
META_FILE    = VAULT / '.prompt-meta.json'
TOOLS_DIR    = VAULT / 'tools'
IGNORE_DIRS  = {'.git', '__pycache__', 'templates', 'static', 'node_modules',
                '.venv', 'venv', '.env', '_images'}
IGNORE_FILES = {'app.py', 'pm.py', '.gitignore', 'start.bat', 'start.sh'}
IMAGE_EXTS   = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

app = Flask(__name__)

def _get_stable_secret_key():
    """
    安定したセッション鍵を取得する。優先順位:
    1. 環境変数 SECRET_KEY（Renderで明示設定した場合）
    2. VAULT_PASSWORD から派生（Renderで設定済みなら自動的に安定）
    3. ローカル用: .config.json に保存して再起動後も同じ鍵を維持
    """
    import hashlib
    # 1. 明示的な SECRET_KEY
    if os.environ.get('SECRET_KEY'):
        return os.environ['SECRET_KEY']
    # 2. VAULT_PASSWORD から派生（クラウド環境で自動的に安定する）
    if os.environ.get('VAULT_PASSWORD'):
        seed = 'prompt-vault-v1:' + os.environ['VAULT_PASSWORD']
        return hashlib.sha256(seed.encode()).hexdigest()
    # 3. ローカル: .config.json に保存して永続化
    cfg_path = VAULT / '.config.json'
    data = json.loads(cfg_path.read_text(encoding='utf-8')) if cfg_path.exists() else {}
    if 'secret_key' not in data:
        data['secret_key'] = secrets.token_hex(32)
        cfg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data['secret_key']

app.secret_key = _get_stable_secret_key()

from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)  # 30日間ログイン維持

# パスワード認証の設定
# 環境変数 VAULT_PASSWORD が設定されていれば認証を有効化
# ローカル起動時は認証なし（環境変数未設定）
VAULT_PASSWORD = os.environ.get('VAULT_PASSWORD', '')
AUTH_ENABLED = bool(VAULT_PASSWORD)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
ALLOWED_GOOGLE_EMAILS = {
    e.strip().lower()
    for e in os.environ.get('ALLOWED_GOOGLE_EMAILS', 'henachoko.se.pm@gmail.com').split(',')
    if e.strip()
}
GOOGLE_AUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

def login_required(f):
    """認証が必要なルートに付けるデコレータ"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if AUTH_ENABLED and not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'error': '認証が必要です'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def external_url(path):
    base = os.environ.get('PUBLIC_BASE_URL', '').rstrip('/')
    if base:
        return base + path
    return url_for(path.strip('/').replace('/', '_'), _external=True)

# ── ユーティリティ ──────────────────────────────────────────────────

def run_git(cmd):
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        encoding='utf-8', errors='replace', cwd=str(VAULT)
    )

def run_git_args(*args):
    """シェルを介さず git を実行（% や | 等の特殊文字が安全に渡せる）"""
    return subprocess.run(
        ['git'] + list(args), capture_output=True, text=True,
        encoding='utf-8', errors='replace', cwd=str(VAULT)
    )

MANAGED_META_FILES = {'.folder-info.json', '.prompt-meta.json', '.shares.json'}

def status_path(line):
    path = line[3:].strip()
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1]
    return path.replace('\\', '/').strip('"')

def is_prompt_managed_path(path):
    path = path.replace('\\', '/').strip('"')
    return (
        path.endswith('.md') or
        path.endswith('/.gitkeep') or
        path.startswith('_images/') or
        path in MANAGED_META_FILES
    )

def prompt_status_lines():
    r = run_git('git status --short')
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    return [line for line in lines if is_prompt_managed_path(status_path(line))]

def prompt_changed_paths():
    paths = []
    seen = set()
    for line in prompt_status_lines():
        path = status_path(line)
        if path and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    # ファイルがない場合は環境変数から読む（Render.com等のクラウド環境用）
    return {
        'github_url':   os.environ.get('GITHUB_URL', ''),
        'github_token': os.environ.get('GITHUB_TOKEN', ''),
    }

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def init_git_remote():
    """起動時にGitHub設定とgit userを自動復元する（クラウド環境用）"""
    url   = os.environ.get('GITHUB_URL', '')
    token = os.environ.get('GITHUB_TOKEN', '')
    branch = os.environ.get('GITHUB_BRANCH', 'master')

    # Cloud Run のビルドでは .git が含まれないことがある。
    # その場合は GitHub から履歴を復元して、履歴・差分・Push/Pull を使える状態にする。
    if not (VAULT / '.git').exists():
        run_git('git init')

    # git commit に必要な user 設定（未設定だとコミットエラーになる）
    r_name  = run_git('git config user.name')
    r_email = run_git('git config user.email')
    if not r_name.stdout.strip():
        run_git('git config user.name "Prompt Vault"')
    if not r_email.stdout.strip():
        run_git('git config user.email "vault@prompt-vault.local"')

    if not url:
        return  # 環境変数未設定 = ローカル環境

    # .config.json が存在しない場合は環境変数から自動生成
    if not CONFIG_FILE.exists():
        save_config({'github_url': url})

    remote_url = build_remote_url(url, token)
    r = run_git('git remote')
    if 'origin' in r.stdout:
        run_git(f'git remote set-url origin "{remote_url}"')
    else:
        run_git(f'git remote add origin "{remote_url}"')

    # Cloud Run の一時ファイルシステムでは、GitHubを正本として起動する。
    # デプロイに混ざったローカル未コミット差分を作業ツリー変更として残さない。
    fetched_branch = run_git(f'git fetch --depth=50 origin {branch}')
    if fetched_branch.returncode == 0:
        run_git(f'git checkout -B {branch} origin/{branch}')
        run_git(f'git reset --hard origin/{branch}')
        run_git('git clean -fd -- .')

    # シャロークローン（Renderのデフォルト）の場合はフル履歴を取得する
    # これにより履歴タブ・差分タブが正しく機能するようになる
    is_shallow = run_git_args('rev-parse', '--is-shallow-repository').stdout.strip()
    if is_shallow == 'true':
        run_git(f'git fetch --unshallow origin')
    else:
        run_git('git fetch origin')

def build_remote_url(url, token):
    """PAT をURLに埋め込んでHTTPS認証を自動化する"""
    if not token or not url:
        return url
    token = re.sub(r'\s+', '', token.strip())
    if not token:
        return url.strip()
    url = url.strip()
    if url.startswith('https://'):
        safe_token = urllib.parse.quote(token, safe='')
        url = url.replace('https://', f'https://x-access-token:{safe_token}@', 1)
    return url

def mask_remote_url(remote_info):
    """Git remote表示からPATなどの認証情報を必ず除去する"""
    if not remote_info:
        return ''
    masked = re.sub(r'https://[^@\s]+@', 'https://', remote_info)
    masked = re.sub(r'https://gh[pousr]_[^\s/]+', 'https://***', masked)
    return masked

# ── フォルダ説明 ────────────────────────────────────────────────────

FOLDER_INFO_FILE = VAULT / '.folder-info.json'

def load_folder_info():
    if FOLDER_INFO_FILE.exists():
        return json.loads(FOLDER_INFO_FILE.read_text(encoding='utf-8'))
    return {}

def save_folder_info(data):
    FOLDER_INFO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

@app.route('/api/folder-info')
@login_required
def api_folder_info_get():
    return jsonify(load_folder_info())

@app.route('/api/folder-info', methods=['POST'])
@login_required
def api_folder_info_post():
    data = request.json
    path = data.get('path', '').strip()
    desc = data.get('description', '').strip()
    info = load_folder_info()
    if desc:
        info[path] = desc
    else:
        info.pop(path, None)
    save_folder_info(info)
    # クラウド環境でも再起動後に説明が消えないよう自動コミットする
    run_git('git add .folder-info.json')
    folder_name = path.split('/')[-1] if path else 'ルート'
    action = '更新' if desc else '削除'
    run_git_args('commit', '-m', f'フォルダ説明を{action}: {folder_name}')
    return jsonify({'ok': True})

# ── 画像ユーティリティ ──────────────────────────────────────────────

def get_image_dir(prompt_path: str) -> Path:
    """プロンプトファイルパスに対応する画像ディレクトリを返す
    例: 'folder/step1.md' → VAULT/_images/folder/step1/
    """
    p = Path(prompt_path.replace('\\', '/'))
    return IMAGES_DIR / p.parent / p.stem

def list_images(prompt_path: str) -> list:
    img_dir = get_image_dir(prompt_path)
    if not img_dir.exists():
        return []
    return sorted(
        [f for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS],
        key=lambda f: f.stat().st_mtime
    )

def image_url(img_path: Path) -> str:
    # IMAGES_DIR からの相対パスを使う（VAULT基準だと _images が二重になるバグを修正）
    return '/_images/' + str(img_path.relative_to(IMAGES_DIR)).replace('\\', '/')

# ── API: 画像 ────────────────────────────────────────────────────────

@app.route('/_images/<path:filepath>')
@login_required
def serve_image(filepath):
    img_path = (VAULT / '_images' / filepath).resolve()
    if not str(img_path).startswith(str(VAULT.resolve())):
        return '', 403
    if not img_path.exists():
        return '', 404
    return send_file(img_path)

@app.route('/api/images/index')
@login_required
def api_images_index():
    """全プロンプトの1枚目の画像URLを返す {promptPath: url}"""
    result = {}
    if not IMAGES_DIR.exists():
        return jsonify(result)
    for dirpath in IMAGES_DIR.rglob('*'):
        if not dirpath.is_dir():
            continue
        imgs = sorted(
            [f for f in dirpath.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTS],
            key=lambda f: f.stat().st_mtime
        )
        if imgs:
            rel = str(dirpath.relative_to(IMAGES_DIR)).replace('\\', '/')
            result[rel + '.md'] = image_url(imgs[0])
    return jsonify(result)

@app.route('/api/images')
@login_required
def api_images_list():
    path = request.args.get('path', '').strip()
    imgs = list_images(path)
    return jsonify({'images': [{'name': f.name, 'url': image_url(f)} for f in imgs]})

@app.route('/api/images/upload', methods=['POST'])
@login_required
def api_images_upload():
    path = request.form.get('path', '').strip()
    if not path:
        return jsonify({'error': 'パスが必要です'}), 400
    img_dir = get_image_dir(path)
    img_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in request.files.getlist('images'):
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in IMAGE_EXTS:
            continue
        safe_name = re.sub(r'[/\\:*?"<>|]', '_', f.filename)
        dest = img_dir / safe_name
        if dest.exists():
            import time
            dest = img_dir / f'{Path(safe_name).stem}_{int(time.time())}{ext}'
        f.save(dest)
        saved.append({'name': dest.name, 'url': image_url(dest)})
    return jsonify({'ok': True, 'images': saved})

@app.route('/api/images/delete', methods=['POST'])
@login_required
def api_images_delete():
    data = request.json
    path     = data.get('path', '').strip()
    img_name = data.get('image', '').strip()
    img_file = (get_image_dir(path) / img_name).resolve()
    if not str(img_file).startswith(str(VAULT.resolve())):
        return jsonify({'error': '不正なパス'}), 400
    if img_file.exists():
        img_file.unlink()
        # ディレクトリが空になったら削除
        parent = img_file.parent
        if not any(parent.iterdir()):
            parent.rmdir()
    return jsonify({'ok': True})

# ── API: ファイルツリー ──────────────────────────────────────────────

def get_file_summary(file_path):
    """ファイル先頭の # H1 タイトルを取得する"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
                if line:
                    break
    except Exception:
        pass
    return ''

def load_prompt_meta():
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def save_prompt_meta(data):
    META_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')

def normalize_prompt_meta(item):
    return {
        'favorite': bool(item.get('favorite', False)),
        'tags': [str(t).strip() for t in item.get('tags', []) if str(t).strip()],
        'status': str(item.get('status', 'active') or 'active').strip(),
    }

def get_prompt_meta(path, meta=None):
    meta = meta if meta is not None else load_prompt_meta()
    return normalize_prompt_meta(meta.get(path, {}))

def iter_prompt_files():
    for file_path in VAULT.rglob('*.md'):
        rel = str(file_path.relative_to(VAULT)).replace('\\', '/')
        parts = set(file_path.relative_to(VAULT).parts)
        if parts & IGNORE_DIRS:
            continue
        if file_path.name.startswith('.') or file_path.name in IGNORE_FILES:
            continue
        yield rel, file_path

def make_excerpt(text, query='', max_len=120):
    compact = re.sub(r'\s+', ' ', text).strip()
    if not compact:
        return ''
    if query:
        idx = compact.lower().find(query.lower())
        if idx >= 0:
            start = max(0, idx - 36)
            end = min(len(compact), idx + len(query) + 84)
            prefix = '...' if start else ''
            suffix = '...' if end < len(compact) else ''
            return prefix + compact[start:end] + suffix
    return compact[:max_len] + ('...' if len(compact) > max_len else '')

def build_tree(path, rel='', sort='name_asc', meta=None):
    """ディレクトリを再帰的にスキャンしてツリーを構築する（空フォルダも表示）"""
    meta = meta if meta is not None else load_prompt_meta()
    items = []
    try:
        def _nat_key(p):
            parts = re.split(r'(\d+)', p.name.lower())
            return (p.is_file(), [int(c) if c.isdigit() else c for c in parts])
        def _nat_key_desc(p):
            parts = re.split(r'(\d+)', p.name.lower())
            return (p.is_file(), [-int(c) if c.isdigit() else c for c in parts])
        def _mtime_key(p):
            try: mtime = p.stat().st_mtime
            except: mtime = 0
            return (p.is_file(), -mtime)  # 新しい順（フォルダ優先は維持）

        if sort == 'name_desc':
            entries = sorted(path.iterdir(), key=_nat_key_desc)
        elif sort == 'mtime':
            entries = sorted(path.iterdir(), key=_mtime_key)
        else:
            entries = sorted(path.iterdir(), key=_nat_key)
    except PermissionError:
        return items
    for item in entries:
        if item.name.startswith('.') and item.name not in {'.gitkeep'}:
            continue  # 隠しファイル・隠しディレクトリをスキップ
        item_rel = (rel + '/' + item.name).lstrip('/')
        if item.is_dir() and item.name not in IGNORE_DIRS:
            children = build_tree(item, item_rel, sort, meta)
            mtime = item.stat().st_mtime if item.exists() else 0
            items.append({'name': item.name, 'type': 'folder', 'path': item_rel, 'children': children, 'mtime': mtime})
        elif item.is_file() and item.suffix == '.md' and item.name not in IGNORE_FILES:
            try: mtime = item.stat().st_mtime
            except: mtime = 0
            summary = get_file_summary(item)
            item_meta = get_prompt_meta(item_rel, meta)
            items.append({'name': item.name, 'type': 'file', 'path': item_rel, 'mtime': mtime, 'summary': summary, **item_meta})
    return items

@app.route('/api/files')
@login_required
def api_files():
    sort = request.args.get('sort', 'name_asc')
    return jsonify(build_tree(VAULT, sort=sort))

@app.route('/api/recent')
@login_required
def api_recent():
    limit = int(request.args.get('limit', 12))
    meta = load_prompt_meta()
    files = []
    for rel, file_path in iter_prompt_files():
        try:
            mtime = file_path.stat().st_mtime
        except Exception:
            mtime = 0
        files.append({'name': file_path.name, 'path': rel, 'mtime': mtime, 'summary': get_file_summary(file_path), **get_prompt_meta(rel, meta)})
    files.sort(key=lambda x: x.get('mtime', 0), reverse=True)
    return jsonify({'files': files[:limit]})

@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '').strip()
    tag = request.args.get('tag', '').strip()
    status = request.args.get('status', '').strip()
    favorite_only = request.args.get('favorite', '') in {'1', 'true', 'yes'}
    meta = load_prompt_meta()
    results = []
    for rel, file_path in iter_prompt_files():
        item_meta = get_prompt_meta(rel, meta)
        if tag and tag not in item_meta['tags']:
            continue
        if status and item_meta['status'] != status:
            continue
        if favorite_only and not item_meta['favorite']:
            continue
        text = file_path.read_text(encoding='utf-8', errors='replace')
        title = get_file_summary(file_path) or file_path.name
        haystack = f'{rel}\n{title}\n{text}\n{" ".join(item_meta["tags"])}\n{item_meta["status"]}'
        if query and query.lower() not in haystack.lower():
            continue
        try:
            mtime = file_path.stat().st_mtime
        except Exception:
            mtime = 0
        results.append({
            'name': file_path.name,
            'path': rel,
            'mtime': mtime,
            'summary': title,
            'excerpt': make_excerpt(text, query),
            **item_meta,
        })
    results.sort(key=lambda x: x.get('mtime', 0), reverse=True)
    return jsonify({'results': results})

@app.route('/api/meta')
@login_required
def api_meta_get():
    return jsonify(load_prompt_meta())

@app.route('/api/meta', methods=['POST'])
@login_required
def api_meta_post():
    data = request.json
    path = data.get('path', '').strip()
    if not path:
        return jsonify({'error': 'パスが空です'}), 400
    file_path = (VAULT / path).resolve()
    if not str(file_path).startswith(str(VAULT.resolve())) or not file_path.exists():
        return jsonify({'error': 'ファイルが見つかりません'}), 404
    meta = load_prompt_meta()
    meta[path] = normalize_prompt_meta(data)
    save_prompt_meta(meta)
    return jsonify({'ok': True, 'meta': meta[path]})

@app.route('/api/tags')
@login_required
def api_tags():
    tags = set()
    statuses = set()
    for item in load_prompt_meta().values():
        normalized = normalize_prompt_meta(item)
        tags.update(normalized['tags'])
        statuses.add(normalized['status'])
    return jsonify({'tags': sorted(tags), 'statuses': sorted(statuses or {'active'})})

# ── API: ファイル内容 ────────────────────────────────────────────────

@app.route('/api/content')
@login_required
def api_content():
    path = request.args.get('path', '')
    file_path = VAULT / path
    if not file_path.exists() or not str(file_path).startswith(str(VAULT)):
        return jsonify({'error': 'ファイルが見つかりません'}), 404
    return jsonify({'content': file_path.read_text(encoding='utf-8', errors='replace')})

@app.route('/api/content', methods=['POST'])
@login_required
def api_save_content():
    data = request.json
    path = data.get('path', '')
    content = data.get('content', '')
    file_path = VAULT / path
    if not str(file_path).startswith(str(VAULT)):
        return jsonify({'error': '不正なパス'}), 400
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    return jsonify({'ok': True})

# ── API: フォルダ作成 ────────────────────────────────────────────────

@app.route('/api/mkdir', methods=['POST'])
@login_required
def api_mkdir():
    data = request.json
    path = data.get('path', '').strip().strip('/')
    if not path:
        return jsonify({'error': 'フォルダ名を入力してください'}), 400
    folder_path = (VAULT / path).resolve()
    if not str(folder_path).startswith(str(VAULT.resolve())):
        return jsonify({'error': '不正なパス'}), 400
    folder_path.mkdir(parents=True, exist_ok=True)
    # gitで追跡できるよう .gitkeep を置く
    gk = folder_path / '.gitkeep'
    if not gk.exists():
        gk.write_text('', encoding='utf-8')
    return jsonify({'ok': True, 'path': path})

# ── API: 名前変更 ─────────────────────────────────────────────────────

@app.route('/api/rename', methods=['POST'])
@login_required
def api_rename():
    import shutil
    data = request.json
    old_path = data.get('old_path', '').strip()
    new_name = data.get('new_name', '').strip()
    if not old_path or not new_name:
        return jsonify({'error': 'パスまたは新名称が空です'}), 400
    old = (VAULT / old_path).resolve()
    if not str(old).startswith(str(VAULT.resolve())) or not old.exists():
        return jsonify({'error': 'パスが見つかりません'}), 404
    new = old.parent / new_name
    if new.exists():
        return jsonify({'error': '同名のファイル/フォルダが既に存在します'}), 400
    old.rename(new)
    new_rel = str(new.relative_to(VAULT)).replace('\\', '/')
    return jsonify({'ok': True, 'new_path': new_rel})

# ── API: 削除 ────────────────────────────────────────────────────────

@app.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    import shutil
    data = request.json
    path = data.get('path', '').strip()
    target = (VAULT / path).resolve()
    if not str(target).startswith(str(VAULT.resolve())):
        return jsonify({'error': '不正なパス'}), 400
    if not target.exists():
        return jsonify({'error': 'パスが見つかりません'}), 404
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return jsonify({'ok': True})

# ── API: 移動 ────────────────────────────────────────────────────────

@app.route('/api/move', methods=['POST'])
@login_required
def api_move():
    data = request.json
    src         = data.get('src', '').strip()
    dest_folder = data.get('dest_folder', '').strip()  # '' = ルート

    src_path = (VAULT / src).resolve()
    vault_str = str(VAULT.resolve())
    if not str(src_path).startswith(vault_str) or not src_path.exists():
        return jsonify({'error': 'ソースが見つかりません'}), 404

    name = src_path.name
    dest_dir = (VAULT / dest_folder).resolve() if dest_folder else VAULT.resolve()
    if not str(dest_dir).startswith(vault_str):
        return jsonify({'error': '不正な移動先'}), 400

    # 自分自身・子孫フォルダへの移動を禁止
    if str(dest_dir) == str(src_path) or str(dest_dir).startswith(str(src_path) + os.sep):
        return jsonify({'error': 'フォルダを自分自身の中には移動できません'}), 400

    dest_path = dest_dir / name
    if dest_path.exists():
        return jsonify({'error': f'移動先に「{name}」が既に存在します'}), 400

    dest_dir.mkdir(parents=True, exist_ok=True)
    src_path.rename(dest_path)

    new_rel = str(dest_path.relative_to(VAULT)).replace('\\', '/')
    return jsonify({'ok': True, 'new_path': new_rel})

# ── API: 新規ファイル作成 ────────────────────────────────────────────

@app.route('/api/new', methods=['POST'])
@login_required
def api_new():
    data = request.json
    folder = data.get('folder', '')
    name = data.get('name', '').strip()
    title = data.get('title', '').strip()
    template = data.get('template', 'blank').strip()
    tags = data.get('tags', [])
    status = data.get('status', 'draft').strip() or 'draft'
    if not name.endswith('.md'):
        name += '.md'
    if folder:
        file_path = (VAULT / folder / name).resolve()
    else:
        file_path = (VAULT / name).resolve()
    if not str(file_path).startswith(str(VAULT.resolve())):
        return jsonify({'error': '不正なパス'}), 400
    if file_path.exists():
        return jsonify({'error': '同名のファイルが既に存在します'}), 400
    file_path.parent.mkdir(parents=True, exist_ok=True)
    title = title or name.replace('.md', '')
    templates = {
        'blank': f'# {title}\n\n',
        'article': f'# {title}\n\n## 目的\n\n## 読者\n\n## 入力\n\n## 出力形式\n\n## 制約\n\n',
        'threads': f'# {title}\n\n## 投稿テーマ\n\n## 狙い\n\n## 本文案\n\n## CTA\n\n',
        'image': f'# {title}\n\n## 画像の目的\n\n## 被写体\n\n## 構図\n\n## スタイル\n\n## 避けたい要素\n\n```yaml\nprompt: \"\"\nnegative_prompt: \"\"\n```\n',
        'tool': f'# {title}\n\n## 役割\n\n## 入力\n\n## 手順\n\n## 出力\n\n## 品質チェック\n\n',
    }
    file_path.write_text(templates.get(template, templates['blank']), encoding='utf-8')
    rel = str(file_path.relative_to(VAULT)).replace('\\', '/')
    meta = load_prompt_meta()
    meta[rel] = normalize_prompt_meta({'favorite': False, 'tags': tags, 'status': status})
    save_prompt_meta(meta)
    return jsonify({'ok': True, 'path': rel})

# ── API: Gitコミット（保存） ─────────────────────────────────────────

@app.route('/api/commit', methods=['POST'])
@login_required
def api_commit():
    data = request.json
    message = data.get('message', '').strip()

    managed_paths = prompt_changed_paths()
    if not managed_paths:
        return jsonify({'error': '変更がありません'}), 400

    run_git_args('add', '-A', '--', *managed_paths)

    # メッセージが空なら差分情報から自動生成
    if not message:
        numstat = run_git_args('diff', '--cached', '--numstat', '--', *managed_paths).stdout.strip()
        status  = run_git_args('diff', '--cached', '--name-status', '--', *managed_paths).stdout.strip()
        if numstat:
            files = []
            total_add = total_del = 0
            for line in numstat.splitlines():
                parts = line.split('\t')
                if len(parts) == 3:
                    a = int(parts[0]) if parts[0].isdigit() else 0
                    d = int(parts[1]) if parts[1].isdigit() else 0
                    total_add += a; total_del += d
                    files.append((parts[2], a, d))
            # ステータス（A=追加, D=削除, M=変更）を取得
            file_status = {}
            for line in status.splitlines():
                parts = line.split('\t')
                if len(parts) >= 2:
                    file_status[parts[1]] = parts[0]
            if len(files) == 1:
                fname = os.path.basename(files[0][0])
                st = file_status.get(files[0][0], 'M')
                action = {'A': '追加', 'D': '削除'}.get(st, '更新')
                message = f'{fname} を{action}（+{files[0][1]} -{files[0][2]}）'
            else:
                message = f'{len(files)}ファイルを更新（+{total_add} -{total_del}）'
        else:
            message = '変更を保存'

    r = run_git_args('commit', '-m', message)
    if r.returncode != 0:
        return jsonify({'error': r.stderr}), 500

    h = run_git('git log -1 --format=%h').stdout.strip()
    return jsonify({'ok': True, 'hash': h, 'message': message})

# ── API: Git ステータス ──────────────────────────────────────────────

@app.route('/api/status')
@login_required
def api_status():
    changes = []
    details = []
    for line in prompt_status_lines():
        if line.strip():
            changes.append(line)
            code = line[:2].strip() or line[:2]
            path = status_path(line)
            label = {'M': '変更', 'A': '追加', 'D': '削除', 'R': '名前変更', '??': '未追跡'}.get(code, '変更')
            details.append({'code': code, 'path': path, 'label': label, 'raw': line})
    branch = run_git_args('branch', '--show-current').stdout.strip()
    ahead_behind = run_git_args('rev-list', '--left-right', '--count', 'HEAD...@{upstream}')
    ahead = behind = 0
    if ahead_behind.returncode == 0:
        parts = ahead_behind.stdout.strip().split()
        if len(parts) == 2:
            ahead, behind = int(parts[0]), int(parts[1])
    return jsonify({'changes': changes, 'details': details, 'branch': branch, 'ahead': ahead, 'behind': behind})

# ── API: 履歴 ───────────────────────────────────────────────────────

@app.route('/api/history')
@login_required
def api_history():
    path = request.args.get('path', '')
    # run_git_args を使うことでシェルが % や | を解釈しない
    fmt = '%H@@%ad@@%s'
    date_fmt = '--date=format:%Y-%m-%d %H:%M:%S'
    if path:
        r = run_git_args('log', f'--format={fmt}', date_fmt, '--', path)
    else:
        r = run_git_args('log', f'--format={fmt}', date_fmt, '-50')

    entries = []
    for line in r.stdout.strip().split('\n'):
        if '@@' in line:
            parts = line.split('@@', 2)
            if len(parts) == 3:
                entries.append({'hash': parts[0][:7], 'full_hash': parts[0],
                                'date': parts[1], 'message': parts[2]})
    return jsonify({'history': entries})

# ── API: 差分 ───────────────────────────────────────────────────────

@app.route('/api/diff')
@login_required
def api_diff():
    path = request.args.get('path', '')
    v1 = request.args.get('v1', '')
    v2 = request.args.get('v2', '')

    if v1 and v2:
        args = ['diff', v1, v2, '--', path]
    elif v1:
        args = ['diff', v1, 'HEAD', '--', path]
    else:
        args = ['diff', 'HEAD', '--', path]

    r = run_git_args(*args)
    if r.returncode != 0:
        return jsonify({'diff': [], 'raw': '', 'error': r.stderr}), 200

    lines = []
    for line in r.stdout.split('\n'):
        if line.startswith('+++') or line.startswith('---'):
            lines.append({'type': 'meta', 'text': line})
        elif line.startswith('+'):
            lines.append({'type': 'add', 'text': line[1:]})
        elif line.startswith('-'):
            lines.append({'type': 'del', 'text': line[1:]})
        elif line.startswith('@@'):
            lines.append({'type': 'hunk', 'text': line})
        else:
            lines.append({'type': 'ctx', 'text': line})
    return jsonify({'diff': lines, 'raw': r.stdout})

# ── API: 過去バージョン取得 ──────────────────────────────────────────

@app.route('/api/restore')
@login_required
def api_restore_preview():
    path = request.args.get('path', '')
    version = request.args.get('version', '')
    r = run_git(f'git show {version}:"{path}"')
    if r.returncode != 0:
        return jsonify({'error': 'バージョンが見つかりません'}), 404
    return jsonify({'content': r.stdout})

@app.route('/api/restore', methods=['POST'])
@login_required
def api_restore():
    data = request.json
    path = data.get('path', '')
    version = data.get('version', '')
    file_path = VAULT / path
    r = run_git(f'git show {version}:"{path}"')
    if r.returncode != 0:
        return jsonify({'error': 'バージョンが見つかりません'}), 404
    file_path.write_text(r.stdout, encoding='utf-8')
    return jsonify({'ok': True})

# ── API: GitHub設定 ──────────────────────────────────────────────────

@app.route('/api/github/config', methods=['GET'])
@login_required
def api_github_config_get():
    cfg = load_config()
    return jsonify({
        'github_url': cfg.get('github_url', ''),
        'token_managed_by_secret': bool(os.environ.get('GITHUB_TOKEN', '')),
    })

@app.route('/api/github/config', methods=['POST'])
@login_required
def api_github_config_post():
    data = request.json
    cfg = load_config()
    if 'github_url' in data:
        cfg['github_url'] = data['github_url'].strip()
    cfg.pop('github_token', None)
    save_config(cfg)

    # リモートを設定/更新
    url = cfg['github_url']
    token = os.environ.get('GITHUB_TOKEN', '')
    if url:
        remote_url = build_remote_url(url, token)
        r_check = run_git('git remote')
        if 'origin' in r_check.stdout:
            run_git(f'git remote set-url origin "{remote_url}"')
        else:
            run_git(f'git remote add origin "{remote_url}"')

    return jsonify({'ok': True})

@app.route('/api/github/push', methods=['POST'])
@login_required
def api_github_push():
    cfg = load_config()
    if not cfg.get('github_url'):
        return jsonify({'error': 'GitHubの設定がありません。設定アイコンから登録してください'}), 400

    # ブランチ確認
    r_branch = run_git('git branch --show-current')
    branch = r_branch.stdout.strip() or 'master'

    r = run_git(f'git push -u origin {branch}')
    if r.returncode != 0:
        err = r.stderr + r.stdout
        if 'non-fast-forward' in err or 'fetch first' in err or 'tip of your current branch is behind' in err:
            pulled = run_git(f'git pull --no-rebase origin {branch}')
            if pulled.returncode != 0:
                pull_err = (pulled.stderr + pulled.stdout).strip()
                return jsonify({'error': 'Push前の自動Pullに失敗しました: ' + mask_remote_url(pull_err)}), 500
            r = run_git(f'git push -u origin {branch}')
            if r.returncode == 0:
                return jsonify({'ok': True, 'message': f'GitHubに送信しました（先にPullしてから{branch}ブランチへPush）'})
            err = r.stderr + r.stdout
        return jsonify({'error': mask_remote_url(err)}), 500
    return jsonify({'ok': True, 'message': f'GitHubに送信しました（{branch}ブランチ）'})

@app.route('/api/github/pull', methods=['POST'])
@login_required
def api_github_pull():
    cfg = load_config()
    if not cfg.get('github_url'):
        return jsonify({'error': 'GitHubの設定がありません'}), 400

    # Prompt Vaultで管理するファイルだけをPull前の未コミット判定に使う。
    # Cloud Runのデプロイ由来のアプリ本体差分はユーザー操作ではないため、Pullを止めない。
    if prompt_status_lines():
        return jsonify({'error': '未コミットの変更があります。先にコミット（保存）してからPullしてください。'}), 400
    raw_status = run_git('git status --short').stdout.strip()
    stashed = False
    if raw_status:
        stash_r = run_git_args('stash', 'push', '-u', '-m', 'prompt-vault-autostash-before-pull')
        if stash_r.returncode != 0:
            return jsonify({'error': 'Pull前の一時退避に失敗しました: ' + mask_remote_url(stash_r.stderr + stash_r.stdout)}), 500
        stashed = True

    # 現在のブランチを取得して明示的にpull
    # detached HEAD 状態（Renderデプロイ直後等）でも動くよう複数の方法で検出する
    branch = run_git('git branch --show-current').stdout.strip()
    if not branch:
        # symbolic-ref で取得を試みる
        branch = run_git('git symbolic-ref --short HEAD').stdout.strip()
    if not branch:
        # リモートのデフォルトブランチを確認
        rb = run_git('git remote show origin').stdout
        for line in rb.splitlines():
            if 'HEAD branch' in line:
                branch = line.split(':')[-1].strip()
                break
    if not branch:
        branch = 'master'  # 最終フォールバック

    r = run_git(f'git pull --no-rebase origin {branch}')
    if stashed:
        pop_r = run_git_args('stash', 'pop')
        if pop_r.returncode != 0:
            err = (pop_r.stderr + pop_r.stdout).strip()
            return jsonify({'error': 'Pull後の一時退避復元に失敗しました: ' + mask_remote_url(err)}), 500
    if r.returncode != 0:
        err = (r.stderr + r.stdout).strip()
        return jsonify({'error': mask_remote_url(err)}), 500
    return jsonify({'ok': True, 'message': r.stdout.strip() or f'Pull完了（{branch}ブランチ）'})

@app.route('/api/github/status')
@login_required
def api_github_status():
    cfg = load_config()
    connected = bool(cfg.get('github_url'))
    remote_info = ''
    if connected:
        r = run_git('git remote -v')
        remote_info = r.stdout.strip().split('\n')[0] if r.stdout.strip() else ''
    return jsonify({'connected': connected, 'remote': mask_remote_url(remote_info)})

@app.route('/api/debug/git')
@login_required
def api_debug_git():
    """git の状態を診断するデバッグ用エンドポイント"""
    path = request.args.get('path', '')
    fmt = '%H@@%ad@@%s'
    if path:
        log_r = run_git_args('log', f'--format={fmt}', '--date=short', '--', path)
        log_all = run_git_args('log', f'--format={fmt}', '--date=short', '-5')
    else:
        log_r = run_git_args('log', f'--format={fmt}', '--date=short', '-5')
        log_all = log_r
    return jsonify({
        'vault_path': str(VAULT),
        'git_dir_exists': (VAULT / '.git').exists(),
        'log_stdout': log_r.stdout[:2000],
        'log_stderr': log_r.stderr[:500],
        'log_all_stdout': log_all.stdout[:2000],
        'branch': run_git('git branch --show-current').stdout.strip(),
        'status': run_git('git status --short').stdout[:500],
        'remote': mask_remote_url(run_git('git remote -v').stdout[:500]),
        'shallow': run_git_args('rev-parse', '--is-shallow-repository').stdout.strip(),
        'head': run_git_args('rev-parse', 'HEAD').stdout.strip(),
    })

# ── ログイン ─────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not AUTH_ENABLED:
        return redirect('/')
    error = ''
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == VAULT_PASSWORD:
            session.permanent = True  # 30日間クッキーを保持
            session['logged_in'] = True
            session['login_method'] = 'password'
            return redirect('/')
        error = 'パスワードが違います'
    return render_template('login.html', error=error, google_enabled=GOOGLE_AUTH_ENABLED)

@app.route('/auth/google')
def auth_google_start():
    if not GOOGLE_AUTH_ENABLED:
        return redirect('/login')
    state = secrets.token_urlsafe(24)
    session['oauth_state'] = state
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': external_url('/auth/google/callback'),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params))

@app.route('/auth/google/callback')
def auth_google_callback():
    if not GOOGLE_AUTH_ENABLED:
        return redirect('/login')
    if request.args.get('state') != session.get('oauth_state'):
        return render_template('login.html', error='Googleログインを確認できませんでした', google_enabled=True), 400
    code = request.args.get('code', '')
    if not code:
        return render_template('login.html', error='Googleログインがキャンセルされました', google_enabled=True), 400

    token_body = urllib.parse.urlencode({
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': external_url('/auth/google/callback'),
        'grant_type': 'authorization_code',
    }).encode('utf-8')
    token_req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=token_body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(token_req, timeout=15) as res:
            token_data = json.loads(res.read().decode('utf-8'))
        access_token = token_data.get('access_token', '')
        user_req = urllib.request.Request(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        with urllib.request.urlopen(user_req, timeout=15) as res:
            user = json.loads(res.read().decode('utf-8'))
    except Exception:
        return render_template('login.html', error='Googleログインに失敗しました', google_enabled=True), 400

    email = (user.get('email') or '').lower()
    if not user.get('email_verified') or email not in ALLOWED_GOOGLE_EMAILS:
        return render_template('login.html', error='このGoogleアカウントではログインできません', google_enabled=True), 403

    session.permanent = True
    session['logged_in'] = True
    session['login_method'] = 'google'
    session['user_email'] = email
    session.pop('oauth_state', None)
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ── 共有リンク ──────────────────────────────────────────────────────

def load_shares():
    if SHARES_FILE.exists():
        return json.loads(SHARES_FILE.read_text(encoding='utf-8'))
    return {}

def save_shares(data):
    SHARES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

@app.route('/api/share', methods=['POST'])
@login_required
def api_share_create():
    from datetime import datetime
    data = request.json
    path = data.get('path', '').strip()
    file_path = (VAULT / path).resolve()
    if not str(file_path).startswith(str(VAULT.resolve())) or not file_path.exists():
        return jsonify({'error': 'ファイルが見つかりません'}), 404
    shares = load_shares()
    # 既存トークンがあればそのまま返す
    for token, info in shares.items():
        if info.get('path') == path:
            return jsonify({'ok': True, 'token': token, 'existed': True})
    token = secrets.token_urlsafe(24)
    shares[token] = {'path': path, 'created_at': datetime.now().isoformat()}
    save_shares(shares)
    return jsonify({'ok': True, 'token': token, 'existed': False})

@app.route('/api/share', methods=['DELETE'])
@login_required
def api_share_delete():
    data = request.json
    token = data.get('token', '').strip()
    shares = load_shares()
    if token in shares:
        del shares[token]
        save_shares(shares)
    return jsonify({'ok': True})

@app.route('/api/share/info')
@login_required
def api_share_info():
    path = request.args.get('path', '').strip()
    shares = load_shares()
    for token, info in shares.items():
        if info.get('path') == path:
            return jsonify({'token': token, 'created_at': info.get('created_at', '')})
    return jsonify({'token': None})

@app.route('/share/<token>')
def share_view(token):
    shares = load_shares()
    if token not in shares:
        return render_template('share.html', error='このリンクは無効か、削除されています。',
                               content=None, title=None, images=[]), 404
    path = shares[token].get('path', '')
    file_path = (VAULT / path).resolve()
    if not str(file_path).startswith(str(VAULT.resolve())) or not file_path.exists():
        return render_template('share.html', error='ファイルが見つかりません。',
                               content=None, title=None, images=[]), 404
    content = file_path.read_text(encoding='utf-8', errors='replace')
    title = get_file_summary(file_path) or file_path.stem
    imgs = list_images(path)
    image_urls = [f'/share/{token}/_img/{img.name}' for img in imgs]
    return render_template('share.html', error=None, content=content,
                           title=title, token=token, path=path, images=image_urls)

@app.route('/share/<token>/_img/<filename>')
def share_image(token, filename):
    shares = load_shares()
    if token not in shares:
        return '', 404
    path = shares[token].get('path', '')
    img_dir = get_image_dir(path)
    safe_name = Path(filename).name
    img_path = (img_dir / safe_name).resolve()
    if not str(img_path).startswith(str(VAULT.resolve())) or not img_path.exists():
        return '', 404
    return send_file(img_path)

# ── ツールダウンロード ───────────────────────────────────────────────

@app.route('/tools/download/<path:filename>')
@login_required
def download_tool(filename):
    safe = (TOOLS_DIR / filename).resolve()
    if not str(safe).startswith(str(TOOLS_DIR.resolve())):
        return '', 403
    if not safe.exists():
        return '', 404
    return send_file(safe, as_attachment=True, download_name=Path(filename).name)

# ── Ping（スリープ防止用）────────────────────────────────────────────

@app.route('/ping')
def ping():
    return 'ok', 200


# ── QUARTET MUSIC（公開・認証不要）────────────────────────────────────

@app.route('/quartet/')
@app.route('/quartet/index.html')
def quartet_index():
    return send_from_directory('static/quartet', 'index.html')

@app.route('/quartet/<path:filepath>')
def quartet_static(filepath):
    return send_from_directory('static/quartet', filepath)

# ── メインページ ─────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ── 起動 ────────────────────────────────────────────────────────────

def open_browser():
    import time; time.sleep(1.0)
    webbrowser.open('http://127.0.0.1:5000')

init_git_remote()

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    port = int(os.environ.get('PORT', '5000'))
    print('=' * 50)
    print('  Prompt Vault 起動中...')
    print(f'  ブラウザが開きます: http://127.0.0.1:{port}')
    print('  終了するには Ctrl+C を押してください')
    print('=' * 50)
    app.run(debug=False, host='0.0.0.0', port=port)

"""
Prompt Vault - プロンプト管理Webアプリ
起動: python app.py  または  start.bat をダブルクリック
"""
import json
import os
import subprocess
import webbrowser
import threading
import secrets
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session, redirect, url_for

VAULT = Path(__file__).parent
CONFIG_FILE = VAULT / '.config.json'
IGNORE_DIRS = {'.git', '__pycache__', 'templates', 'static', 'node_modules', '.venv', 'venv', '.env'}
IGNORE_FILES = {'app.py', 'pm.py', '.gitignore', 'start.bat', 'start.sh'}

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

# ── ユーティリティ ──────────────────────────────────────────────────

def run_git(cmd):
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        encoding='utf-8', errors='replace', cwd=str(VAULT)
    )

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
    """起動時にGitHub設定を自動復元する（クラウド環境用）
    環境変数 GITHUB_URL / GITHUB_TOKEN が設定されていれば
    .config.json がなくても自動で接続状態に復元する。
    """
    url   = os.environ.get('GITHUB_URL', '')
    token = os.environ.get('GITHUB_TOKEN', '')
    if not url:
        return  # 環境変数未設定 = ローカル環境 → 何もしない

    # .config.json が存在しない場合は環境変数から自動生成
    if not CONFIG_FILE.exists():
        save_config({'github_url': url, 'github_token': token})

    remote_url = build_remote_url(url, token)
    r = run_git('git remote')
    if 'origin' in r.stdout:
        run_git(f'git remote set-url origin "{remote_url}"')
    else:
        run_git(f'git remote add origin "{remote_url}"')

def build_remote_url(url, token):
    """PAT をURLに埋め込んでHTTPS認証を自動化する"""
    if not token or not url:
        return url
    url = url.strip()
    if url.startswith('https://'):
        url = url.replace('https://', f'https://{token}@', 1)
    return url

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
    return jsonify({'ok': True})

# ── API: ファイルツリー ──────────────────────────────────────────────

def build_tree(path, rel=''):
    """ディレクトリを再帰的にスキャンしてツリーを構築する（空フォルダも表示）"""
    items = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return items
    for item in entries:
        if item.name.startswith('.') and item.name not in {'.gitkeep'}:
            continue  # 隠しファイル・隠しディレクトリをスキップ
        item_rel = (rel + '/' + item.name).lstrip('/')
        if item.is_dir() and item.name not in IGNORE_DIRS:
            children = build_tree(item, item_rel)
            items.append({'name': item.name, 'type': 'folder', 'path': item_rel, 'children': children})
        elif item.is_file() and item.suffix == '.md' and item.name not in IGNORE_FILES:
            items.append({'name': item.name, 'type': 'file', 'path': item_rel})
    return items

@app.route('/api/files')
@login_required
def api_files():
    return jsonify(build_tree(VAULT))

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

# ── API: 新規ファイル作成 ────────────────────────────────────────────

@app.route('/api/new', methods=['POST'])
@login_required
def api_new():
    data = request.json
    folder = data.get('folder', '')
    name = data.get('name', '').strip()
    if not name.endswith('.md'):
        name += '.md'
    if folder:
        file_path = VAULT / folder / name
    else:
        file_path = VAULT / name
    if file_path.exists():
        return jsonify({'error': '同名のファイルが既に存在します'}), 400
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f'# {name.replace(".md","")}\n\n', encoding='utf-8')
    rel = str(file_path.relative_to(VAULT)).replace('\\', '/')
    return jsonify({'ok': True, 'path': rel})

# ── API: Gitコミット（保存） ─────────────────────────────────────────

@app.route('/api/commit', methods=['POST'])
@login_required
def api_commit():
    data = request.json
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'コメントを入力してください'}), 400

    r_status = run_git('git status --short')
    if not r_status.stdout.strip():
        return jsonify({'error': '変更がありません'}), 400

    run_git('git add -A')
    r = run_git(f'git commit -m "{message}"')
    if r.returncode != 0:
        return jsonify({'error': r.stderr}), 500

    h = run_git('git log -1 --format=%h').stdout.strip()
    return jsonify({'ok': True, 'hash': h, 'message': message})

# ── API: Git ステータス ──────────────────────────────────────────────

@app.route('/api/status')
@login_required
def api_status():
    r = run_git('git status --short')
    changes = []
    for line in r.stdout.strip().split('\n'):
        if line.strip():
            changes.append(line)
    return jsonify({'changes': changes})

# ── API: 履歴 ───────────────────────────────────────────────────────

@app.route('/api/history')
@login_required
def api_history():
    path = request.args.get('path', '')
    if path:
        cmd = f'git log --format=%H|%ad|%s --date=format:"%Y-%m-%d %H:%M" -- "{path}"'
    else:
        cmd = 'git log --format=%H|%ad|%s --date=format:"%Y-%m-%d %H:%M" -30'

    r = run_git(cmd)
    entries = []
    for line in r.stdout.strip().split('\n'):
        if '|' in line:
            parts = line.split('|', 2)
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
        cmd = f'git diff {v1} {v2} -- "{path}"'
    elif v1:
        cmd = f'git diff {v1} HEAD -- "{path}"'
    else:
        cmd = f'git diff HEAD -- "{path}"'

    r = run_git(cmd)
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
    # トークンはマスクして返す
    token = cfg.get('github_token', '')
    masked = token[:4] + '****' if len(token) > 4 else ('****' if token else '')
    return jsonify({'github_url': cfg.get('github_url', ''), 'token_masked': masked,
                    'has_token': bool(token)})

@app.route('/api/github/config', methods=['POST'])
@login_required
def api_github_config_post():
    data = request.json
    cfg = load_config()
    if 'github_url' in data:
        cfg['github_url'] = data['github_url'].strip()
    if 'github_token' in data and data['github_token']:
        cfg['github_token'] = data['github_token'].strip()
    save_config(cfg)

    # リモートを設定/更新
    url = cfg['github_url']
    token = cfg.get('github_token', '')
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
        # 初回pushの場合は --set-upstream が必要なこともある
        err = r.stderr + r.stdout
        return jsonify({'error': err}), 500
    return jsonify({'ok': True, 'message': f'GitHubに送信しました（{branch}ブランチ）'})

@app.route('/api/github/pull', methods=['POST'])
@login_required
def api_github_pull():
    cfg = load_config()
    if not cfg.get('github_url'):
        return jsonify({'error': 'GitHubの設定がありません'}), 400

    r = run_git('git pull')
    if r.returncode != 0:
        return jsonify({'error': r.stderr}), 500
    return jsonify({'ok': True, 'message': r.stdout.strip() or 'Pull完了'})

@app.route('/api/github/status')
@login_required
def api_github_status():
    cfg = load_config()
    connected = bool(cfg.get('github_url'))
    remote_info = ''
    if connected:
        r = run_git('git remote -v')
        remote_info = r.stdout.strip().split('\n')[0] if r.stdout.strip() else ''
    return jsonify({'connected': connected, 'remote': remote_info})

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
            return redirect('/')
        error = 'パスワードが違います'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

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
    print('=' * 50)
    print('  Prompt Vault 起動中...')
    print('  ブラウザが開きます: http://127.0.0.1:5000')
    print('  終了するには Ctrl+C を押してください')
    print('=' * 50)
    app.run(debug=False, port=5000)

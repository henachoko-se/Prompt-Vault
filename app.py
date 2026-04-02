"""
Prompt Vault - プロンプト管理Webアプリ
起動: python app.py  または  start.bat をダブルクリック
"""
import json
import os
import subprocess
import webbrowser
import threading
import re
from pathlib import Path
from flask import Flask, request, jsonify, render_template

VAULT = Path(__file__).parent
CONFIG_FILE = VAULT / '.config.json'
IGNORE_DIRS = {'.git', '__pycache__', 'templates', 'static', 'node_modules'}
IGNORE_FILES = {'app.py', 'pm.py', '.gitignore', 'start.bat', 'start.sh'}

app = Flask(__name__)

# ── ユーティリティ ──────────────────────────────────────────────────

def run_git(cmd):
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        encoding='utf-8', errors='replace', cwd=str(VAULT)
    )

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    return {'github_url': '', 'github_token': ''}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def build_remote_url(url, token):
    """PAT をURLに埋め込んでHTTPS認証を自動化する"""
    if not token or not url:
        return url
    url = url.strip()
    if url.startswith('https://'):
        url = url.replace('https://', f'https://{token}@', 1)
    return url

# ── API: ファイルツリー ──────────────────────────────────────────────

@app.route('/api/files')
def api_files():
    tree = []
    for item in sorted(VAULT.iterdir()):
        if item.is_dir() and item.name not in IGNORE_DIRS:
            files = sorted([
                f.name for f in item.glob('*.md')
            ])
            if files:
                tree.append({'folder': item.name, 'files': files})
        elif item.is_file() and item.suffix == '.md' and item.name not in IGNORE_FILES:
            tree.append({'folder': '', 'files': [item.name]})
    return jsonify(tree)

# ── API: ファイル内容 ────────────────────────────────────────────────

@app.route('/api/content')
def api_content():
    path = request.args.get('path', '')
    file_path = VAULT / path
    if not file_path.exists() or not str(file_path).startswith(str(VAULT)):
        return jsonify({'error': 'ファイルが見つかりません'}), 404
    return jsonify({'content': file_path.read_text(encoding='utf-8', errors='replace')})

@app.route('/api/content', methods=['POST'])
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

# ── API: 新規ファイル作成 ────────────────────────────────────────────

@app.route('/api/new', methods=['POST'])
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
def api_status():
    r = run_git('git status --short')
    changes = []
    for line in r.stdout.strip().split('\n'):
        if line.strip():
            changes.append(line)
    return jsonify({'changes': changes})

# ── API: 履歴 ───────────────────────────────────────────────────────

@app.route('/api/history')
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
def api_restore_preview():
    path = request.args.get('path', '')
    version = request.args.get('version', '')
    r = run_git(f'git show {version}:"{path}"')
    if r.returncode != 0:
        return jsonify({'error': 'バージョンが見つかりません'}), 404
    return jsonify({'content': r.stdout})

@app.route('/api/restore', methods=['POST'])
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
def api_github_config_get():
    cfg = load_config()
    # トークンはマスクして返す
    token = cfg.get('github_token', '')
    masked = token[:4] + '****' if len(token) > 4 else ('****' if token else '')
    return jsonify({'github_url': cfg.get('github_url', ''), 'token_masked': masked,
                    'has_token': bool(token)})

@app.route('/api/github/config', methods=['POST'])
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
def api_github_pull():
    cfg = load_config()
    if not cfg.get('github_url'):
        return jsonify({'error': 'GitHubの設定がありません'}), 400

    r = run_git('git pull')
    if r.returncode != 0:
        return jsonify({'error': r.stderr}), 500
    return jsonify({'ok': True, 'message': r.stdout.strip() or 'Pull完了'})

@app.route('/api/github/status')
def api_github_status():
    cfg = load_config()
    connected = bool(cfg.get('github_url'))
    remote_info = ''
    if connected:
        r = run_git('git remote -v')
        remote_info = r.stdout.strip().split('\n')[0] if r.stdout.strip() else ''
    return jsonify({'connected': connected, 'remote': remote_info})

# ── メインページ ─────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── 起動 ────────────────────────────────────────────────────────────

def open_browser():
    import time; time.sleep(1.0)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    print('=' * 50)
    print('  Prompt Vault 起動中...')
    print('  ブラウザが開きます: http://127.0.0.1:5000')
    print('  終了するには Ctrl+C を押してください')
    print('=' * 50)
    app.run(debug=False, port=5000)

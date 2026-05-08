# Prompt Vault - Codex引継ぎ文書

## プロジェクト概要

**Prompt Vault** は、AIプロンプト（`.md` ファイル）をブラウザ上で管理・編集・バージョン管理するWebアプリ。
ローカル（Windows PC）とクラウド（Render.com）の両方で動作する。

---

## 技術スタック

| 項目 | 内容 |
|------|------|
| バックエンド | Python + Flask |
| フロントエンド | Vanilla JS + HTML/CSS（ビルドツールなし） |
| バージョン管理 | Git（ローカルのVaultフォルダがそのままgitリポジトリ） |
| クラウドホスティング | Render.com（`gunicorn app:app`） |
| GitHubリポジトリ | `https://github.com/henachoko-se/Prompt-Vault` |
| 依存パッケージ | `flask>=3.0.0`, `gunicorn>=21.2.0`（`requirements.txt`） |

---

## ファイル構成

```
prompt_vault/
├── app.py                  ← Flaskアプリ本体（バックエンド全体）
├── pm.py                   ← CLIツール（git操作・プロンプト検索）
├── start.bat               ← ローカル起動用バッチ（python app.py を実行）
├── render.yaml             ← Render.comデプロイ設定
├── requirements.txt        ← pip依存パッケージ（flask, gunicorn のみ）
├── CLAUDE.md               ← Claude Code向けルール（全体共通）
├── .config.json            ← GitHubのURL・PAT・secret_keyを保存（.gitignore済）
├── .folder-info.json       ← フォルダの表示名を管理（Prompt Vault UIで使用）
├── .gitignore              ← .config.json / __pycache__ / .DS_Store 等を除外
├── templates/
│   ├── index.html          ← メインUI（SPA、全JS・CSSをここに内包）
│   ├── login.html          ← パスワードログイン画面
│   └── share.html          ← 共有リンク閲覧画面（認証不要）
├── static/                 ← 現状ほぼ空（将来の静的ファイル用）
├── _images/                ← 各プロンプトに紐づく画像ファイルの保存先
│   └── [フォルダ名]/[ファイル名（拡張子なし）]/画像.png ...
│
├── team_building_science/  ← コンテンツフォルダ（チームビルディングの科学）
├── family_building_science/← コンテンツフォルダ（家庭ビルディングの科学）
├── ai_asobi_kenkyusho/     ← コンテンツフォルダ（AIあそび研究所）
├── threads_prompts/        ← コンテンツフォルダ（Threads投稿用）
└── ...（その他コンテンツフォルダ）
```

---

## app.py の構造

### 定数・設定

```python
VAULT       = Path(__file__).parent          # Vaultルートディレクトリ
CONFIG_FILE = VAULT / '.config.json'         # GitHub設定ファイル
SHARES_FILE = VAULT / '.shares.json'         # 共有リンク管理
IMAGES_DIR  = VAULT / '_images'             # 画像保存ディレクトリ
IGNORE_DIRS = {'.git', '__pycache__', 'templates', 'static', ...}
IGNORE_FILES = {'app.py', 'pm.py', ...}
IMAGE_EXTS  = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
```

### 認証

- 環境変数 `VAULT_PASSWORD` が設定されている場合のみ認証有効（クラウド用）
- ローカル起動（環境変数なし）は認証スキップ
- セッションは30日間維持
- `@login_required` デコレータで各エンドポイントを保護

### ファイルツリーの仕組み

- `build_tree()` が VAULT 配下を再帰スキャン
- **`.md` ファイルのみ**表示（`.yaml` 等は表示されない）
- `.` 始まりのファイル・フォルダはスキップ（`.gitkeep` を除く）
- `IGNORE_DIRS` に含まれるフォルダはスキップ
- ファイルの「タイトル」は先頭の `# H1` から取得

### `.folder-info.json` の役割

- フォルダごとの「説明文（表示名）」を管理するJSONファイル
- UIでフォルダ名の下に表示される説明テキスト
- **フォルダの表示/非表示のフィルターではない**（フォルダは全て表示される）
- 新しいフォルダをUIに表示させるには、このファイルへの追記は不要

```json
{
  "team_building_science": "チームビルディングの科学",
  "family_building_science": "家庭ビルディングの科学",
  "ai_asobi_kenkyusho": "AIあそび研究所"
}
```

---

## APIエンドポイント一覧

### ファイル操作

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/files?sort=name_asc` | ファイルツリー取得（`.md`のみ） |
| GET | `/api/content?path=xxx` | ファイル内容取得 |
| POST | `/api/content` | ファイル保存（`{path, content}`） |
| POST | `/api/new` | 新規ファイル作成（`{folder, name}`） |
| POST | `/api/mkdir` | フォルダ作成（`{path}`） |
| POST | `/api/rename` | 名前変更（`{old_path, new_name}`） |
| POST | `/api/delete` | 削除（`{path}`） |
| POST | `/api/move` | 移動（`{src, dest_folder}`） |

### Git操作

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/status` | 未コミット変更の確認 |
| POST | `/api/commit` | コミット（`{message}`、空なら自動生成） |
| GET | `/api/history?path=xxx` | 履歴一覧（省略で全体50件） |
| GET | `/api/diff?path=xxx&v1=xxx` | 差分取得 |
| GET | `/api/restore?path=xxx&version=xxx` | 過去バージョンプレビュー |
| POST | `/api/restore` | 過去バージョンに戻す |

### GitHub連携

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/github/status` | 接続状態確認 |
| GET/POST | `/api/github/config` | URL・PAT設定 |
| POST | `/api/github/push` | GitHub へ Push |
| POST | `/api/github/pull` | GitHub から Pull |

### 画像

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/images?path=xxx` | プロンプトに紐づく画像一覧 |
| GET | `/api/images/index` | 全プロンプトのサムネイル取得 |
| POST | `/api/images/upload` | 画像アップロード |
| POST | `/api/images/delete` | 画像削除 |

### フォルダ説明

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/folder-info` | `.folder-info.json` 取得 |
| POST | `/api/folder-info` | フォルダ説明の更新（自動コミットあり） |

### その他

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET/POST | `/login` | ログイン |
| GET | `/logout` | ログアウト |
| POST | `/api/share` | 共有リンク発行 |
| GET | `/share/<token>` | 共有リンク閲覧（認証不要） |
| GET | `/ping` | スリープ防止用ヘルスチェック |
| GET | `/api/debug/git` | git状態診断 |

---

## ローカル開発のセットアップ

```bash
cd C:\Users\henac\prompt_vault

# 依存パッケージインストール
pip install -r requirements.txt

# 起動（ブラウザが自動で開く）
python app.py
# または
start.bat をダブルクリック

# アクセス
http://127.0.0.1:5000
```

ローカル起動時は `VAULT_PASSWORD` 環境変数が未設定のため**認証スキップ**。

---

## Renderデプロイ

- `render.yaml` に設定済み
- 環境変数は Render ダッシュボードで設定：
  - `VAULT_PASSWORD` : 手動設定（ログインパスワード）
  - `SECRET_KEY` : 自動生成
  - `GITHUB_URL` : GitHubリポジトリURL
  - `GITHUB_TOKEN` : GitHub PAT（`.config.json` に保存）

---

## 重要な設計ルール・注意点

### `.md` ファイルのみ対象
- `build_tree()` は `.md` ファイルのみ返す
- `.yaml`, `.json` 等は UIに表示されない
- 画像生成プロンプト（YAML）は `.md` でラップして保存すること

### H1タイトル必須
- 全 `.md` ファイルの先頭行は `# タイトル` が必須
- サイドバーのファイル名表示に使われる
- タイトルがないとファイル名（拡張子付き）がそのまま表示される

### セキュリティ
- パストラバーサル対策：全ファイル操作で VAULT ルート外へのアクセスを拒否
- `.config.json` は `.gitignore` 済み（GitHubに公開されない）
- PAT はURLに埋め込んで `git remote set-url` で認証

### クラウド vs ローカルの差異
- クラウド（Render）: Pull しないとGitHubの最新が反映されない
- ローカル: ファイル作成と同時にUIに反映（ページリロードで確認）

### フォルダ構造
- コンテンツフォルダは直下に自由に作成可能
- `IGNORE_DIRS` に含まれるフォルダ名は使用不可：
  `.git`, `__pycache__`, `templates`, `static`, `node_modules`, `.venv`, `venv`, `.env`, `_images`

---

## 現在のコンテンツフォルダ

| フォルダ | 内容 |
|---------|------|
| `team_building_science/` | チームビルディングの科学（Vol.76〜、ツール類） |
| `family_building_science/` | 家庭ビルディングの科学 |
| `ai_asobi_kenkyusho/` | AIあそび研究所（記事・漫画プロンプト） |
| `threads_prompts/` | Threads投稿用プロンプト |
| `character_goods/` | キャラクターグッズ販売用 |
| `ao_fullremote_note/` | フルリモートnote関連 |

---

## よくある作業パターン

### 新しいコンテンツフォルダを追加する
1. フォルダを作成して `.md` ファイルを入れる
2. `.folder-info.json` に `"フォルダ名": "表示説明"` を追記（任意）
3. `git add`, `git commit`, `git push`
4. Render側で「⬇ Pull」ボタンを押す

### 画像をプロンプトに紐づける
- `_images/[フォルダ名]/[mdファイル名（拡張子なし）]/` に画像を置く
- UIからアップロードも可能

### 共有リンクを発行する
- UIでファイルを開き、共有ボタンから発行
- `/share/<token>` で認証なし閲覧可能
- トークンは `.shares.json` で管理

---

## 関連ファイル（コンテンツ側）

| ファイル | 役割 |
|---------|------|
| `CLAUDE.md` | Claude Code向けルール（全体） |
| `team_building_science/CLAUDE.md` | チームビルディング記事作成ルール |
| `team_building_science/persona_guideline.md` | 記事のペルソナ・トンマナ定義 |
| `team_building_science/_tools/` | 記事作成・QA用プロンプトツール群 |

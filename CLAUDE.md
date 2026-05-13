# Prompt Vault - 全体ルール

このファイルはClaude Codeが参照する全体共通ルールです。
サブフォルダに独自の `CLAUDE.md` がある場合は、そちらも合わせて参照してください。

---

## 最重要: Cloud Run 移行後の運用前提

Prompt Vault は以前 Render.com で運用していましたが、現在の本番環境は **Google Cloud Run** です。
Claude Code は Render 前提で判断しないでください。

- 本番ホスティング: Google Cloud Run
- GCPプロジェクト: `meeting-opportunity-agent`
- リージョン: `asia-northeast1`
- Cloud Runサービス名: `prompt-vault`
- GitHubリポジトリ: `https://github.com/henachoko-se/Prompt-Vault`
- デプロイスクリプト: `C:\Users\henac\prompt_vault\deploy_cloud_run.ps1`
- Cloud Runの認証情報: Google Cloud Secret Manager で管理
- GitHub PATのSecret名: `prompt-vault-github-token`

### Claude Codeへの判断ルール

- `render.yaml` や Render 関連の古い記述が残っていても、本番運用の正は Cloud Run とみなす
- GitHubトークンを `.config.json` やPrompt Vaultの画面内設定へ保存しない
- GitHubトークンを更新する場合は Secret Manager の `prompt-vault-github-token` に新しいバージョンを追加し、その後 `deploy_cloud_run.ps1` を再実行する
- Cloud Runのファイルシステムは永続ではないため、Prompt Vault上で編集した内容は「保存」でコミットし、「Push」でGitHubへ送る
- Cloud Runへのデプロイ後は、必要に応じてPrompt Vault画面で「Pull」してGitHub側の最新状態を取得する
- Cloud Runでは `.git` がデプロイ対象から除外されるため、アプリ起動時にGitHubの履歴へ接続し直す設計になっている

詳しい移行後の説明は `CLOUD_RUN_CLAUDE_GUIDE.md` を参照してください。

---

## ファイル作成ルール

### H1タイトルの付与（必須）

**すべての `.md` ファイルの先頭行には `# タイトル` を必ず記載すること。**

- タイトルは**日本語**で、そのファイルの内容を一言で表すものにする
- ユーザーから渡されたプロンプトにH1がない場合は、内容を読んで適切な日本語タイトルを自動的に付与する
- 理由：サイドバーのファイル一覧でH1がそのまま概要として表示されるため、タイトルがないとファイルの中身が一目で分からなくなる

**例：**
```
# アイドルサイン作成プロンプト   ← これがサイドバーに表示される
```

**タイトルの付け方の目安：**
- プロンプト系 → `〇〇を△△するプロンプト`
- 記事系 → 記事タイトルをそのまま
- ログ・レポート系 → `〇〇 ××ログ / レポート`
- 設定・ガイドライン系 → 内容を端的に表す名詞句

---

## フォルダ構成

```
threads_prompts/    Threads投稿用プロンプトのアーカイブ
family_building_science/  家庭ビルディングの科学マガジン関連
team_building_science/    チームビルディングの科学マガジン関連
team_building/            チームビルディング関連プロンプト
character_goods/          キャラクターグッズ関連
```

# Prompt Vault - 全体ルール

このファイルはClaude Codeが参照する全体共通ルールです。
サブフォルダに独自の `CLAUDE.md` がある場合は、そちらも合わせて参照してください。

---

## シリーズ横断制作ルール

`チームビルディングの科学`、`AIあそび研究所`、`家庭ビルディングの科学` の記事・図解・画像生成・SNS展開では、必ず `series_base_rules.md` も参照してください。

特に以下は3シリーズ共通の基本ルールです。

- 画像は「読める」だけでなく、シリーズらしさと保存したくなる見た目を持たせる
- へなP、ぶかP、AIあそび研究所キャラ、へなP台所版の使い分けを守る
- 華やかさ・文字量・図解密度を別パラメータとして扱う
- note本文はスマホ閲覧を優先し、原則として縦長比率を検討する
- AIあそび研究所以外では、ChatGPT・Claude・Gemini風キャラを勝手に追加しない
- 生成画像はリポジトリ内だけでなく、指定のOneDrive実フォルダにも整理する

Codexでこれらのシリーズを制作・検証する場合は、`.codex/agents/` の子エージェント定義を参照してください。
記事チェック、プロンプトQA、図解生成、生成画像チェックは役割を分け、メインエージェントが結果を統合して最終判断します。

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
- Codex/Claude Codeがローカルで `.md` コンテンツを新規作成・更新した場合、**ローカル保存だけで完了扱いにしない**。ユーザーが明示しなくても、原則として該当ファイルを `git add` → `git commit` → `git push origin master` し、クラウド版Prompt Vaultで表示される必要があるコンテンツはCloud Runへ再デプロイして、ブラウザ更新後に表示される状態まで対応する
- 上記反映作業では、`git status --short` で対象差分を確認し、無関係な既存変更は触らない。pushがリモート先行で拒否された場合は、作成したコミットを保ったまま `git pull --rebase origin master` で取り込んでから再pushする
- `gcloud` がSSL証明書エラーで止まる場合は、一時対応を行ってもよいが、最後に変更したgcloud設定を元へ戻す

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

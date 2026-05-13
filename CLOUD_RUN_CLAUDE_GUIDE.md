# Prompt Vault Cloud Run運用ガイド

この資料は、Claude CodeがPrompt Vaultを正しく扱うための運用メモです。
Prompt Vaultは以前Render.comで動いていましたが、現在の本番環境はGoogle Cloud Runです。

## 現在の本番構成

| 項目 | 値 |
|---|---|
| ホスティング | Google Cloud Run |
| GCPプロジェクト | `meeting-opportunity-agent` |
| リージョン | `asia-northeast1` |
| Cloud Runサービス名 | `prompt-vault` |
| GitHubリポジトリ | `https://github.com/henachoko-se/Prompt-Vault` |
| デプロイスクリプト | `C:\Users\henac\prompt_vault\deploy_cloud_run.ps1` |
| 主要URL | `https://prompt-vault-hvvjnok6mq-an.a.run.app` |
| Cloud RunサービスURL | `https://prompt-vault-426912242982.asia-northeast1.run.app` |

## Claude Codeが必ず守ること

1. Render.comは旧環境として扱う
2. 本番の修正・調査・デプロイはCloud Run前提で考える
3. GitHub PATを `.config.json` やPrompt Vaultの画面内設定へ保存しない
4. GitHub PATはGoogle Cloud Secret Managerの `prompt-vault-github-token` で管理する
5. Secretを更新したら、Cloud Runへ反映するため `deploy_cloud_run.ps1` を再実行する
6. Cloud Runのファイルシステムは永続ではないため、Prompt Vaultで編集した内容は必ずGitHubへPushする

## Secret Managerで管理する値

| Secret名 | 用途 |
|---|---|
| `prompt-vault-password` | Prompt Vaultのログインパスワード |
| `prompt-vault-github-token` | GitHubへPull/PushするためのPAT |
| `prompt-vault-secret-key` | Flaskセッション用の秘密鍵 |
| `google-client-id` | Googleログイン用OAuthクライアントID |
| `google-client-secret` | Googleログイン用OAuthクライアントシークレット |

GitHub PATは、`henachoko-se/Prompt-Vault` に対して書き込み可能な権限が必要です。
Fine-grained tokenの場合は `Contents: Read and write` を付けます。

## Cloud Runデプロイ

Claude CodeがCloud Runへ反映する場合は、次を実行します。

```powershell
cd C:\Users\henac\prompt_vault
.\deploy_cloud_run.ps1
```

このスクリプトは以下を行います。

- GCPプロジェクトを `meeting-opportunity-agent` に設定
- 必要なSecretへのアクセス権をCloud Run実行サービスアカウントへ付与
- `prompt-vault` サービスをCloud Runへデプロイ
- `GITHUB_TOKEN` などをSecret Managerから環境変数として注入
- Cloud RunのCPU boostを有効化

## GitHub連携の考え方

Prompt VaultはGitHubを永続ストレージとして使います。
Cloud Runのコンテナ内ファイルシステムは一時的なので、Cloud Run上で編集した内容を残すには次の流れが必要です。

1. Prompt Vault画面で編集する
2. 画面下部の「保存」でgit commitする
3. 「Push」でGitHubへ送る

別の環境でGitHub側が更新された場合は、必要に応じてPrompt Vault画面で「Pull」します。

## `.git` と履歴復元

Cloud Runへのデプロイでは `.gcloudignore` により `.git` は送られません。
そのため、Prompt Vaultは起動時に次の処理でGitHub履歴へ接続します。

- `git init`
- `origin` を `GITHUB_URL` に設定
- `GITHUB_TOKEN` を使ってGitHubへ認証
- `GITHUB_BRANCH`、通常は `master`、をfetch
- Cloud Runの作業ツリーをGitHub履歴へ接続

この設計により、Cloud Run上でも履歴・差分・Pull・Pushが動きます。

## トークン設定で間違えやすい点

Prompt Vaultの画面内にPATを保存する運用は廃止しました。
現在はSecret Managerのみを正とします。

間違い:

```text
Prompt Vault画面のGitHub設定にPATを入力する
.config.json に github_token を保存する
Renderの環境変数を更新する
```

正しい対応:

```text
Secret Manager の prompt-vault-github-token に新しいバージョンを追加する
deploy_cloud_run.ps1 を実行してCloud Runへ反映する
```

## Claude Code向け認識文

以下の文をClaude Codeの作業開始時の前提として扱います。

```text
このPrompt Vaultリポジトリは、旧Render運用からGoogle Cloud Run運用へ移行済みです。
本番はCloud Runサービス prompt-vault、GCPプロジェクト meeting-opportunity-agent、リージョン asia-northeast1 です。
GitHub PATはPrompt Vault内や .config.json ではなく、Google Cloud Secret Manager の prompt-vault-github-token で管理します。
修正を本番へ反映する場合は C:\Users\henac\prompt_vault\deploy_cloud_run.ps1 を実行します。
Cloud Runのファイルシステムは永続ではないため、Prompt Vault上の編集は保存でcommitし、PushでGitHubへ送る必要があります。
Render関連の古い資料や render.yaml が残っていても、本番運用判断ではCloud Runを正としてください。
```


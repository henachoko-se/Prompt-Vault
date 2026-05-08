# Prompt Vault を Cloud Run に移す手順

費用を抑えるため、最小インスタンスは `0` にします。

## 前提

- GCPプロジェクト: `meeting-opportunity-agent`
- リージョン: `asia-northeast1`
- Cloud Runサービス名: `prompt-vault`
- GitHubリポジトリ: `https://github.com/henachoko-se/Prompt-Vault`

Cloud Runのファイルシステムは永続ではありません。Prompt Vaultで編集した内容は、必ずUIの「保存」でコミットし、「Push」でGitHubへ送ってください。

## 初回だけ有効化

```powershell
gcloud config set project meeting-opportunity-agent
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

## Secret Manager に値を入れる

既に同名Secretがある場合は作成コマンドを飛ばして、`versions add` だけ実行してください。

```powershell
gcloud secrets create prompt-vault-password --replication-policy=automatic
gcloud secrets versions add prompt-vault-password --data-file=-

gcloud secrets create prompt-vault-github-token --replication-policy=automatic
gcloud secrets versions add prompt-vault-github-token --data-file=-

gcloud secrets create prompt-vault-secret-key --replication-policy=automatic
gcloud secrets versions add prompt-vault-secret-key --data-file=-
```

入力する値:

- `prompt-vault-password`: Cloud版Prompt Vaultのログインパスワード
- `prompt-vault-github-token`: GitHub PAT
- `prompt-vault-secret-key`: 任意の長いランダム文字列
- `google-client-id` / `google-client-secret`: Googleログイン用OAuthクライアント。既存Secretを流用します。

Google OAuthクライアントの承認済みリダイレクトURIに次を追加してください。

```text
https://prompt-vault-hvvjnok6mq-an.a.run.app/auth/google/callback
```

## デプロイ

`C:\Users\henac\prompt_vault` で実行します。

```powershell
gcloud run deploy prompt-vault `
  --source . `
  --region asia-northeast1 `
  --allow-unauthenticated `
  --min-instances 0 `
  --max-instances 2 `
  --memory 512Mi `
  --cpu 1 `
  --set-env-vars GITHUB_URL=https://github.com/henachoko-se/Prompt-Vault,GITHUB_BRANCH=master,PUBLIC_BASE_URL=https://prompt-vault-hvvjnok6mq-an.a.run.app,ALLOWED_GOOGLE_EMAILS=henachoko.se.pm@gmail.com `
  --set-secrets VAULT_PASSWORD=prompt-vault-password:latest,GITHUB_TOKEN=prompt-vault-github-token:latest,SECRET_KEY=prompt-vault-secret-key:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest
```

## 起動を少し速くする設定

```powershell
gcloud run services update prompt-vault `
  --region asia-northeast1 `
  --cpu-boost
```

## デプロイ後の確認

```powershell
gcloud run services describe prompt-vault --region asia-northeast1 --format "value(status.url)"
```

表示されたURLにアクセスします。Cloud版は `VAULT_PASSWORD` があるのでログイン画面が出ます。

## 運用メモ

- コスト優先: `--min-instances 0`
- 起動が遅いと感じたら: `--min-instances 1` に変更
- 低利用なら無料枠内に収まる可能性が高い
- 編集後は「保存」→「Push」を忘れない
- 別端末やCloud側で更新した後は、必要に応じて「Pull」

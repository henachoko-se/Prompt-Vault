$ErrorActionPreference = "Stop"

$Project = "meeting-opportunity-agent"
$Region = "asia-northeast1"
$Service = "prompt-vault"
$GithubUrl = "https://github.com/henachoko-se/Prompt-Vault"
$GithubBranch = "master"
$Gcloud = "C:\Users\henac\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$ServiceAccount = "426912242982-compute@developer.gserviceaccount.com"

& $Gcloud config set project $Project

foreach ($Secret in @("prompt-vault-password", "prompt-vault-github-token", "prompt-vault-secret-key", "google-client-id", "google-client-secret")) {
  & $Gcloud secrets add-iam-policy-binding $Secret `
    --member "serviceAccount:$ServiceAccount" `
    --role "roles/secretmanager.secretAccessor" `
    --project $Project | Out-Null
}

& $Gcloud run deploy $Service `
  --source . `
  --clear-base-image `
  --region $Region `
  --allow-unauthenticated `
  --min-instances 0 `
  --max-instances 2 `
  --memory 512Mi `
  --cpu 1 `
  --set-env-vars "GITHUB_URL=$GithubUrl,GITHUB_BRANCH=$GithubBranch,PUBLIC_BASE_URL=https://prompt-vault-hvvjnok6mq-an.a.run.app,ALLOWED_GOOGLE_EMAILS=henachoko.se.pm@gmail.com" `
  --set-secrets "VAULT_PASSWORD=prompt-vault-password:latest,GITHUB_TOKEN=prompt-vault-github-token:latest,SECRET_KEY=prompt-vault-secret-key:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest"

& $Gcloud run services update $Service `
  --region $Region `
  --cpu-boost

$Url = & $Gcloud run services describe $Service --region $Region --format "value(status.url)"
Write-Host ""
Write-Host "Prompt Vault deployed:" $Url

# Meeting Opportunity Agent MVP

## 概要

会議音声またはテキストから、商談中の課題・提案チャンス・次アクションをリアルタイムに整理するMVPアプリ。
Googleログイン、Gemini API、Cloud Run、Secret Manager、Firestoreログ保存に対応。

## アプリURL

- Cloud Run: https://meeting-opportunity-agent-hvvjnok6mq-an.a.run.app
- 代替URL: https://meeting-opportunity-agent-426912242982.asia-northeast1.run.app

## GitHub

- Repository: https://github.com/henachoko-se/meeting-opportunity-agent
- Backup tag: backup-2026-05-11-mvp
- Backup commit: b055ff3 Backup current MVP version

## 主な機能

- Googleログイン認証
- 管理者画面でログイン履歴を確認
- Firestoreにログイン履歴を保存
- TTLでログイン履歴を自動削除
- 録音中の経過秒数表示
- 区間解析の失敗時再送
- 会議タイトル入力
- 会議の前提・文脈入力
- 会議中断/再開ログ
- 結果履歴
- 最終提案メモのMarkdownコピー/保存
- 会議内容を整理した議事録作成
- スマホ向けレイアウト調整

## Geminiモデル設定

- 区間解析: gemini-3.1-flash-lite-preview
- 最終提案メモ: 画面で選択したモデル
- 議事録作成: 画面で選択したモデル

## GCP構成

- Project ID: meeting-opportunity-agent
- Project number: 426912242982
- Region: asia-northeast1
- Cloud Run service: meeting-opportunity-agent
- Secret Manager:
  - gemini-api-key
  - google-client-id
  - google-client-secret
  - meeting-agent-access-token
- Firestore collection:
  - login_events

## セキュリティメモ

- Gemini APIキーは画面・ファイルに保存しない
- APIキーはSecret ManagerからCloud Runへ注入
- 会議音声・会議本文はFirestoreへ保存しない
- Firestoreに保存するのはログイン履歴のみ
- 管理画面は管理者メールのみアクセス可能
- 露出したAPIキーはローテーション推奨

## 次に検討すること

- 会議終了後の共有リンク
- 顧客別・案件別の議事録保存
- ログ保存期間の運用ルール整備
- 商用利用時のOAuth確認・プライバシーポリシー整備
- 利用者別の権限管理

# Vol.104 画像生成ログ

## 生成方針

- 図解しおりPro版の判断ロジックをベースに、記事内の図解挿入箇所を先に特定する
- チームビルディングの科学なので、画像には原則へなPを使う
- note本文用図解は、スマホ可読性を優先して4:5など縦長を基本にする
- AIは採否判断者ではなく、チャット画面・チェックリスト・補助UIとして表現する

## 参照キャラクター

`C:\Users\henac\OneDrive\ドキュメント\AI\へなちょこPM\へなP.jpg`

## 生成済み画像

`zukaishiori_full_test_20260611/` に、図解しおりフルパイプラインテストで生成した候補画像を保存済み。

## 最終採用画像（2026-06-11）

| 用途 | リポジトリ内ファイル | 外部保存ファイル |
|---|---|---|
| noteヘッダー | `vol104_header.png` | `vol104_header.png` |
| 図解① 公正採用ガードレール | `zukaishiori_full_test_20260611/03_fair_hiring_guardrails.png` | `vol104_01_guardrails.png` |
| 図解② 面接準備フロー | `zukaishiori_full_test_20260611/04_ai_prep_flow.png` | `vol104_02_prep_flow.png` |

## 最終画像の外部保存先

`C:\Users\henac\OneDrive\ドキュメント\AI\へなちょこPM\チームビルディングの科学`

## 採用判断メモ

- `vol104_header.png` は、へなP入りの1.91:1ヘッダーに日本語コピーを正確に合成した正式版。
- `03_fair_hiring_guardrails.png` は現版採用。ただし画像内にシリーズ名・Vol番号・追加コピーが入ったため、再生成時は `infographic_guardrails.md` の禁止事項に従って抑制する。
- `04_ai_prep_flow.png` は現版採用。再生成時は下部帯を「採否判断は人間が行う」に寄せる。
- 推奨候補の `02_brain_tasks.png`、任意候補の `07_pm_case_questions.png` は比較用生成フォルダに残し、本文挿入画像には含めない。

## QA観点

- へなPが参照画像に近い
- 日本語文字が読める
- スマホ本文で見やすい
- AIが採否判断しているように見えない
- 候補者の個人情報が読める形で出ていない
- 記事本文の該当箇所と意味がズレていない

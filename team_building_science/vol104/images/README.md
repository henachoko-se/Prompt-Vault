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

## 最終採用画像（2026-06-11更新）

| 用途 | リポジトリ内ファイル | 外部保存ファイル |
|---|---|---|
| noteヘッダー | `vol104_header.png` | `vol104_header.png` |
| 図解① 面接前の脳内タスク | `zukaishiori_full_test_20260611/02_brain_tasks.png` | `vol104_01_brain_tasks.png` |
| 図解② 公正採用ガードレール | `vol104_02_guardrails.png` | `vol104_02_guardrails.png` |
| 図解③ 面接準備フロー | `zukaishiori_full_test_20260611/04_ai_prep_flow.png` | `vol104_03_prep_flow.png` |
| 図解④ PM経歴の確認点分解 | `zukaishiori_full_test_20260611/07_pm_case_questions.png` | `vol104_04_pm_questions.png` |
| 図解⑤ 使う前チェック | `zukaishiori_full_test_20260611/08_before_use_check.png` | `vol104_05_before_use_check.png` |

## 最終画像の外部保存先

`C:\Users\henac\OneDrive\ドキュメント\AI\へなちょこPM\チームビルディングの科学`

## 採用判断メモ

- `vol104_header.png` は画像生成版を採用。後加工でタイトル帯を貼る運用はしない。`header_image.md` の生成プロンプトで、noteタイトルと同じ訴求の強いヘッダーを作る。
- `02_brain_tasks.png` は現版採用。科学的メカニズムの直後に置き、面接前の認知負荷を見える化する。
- `vol104_02_guardrails.png` は再生成版を採用。旧候補 `zukaishiori_full_test_20260611/03_fair_hiring_guardrails.png` にあったシリーズ名・Vol番号を除外した正式版。
- `04_ai_prep_flow.png` は現版採用。再生成時は下部帯を「採否判断は人間が行う」に寄せる。
- `07_pm_case_questions.png` は現版採用。実例セクションで「PM経験ありそう」で終わらせない意図を補強する。
- `08_before_use_check.png` は現版採用。プロンプトリンク前に置き、応募者情報の扱いを注意喚起する。
- `01_opening_worry.png` はヘッダーと役割が重なるため不採用。
- `03_fair_hiring_guardrails.png` はシリーズ名・Vol番号が入っているため不採用。正式版は `vol104_02_guardrails.png`。
- `05_three_benefits.png` は採用領域では訴求が軽く見えるため不採用。
- `06_bias_to_structure.png` は「合格かも？」が採否判断に寄って見えるため不採用。

## QA観点

- へなPが参照画像に近い
- 日本語文字が読める
- スマホ本文で見やすい
- AIが採否判断しているように見えない
- 候補者の個人情報が読める形で出ていない
- 記事本文の該当箇所と意味がズレていない

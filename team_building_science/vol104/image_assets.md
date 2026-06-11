# Vol.104 画像アセット一覧

## 保存先ルール

記事内で使う最終画像は、以下のフォルダにも保存する。

`C:\Users\henac\OneDrive\ドキュメント\AI\へなちょこPM\チームビルディングの科学`

チームビルディングの科学の画像は、原則として `へなP` を参照キャラクターとして使う。

参照画像:

`C:\Users\henac\OneDrive\ドキュメント\AI\へなちょこPM\へなP.jpg`

## 図解しおり候補マップ

| 優先度 | 画像 | 挿入位置 | 図解型 | 比率 | 目的 | ファイル名 |
|---|---|---|---|---|---|---|
| 必須 | ヘッダー | noteヘッダー | No.52 Transformation | 1.91:1 | 読み込み負荷から準備完了への変化を伝える | `vol104_header.png` |
| 必須 | 面接前の脳内タスク | 科学的メカニズム後 | No.41 問題→原因→解決 | 4:5 | 面接準備の認知負荷を見える化する | `vol104_01_brain_tasks.png` |
| 必須 | 公正採用ガードレール | 公正採用セクション末尾 | No.6 NG/OK | 4:5 | AIに任せる範囲と任せない範囲を明確にする | `vol104_02_guardrails.png` |
| 必須 | 面接準備フロー | AI予習係セクション冒頭 | No.16 縦フロー | 4:5 | 募集要件→候補者資料→準備メモの流れを示す | `vol104_03_prep_flow.png` |
| 推奨 | PM経歴の確認点分解 | 実際の動きセクション | No.10 Before/After | 4:5 | 「PM経験ありそう」で終わらせない例を補強する | `vol104_04_pm_questions.png` |
| 必須 | 使う前チェック | お土産プロンプト直前 | No.46 チェックリスト | 4:5 | 応募者情報をAIに入れる前の確認事項を示す | `vol104_05_before_use_check.png` |

## 最終採用セット（2026-06-11更新）

| 用途 | 記事上の位置 | リポジトリ内の元ファイル | 指定OneDrive保存名 | 判定 |
|---|---|---|---|---|
| ヘッダー | noteヘッダー | `team_building_science/vol104/images/vol104_header.png` | `vol104_header.png` | 採用。noteタイトルと同じ訴求の画像生成版 |
| 図解① 面接前の脳内タスク | 科学的メカニズム後 | `team_building_science/vol104/images/zukaishiori_full_test_20260611/02_brain_tasks.png` | `vol104_01_brain_tasks.png` | 採用 |
| 図解② 公正採用ガードレール | 公正採用セクション末尾 | `team_building_science/vol104/images/vol104_02_guardrails.png` | `vol104_02_guardrails.png` | 採用。余計なVol表記なしの再生成版 |
| 図解③ 面接準備フロー | AI予習係セクション冒頭 | `team_building_science/vol104/images/zukaishiori_full_test_20260611/04_ai_prep_flow.png` | `vol104_03_prep_flow.png` | 採用。再生成時は「採否判断」表記を優先 |
| 図解④ PM経歴の確認点分解 | 実際の動きセクション | `team_building_science/vol104/images/zukaishiori_full_test_20260611/07_pm_case_questions.png` | `vol104_04_pm_questions.png` | 採用 |
| 図解⑤ 使う前チェック | お土産プロンプト直前 | `team_building_science/vol104/images/zukaishiori_full_test_20260611/08_before_use_check.png` | `vol104_05_before_use_check.png` | 採用 |

## 現在の生成済み候補

`team_building_science/vol104/images/zukaishiori_full_test_20260611/` に、図解しおりフルパイプラインテストで生成した8枚がある。

主要採用候補:

- `02_brain_tasks.png`
- `team_building_science/vol104/images/vol104_02_guardrails.png`
- `04_ai_prep_flow.png`
- `07_pm_case_questions.png`
- `08_before_use_check.png`
- `team_building_science/vol104/images/vol104_header.png`

正式利用画像は、上記の保存先フォルダへ用途別ファイル名でコピー済み。

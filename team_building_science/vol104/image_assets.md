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
| 必須 | 公正採用ガードレール | 公正採用セクション末尾 | No.6 NG/OK | 4:5 | AIに任せる範囲と任せない範囲を明確にする | `vol104_01_guardrails.png` |
| 必須 | 面接準備フロー | AI予習係セクション冒頭 | No.16 縦フロー | 4:5 | 募集要件→候補者資料→準備メモの流れを示す | `vol104_02_prep_flow.png` |
| 推奨 | 面接前の脳内タスク | 科学的メカニズム後 | No.41 問題→原因→解決 | 4:5 | 面接準備の認知負荷を見える化する | `vol104_03_brain_tasks.png` |
| 任意 | PM経歴の確認点分解 | 実際の動きセクション | No.10 Before/After | 4:5 | 「PM経験ありそう」で終わらせない例を補強する | `vol104_04_pm_questions.png` |

## 最終採用セット（2026-06-11）

| 用途 | 記事上の位置 | リポジトリ内の元ファイル | 指定OneDrive保存名 | 判定 |
|---|---|---|---|---|
| ヘッダー | noteヘッダー | `team_building_science/vol104/images/vol104_header.png` | `vol104_header.png` | 採用 |
| 図解① 公正採用ガードレール | 公正採用セクション末尾 | `team_building_science/vol104/images/zukaishiori_full_test_20260611/03_fair_hiring_guardrails.png` | `vol104_01_guardrails.png` | 採用。再生成時は追加コピーを抑制 |
| 図解② 面接準備フロー | AI予習係セクション冒頭 | `team_building_science/vol104/images/zukaishiori_full_test_20260611/04_ai_prep_flow.png` | `vol104_02_prep_flow.png` | 採用。再生成時は「採否判断」表記を優先 |

推奨・任意の `vol104_03_brain_tasks.png`、`vol104_04_pm_questions.png` は追加候補として扱う。現時点では本文の正式挿入コメントを増やさず、比較用生成フォルダに残す。

## 現在の生成済み候補

`team_building_science/vol104/images/zukaishiori_full_test_20260611/` に、図解しおりフルパイプラインテストで生成した8枚がある。

主要採用候補:

- `03_fair_hiring_guardrails.png`
- `04_ai_prep_flow.png`
- `team_building_science/vol104/images/vol104_header.png`

正式利用画像は、上記の保存先フォルダへ用途別ファイル名でコピー済み。

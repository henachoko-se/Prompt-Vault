# 個人情報スキャナー

指定したフォルダ内のファイルに個人情報が含まれていないかチェックするツールです。  
インストール不要。Python版・PowerShell版の2種類を同梱しています。

---

## ダウンロード

**[pii_scanner.zip をダウンロード](/tools/download/pii_scanner.zip)**

---

## 検出できる個人情報

| 種類 | 例 |
|------|-----|
| メールアドレス | yamada@example.com |
| 電話番号 | 03-1234-5678 / 090-1234-5678 |
| 電話番号（ハイフンなし） | 09012345678 |
| マイナンバー | 1234-5678-9012 |
| クレジットカード番号 | 4111-1111-1111-1111 |
| 生年月日 | 1990年5月15日 / 1990/5/15 |
| 郵便番号 | 〒150-0001 |

---

## 使い方

### PowerShell版（インストール不要・今すぐ使える）

```powershell
# 基本スキャン
.\pii_scanner.ps1 -FolderPath "C:\Users\User\Documents"

# CSV出力付き
.\pii_scanner.ps1 -FolderPath "C:\Users\User\Documents" -OutputCsv "result.csv"
```

### Python版（Python承認後）

```powershell
# 基本スキャン
python pii_scanner.py C:\Users\User\Documents

# CSV出力付き
python pii_scanner.py C:\Users\User\Documents result.csv
```

---

## 対応ファイル形式

`.txt` `.csv` `.log` `.tsv` `.json` `.xml` `.html` `.md` `.yaml` `.ini` `.conf` `.sql` `.py` `.js`

---

## 注意

- **誤検知あり**：正規表現ベースのため、電話番号の一部が郵便番号として検出されるケースがあります。結果は「要確認リスト」として活用してください。
- **.docx / .xlsx / .pdf は非対応**（バイナリファイル）

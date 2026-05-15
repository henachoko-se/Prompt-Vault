<#
.SYNOPSIS
    個人情報スキャナー - 指定フォルダ内の個人情報をチェックします

.DESCRIPTION
    テキスト系ファイルをスキャンし、メールアドレス・電話番号・マイナンバー等の
    個人情報パターンを検出します。インストール不要・Windows標準のPowerShellで動作します。

.PARAMETER FolderPath
    スキャン対象のフォルダパス（必須）

.PARAMETER OutputCsv
    検出結果を保存するCSVファイルパス（省略可）

.EXAMPLE
    .\pii_scanner.ps1 -FolderPath "C:\Users\User\Documents"
    .\pii_scanner.ps1 -FolderPath "C:\Users\User\Documents" -OutputCsv "result.csv"
#>

param(
    [Parameter(Mandatory = $true, HelpMessage = "スキャン対象のフォルダパスを指定してください")]
    [string]$FolderPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputCsv
)

# ---------------------------------------------------------------
# 設定: スキャン対象の拡張子
# ---------------------------------------------------------------
$TargetExtensions = @(
    '.txt', '.csv', '.log', '.tsv',
    '.json', '.xml', '.html', '.htm',
    '.md', '.yaml', '.yml',
    '.ini', '.conf', '.sql', '.py', '.js'
)

# ---------------------------------------------------------------
# 設定: 検出パターン
# ---------------------------------------------------------------
$Patterns = [ordered]@{
    'メールアドレス'         = '[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    '電話番号'               = '0\d{1,4}[-\s]\d{1,4}[-\s]\d{3,4}'
    '電話番号(ハイフンなし)' = '(?<!\d)0[789]0\d{8}(?!\d)|(?<!\d)0\d{9,10}(?!\d)'
    'マイナンバー'           = '(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)'
    'クレジットカード番号'   = '(?<!\d)(?:\d{4}[-\s]?){3}\d{4}(?!\d)'
    '生年月日'               = '\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?'
    '郵便番号'               = '〒?\d{3}-\d{4}'
}

# ---------------------------------------------------------------
# 関数: 1ファイルをスキャン
# ---------------------------------------------------------------
function Invoke-ScanFile {
    param([string]$FilePath)

    $results = [System.Collections.Generic.List[PSCustomObject]]::new()

    try {
        $lines = [System.IO.File]::ReadAllLines($FilePath, [System.Text.Encoding]::UTF8)
    } catch {
        $results.Add([PSCustomObject]@{
            Type    = 'ファイル読み込みエラー'
            LineNo  = 0
            Match   = $_.Exception.Message
            Context = ''
        })
        return $results
    }

    $lineNo = 0
    foreach ($line in $lines) {
        $lineNo++
        foreach ($piiType in $Patterns.Keys) {
            $rx = [regex]::new($Patterns[$piiType])
            $matches = $rx.Matches($line)
            foreach ($m in $matches) {
                $ctx = $line.Trim()
                if ($ctx.Length -gt 100) { $ctx = $ctx.Substring(0, 100) + '...' }
                $results.Add([PSCustomObject]@{
                    Type    = $piiType
                    LineNo  = $lineNo
                    Match   = $m.Value
                    Context = $ctx
                })
            }
        }
    }

    return $results
}

# ---------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------
if (-not (Test-Path -Path $FolderPath -PathType Container)) {
    Write-Error "エラー: フォルダが見つかりません: $FolderPath"
    exit 1
}

# 相対パス指定された場合に絶対パスへ変換
$FolderPath = (Resolve-Path $FolderPath).Path.TrimEnd('\')

$sep = '=' * 62
Write-Host ""
Write-Host $sep
Write-Host "  個人情報スキャナー" -ForegroundColor Cyan
Write-Host "  スキャン対象 : $FolderPath"
Write-Host "  実行日時     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host $sep
Write-Host ""

$allResults   = [System.Collections.Generic.List[PSCustomObject]]::new()
$scannedCount = 0
$hitFiles     = 0

$files = Get-ChildItem -Path $FolderPath -Recurse -File |
         Where-Object { $TargetExtensions -contains $_.Extension.ToLower() } |
         Sort-Object FullName

foreach ($file in $files) {
    $scannedCount++
    $fileResults = Invoke-ScanFile -FilePath $file.FullName

    if ($fileResults.Count -eq 0) { continue }

    $hitFiles++
    $rel = $file.FullName.Substring($FolderPath.TrimEnd('\').Length).TrimStart('\')
    Write-Host "[検出] $rel" -ForegroundColor Yellow

    foreach ($r in $fileResults) {
        Write-Host ("  行{0,4}  [{1}]  {2}" -f $r.LineNo, $r.Type, $r.Match) -ForegroundColor Red
        Write-Host "         文脈: $($r.Context)"
    }
    Write-Host ""

    foreach ($r in $fileResults) {
        $allResults.Add([PSCustomObject]@{
            ファイル = $file.FullName.Substring($FolderPath.TrimEnd('\').Length).TrimStart('\')
            行番号   = $r.LineNo
            種類     = $r.Type
            検出値   = $r.Match
            文脈     = $r.Context
        })
    }
}

# サマリー表示
Write-Host ""
Write-Host $sep
Write-Host "  スキャン結果サマリー" -ForegroundColor Cyan
Write-Host $sep
Write-Host "  スキャンファイル数 : $scannedCount"

if ($hitFiles -gt 0) {
    Write-Host "  問題あり           : $hitFiles ファイル" -ForegroundColor Yellow
    Write-Host "  検出件数           : $($allResults.Count) 件" -ForegroundColor Red
} else {
    Write-Host "  問題あり           : 0 ファイル" -ForegroundColor Green
    Write-Host "  検出件数           : 0 件"        -ForegroundColor Green
}

# CSV出力
if ($OutputCsv -and $allResults.Count -gt 0) {
    $allResults | Export-Csv -Path $OutputCsv -Encoding UTF8BOM -NoTypeInformation
    $resolved = (Resolve-Path $OutputCsv).Path
    Write-Host ""
    Write-Host "  レポート保存先     : $resolved"
}

Write-Host $sep
Write-Host ""

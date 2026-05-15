#!/usr/bin/env python3
"""
PII Scanner - 個人情報スキャナー
指定フォルダ内のファイルに個人情報が含まれていないかチェックします
外部ライブラリ不要（標準ライブラリのみ使用）

使い方:
    python pii_scanner.py <フォルダパス>
    python pii_scanner.py <フォルダパス> <出力CSVパス>

例:
    python pii_scanner.py C:\Users\User\Documents
    python pii_scanner.py C:\Users\User\Documents result.csv
"""

import re
import os
import csv
import sys
from pathlib import Path
from datetime import datetime

# スキャン対象の拡張子
TARGET_EXTENSIONS = {
    '.txt', '.csv', '.log', '.tsv',
    '.json', '.xml', '.html', '.htm',
    '.md', '.yaml', '.yml',
    '.ini', '.conf', '.sql', '.py', '.js',
}

# 検出パターン定義
PATTERNS = {
    'メールアドレス': re.compile(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    ),
    '電話番号': re.compile(
        r'0\d{1,4}[-\s]\d{1,4}[-\s]\d{3,4}'
    ),
    '電話番号(ハイフンなし)': re.compile(
        r'(?<!\d)0[789]0\d{8}(?!\d)|(?<!\d)0\d{9,10}(?!\d)'
    ),
    'マイナンバー': re.compile(
        r'(?<!\d)\d{4}[-\s]?\d{4}[-\s]?\d{4}(?!\d)'
    ),
    'クレジットカード番号': re.compile(
        r'(?<!\d)(?:\d{4}[-\s]?){3}\d{4}(?!\d)'
    ),
    '生年月日': re.compile(
        r'\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?'
    ),
    '郵便番号': re.compile(
        r'〒?\d{3}-\d{4}'
    ),
}

# コンソール出力用の色（Windows対応）
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7
    )
    USE_COLOR = True
except Exception:
    USE_COLOR = False

def color(text, code):
    if USE_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text

RED    = lambda t: color(t, '31')
YELLOW = lambda t: color(t, '33')
GREEN  = lambda t: color(t, '32')
BOLD   = lambda t: color(t, '1')


def scan_file(filepath):
    """1ファイルをスキャンして検出結果リストを返す"""
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return [{'type': 'ファイル読み込みエラー', 'line': 0, 'match': str(e), 'context': ''}]

    for lineno, line in enumerate(lines, 1):
        for pii_type, pattern in PATTERNS.items():
            for m in pattern.finditer(line):
                context = line.strip()
                if len(context) > 100:
                    context = context[:100] + '...'
                results.append({
                    'type':    pii_type,
                    'line':    lineno,
                    'match':   m.group(),
                    'context': context,
                })

    return results


def scan_folder(folder_path, output_csv=None):
    """フォルダ内の全対象ファイルをスキャンする"""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        print(f"エラー: フォルダが見つかりません: {folder_path}")
        sys.exit(1)

    sep = '=' * 62
    print(f"\n{sep}")
    print(BOLD("  個人情報スキャナー"))
    print(f"  スキャン対象 : {folder_path}")
    print(f"  実行日時     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{sep}\n")

    all_results = []
    scanned_count = 0
    hit_files = 0

    for filepath in sorted(folder.rglob('*')):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in TARGET_EXTENSIONS:
            continue

        scanned_count += 1
        file_results = scan_file(filepath)

        if not file_results:
            continue

        hit_files += 1
        rel = filepath.relative_to(folder)
        print(YELLOW(f"[検出] {rel}"))

        for r in file_results:
            print(f"  行 {r['line']:4d}  " + RED(f"[{r['type']}]") + f"  {r['match']}")
            print(f"         文脈: {r['context']}")

        print()

        for r in file_results:
            all_results.append({
                'ファイル': str(filepath.relative_to(folder)),
                '行番号':   r['line'],
                '種類':     r['type'],
                '検出値':   r['match'],
                '文脈':     r['context'],
            })

    # サマリー表示
    print(f"\n{sep}")
    print(BOLD("  スキャン結果サマリー"))
    print(sep)
    print(f"  スキャンファイル数 : {scanned_count}")
    if hit_files > 0:
        print(YELLOW(f"  問題あり           : {hit_files} ファイル"))
        print(RED(  f"  検出件数           : {len(all_results)} 件"))
    else:
        print(GREEN( "  問題あり           : 0 ファイル"))
        print(GREEN( "  検出件数           : 0 件"))

    # CSV出力
    if output_csv and all_results:
        out_path = Path(output_csv)
        with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(
                f, fieldnames=['ファイル', '行番号', '種類', '検出値', '文脈']
            )
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\n  レポート保存先     : {out_path.resolve()}")

    print(f"{sep}\n")
    return all_results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    folder_path = sys.argv[1]
    output_csv  = sys.argv[2] if len(sys.argv) >= 3 else None
    scan_folder(folder_path, output_csv)


if __name__ == '__main__':
    main()

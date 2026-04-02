#!/usr/bin/env python3
"""
pm.py - Prompt Manager
プロンプトのバージョン管理・取り出しツール

使い方:
  python pm.py list                        # プロンプト一覧
  python pm.py show <name>                 # プロンプト内容を表示
  python pm.py save "<コメント>"            # 現在の状態を保存（git commit）
  python pm.py history [name]              # 変更履歴を表示
  python pm.py diff <name> [v1] [v2]       # バージョン間の差分を表示
  python pm.py restore <name> <version>    # 過去バージョンを取り出す
  python pm.py search <キーワード>          # プロンプト内を検索
"""

import sys
import os
import subprocess
import glob
from pathlib import Path

VAULT = Path(__file__).parent
os.chdir(VAULT)

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')

def find_prompt(name):
    """名前でプロンプトファイルを検索（部分一致・拡張子省略可）"""
    # 完全一致
    if Path(name).exists():
        return Path(name)
    # .md 付加
    if Path(name + '.md').exists():
        return Path(name + '.md')
    # 部分一致で探す
    matches = list(VAULT.rglob(f'*{name}*.md'))
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"複数候補があります。番号を選んでください:")
        for i, m in enumerate(matches):
            print(f"  {i+1}. {m.relative_to(VAULT)}")
        try:
            idx = int(input("番号: ")) - 1
            return matches[idx]
        except:
            return None
    return None

def cmd_list():
    """プロンプト一覧を表示"""
    print("\n=== プロンプト一覧 ===\n")
    for folder in sorted(VAULT.iterdir()):
        if folder.is_dir() and not folder.name.startswith('.') and folder.name != '__pycache__':
            mds = sorted(folder.glob('*.md'))
            if mds:
                print(f"📁 {folder.name}/")
                for md in mds:
                    size = md.stat().st_size
                    # 最終更新コミット日時を取得
                    r = run(f'git log -1 --format="%ad %s" --date=format:"%Y-%m-%d" -- "{md.relative_to(VAULT)}"')
                    log = r.stdout.strip() or '(未コミット)'
                    print(f"   📄 {md.name:<40} {log}")

    # コミットされていないファイルも表示
    r = run('git status --short')
    if r.stdout.strip():
        print("\n⚠️  未保存の変更あり（python pm.py save \"コメント\" で保存）:")
        for line in r.stdout.strip().split('\n'):
            print(f"   {line}")
    print()

def cmd_show(name):
    """プロンプト内容を表示"""
    path = find_prompt(name)
    if not path:
        print(f"エラー: '{name}' が見つかりません")
        cmd_list()
        return
    print(f"\n=== {path.relative_to(VAULT)} ===\n")
    print(path.read_text(encoding='utf-8'))

def cmd_save(comment):
    """現在の状態をgitにコミット（保存）"""
    r = run('git status --short')
    if not r.stdout.strip():
        print("変更はありません。保存するものがありません。")
        return

    print("変更されたファイル:")
    for line in r.stdout.strip().split('\n'):
        print(f"  {line}")

    run('git add -A')
    r = run(f'git commit -m "{comment}"')
    if r.returncode == 0:
        # コミットハッシュを取得
        h = run('git log -1 --format="%h"').stdout.strip()
        print(f"\n✅ 保存しました！ バージョン: {h}")
        print(f"   コメント: {comment}")
    else:
        print(f"エラー: {r.stderr}")

def cmd_history(name=None):
    """変更履歴を表示"""
    if name:
        path = find_prompt(name)
        if not path:
            print(f"エラー: '{name}' が見つかりません")
            return
        rel = path.relative_to(VAULT)
        print(f"\n=== {rel} の変更履歴 ===\n")
        r = run(f'git log --format="%h  %ad  %s" --date=format:"%Y-%m-%d %H:%M" -- "{rel}"')
    else:
        print(f"\n=== 全体の変更履歴 ===\n")
        r = run('git log --format="%h  %ad  %s" --date=format:"%Y-%m-%d %H:%M"')

    if not r.stdout.strip():
        print("履歴がありません。まず保存してください。")
        return

    print(f"{'バージョン':<10} {'日時':<18} コメント")
    print("-" * 60)
    for line in r.stdout.strip().split('\n'):
        print(f"  {line}")
    print()

def cmd_diff(name, v1=None, v2=None):
    """バージョン間の差分を表示"""
    path = find_prompt(name)
    if not path:
        print(f"エラー: '{name}' が見つかりません")
        return
    rel = path.relative_to(VAULT)

    if v1 and v2:
        r = run(f'git diff {v1} {v2} -- "{rel}"')
    elif v1:
        r = run(f'git diff {v1} HEAD -- "{rel}"')
    else:
        # 最後のコミットとの差分
        r = run(f'git diff HEAD -- "{rel}"')

    if not r.stdout.strip():
        print("差分がありません。")
        return

    for line in r.stdout.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            print(f"\033[32m{line}\033[0m")  # 緑（追加）
        elif line.startswith('-') and not line.startswith('---'):
            print(f"\033[31m{line}\033[0m")  # 赤（削除）
        else:
            print(line)

def cmd_restore(name, version):
    """過去バージョンのプロンプトを取り出して表示（上書きはしない）"""
    path = find_prompt(name)
    if not path:
        print(f"エラー: '{name}' が見つかりません")
        return
    rel = path.relative_to(VAULT)

    r = run(f'git show {version}:"{rel}"')
    if r.returncode != 0:
        print(f"エラー: バージョン '{version}' が見つかりません")
        print("履歴を確認: python pm.py history " + name)
        return

    print(f"\n=== {rel} @ {version} ===\n")
    print(r.stdout)

    ans = input(f"\nこのバージョンで {path.name} を上書きしますか？ (yes/no): ")
    if ans.lower() in ('yes', 'y', 'はい'):
        path.write_text(r.stdout, encoding='utf-8')
        print(f"✅ {path.name} をバージョン {version} に戻しました")
        print("   変更は保存されていません。必要なら: python pm.py save \"v{version}に戻した\"")
    else:
        print("上書きをキャンセルしました。")

def cmd_search(keyword):
    """プロンプト内をキーワード検索"""
    print(f"\n=== '{keyword}' の検索結果 ===\n")
    found = False
    for md in VAULT.rglob('*.md'):
        content = md.read_text(encoding='utf-8', errors='replace')
        if keyword.lower() in content.lower():
            lines = content.split('\n')
            hits = [(i+1, l) for i,l in enumerate(lines) if keyword.lower() in l.lower()]
            print(f"📄 {md.relative_to(VAULT)}")
            for lineno, line in hits[:5]:
                print(f"   L{lineno}: {line.strip()[:80]}")
            if len(hits) > 5:
                print(f"   ... 他 {len(hits)-5} 件")
            found = True
    if not found:
        print(f"'{keyword}' は見つかりませんでした。")
    print()

def cmd_help():
    print(__doc__)

# --- メイン ---
def main():
    args = sys.argv[1:]
    if not args:
        cmd_help()
        return

    cmd = args[0].lower()

    if cmd == 'list':
        cmd_list()
    elif cmd == 'show' and len(args) >= 2:
        cmd_show(args[1])
    elif cmd == 'save' and len(args) >= 2:
        cmd_save(' '.join(args[1:]))
    elif cmd == 'history':
        cmd_history(args[1] if len(args) >= 2 else None)
    elif cmd == 'diff' and len(args) >= 2:
        cmd_diff(args[1], args[2] if len(args) >= 3 else None, args[3] if len(args) >= 4 else None)
    elif cmd == 'restore' and len(args) >= 3:
        cmd_restore(args[1], args[2])
    elif cmd == 'search' and len(args) >= 2:
        cmd_search(args[1])
    else:
        cmd_help()

if __name__ == '__main__':
    main()

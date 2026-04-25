#!/usr/bin/env python3
"""note記事のトンマナ自動チェック（PreToolUse hook for git commit）

チームビルディングの科学・家庭ビルディングの科学の記事をコミット時に検査し、
スキ＆フォローCTA・Tagsハッシュタグ形式・禁止語などの抜けを検出する。

仕様:
- stdin に Claude Code からの hook payload (JSON) が渡される
- ステージされた article.md だけを対象にチェック
- 違反があれば permissionDecision="ask" で Claude にユーザー確認を促す
- 通過時は exit 0、JSONも何も出力しない
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_FAMILY = [
    "家事は愛情",
    "主婦の味方",
    "ママの強い味方",
    "お母さん業",
    "ママ業",
    "手抜き",
    "ズボラさん向け",
    "お母さんの手作りが一番",
    "魔法のように",
    "これだけで全て解決",
    "絶対にラクになる",
]


def get_staged_article_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [
        f
        for f in files
        if f.endswith("article.md")
        and ("team_building_science/" in f or "family_building_science/" in f)
    ]


def check_article(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        content = p.read_text(encoding="utf-8")
    except OSError:
        return []

    violations: list[str] = []
    is_team = "team_building_science/" in path
    is_family = "family_building_science/" in path

    if "スキ" not in content or "フォロー" not in content:
        violations.append("スキ＆フォローCTAが見当たりません")

    lines = [line.rstrip() for line in content.splitlines()]
    has_hashtag_line = any(
        re.match(r"^(#\S+\s+){1,}#\S+\s*$", line.strip()) for line in lines
    )
    has_tags_label = any(line.strip().startswith("Tags:") for line in lines)

    if not has_hashtag_line and not has_tags_label:
        violations.append(
            "ハッシュタグ形式のTags行が見当たりません（例: #タグ #タグ #タグ）"
        )

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Tags:"):
            payload = stripped[len("Tags:"):]
            if "," in payload or "、" in payload:
                violations.append(
                    "Tags行がカンマ区切りです（noteではタグとして機能しません。スペース区切りハッシュタグを使ってください）"
                )
            if "#" not in payload:
                violations.append("Tags行に「#」が含まれていません")

    if is_team and "次回もお楽しみに" not in content:
        violations.append("「次回もお楽しみに。」の定型締め文が見当たりません")

    if is_family:
        for word in FORBIDDEN_FAMILY:
            if word in content:
                violations.append(f"禁止語「{word}」が含まれています")

    if violations:
        return [f"{path}: {v}" for v in violations]
    return []


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = payload.get("tool_input", {}).get("command", "") or ""
    if not re.search(r"\bgit\s+commit\b", command):
        return 0

    targets = get_staged_article_files()
    if not targets:
        return 0

    all_violations: list[str] = []
    for path in targets:
        all_violations.extend(check_article(path))

    if not all_violations:
        return 0

    reason = "記事のトンマナチェックで以下が見つかりました:\n" + "\n".join(
        f"  - {v}" for v in all_violations
    ) + "\n\n意図的に通したい場合のみ、ユーザーに内容を伝えて確認の上で進めてください。"

    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

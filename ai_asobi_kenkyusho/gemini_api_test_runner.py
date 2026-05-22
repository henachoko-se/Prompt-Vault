import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


MODEL = os.getenv("GEMINI_TEST_MODEL", "gemini-3.1-pro-preview")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
ROOT = Path(__file__).parent
PROMPT_FILE = ROOT / "kikaku_ranking_prompt.md"
OUT_FILE = ROOT / "gemini_api_test_output.json"


def extract_prompt(markdown: str) -> str:
    match = re.search(r"```text\n(.*?)\n```", markdown, flags=re.S)
    if not match:
        raise RuntimeError("完成版プロンプトのtextコードブロックが見つかりません。")
    return match.group(1)


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY または GOOGLE_API_KEY が未設定です。", file=sys.stderr)
        return 2

    prompt = extract_prompt(PROMPT_FILE.read_text(encoding="utf-8"))
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        ENDPOINT.format(model=MODEL, key=api_key),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as res:
            body = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Gemini API error {exc.code}: {detail[:1000]}", file=sys.stderr)
        return 1

    OUT_FILE.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    text = "".join(
        part.get("text", "")
        for part in body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

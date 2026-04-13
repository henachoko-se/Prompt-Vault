"""
PNG → PDF 変換ツール
指定フォルダ内のPNGファイルをファイル名順に並べてPDFに変換します。

使い方:
  python png_to_pdf.py                        # カレントディレクトリのPNGをPDF化
  python png_to_pdf.py C:/path/to/images      # フォルダを指定
  python png_to_pdf.py C:/path/to/images output.pdf  # 出力ファイル名も指定
"""

import sys
from pathlib import Path
from PIL import Image


def png_to_pdf(folder: str = ".", output: str = None):
    folder_path = Path(folder).resolve()

    # PNGファイルをファイル名順に取得
    png_files = sorted(folder_path.glob("*.png"), key=lambda p: p.name.lower())
    if not png_files:
        print(f"PNGファイルが見つかりませんでした: {folder_path}")
        return

    # 出力ファイル名（未指定の場合はフォルダ名.pdf）
    if output is None:
        output = folder_path / f"{folder_path.name}.pdf"
    else:
        output = Path(output)

    print(f"対象フォルダ: {folder_path}")
    print(f"出力先:       {output}")
    print(f"ファイル数:   {len(png_files)} 枚")
    for f in png_files:
        print(f"  {f.name}")

    # 画像を読み込んでRGBに変換
    images = []
    for f in png_files:
        img = Image.open(f).convert("RGB")
        images.append(img)

    # PDF保存（1枚目をベースに残りを追記）
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
    )
    print(f"\nPDF作成完了: {output}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        png_to_pdf()
    elif len(args) == 1:
        png_to_pdf(args[0])
    else:
        png_to_pdf(args[0], args[1])

"""
PNG → PDF 変換ツール（GUI版）
フォルダを選択するだけでPDFに変換します。
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image


def convert(folder_path: Path, status_var: tk.StringVar, listbox: tk.Listbox):
    png_files = sorted(folder_path.glob("*.png"), key=lambda p: p.name.lower())
    if not png_files:
        messagebox.showwarning("警告", "PNGファイルが見つかりませんでした。")
        return

    output = folder_path / f"{folder_path.name}.pdf"

    listbox.delete(0, tk.END)
    for f in png_files:
        listbox.insert(tk.END, f.name)

    status_var.set(f"変換中... ({len(png_files)}枚)")

    images = [Image.open(f).convert("RGB") for f in png_files]
    images[0].save(output, save_all=True, append_images=images[1:])

    status_var.set(f"完了: {output.name}")
    messagebox.showinfo("完了", f"PDFを作成しました。\n\n{output}")


def select_folder(status_var: tk.StringVar, listbox: tk.Listbox):
    folder = filedialog.askdirectory(title="PNGが入ったフォルダを選択")
    if not folder:
        return
    folder_path = Path(folder)
    status_var.set(f"フォルダ: {folder_path.name}")
    convert(folder_path, status_var, listbox)


def main():
    root = tk.Tk()
    root.title("PNG → PDF 変換ツール")
    root.geometry("480x360")
    root.resizable(False, False)

    # タイトル
    tk.Label(root, text="PNG → PDF 変換ツール", font=("", 14, "bold")).pack(pady=16)

    # フォルダ選択ボタン
    tk.Button(
        root,
        text="フォルダを選択して変換",
        font=("", 12),
        width=24,
        height=2,
        command=lambda: select_folder(status_var, listbox),
    ).pack(pady=8)

    # ファイル一覧
    tk.Label(root, text="変換対象ファイル:").pack(anchor="w", padx=20)
    frame = tk.Frame(root)
    frame.pack(padx=20, fill="both", expand=True)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=8)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    # ステータス
    status_var = tk.StringVar(value="フォルダを選択してください")
    tk.Label(root, textvariable=status_var, fg="gray").pack(pady=8)

    root.mainloop()


if __name__ == "__main__":
    main()

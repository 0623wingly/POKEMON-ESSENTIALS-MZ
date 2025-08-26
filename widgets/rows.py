# widgets/rows.py — 共通行ウィジェット群（フォント大きめ＆統一スタイル）

import tkinter as tk
from tkinter import ttk

# 好みで変えてOK
BASE_FONT_FAMILY = "Yu Gothic UI"
BASE_FONT_SIZE = 32  # 入力欄の中の文字も大きくしたい要望に合わせて太め

# 初期化済みかどうかのフラグ
__STYLES_READY = False

def setup_widget_styles(size: int = BASE_FONT_SIZE, family: str = BASE_FONT_FAMILY):
    """
    ttk 用のスタイルをまとめて用意する。
    gui_app 起動時や最初の行コンポーネント作成前に一度呼ばれる想定。
    """
    global __STYLES_READY
    if __STYLES_READY:
        return
    style = ttk.Style()
    style.configure("Big.TLabel", font=(family, size))
    style.configure("Big.TEntry", font=(family, size))
    style.configure("Big.TCombobox", font=(family, size))
    style.configure("Big.TButton", font=(family, size))
    style.configure("Big.TFrame")  # 形だけ（親にスタイルを付けたいとき用）
    __STYLES_READY = True


def row_text(parent, label: str, textvar: tk.StringVar, width: int = 40):
    """ラベル + テキスト入力（1行）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    ent = ttk.Entry(frm, textvariable=textvar, width=width, style="Big.TEntry")
    ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, ent


def row_number(parent, label: str, textvar: tk.StringVar, width: int = 10):
    """ラベル + 数値入力（バリデーションは上位で任意に）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    ent = ttk.Entry(frm, textvariable=textvar, width=width, style="Big.TEntry")
    ent.pack(side=tk.LEFT)
    return frm, ent


def row_combo(parent, label: str, var: tk.StringVar, values, width: int = 30):
    """ラベル + コンボボックス（readonly）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    cb = ttk.Combobox(frm, textvariable=var, values=values, width=width,
                      state="readonly", style="Big.TCombobox")
    cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, cb


def row_two_combos(parent, label: str, var1: tk.StringVar, var2: tk.StringVar, values, width: int = 20):
    """ラベル + コンボ2つ（同一行・Types/EggGroups向け）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    cb1 = ttk.Combobox(frm, textvariable=var1, values=values, width=width,
                       state="readonly", style="Big.TCombobox")
    cb2 = ttk.Combobox(frm, textvariable=var2, values=values, width=width,
                       state="readonly", style="Big.TCombobox")
    cb1.pack(side=tk.LEFT, padx=(0, 8))
    cb2.pack(side=tk.LEFT)
    return frm, (cb1, cb2)


def row_stats(parent, labels, vars_):
    """ステータス用の6項目（ラベル＋Entry）を横並びグリッドで"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    for i, (lab, var) in enumerate(zip(labels, vars_)):
        ttk.Label(frm, text=lab, style="Big.TLabel").grid(row=0, column=2*i, padx=(0, 6), pady=2, sticky="e")
        ent = ttk.Entry(frm, textvariable=var, width=6, style="Big.TEntry")
        ent.grid(row=0, column=2*i+1, padx=(0, 12), pady=2, sticky="w")
    return frm

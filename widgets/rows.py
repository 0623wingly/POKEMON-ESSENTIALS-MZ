# Write updated rows.py (v1.1) implementing font-linked widget sizing (Entry/Combobox/Button).
# 変更点:
# - BASE_FONT_SIZE を変えると、Entry/Combobox/Button の「中の文字サイズ＋ボックスの高さ/パディング」も連動して拡大縮小
# - 既存の row_* API は互換維持（呼び出し側の修正不要）

import tkinter as tk
from tkinter import ttk

# ユーザーが調整する基本フォント
BASE_FONT_FAMILY = "Yu Gothic UI"
BASE_FONT_SIZE = 32  # ← ここを変えるとフォント＋ボックスの大きさが変わる

__STYLES_READY = False
__CACHED_SIZE = None
__CACHED_FAMILY = None

def setup_widget_styles(size: int = BASE_FONT_SIZE, family: str = BASE_FONT_FAMILY):
    """
    ttk 用の「Big.*」スタイル群を作成/更新する。
    フォントサイズに応じて Entry / Combobox / Button の高さやパディングも調整する。
    """
    global __STYLES_READY, __CACHED_SIZE, __CACHED_FAMILY
    if __STYLES_READY and size == __CACHED_SIZE and family == __CACHED_FAMILY:
        return

    style = ttk.Style()
    # 現在テーマでの既定レイアウトを参照
    # Windowsの 'vista' / 'xpnative'、macOS の 'aqua'、Linux の 'clam' など環境差を吸収しつつ padding を足す。
    # 一部テーマでは arrowsize が無いので try/except で安全に。
    pad_y = max(6, size // 4)      # 縦の余白（ボックス高さのベース）
    pad_x = max(8, size // 5)      # 横の余白
    btn_pad_y = max(6, size // 5)
    btn_pad_x = max(10, size // 4)

    # 共通フォント
    style.configure("Big.TLabel", font=(family, size))
    style.configure("Big.TFrame")  # ダミー

    # Entry
    style.configure(
        "Big.TEntry",
        font=(family, size),
        padding=(pad_x, pad_y)  # 外側パディングで高さを稼ぐ
    )
    # いくつかのテーマで field 内側の余白を増やすために layout を上書き
    try:
        base_layout = style.layout("TEntry")
        if base_layout:
            style.layout("Big.TEntry", base_layout)
    except tk.TclError:
        pass

    # Combobox
    style.configure(
        "Big.TCombobox",
        font=(family, size),
        padding=(pad_x, pad_y)
    )
    try:
        base_layout = style.layout("TCombobox")
        if base_layout:
            style.layout("Big.TCombobox", base_layout)
        # 矢印サイズが指定できるテーマなら拡大
        try:
            style.configure("Big.TCombobox", arrowsize=max(12, size))
        except tk.TclError:
            pass
    except tk.TclError:
        pass

    # Button
    style.configure(
        "Big.TButton",
        font=(family, size),
        padding=(btn_pad_x, btn_pad_y)
    )

    __STYLES_READY = True
    __CACHED_SIZE = size
    __CACHED_FAMILY = family


# ===== 行ウィジェット =====

def row_text(parent, label: str, textvar: tk.StringVar, width: int = 40):
    """ラベル + テキスト入力（1行）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    ent = ttk.Entry(frm, textvariable=textvar, width=width, style="Big.TEntry")
    ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, ent


def row_number(parent, label: str, textvar: tk.StringVar, width: int = 10):
    """ラベル + 数値入力（バリデーションは上位で）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    ent = ttk.Entry(frm, textvariable=textvar, width=width, style="Big.TEntry")
    ent.pack(side=tk.LEFT)
    return frm, ent


def row_combo(parent, label: str, var: tk.StringVar, values, width: int = 30, readonly: bool = True):
    """ラベル + コンボボックス"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    state = "readonly" if readonly else "normal"
    cb = ttk.Combobox(frm, textvariable=var, values=values, width=width, state=state, style="Big.TCombobox")
    cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, cb


def row_two_combos(parent, label: str, var1: tk.StringVar, var2: tk.StringVar, values, width: int = 20, readonly: bool = True):
    """ラベル + コンボ2つ（Types/EggGroups 向け）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    state = "readonly" if readonly else "normal"
    cb1 = ttk.Combobox(frm, textvariable=var1, values=values, width=width, state=state, style="Big.TCombobox")
    cb2 = ttk.Combobox(frm, textvariable=var2, values=values, width=width, state=state, style="Big.TCombobox")
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
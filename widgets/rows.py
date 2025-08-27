# rows.py v1.2.1 — 共通行ウィジェット群（フォントとボックスサイズ連動 + Spin対応）
# 変更点(v1.2):
# - Spinbox 行(row_spin)と、6ステータス用スピン(row_stats_spin)を追加
# - 最小/最大/ステップを指定でき、フォーカスアウトや入力でも自動クリップ
# - 既存関数は互換維持
#
# 既定フォント: ラベル(BASE_FONT_SIZE)、ボックス(BOX_FONT_SIZE)

import tkinter as tk
from tkinter import ttk

# ===== フォント設定 =====
LABEL_FONT_FAMILY = "Yu Gothic UI"
BASE_FONT_SIZE   = 16   # ラベル
BOX_FONT_FAMILY  = "Yu Gothic UI"
BOX_FONT_SIZE    = 24   # 入力内部文字＆高さ

__STYLES_READY = False
__CACHE = {}

def setup_widget_styles(
    label_size: int = BASE_FONT_SIZE,
    label_family: str = LABEL_FONT_FAMILY,
    box_size: int = BOX_FONT_SIZE,
    box_family: str = BOX_FONT_FAMILY
):
    global __STYLES_READY, __CACHE
    key = (label_size, label_family, box_size, box_family)
    if __STYLES_READY and __CACHE.get("k") == key:
        return

    style = ttk.Style()

    style.configure("Big.TLabel", font=(label_family, label_size))
    style.configure("Big.TFrame")

    pad_y = max(6, box_size // 4)
    pad_x = max(8, box_size // 5)
    btn_pad_y = max(6, box_size // 5)
    btn_pad_x = max(10, box_size // 4)

    style.configure("Big.TEntry", font=(box_family, box_size), padding=(pad_x, pad_y))
    try:
        base_layout = style.layout("TEntry")
        if base_layout:
            style.layout("Big.TEntry", base_layout)
    except tk.TclError:
        pass

    style.configure("Big.TCombobox", font=(box_family, box_size), padding=(pad_x, pad_y))
    try:
        base_layout = style.layout("TCombobox")
        if base_layout:
            style.layout("Big.TCombobox", base_layout)
        try:
            style.configure("Big.TCombobox", arrowsize=max(12, int(box_size*0.9)))
        except tk.TclError:
            pass
    except tk.TclError:
        pass

    style.configure("Big.TButton", font=(box_family, box_size), padding=(btn_pad_x, btn_pad_y))

    __STYLES_READY = True
    __CACHE["k"] = key


# ===== 行ウィジェット =====

def row_text(parent, label: str, textvar: tk.StringVar, width: int = 40):
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    # ★ font を直接指定して確実に反映させる
    ent = ttk.Entry(
        frm,
        textvariable=textvar,
        width=width,
        style="Big.TEntry",
        font=(BOX_FONT_FAMILY, BOX_FONT_SIZE)  # ← 追加
    )
    ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, ent


def row_number(parent, label: str, textvar: tk.StringVar, width: int = 10):
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    ent = ttk.Entry(
        frm,
        textvariable=textvar,
        width=width,
        style="Big.TEntry",
        font=(BOX_FONT_FAMILY, BOX_FONT_SIZE)  # ★追加：ボックス内文字サイズを直指定
    )
    ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
    return frm, ent

def row_combo(parent, label: str, var: tk.StringVar, values, width: int = 30, readonly: bool = True):
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    state = "readonly" if readonly else "normal"
    cb = ttk.Combobox(
        frm,
        textvariable=var,
        values=values,
        width=width,
        state=state,
        style="Big.TCombobox",
        # ★ 本体にも直にフォント指定
        font=(BOX_FONT_FAMILY, BOX_FONT_SIZE)
    )
    cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

    return frm, cb

def row_two_combos(parent, label: str, var1: tk.StringVar, var2: tk.StringVar, values, width: int = 20, readonly: bool = True):
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))
    state = "readonly" if readonly else "normal"
    cb1 = ttk.Combobox(
        frm, textvariable=var1, values=values, width=width,
        state=state, style="Big.TCombobox",
        font=(BOX_FONT_FAMILY, BOX_FONT_SIZE)   # ★
    )
    cb2 = ttk.Combobox(
        frm, textvariable=var2, values=values, width=width,
        state=state, style="Big.TCombobox",
        font=(BOX_FONT_FAMILY, BOX_FONT_SIZE)   # ★
    )
    cb1.pack(side=tk.LEFT, padx=(0, 8))
    cb2.pack(side=tk.LEFT)

    return frm, (cb1, cb2)

def row_stats(parent, labels, vars_):
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    for i, (lab, var) in enumerate(zip(labels, vars_)):
        ttk.Label(frm, text=lab, style="Big.TLabel").grid(row=0, column=2*i, padx=(0, 6), pady=2, sticky="e")
        ent = ttk.Entry(frm, textvariable=var, width=6, style="Big.TEntry")
        ent.grid(row=0, column=2*i+1, padx=(0, 12), pady=2, sticky="w")
    return frm


# ===== Spin版（数値増減ウィジェット） =====

def _clamp(num_str: str, mn: int, mx: int) -> str:
    try:
        v = int(num_str)
    except Exception:
        return str(mn)
    if v < mn: v = mn
    if v > mx: v = mx
    return str(v)

def row_spin(parent, label: str, textvar: tk.StringVar, mn: int, mx: int, step: int = 1, width: int = 8):
    """ラベル + Spinbox（スクロール/クリックで増減、入力も可、範囲外は自動クリップ）"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    ttk.Label(frm, text=label, style="Big.TLabel").pack(side=tk.LEFT, padx=(0, 8))

    # tk.Spinbox を使ってフォントを直接指定（ttk版が無い環境もあるため）
    sp = tk.Spinbox(frm, from_=mn, to=mx, increment=step, textvariable=textvar,
                    width=width, font=(BOX_FONT_FAMILY, BOX_FONT_SIZE))
    sp.pack(side=tk.LEFT)

    def on_validate(event=None):
        textvar.set(_clamp(textvar.get(), mn, mx))

    sp.bind("<FocusOut>", on_validate)
    sp.bind("<Return>", on_validate)
    # マウスホイールは OS によりイベントが違うのでそのままでもOK（Spinboxが処理）

    return frm, sp

def row_stats_spin(parent, labels, vars_, mn: int, mx: int, step: int = 1):
    """6つの数値を Spinbox で横並びに"""
    setup_widget_styles()
    frm = ttk.Frame(parent, style="Big.TFrame")
    for i, (lab, var) in enumerate(zip(labels, vars_)):
        ttk.Label(frm, text=lab, style="Big.TLabel").grid(row=0, column=2*i, padx=(0, 6), pady=2, sticky="e")
        sp = tk.Spinbox(frm, from_=mn, to=mx, increment=step, textvariable=var,
                        width=6, font=(BOX_FONT_FAMILY, BOX_FONT_SIZE))
        sp.grid(row=0, column=2*i+1, padx=(0, 12), pady=2, sticky="w")
        def make_bind(v=var):  # クロージャで var を束縛
            def _on_validate(event=None):
                v.set(_clamp(v.get(), mn, mx))
            return _on_validate
        sp.bind("<FocusOut>", make_bind())
        sp.bind("<Return>", make_bind())
    return frm

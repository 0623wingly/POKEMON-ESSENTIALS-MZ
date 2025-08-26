# widgets/moves_dialog.py — わざ編集用ダイアログ
# ・Lv.つき（レベル技）と Lv.なし（教え技 / タマゴ技）を切り替え
# ・OK で result にリストを格納して親に返す

import tkinter as tk
from tkinter import ttk, simpledialog

BASE_FONT = ("Yu Gothic UI", 14)


class MovesDialog(tk.Toplevel):
    def __init__(self, master, all_moves, title="わざ編集", with_level=False, initial=None):
        super().__init__(master)
        self.title(title)
        self.geometry("500x500")
        self.transient(master)
        self.grab_set()

        self.with_level = with_level
        self.all_moves = all_moves  # 候補（rscから読み込んだもの）
        self.result = None

        # 初期リスト
        self.moves = list(initial) if initial else []

        # UI
        self._make_widgets()

    def _make_widgets(self):
        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, padx=8, pady=4)

        # レベル欄（with_level=True のときだけ）
        if self.with_level:
            ttk.Label(frm_top, text="Lv:", font=BASE_FONT).pack(side=tk.LEFT)
            self.v_lv = tk.StringVar()
            self.ent_lv = ttk.Entry(frm_top, textvariable=self.v_lv, width=6, font=BASE_FONT)
            self.ent_lv.pack(side=tk.LEFT, padx=(4, 12))
        else:
            self.v_lv = None

        # わざ候補選択
        self.v_move = tk.StringVar()
        self.cb = ttk.Combobox(frm_top, textvariable=self.v_move, values=self.all_moves,
                               state="readonly", width=25, font=BASE_FONT)
        self.cb.pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="追加", command=self.add_move).pack(side=tk.LEFT, padx=4)

        # 現在のリスト
        self.lb = tk.Listbox(self, font=BASE_FONT)
        self.lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        for m in self.moves:
            self.lb.insert(tk.END, m)

        # 下ボタン
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill=tk.X, pady=6)
        ttk.Button(frm_btn, text="削除", command=self.del_move).pack(side=tk.LEFT, padx=6)
        ttk.Button(frm_btn, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=6)
        ttk.Button(frm_btn, text="キャンセル", command=self.on_cancel).pack(side=tk.RIGHT, padx=6)

    def add_move(self):
        mv = self.v_move.get().strip()
        if not mv:
            return
        if self.with_level:
            lv = self.v_lv.get().strip()
            if lv.isdigit():
                entry = f"Lv{lv}:{mv}"
            else:
                entry = mv
        else:
            entry = mv
        self.moves.append(entry)
        self.lb.insert(tk.END, entry)

    def del_move(self):
        i = self.lb.curselection()
        if not i:
            return
        idx = i[0]
        self.lb.delete(idx)
        self.moves.pop(idx)

    def on_ok(self):
        self.result = self.moves
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

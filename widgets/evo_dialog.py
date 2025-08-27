# widgets/evo_dialog.py — 進化編集ダイアログ
# 目的：
#   [進化先] [Method] [Parameter] の行を複数管理して、
#   OK で PBS の "Evolutions" 用配列（["TARGET,Method,Param", ...]）を result に返す。
#
# 使い方（親側）：
#   dlg = EvoDialog(self, species_list=..., items_list=..., moves_list=..., title="進化の編集", initial=initial_list)
#   self.wait_window(dlg)
#   if dlg.result is not None:
#       # dlg.result は ["TARGET,Method,Param", ...]
#       # 連結して "Evolutions" に入れるなら: " ".join(dlg.result)
#       ...

import tkinter as tk
from tkinter import ttk, messagebox

BASE_FONT = ("Yu Gothic UI", 14)

# よく使う進化メソッド（Essentials 準拠の一般例）
# ※ ゲーム側の導入済みメソッド名に合わせて編集してね
#   ( method_id, 表示名, パラメータのヒント/期待型 )
METHODS = [
    ("Level",             "レベル",             "数値（例: 16）"),
    ("LevelMale",         "レベル（♂）",       "数値"),
    ("LevelFemale",       "レベル（♀）",       "数値"),
    ("LevelDay",          "レベル（昼）",       "数値"),
    ("LevelNight",        "レベル（夜）",       "数値"),
    ("Happiness",         "なつき進化",         "（なし or 0）"),
    ("HappinessDay",      "なつき（昼）",       "（なし or 0）"),
    ("HappinessNight",    "なつき（夜）",       "（なし or 0）"),
    ("Item",              "どうぐ使用",         "アイテムID"),
    ("Trade",             "通信交換",           "（なし or 0）"),
    ("TradeItem",         "通信交換（道具）",   "アイテムID"),
    ("HoldItem",          "道具を持たせてLv.",  "アイテムID"),  # ゲーム側メソッドに合わせて
    ("Location",          "場所",               "マップ/場所ID"),
    ("Move",              "特定の技",           "わざID"),
    ("Party",             "手持ち条件",         "種族ID"),
    ("Type",              "タイプ",             "タイプID"),
    ("Weather",           "天候",               "例: Sun,Rain..."),
    ("Time",              "時間帯",             "例: Day,Night..."),
    ("Friendship",        "なつき度（別名）",   "数値 or 0"),    # プロジェクト依存
    ("Custom",            "カスタム",           "自由入力"),
]

# method_id から、パラメータ用の入力UIを切り替えるための分類
METHOD_PARAM_KIND = {
    # 数値（Spinbox）
    "Level": "number", "LevelMale": "number", "LevelFemale": "number",
    "LevelDay": "number", "LevelNight": "number",
    "Friendship": "number",
    # アイテム（Combobox/テキスト）
    "Item": "item", "TradeItem": "item", "HoldItem": "item",
    # わざ（Combobox/テキスト）
    "Move": "move",
    # 場所（テキスト or Combobox（将来拡張で））
    "Location": "text",
    # 通信／なつき系などパラメータ不要
    "Happiness": "none", "HappinessDay": "none", "HappinessNight": "none",
    "Trade": "none",
    # 種族/タイプ/天候/時間帯/パーティ条件などはテキスト入力に寄せる（選択肢を渡せばCombobox化も可）
    "Party": "species",
    "Type": "text",
    "Weather": "text",
    "Time": "text",
    # カスタム
    "Custom": "text",
}

def _method_label(mid: str) -> str:
    for k, name, _ in METHODS:
        if k == mid:
            return name
    return mid


class EvoDialog(tk.Toplevel):
    def __init__(self, master,
                 species_list=None,
                 items_list=None,
                 moves_list=None,
                 title="進化の編集",
                 initial=None):
        super().__init__(master)
        self.title(title)
        self.geometry("720x520")
        self.transient(master)
        self.grab_set()

        self.species_list = species_list or []  # 種族候補（IDのリスト）
        self.items_list = items_list or []      # アイテム候補（IDのリスト）
        self.moves_list = moves_list or []      # わざ候補（IDのリスト）

        # 内部データ：dict の配列で持ち、表示はListboxへ
        # 1件 = {"species": "TARGET", "method": "Level", "param": "16"}
        self.entries = []
        if initial:
            # initial は "TARGET,Method,Param" の配列 or スペース区切りの文字列を想定
            if isinstance(initial, str):
                raw_parts = [p for p in initial.split() if p.strip()]
            else:
                raw_parts = list(initial)
            for it in raw_parts:
                parts = [p.strip() for p in it.split(",")]
                if len(parts) == 3:
                    self.entries.append({"species": parts[0], "method": parts[1], "param": parts[2]})
                elif len(parts) == 2:
                    self.entries.append({"species": parts[0], "method": parts[1], "param": ""})

        # 編集フォームの状態
        self.edit_index = None  # None=新規、int=更新モード

        self._build_ui()
        self._refresh_listbox()

    # ---------------- UI 構築 ----------------
    def _build_ui(self):
        # 上段：入力フォーム
        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, padx=10, pady=(10, 6))

        # 種族
        ttk.Label(frm_top, text="進化先（種族ID）", font=BASE_FONT).grid(row=0, column=0, sticky="w")
        self.v_species = tk.StringVar()
        self.cb_species = ttk.Combobox(frm_top, textvariable=self.v_species, values=self.species_list,
                                       width=28, font=BASE_FONT)
        self.cb_species.grid(row=1, column=0, padx=(0, 8), pady=(2, 8), sticky="w")

        # メソッド
        ttk.Label(frm_top, text="Method", font=BASE_FONT).grid(row=0, column=1, sticky="w")
        self.v_method = tk.StringVar()
        method_values = [f"{mid}:{name}" for mid, name, _ in METHODS]
        self.cb_method = ttk.Combobox(frm_top, textvariable=self.v_method, values=method_values,
                                      state="readonly", width=24, font=BASE_FONT)
        self.cb_method.grid(row=1, column=1, padx=(0, 8), pady=(2, 8), sticky="w")
        self.cb_method.bind("<<ComboboxSelected>>", self._on_method_changed)

        # パラメータ（動的に UI を差し替える）
        ttk.Label(frm_top, text="Parameter", font=BASE_FONT).grid(row=0, column=2, sticky="w")
        self.param_holder = ttk.Frame(frm_top)     # ここに動的ウィジェットを置く
        self.param_holder.grid(row=1, column=2, padx=(0, 8), pady=(2, 8), sticky="w")
        self._current_param_widget = None
        self._param_var = tk.StringVar()
        self._build_param_widget(kind="text")      # 初期はテキスト

        # ヒント
        self.lbl_hint = ttk.Label(frm_top, text="", font=("Yu Gothic UI", 11), foreground="#888")
        self.lbl_hint.grid(row=2, column=0, columnspan=3, sticky="w")

        # 追加/更新ボタン
        btnfrm = ttk.Frame(self)
        btnfrm.pack(fill=tk.X, padx=10, pady=(0, 6))
        self.btn_add = ttk.Button(btnfrm, text="追加", command=self._on_add)
        self.btn_add.pack(side=tk.LEFT)
        self.btn_reset = ttk.Button(btnfrm, text="リセット", command=self._reset_form)
        self.btn_reset.pack(side=tk.LEFT, padx=6)

        # 中段：リスト
        mid = ttk.Frame(self)
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self.lb = tk.Listbox(mid, font=BASE_FONT, height=12)
        self.lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(mid, orient=tk.VERTICAL, command=self.lb.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.lb.config(yscrollcommand=sb.set)

        # 下段：操作ボタン
        btm = ttk.Frame(self)
        btm.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btm, text="上へ", command=self._on_up).pack(side=tk.LEFT)
        ttk.Button(btm, text="下へ", command=self._on_down).pack(side=tk.LEFT, padx=6)
        ttk.Button(btm, text="編集", command=self._on_edit).pack(side=tk.LEFT, padx=6)
        ttk.Button(btm, text="削除", command=self._on_delete).pack(side=tk.LEFT, padx=6)
        ttk.Button(btm, text="OK", command=self._on_ok).pack(side=tk.RIGHT)
        ttk.Button(btm, text="キャンセル", command=self._on_cancel).pack(side=tk.RIGHT, padx=6)

    def _build_param_widget(self, kind: str):
        # 既存を破棄
        for w in self.param_holder.winfo_children():
            w.destroy()
        self._current_param_widget = None

        if kind == "number":
            sv = self._param_var
            sp = ttk.Spinbox(self.param_holder, from_=1, to=255, textvariable=sv, width=8, font=BASE_FONT)
            sp.pack(anchor="w")
            self._current_param_widget = sp
        elif kind == "item":
            # items_list があればコンボ、無ければ Entry
            if self.items_list:
                cb = ttk.Combobox(self.param_holder, values=self.items_list,
                                  textvariable=self._param_var, width=24, state="readonly", font=BASE_FONT)
                cb.pack(anchor="w")
                self._current_param_widget = cb
            else:
                ent = ttk.Entry(self.param_holder, textvariable=self._param_var, width=24, font=BASE_FONT)
                ent.pack(anchor="w")
                self._current_param_widget = ent
        elif kind == "move":
            if self.moves_list:
                cb = ttk.Combobox(self.param_holder, values=self.moves_list,
                                  textvariable=self._param_var, width=24, state="readonly", font=BASE_FONT)
                cb.pack(anchor="w")
                self._current_param_widget = cb
            else:
                ent = ttk.Entry(self.param_holder, textvariable=self._param_var, width=24, font=BASE_FONT)
                ent.pack(anchor="w")
                self._current_param_widget = ent
        elif kind == "species":
            if self.species_list:
                cb = ttk.Combobox(self.param_holder, values=self.species_list,
                                  textvariable=self._param_var, width=24, state="readonly", font=BASE_FONT)
                cb.pack(anchor="w")
                self._current_param_widget = cb
            else:
                ent = ttk.Entry(self.param_holder, textvariable=self._param_var, width=24, font=BASE_FONT)
                ent.pack(anchor="w")
                self._current_param_widget = ent
        else:
            # "text" or "none"
            if kind == "none":
                self._param_var.set("")  # パラメータ不要
                ent = ttk.Entry(self.param_holder, textvariable=self._param_var, width=24, font=BASE_FONT, state="disabled")
            else:
                ent = ttk.Entry(self.param_holder, textvariable=self._param_var, width=24, font=BASE_FONT)
            ent.pack(anchor="w")
            self._current_param_widget = ent

    # ---------------- イベント処理 ----------------
    def _on_method_changed(self, event=None):
        val = self.v_method.get().strip()
        mid = val.split(":", 1)[0] if ":" in val else val
        kind = METHOD_PARAM_KIND.get(mid, "text")
        # ヒント更新
        hint = ""
        for m, name, h in METHODS:
            if m == mid:
                hint = f"param: {h}"
        self.lbl_hint.config(text=hint)
        # UI差し替え
        self._build_param_widget(kind)

    def _reset_form(self):
        self.edit_index = None
        self.btn_add.config(text="追加")
        self.v_species.set("")
        self.v_method.set("")
        self._param_var.set("")
        self._build_param_widget("text")
        self.lbl_hint.config(text="")

    def _validate_one(self, species, method, param):
        if not species:
            messagebox.showwarning("入力不足", "進化先（種族ID）を入力してください。")
            return False
        mid = method.split(":", 1)[0] if ":" in method else method
        if not mid:
            messagebox.showwarning("入力不足", "Method を選択してください。")
            return False
        kind = METHOD_PARAM_KIND.get(mid, "text")
        if kind == "number":
            if not param.isdigit():
                messagebox.showwarning("形式エラー", "Parameter は数値で入力してください。")
                return False
        # それ以外は自由入力（空許容のメソッドもある）
        return True

    def _on_add(self):
        species = self.v_species.get().strip()
        method = self.v_method.get().strip()
        param = self._param_var.get().strip()
        if not self._validate_one(species, method, param):
            return
        mid = method.split(":", 1)[0] if ":" in method else method
        entry = {"species": species, "method": mid, "param": param}

        if self.edit_index is None:
            self.entries.append(entry)
        else:
            self.entries[self.edit_index] = entry
        self._refresh_listbox()
        self._reset_form()

    def _on_edit(self):
        sel = self.lb.curselection()
        if not sel:
            return
        idx = sel[0]
        e = self.entries[idx]
        self.edit_index = idx
        self.btn_add.config(text="更新")
        self.v_species.set(e["species"])
        # コンボボックスは "id:label" なので id を先頭に持つ項目を探す
        label = _method_label(e["method"])
        self.v_method.set(f"{e['method']}:{label}")
        self._build_param_widget(METHOD_PARAM_KIND.get(e["method"], "text"))
        self._param_var.set(e["param"])

    def _on_delete(self):
        sel = self.lb.curselection()
        if not sel:
            return
        idx = sel[0]
        self.entries.pop(idx)
        self._refresh_listbox()
        self._reset_form()

    def _on_up(self):
        sel = self.lb.curselection()
        if not sel or sel[0] == 0:
            return
        i = sel[0]
        self.entries[i-1], self.entries[i] = self.entries[i], self.entries[i-1]
        self._refresh_listbox()
        self.lb.select_set(i-1)

    def _on_down(self):
        sel = self.lb.curselection()
        if not sel or sel[0] >= len(self.entries) - 1:
            return
        i = sel[0]
        self.entries[i+1], self.entries[i] = self.entries[i], self.entries[i+1]
        self._refresh_listbox()
        self.lb.select_set(i+1)

    def _refresh_listbox(self):
        self.lb.delete(0, tk.END)
        for e in self.entries:
            disp = f"{e['species']}  |  {e['method']}  |  {e['param'] or '—'}"
            self.lb.insert(tk.END, disp)

    def _on_ok(self):
        # PBS は "TARGET,Method,Param" の並びを空白区切りで持たせるのが一般的
        out = []
        for e in self.entries:
            m = e["method"]
            p = e["param"]
            # パラメータ不要メソッドは "0" にする運用もある。空のままでもOKにしておく。
            if METHOD_PARAM_KIND.get(m) == "none" and not p:
                p = "0"
            out.append(f"{e['species']},{m},{p}")
        self.result = out
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

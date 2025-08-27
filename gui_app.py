# gui_app.py — PBS Editor main GUI (v1.4)
# ステップ7: 選択肢は日本語表記のみ（値一覧は jp のみを渡す）
# - Types / GenderRatio / GrowthRate / EggGroups / Color / Shape / Habitat は
#   コンボの values が日本語だけになるように統一。
# - 保存時は日本語→ID へ変換、読込時は ID→日本語 へ変換（既存ロジックを維持）。
#
# 依存: pbs_utils.py, widgets/rows.py, widgets/moves_dialog.py, widgets/evo_dialog.py

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pbs_utils import (
    parsePBS, stringify_section, replace_section_in_text
)
from widgets.rows import (
    row_text, row_number, row_combo, row_two_combos, row_stats
)
from widgets.moves_dialog import MovesDialog
from widgets.evo_dialog import EvoDialog

APP_TITLE = "PBS Editor v3.8 (split) — v1.4 (JP-only values)"

# -----------------------------
# マスターデータ（id, jp）
# -----------------------------
TYPES = [
    ("", "—"),
    ("NORMAL","ノーマル"),("FIGHTING","かくとう"),("POISON","どく"),("GROUND","じめん"),
    ("FLYING","ひこう"),("BUG","むし"),("ROCK","いわ"),("GHOST","ゴースト"),("STEEL","はがね"),
    ("FIRE","ほのお"),("WATER","みず"),("ELECTRIC","でんき"),("GRASS","くさ"),("ICE","こおり"),
    ("PSYCHIC","エスパー"),("DRAGON","ドラゴン"),("DARK","あく"),("FAIRY","フェアリー"),
    ("SOUND","おと"),("SAND","すな"),("FOSSIL","かせき"),("WIND","かぜ"),("SNOW","ゆき"),
    ("SHINE","ひかり"),("SHADE","やみ"),("GOD","かみ")
]

GENDER = [
    ("AlwaysMale","♂のみ"),("AlwaysFemale","♀のみ"),("Genderless","性別不明"),
    ("FemaleOneEighth","♂87.5/♀12.5"),("Female25Percent","♂75/♀25"),("Female50Percent","♂50/♀50"),
    ("Female75Percent","♂25/♀75"),("FemaleSevenEighths","♂12.5/♀87.5"),
]

GROWTH = [
    ("Medium","100万タイプ"),("Erratic","60万タイプ"),("Fluctuating","164万タイプ"),
    ("Parabolic","105万タイプ"),("Fast","80万タイプ"),("Slow","125万タイプ"),
]

EGG_GROUPS = [
    ("","—"),
    ("Undiscovered","タマゴみはっけん"),("Monster","かいじゅう"),("Water1","すいちゅう１"),
    ("Bug","むし"),("Flying","ひこう"),("Field","りくじょう"),("Fairy","ようせい"),
    ("Grass","しょくぶつ"),("HumanLike","ひとがた"),("Water3","すいちゅう３"),("Mineral","こうぶつ"),
    ("Amorphous","ふていけい"),("Water2","すいちゅう２"),("Dragon","ドラゴン"),
    ("Ditto","かみ"),("NoEggs","None")
]

COLORS = [
    ("","—"),("Red","あか"),("Blue","あお"),("Yellow","き"),("Green","みどり"),
    ("Black","くろ"),("Brown","ちゃ"),("Purple","むらさき"),("Gray","はい"),
    ("White","しろ"),("Pink","もも")
]

SHAPES = [
    ("","—"),
    ("Head","あたま"),("Serpentine","へび"),("Finned","ひれ"),("HeadArms","あたまとうで"),
    ("HeadBase","あたまとからだ"),("BipedalTail","尾もち2ほんあし"),("HeadLegs","あたまとあし"),
    ("Quadruped","4ほんあし"),("Winged","つばさ"),("Multiped","ふくすうあし"),
    ("MultiBody","ふくすうからだ"),("Bipedal","尾なし2ほんあし"),("MultiWinged","はなえありむし"),
    ("Insectoid","はねなしむし")
]

HABITATS = [
    ("","—"),
    ("None","生息地不明"),("Grassland","草原"),("Forest","森林"),("WatersEdge","水辺"),("Sea","海"),
    ("Cave","洞窟"),("Mountain","山岳"),("RoughTerrain","荒地"),("Urban","都市"),("Marsh","湿地"),
    ("Snow","雪原"),("Volcano","火山"),("Space","宇宙"),("Desert","砂漠"),("Ruins","遺跡"),
    ("Seafloor","海底"),("Graveyard","墓場"),("Distortion","異空間"),("Rare","レア")
]

def id2jp(pairs): return {i:jp for i,jp in pairs}
def jp2id(pairs): return {jp:i for i,jp in pairs}

TYPES_I2J, TYPES_J2I       = id2jp(TYPES), jp2id(TYPES)
GENDER_I2J, GENDER_J2I     = id2jp(GENDER), jp2id(GENDER)
GROWTH_I2J, GROWTH_J2I     = id2jp(GROWTH), jp2id(GROWTH)
EGG_I2J, EGG_J2I           = id2jp(EGG_GROUPS), jp2id(EGG_GROUPS)
COLORS_I2J, COLORS_J2I     = id2jp(COLORS), jp2id(COLORS)
SHAPES_I2J, SHAPES_J2I     = id2jp(SHAPES), jp2id(SHAPES)
HABITATS_I2J, HABITATS_J2I = id2jp(HABITATS), jp2id(HABITATS)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x820")
        self.minsize(980, 720)

        # 状態
        self._saving = False
        self.rsc_dir = None
        self.original_text = ""
        self.sections = []
        self.sec_by_id = {}
        self.current_id = None

        # rsc候補
        self.moves_list = []
        self.items_pairs = []   # (id, jp)
        self.items_id2jp = {}
        self.items_jp2id = {}

        self.species_values = []

        self._make_menu()
        self._make_layout()

    # ----------------- メニュー -----------------
    def _make_menu(self):
        m = tk.Menu(self)
        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="rscフォルダを選択…", command=self.choose_rsc)
        fm.add_command(label="PBSファイルを開く…", command=self.open_pbs)
        fm.add_separator()
        fm.add_command(label="全体を書き出し…", command=self.export_all)
        fm.add_separator()
        fm.add_command(label="終了", command=self.destroy)
        m.add_cascade(label="ファイル", menu=fm)
        self.config(menu=m)

    # ----------------- レイアウト -----------------
    def _make_layout(self):
        container = ttk.Frame(self); container.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(container, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="ポケモン").pack(anchor="w", padx=6, pady=(8, 0))
        self.lb = tk.Listbox(left)
        self.lb.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 8))
        self.lb.bind("<<ListboxSelect>>", self.on_select_id)

        right = ttk.Frame(container); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(right, highlightthickness=0)
        vsb = ttk.Scrollbar(right, orient="vertical", command=canvas.yview)
        self.form = ttk.Frame(canvas)
        self.form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.form, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = canvas

        # Name / FormName
        self.v_name = tk.StringVar(); self._pack_row_text("Name", self.v_name)
        self.v_form = tk.StringVar(); self._pack_row_text("FormName", self.v_form)

        # Types（values は日本語のみ）
        self.v_type1 = tk.StringVar(); self.v_type2 = tk.StringVar()
        type_values_jp = [jp for _, jp in TYPES]
        self._pack_row_two_combos("Types", self.v_type1, self.v_type2, type_values_jp)

        # BaseStats
        self.v_bs = [tk.StringVar() for _ in range(6)]
        self._pack_row_stats(["ＨＰ","こうげき","ぼうぎょ","とくこう","とくぼう","すばやさ"], self.v_bs)

        # GenderRatio / GrowthRate（values は日本語のみ）
        self.v_gender = tk.StringVar(); self._pack_row_combo("GenderRatio", self.v_gender, [jp for _, jp in GENDER])
        self.v_growth = tk.StringVar(); self._pack_row_combo("GrowthRate", self.v_growth, [jp for _, jp in GROWTH])

        # BaseExp
        self.v_baseexp = tk.StringVar(); self._pack_row_number("BaseExp", self.v_baseexp)

        # EVs
        self.v_evs = [tk.StringVar() for _ in range(6)]
        self._pack_row_stats(["EV_HP","EV_Atk","EV_Def","EV_SpA","EV_SpD","EV_Spe"], self.v_evs)

        # Happiness
        self.v_happy = tk.StringVar(); self._pack_row_number("Happiness", self.v_happy)

        # Abilities (テキストのまま。次ステップで選択式化)
        self.v_abilities = tk.StringVar(); self._pack_row_text("Abilities", self.v_abilities)
        self.v_hidden = tk.StringVar();    self._pack_row_text("HiddenAbilities", self.v_hidden)
        self.v_unique = tk.StringVar();    self._pack_row_text("UniqueAbilities", self.v_unique)
        self.v_shiny  = tk.StringVar();    self._pack_row_text("ShinyUnique", self.v_shiny)

        # わざボタン
        btnfrm = ttk.Frame(self.form); btnfrm.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(btnfrm, text="レベル技を編集…", command=self.edit_level_moves).pack(side=tk.LEFT)
        ttk.Button(btnfrm, text="教え技を編集…", command=self.edit_tutor_moves).pack(side=tk.LEFT, padx=6)
        ttk.Button(btnfrm, text="タマゴ技を編集…", command=self.edit_egg_moves).pack(side=tk.LEFT)

        # EggGroups（二つ選択・values は日本語のみ）
        self.v_egg1 = tk.StringVar(); self.v_egg2 = tk.StringVar()
        egg_values_jp = [jp for _, jp in EGG_GROUPS]
        self._pack_row_two_combos("EggGroups", self.v_egg1, self.v_egg2, egg_values_jp)

        # HatchSteps
        self.v_hatch = tk.StringVar(); self._pack_row_number("HatchSteps", self.v_hatch)

        # Incense / Offspring（同一行）
        row = ttk.Frame(self.form); row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="Incense").grid(row=0, column=0, sticky="e", padx=(0,8))
        self.v_incense = tk.StringVar(); self.cb_incense = ttk.Combobox(row, textvariable=self.v_incense, state="normal", width=30, values=[])
        self.cb_incense.grid(row=0, column=1, sticky="we")
        ttk.Label(row, text="Offspring").grid(row=0, column=2, sticky="e", padx=(18,8))
        self.v_offspring = tk.StringVar(); self.cb_offspring = ttk.Combobox(row, textvariable=self.v_offspring, state="normal", width=35, values=[])
        self.cb_offspring.grid(row=0, column=3, sticky="we")
        row.grid_columnconfigure(1, weight=1); row.grid_columnconfigure(3, weight=1)

        # Height / Weight
        row = ttk.Frame(self.form); row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="Height").grid(row=0, column=0, sticky="e", padx=(0,8))
        self.v_height = tk.StringVar(); ttk.Entry(row, textvariable=self.v_height).grid(row=0, column=1, sticky="we")
        ttk.Label(row, text="Weight").grid(row=0, column=2, sticky="e", padx=(18,8))
        self.v_weight = tk.StringVar(); ttk.Entry(row, textvariable=self.v_weight).grid(row=0, column=3, sticky="we")
        row.grid_columnconfigure(1, weight=1); row.grid_columnconfigure(3, weight=1)

        # Color / Shape（values は日本語のみ）
        row = ttk.Frame(self.form); row.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row, text="Color").grid(row=0, column=0, sticky="e", padx=(0,8))
        self.v_color = tk.StringVar(); self.cb_color = ttk.Combobox(row, textvariable=self.v_color, state="readonly", values=[jp for _, jp in COLORS], width=28)
        self.cb_color.grid(row=0, column=1, sticky="we")
        ttk.Label(row, text="Shape").grid(row=0, column=2, sticky="e", padx=(18,8))
        self.v_shape = tk.StringVar(); self.cb_shape = ttk.Combobox(row, textvariable=self.v_shape, state="readonly", values=[jp for _, jp in SHAPES], width=28)
        self.cb_shape.grid(row=0, column=3, sticky="we")
        row.grid_columnconfigure(1, weight=1); row.grid_columnconfigure(3, weight=1)

        # Habitat（values は日本語のみ）
        self.v_habitat = tk.StringVar(); self._pack_row_combo("Habitat", self.v_habitat, [jp for _, jp in HABITATS])

        # Category / Pokedex / Generation
        self.v_category = tk.StringVar(); self._pack_row_text("Category", self.v_category)
        self.v_pokedex = tk.StringVar()
        frm = ttk.Frame(self.form); frm.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(frm, text="Pokedex").pack(anchor="w")
        self.txt_pokedex = tk.Text(frm, height=4); self.txt_pokedex.pack(fill=tk.X, expand=True)

        self.v_generation = tk.StringVar(); self._pack_row_number("Generation", self.v_generation)

        # Flags（テキストのまま）
        self.v_flags = tk.StringVar(); self._pack_row_text("Flags", self.v_flags)

        # Wild items
        self.v_wild_c = tk.StringVar(); self.cb_wild_c = ttk.Combobox(self.form, textvariable=self.v_wild_c, state="normal"); self._pack_row_inline("WildItemCommon", self.cb_wild_c)
        self.v_wild_u = tk.StringVar(); self.cb_wild_u = ttk.Combobox(self.form, textvariable=self.v_wild_u, state="normal"); self._pack_row_inline("WildItemUncommon", self.cb_wild_u)
        self.v_wild_r = tk.StringVar(); self.cb_wild_r = ttk.Combobox(self.form, textvariable=self.v_wild_r, state="normal"); self._pack_row_inline("WildItemRare", self.cb_wild_r)

        # 進化
        evofrm = ttk.Frame(self.form); evofrm.pack(anchor="w", padx=8, pady=6)
        ttk.Button(evofrm, text="進化を編集…", command=self.edit_evolutions).pack(side=tk.LEFT)

        # Rival / SOS / Rate
        self.v_rival = tk.StringVar(); self.cb_rival = ttk.Combobox(self.form, textvariable=self.v_rival, state="normal"); self._pack_row_inline("RivalSpecies", self.cb_rival)
        self.v_soss  = tk.StringVar(); self.cb_soss  = ttk.Combobox(self.form, textvariable=self.v_soss,  state="normal"); self._pack_row_inline("SpeciesSOS", self.cb_soss)
        self.v_sosrate = tk.StringVar(); self._pack_row_number("CallRateSOS", self.v_sosrate)

        # ツールバー
        top = ttk.Frame(self); top.pack(fill=tk.X, padx=10, pady=(6, 0))
        ttk.Button(top, text="PBSファイルを開く", command=self.open_pbs).pack(side=tk.LEFT)
        ttk.Button(top, text="全体を書き出し", command=self.export_all).pack(side=tk.LEFT, padx=6)

    # ---- 小物UI ----
    def _pack_row_text(self, label, var):
        frm, _ = row_text(self.form, label, var); frm.pack(fill=tk.X, padx=8, pady=6)

    def _pack_row_number(self, label, var):
        frm, _ = row_number(self.form, label, var); frm.pack(fill=tk.X, padx=8, pady=6)

    def _pack_row_combo(self, label, var, values):
        frm, _ = row_combo(self.form, label, var, values); frm.pack(fill=tk.X, padx=8, pady=6)

    def _pack_row_two_combos(self, label, var1, var2, values):
        frm, _ = row_two_combos(self.form, label, var1, var2, values); frm.pack(fill=tk.X, padx=8, pady=6)

    def _pack_row_stats(self, labels, var_list):
        frm = row_stats(self.form, labels, var_list); frm.pack(fill=tk.X, padx=8, pady=6)

    def _pack_row_inline(self, label, widget):
        frm = ttk.Frame(self.form); frm.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(frm, text=label, width=18, anchor="e").pack(side=tk.LEFT, padx=(0,8))
        widget.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ----------------- rsc 読み込み -----------------
    def choose_rsc(self):
        d = filedialog.askdirectory(title="rscフォルダを選択")
        if not d: return
        self.rsc_dir = d
        self.moves_list = self._load_moves_rsc()
        self.items_pairs = self._load_items_pairs()
        self.items_id2jp = {k:v for k,v in self.items_pairs}
        self.items_jp2id = {v:k for k,v in self.items_pairs}
        # Incense 候補（ID が INCENSE で終わるもの）表示は日本語名
        incense = [v for k,v in self.items_pairs if k.upper().endswith("INCENSE")]
        all_items = [v for _,v in self.items_pairs]
        self.cb_incense["values"] = incense if incense else all_items
        self.cb_wild_c["values"] = all_items
        self.cb_wild_u["values"] = all_items
        self.cb_wild_r["values"] = all_items
        messagebox.showinfo("rsc", "候補リストを読み込みました。")

    def _load_moves_rsc(self):
        arr = []
        if not self.rsc_dir or not os.path.isdir(self.rsc_dir): return arr
        for name in os.listdir(self.rsc_dir):
            low = name.lower()
            if low.startswith("moves") and low.endswith(".txt"):
                with open(os.path.join(self.rsc_dir, name), "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line=line.strip()
                        if not line or line.startswith("#"): continue
                        if line.startswith("[") and line.endswith("]"):
                            arr.append(line.strip("[]"))
        return sorted(set(arr))

    def _load_items_pairs(self):
        pairs = []
        if not self.rsc_dir: return pairs
        path = os.path.join(self.rsc_dir, "items.txt")
        if not os.path.isfile(path): return pairs
        import re
        cur_id = None
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or line.startswith(";"): continue
                m = re.match(r"^\[(.+)\]$", line)
                if m:
                    cur_id = m.group(1).strip(); continue
                if cur_id:
                    n = re.match(r"^Name\s*=\s*(.+)$", line)
                    if n:
                        pairs.append((cur_id, n.group(1).strip()))
                        cur_id = None
        return pairs

    # ----------------- PBS 読み込み -----------------
    def open_pbs(self):
        path = filedialog.askopenfilename(title="PBSファイルを開く", filetypes=[("Text","*.txt"),("All","*.*")])
        if not path: return
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        self.original_text = txt
        secs = parsePBS(txt)
        self.sections = secs
        self.sec_by_id = {s["id"]: s for s in secs}
        # 左リスト更新
        self.lb.delete(0, tk.END)
        ids = []
        for s in secs:
            name = s["kv"].get("Name", "")
            self.lb.insert(tk.END, f"{s['id']} — {name}")
            ids.append(s["id"])
        self.species_values = [f"{sid} — {self.sec_by_id[sid]['kv'].get('Name','')}" for sid in ids]
        self.cb_offspring["values"] = self.species_values
        self.cb_rival["values"] = self.species_values
        self.cb_soss["values"] = self.species_values
        # デフォルト選択
        if secs:
            self.lb.select_set(0)
            self.on_select_id()

    # ----------------- 選択反映 -----------------
    def on_select_id(self, event=None):
        i = self.lb.curselection()
        if not i: return
        sec = self.sections[i[0]]
        self.current_id = sec["id"]
        kv = sec["kv"]; g = lambda k: kv.get(k, "")

        self.v_name.set(g("Name")); self.v_form.set(g("FormName"))

        # Types (ID->JP)
        t = (g("Types") or "").split(",")
        self.v_type1.set(TYPES_I2J.get(t[0].strip() if len(t)>0 else "", ""))
        self.v_type2.set(TYPES_I2J.get(t[1].strip() if len(t)>1 else "", ""))

        # BaseStats
        bs = (g("BaseStats") or "").split(",")
        for j in range(6): self.v_bs[j].set(bs[j].strip() if j < len(bs) else "")

        # GenderRatio / GrowthRate (ID->JP)
        self.v_gender.set(GENDER_I2J.get(g("GenderRatio"), g("GenderRatio")))
        self.v_growth.set(GROWTH_I2J.get(g("GrowthRate"), g("GrowthRate")))

        # BaseExp
        self.v_baseexp.set(g("BaseExp"))

        # EVs
        evs = g("EVs"); vals = [""]*6
        if evs:
            parts = evs.replace(",", " ").split()
            ev_map = {"HP":0,"ATTACK":1,"DEFENSE":2,"SPECIAL_ATTACK":3,"SPECIAL_DEFENSE":4,"SPEED":5,
                      "ATK":1,"DEF":2,"SPA":3,"SPD":4,"SPE":5}
            for k,v in zip(parts[::2], parts[1::2]):
                kk = k.upper().strip()
                if kk in ev_map: vals[ev_map[kk]] = v
        for j in range(6): self.v_evs[j].set(vals[j])

        # Happiness
        self.v_happy.set(g("Happiness"))

        # Abilities (そのまま/次ステップでコンボ化)
        self.v_abilities.set(g("Abilities")); self.v_hidden.set(g("HiddenAbilities"))
        self.v_unique.set(g("UniqueAbilities")); self.v_shiny.set(g("ShinyUnique"))

        # Moves
        self.level_moves = [x.strip() for x in (g("Moves") or "").split() if x.strip()]
        self.tutor_moves = [x.strip() for x in (g("TutorMoves") or "").split() if x.strip()]
        self.egg_moves   = [x.strip() for x in (g("EggMoves") or "").split() if x.strip()]

        # EggGroups (ID->JP)
        eg = [x.strip() for x in (g("EggGroups") or "").split(",") if x.strip()]
        self.v_egg1.set(EGG_I2J.get(eg[0], "") if len(eg)>0 else "")
        self.v_egg2.set(EGG_I2J.get(eg[1], "") if len(eg)>1 else "")

        # HatchSteps
        self.v_hatch.set(g("HatchSteps"))

        # Incense / Offspring
        inc = g("Incense"); self.v_incense.set(self.items_id2jp.get(inc, inc))
        self.v_offspring.set(g("Offspring"))

        # Height / Weight
        self.v_height.set(g("Height")); self.v_weight.set(g("Weight"))

        # Color / Shape / Habitat (ID->JP)
        self.v_color.set(COLORS_I2J.get(g("Color"), g("Color")))
        self.v_shape.set(SHAPES_I2J.get(g("Shape"), g("Shape")))
        self.v_habitat.set(HABITATS_I2J.get(g("Habitat"), g("Habitat")))

        # Category / Pokedex / Generation
        self.v_category.set(g("Category"))
        self.txt_pokedex.delete("1.0","end"); self.txt_pokedex.insert("1.0", g("Pokedex"))
        self.v_generation.set(g("Generation"))

        # Flags
        self.v_flags.set(g("Flags"))

        # Wild items (ID->JP表示)
        self.v_wild_c.set(self.items_id2jp.get(g("WildItemCommon"), g("WildItemCommon")))
        self.v_wild_u.set(self.items_id2jp.get(g("WildItemUncommon"), g("WildItemUncommon")))
        self.v_wild_r.set(self.items_id2jp.get(g("WildItemRare"), g("WildItemRare")))

        # Evolutions & others
        self.current_evolutions = g("Evolutions")
        self.v_rival.set(g("RivalSpecies")); self.v_soss.set(g("SpeciesSOS"))
        self.v_sosrate.set(g("CallRateSOS"))

    # ----------------- 反映（保存用） -----------------
    def apply_to_current(self):
        if not self.current_id: return
        sec = self.sec_by_id[self.current_id]
        def setkv(k,v):
            v = "" if v is None else str(v).strip()
            if v == "": sec["kv"].pop(k, None)
            else: sec["kv"][k] = v

        setkv("Name", self.v_name.get()); setkv("FormName", self.v_form.get())

        # Types (JP->ID)
        t1 = TYPES_J2I.get(self.v_type1.get().strip(), "")
        t2 = TYPES_J2I.get(self.v_type2.get().strip(), "")
        setkv("Types", ",".join([x for x in [t1,t2] if x]))

        # BaseStats
        setkv("BaseStats", ",".join(v.get().strip() for v in self.v_bs))

        # GenderRatio / GrowthRate (JP->ID)
        setkv("GenderRatio", GENDER_J2I.get(self.v_gender.get().strip(), self.v_gender.get().strip()))
        setkv("GrowthRate",  GROWTH_J2I.get(self.v_growth.get().strip(), self.v_growth.get().strip()))

        # BaseExp
        setkv("BaseExp", self.v_baseexp.get())

        # EVs
        parts=[]; labs=[("HP",0),("ATTACK",1),("DEFENSE",2),("SPECIAL_ATTACK",3),("SPECIAL_DEFENSE",4),("SPEED",5)]
        for lab,idx in labs:
            val=self.v_evs[idx].get().strip()
            if val: parts.append(f"{lab},{val}")
        setkv("EVs"," ".join(parts))

        # Happiness
        setkv("Happiness", self.v_happy.get())

        # Abilities (テキストのまま)
        setkv("Abilities", self.v_abilities.get()); setkv("HiddenAbilities", self.v_hidden.get())
        setkv("UniqueAbilities", self.v_unique.get()); setkv("ShinyUnique", self.v_shiny.get())

        # Moves
        if hasattr(self,"level_moves"): setkv("Moves"," ".join(self.level_moves))
        if hasattr(self,"tutor_moves"): setkv("TutorMoves"," ".join(self.tutor_moves))
        if hasattr(self,"egg_moves"):   setkv("EggMoves"," ".join(self.egg_moves))

        # EggGroups (JP->ID)
        eg1 = EGG_J2I.get(self.v_egg1.get().strip(), "")
        eg2 = EGG_J2I.get(self.v_egg2.get().strip(), "")
        setkv("EggGroups", ",".join([x for x in [eg1,eg2] if x]))

        # HatchSteps
        setkv("HatchSteps", self.v_hatch.get())

        # Incense / Offspring
        inc_id = self.items_jp2id.get(self.v_incense.get().strip(), self.v_incense.get().strip())
        setkv("Incense", inc_id)
        off = self.v_offspring.get()
        setkv("Offspring", off.split(" —",1)[0] if " —" in off else off)

        # Height / Weight
        setkv("Height", self.v_height.get()); setkv("Weight", self.v_weight.get())

        # Color / Shape / Habitat (JP->ID)
        setkv("Color", COLORS_J2I.get(self.v_color.get().strip(), self.v_color.get().strip()))
        setkv("Shape", SHAPES_J2I.get(self.v_shape.get().strip(), self.v_shape.get().strip()))
        setkv("Habitat", HABITATS_J2I.get(self.v_habitat.get().strip(), self.v_habitat.get().strip()))

        # Category / Pokedex / Generation
        setkv("Category", self.v_category.get())
        setkv("Pokedex", self.txt_pokedex.get("1.0","end").strip())
        setkv("Generation", self.v_generation.get())

        # Flags
        setkv("Flags", self.v_flags.get())

        # Wild items
        setkv("WildItemCommon",   self.items_jp2id.get(self.v_wild_c.get().strip(), self.v_wild_c.get().strip()))
        setkv("WildItemUncommon", self.items_jp2id.get(self.v_wild_u.get().strip(), self.v_wild_u.get().strip()))
        setkv("WildItemRare",     self.items_jp2id.get(self.v_wild_r.get().strip(), self.v_wild_r.get().strip()))

        # Evolutions / Rival / SOS
        if hasattr(self, "current_evolutions"): setkv("Evolutions", self.current_evolutions)
        setkv("RivalSpecies", self.v_rival.get().split(" —",1)[0] if " —" in self.v_rival.get() else self.v_rival.get())
        setkv("SpeciesSOS",   self.v_soss.get().split(" —",1)[0] if " —" in self.v_soss.get() else self.v_soss.get())
        setkv("CallRateSOS",  self.v_sosrate.get())

    # ----------------- 保存系 -----------------
    def export_all(self):
        if not self.original_text:
            messagebox.showinfo("書き出し", "先にPBSファイルを開いてください。"); return
        if self.current_id: self.apply_to_current()
        text = self.original_text
        for s in self.sections:
            snap = self.sec_by_id.get(s["id"])
            if snap: text = replace_section_in_text(text, snap)
        path = filedialog.asksaveasfilename(title="全体ファイルを書き出し", defaultextension=".txt",
                                            initialfile="pokemon_Gen1_edited.txt", filetypes=[("Text","*.txt"),("All","*.*")])
        if not path: return
        with open(path, "w", encoding="utf-8") as f: f.write(text)
        messagebox.showinfo("保存", "全体を書き出しました。")

    # ----------------- ダイアログ -----------------
    def edit_level_moves(self):
        moves = self.moves_list if self.moves_list else []
        initial = getattr(self, "level_moves", [])
        dlg = MovesDialog(self, moves if moves else initial, "レベル技の編集", with_level=True, initial=initial)
        self.wait_window(dlg)
        if dlg.result is not None: self.level_moves = dlg.result

    def edit_tutor_moves(self):
        moves = self.moves_list if self.moves_list else []
        initial = getattr(self, "tutor_moves", [])
        dlg = MovesDialog(self, moves if moves else initial, "教え技の編集", with_level=False, initial=initial)
        self.wait_window(dlg)
        if dlg.result is not None: self.tutor_moves = dlg.result

    def edit_egg_moves(self):
        moves = self.moves_list if self.moves_list else []
        initial = getattr(self, "egg_moves", [])
        dlg = MovesDialog(self, moves if moves else initial, "タマゴ技の編集", with_level=False, initial=initial)
        self.wait_window(dlg)
        if dlg.result is not None: self.egg_moves = dlg.result

    def edit_evolutions(self):
        cur = getattr(self, "current_evolutions", "")
        initial = [p for p in cur.split() if p.strip()] if cur else []
        dlg = EvoDialog(self, species_list=[s.split(" —",1)[0] for s in self.species_values],
                        items_list=[k for k,_ in self.items_pairs],
                        moves_list=self.moves_list, title="進化の編集", initial=initial)
        self.wait_window(dlg)
        if dlg.result is not None: self.current_evolutions = " ".join(dlg.result)


if __name__ == "__main__":
    App().mainloop()

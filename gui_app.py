# gui_app.py — PBS Editor main GUI (v1.2)
# 依存: pbs_utils.py, widgets/rows.py, widgets/moves_dialog.py, widgets/evo_dialog.py
#
# 変更点（v1.2）
# - どこでもスクロール機能を廃止（右側スクロールバーのみ）
# - フィールド順序を指定通りに並べ替え
# - ShinyUnique を追加（rsc/abilities_shiny.txt を読み込み）
# - Incense/Offspring、Height/Weight、Color/Shape を各1行にまとめ
# - 選択式/入力式の方式を見直し（GenderRatio, GrowthRateなどコンボ）
# - 進化ダイアログはメソッドに応じてパラメータUI切替（v1.1実装を継続）

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pbs_utils import parsePBS, stringify_section, replace_section_in_text
from widgets.rows import row_text, row_number, row_combo, row_two_combos, row_stats
from widgets.moves_dialog import MovesDialog
from widgets.evo_dialog import EvoDialog

APP_TITLE = "PBS Editor v3.8 (split) — v1.2"

# -----------------------------
# マスターデータ（選択肢）
# -----------------------------
TYPES = [
    ("", "—"),
    ("NORMAL", "ノーマル"), ("FIGHTING", "かくとう"), ("POISON", "どく"),
    ("GROUND", "じめん"), ("FLYING", "ひこう"), ("BUG", "むし"),
    ("ROCK", "いわ"), ("GHOST", "ゴースト"), ("STEEL", "はがね"),
    ("FIRE", "ほのお"), ("WATER", "みず"), ("ELECTRIC", "でんき"),
    ("GRASS", "くさ"), ("ICE", "こおり"), ("PSYCHIC", "エスパー"),
    ("DRAGON", "ドラゴン"), ("DARK", "あく"), ("FAIRY", "フェアリー"),
    ("SOUND", "おと"), ("SAND", "すな"), ("FOSSIL", "かせき"),
    ("WIND", "かぜ"), ("SNOW", "ゆき"), ("SHINE", "ひかり"),
    ("SHADE", "やみ"), ("GOD", "かみ")
]

GENDER = [
    ("AlwaysMale", "♂のみ"), ("AlwaysFemale", "♀のみ"),
    ("Genderless", "性別不明"),
    ("FemaleOneEighth", "♂87.5/♀12.5"),
    ("Female25Percent", "♂75/♀25"),
    ("Female50Percent", "♂50/♀50"),
    ("Female75Percent", "♂25/♀75"),
    ("FemaleSevenEighths", "♂12.5/♀87.5"),
]

GROWTH = [
    ("Medium", "100万タイプ"),
    ("Erratic", "60万タイプ"),
    ("Fluctuating", "164万タイプ"),
    ("Parabolic", "105万タイプ"),
    ("Fast", "80万タイプ"),
    ("Slow", "125万タイプ"),
]

COLORS = [
    ("", "—"), ("Red", "あか"), ("Blue", "あお"), ("Yellow", "き"),
    ("Green", "みどり"), ("Black", "くろ"), ("Brown", "ちゃ"),
    ("Purple", "むらさき"), ("Gray", "はい"), ("White", "しろ"),
    ("Pink", "もも")
]

SHAPES = [
    ("Head","あたま"),("Serpentine","へび"),("Finned","ひれ"),
    ("HeadArms","あたまとうで"),("HeadBase","あたまとからだ"),
    ("BipedalTail","尾もち2ほんあし"),("HeadLegs","あたまとあし"),
    ("Quadruped","4ほんあし"),("Winged","つばさ"),("Multiped","ふくすうあし"),
    ("MultiBody","ふくすうからだ"),("Bipedal","尾なし2ほんあし"),
    ("MultiWinged","はなえありむし"),("Insectoid","はねなしむし")
]

HABITATS = [
    ("None","生息地不明"),("Grassland","草原"),("Forest","森林"),("WatersEdge","水辺"),
    ("Sea","海"),("Cave","洞窟"),("Mountain","山岳"),("RoughTerrain","荒地"),
    ("Urban","都市"),("Marsh","湿地"),("Snow","雪原"),("Volcano","火山"),
    ("Space","宇宙"),("Desert","砂漠"),("Ruins","遺跡"),
    ("Seafloor","海底"),("Graveyard","墓場"),("Distortion","異空間"),("Rare","レア")
]

EGG_GROUPS = [
    ("", "—"),
    ("Undiscovered","タマゴみはっけん"),("Monster","かいじゅう"),("Water1","すいちゅう１"),
    ("Bug","むし"),("Flying","ひこう"),("Field","りくじょう"),("Fairy","ようせい"),
    ("Grass","しょくぶつ"),("HumanLike","ひとがた"),("Water3","すいちゅう３"),
    ("Mineral","こうぶつ"),("Amorphous","ふていけい"),("Water2","すいちゅう２"),
    ("Dragon","ドラゴン"),("Ditto","かみ"),("NoEggs","None")
]

STAT_LABELS_JP = ["ＨＰ","こうげき","ぼうぎょ","とくこう","とくぼう","すばやさ"]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1150x820")
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
        self.items_pairs = []
        self.items_id2jp = {}
        self.items_jp2id = {}
        self.abilities_pairs = []
        self.abilities_id2jp = {}
        self.abilities_jp2id = {}
        self.uniq_pairs = []
        self.uniq_id2jp = {}
        self.uniq_jp2id = {}
        self.shiny_pairs = []
        self.shiny_id2jp = {}
        self.shiny_jp2id = {}
        self.species_pairs = []  # [(SPECIES_ID, Name), ...]

        # UI
        self._make_menu()
        self._make_layout()

    # ----------------- メニュー -----------------
    def _make_menu(self):
        m = tk.Menu(self)

        fm = tk.Menu(m, tearoff=0)
        fm.add_command(label="rscフォルダを選択…", command=self.choose_rsc)
        fm.add_command(label="PBSファイルを開く…", command=self.open_pbs)
        fm.add_separator()
        fm.add_command(label="このポケモンだけ保存…", command=self.save_current)
        fm.add_command(label="全体を書き出し…", command=self.export_all)
        fm.add_separator()
        fm.add_command(label="終了", command=self.destroy)

        m.add_cascade(label="ファイル", menu=fm)
        self.config(menu=m)

    # ----------------- レイアウト -----------------
    def _make_layout(self):
        root = ttk.Frame(self); root.pack(fill=tk.BOTH, expand=True)

        # 左：IDリスト
        left = ttk.Frame(root, width=320)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="ポケモン").pack(anchor="w", padx=8, pady=(8, 2))
        self.lb = tk.Listbox(left)
        self.lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        self.lb.bind("<<ListboxSelect>>", self.on_select_id)

        # 右：フォーム（縦スクロールバーのみ。どこでもスクロールは廃止）
        right = ttk.Frame(root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, highlightthickness=0)
        self.vsb = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.form = ttk.Frame(self.canvas)

        self.form.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # ====== ここから「指定順序」でフィールド作成 ======
        self._build_fields()

    # ------------- フィールドの作成（順序固定） -------------
    def _build_fields(self):
        # Name
        self.v_name = tk.StringVar()
        frm, _ = row_text(self.form, "Name", self.v_name); frm.pack(anchor="w", padx=8, pady=4)

        # FormName
        self.v_form = tk.StringVar()
        frm, _ = row_text(self.form, "FormName", self.v_form); frm.pack(anchor="w", padx=8, pady=4)

        # Types（1行2列）
        self.v_type1 = tk.StringVar(); self.v_type2 = tk.StringVar()
        type_values = [f"{id_}:{name}" if id_ else "—" for id_, name in TYPES]
        frm, _ = row_two_combos(self.form, "Types", self.v_type1, self.v_type2, type_values)
        frm.pack(anchor="w", padx=8, pady=4)

        # BaseStats（日本語ラベル）
        self.v_bs = [tk.StringVar() for _ in range(6)]
        frm = row_stats(self.form, STAT_LABELS_JP, self.v_bs)
        frm.pack(anchor="w", padx=8, pady=4)

        # GenderRatio / GrowthRate（選択式）
        self.v_gender = tk.StringVar()
        frm, _ = row_combo(self.form, "GenderRatio", self.v_gender, [f"{k}:{v}" for k, v in GENDER]); frm.pack(anchor="w", padx=8, pady=4)

        self.v_growth = tk.StringVar()
        frm, _ = row_combo(self.form, "GrowthRate", self.v_growth, [f"{k}:{v}" for k, v in GROWTH]); frm.pack(anchor="w", padx=8, pady=4)

        # BaseExp
        self.v_baseexp = tk.StringVar()
        frm, _ = row_number(self.form, "BaseExp", self.v_baseexp); frm.pack(anchor="w", padx=8, pady=4)

        # EVs（6項目）
        self.v_evs = [tk.StringVar() for _ in range(6)]
        frm = row_stats(self.form, ["EV_HP","EV_Atk","EV_Def","EV_SpA","EV_SpD","EV_Spe"], self.v_evs)
        frm.pack(anchor="w", padx=8, pady=4)

        # Happiness
        self.v_happy = tk.StringVar()
        frm, _ = row_number(self.form, "Happiness", self.v_happy); frm.pack(anchor="w", padx=8, pady=4)

        # Abilities / HiddenAbilities / UniqueAbilities / ShinyUnique（各コンボ）
        self.v_abilities = tk.StringVar()
        frm, _ = row_text(self.form, "Abilities", self.v_abilities)  # 後で rsc 読み込み時に combobox化も可能
        frm.pack(anchor="w", padx=8, pady=4)

        self.v_hidden = tk.StringVar()
        frm, _ = row_text(self.form, "HiddenAbilities", self.v_hidden)
        frm.pack(anchor="w", padx=8, pady=4)

        self.v_unique = tk.StringVar()
        frm, _ = row_text(self.form, "UniqueAbilities", self.v_unique)
        frm.pack(anchor="w", padx=8, pady=4)

        # ShinyUnique（abilities_shiny.txt）
        self.v_shiny = tk.StringVar()
        self.row_shiny, self.shiny_widget = row_text(self.form, "ShinyUnique", self.v_shiny)
        self.row_shiny.pack(anchor="w", padx=8, pady=4)

        # わざ編集ボタン 3つ（レベル→教え→タマゴ の順）
        btns = ttk.Frame(self.form); btns.pack(anchor="w", padx=8, pady=4)
        ttk.Button(btns, text="レベル技を編集…", command=self.edit_level_moves).pack(side=tk.LEFT)
        ttk.Button(btns, text="教え技を編集…", command=self.edit_tutor_moves).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="タマゴ技を編集…", command=self.edit_egg_moves).pack(side=tk.LEFT)

        # EggGroups（2枠）
        self.v_egg1 = tk.StringVar(); self.v_egg2 = tk.StringVar()
        egg_vals = [f"{k}:{v}" for k,v in EGG_GROUPS]
        frm, _ = row_two_combos(self.form, "EggGroups", self.v_egg1, self.v_egg2, egg_vals)
        frm.pack(anchor="w", padx=8, pady=4)

        # HatchSteps
        self.v_hatch = tk.StringVar()
        frm, _ = row_number(self.form, "HatchSteps", self.v_hatch); frm.pack(anchor="w", padx=8, pady=4)

        # Incense / Offspring（1行）
        row_io = ttk.Frame(self.form); row_io.pack(anchor="w", fill="x", padx=8, pady=4)
        ttk.Label(row_io, text="Incense", width=16).pack(side=tk.LEFT)
        self.v_incense = tk.StringVar()
        self.cmb_incense = ttk.Combobox(row_io, textvariable=self.v_incense, state="readonly", width=30)
        self.cmb_incense.pack(side=tk.LEFT, padx=(0,8))
        ttk.Label(row_io, text="Offspring", width=16).pack(side=tk.LEFT)
        self.v_offspring = tk.StringVar()
        self.cmb_offspring = ttk.Combobox(row_io, textvariable=self.v_offspring, state="readonly", width=30)
        self.cmb_offspring.pack(side=tk.LEFT)

        # Height / Weight（1行）
        row_hw = ttk.Frame(self.form); row_hw.pack(anchor="w", fill="x", padx=8, pady=4)
        ttk.Label(row_hw, text="Height", width=16).pack(side=tk.LEFT)
        self.v_height = tk.StringVar()
        ttk.Entry(row_hw, textvariable=self.v_height, width=10).pack(side=tk.LEFT, padx=(0,8))
        ttk.Label(row_hw, text="Weight", width=16).pack(side=tk.LEFT)
        self.v_weight = tk.StringVar()
        ttk.Entry(row_hw, textvariable=self.v_weight, width=10).pack(side=tk.LEFT)

        # Color / Shape（1行）
        row_cs = ttk.Frame(self.form); row_cs.pack(anchor="w", fill="x", padx=8, pady=4)
        ttk.Label(row_cs, text="Color", width=16).pack(side=tk.LEFT)
        self.v_color = tk.StringVar()
        ttk.Combobox(row_cs, textvariable=self.v_color, values=[f"{k}:{v}" for k,v in COLORS], state="readonly", width=20).pack(side=tk.LEFT, padx=(0,8))
        ttk.Label(row_cs, text="Shape", width=16).pack(side=tk.LEFT)
        self.v_shape = tk.StringVar()
        ttk.Combobox(row_cs, textvariable=self.v_shape, values=[f"{k}:{v}" for k,v in SHAPES], state="readonly", width=20).pack(side=tk.LEFT)

        # Habitat
        self.v_habitat = tk.StringVar()
        frm, _ = row_combo(self.form, "Habitat", self.v_habitat, [f"{k}:{v}" for k,v in HABITATS]); frm.pack(anchor="w", padx=8, pady=4)

        # Category
        self.v_category = tk.StringVar()
        frm, _ = row_text(self.form, "Category", self.v_category); frm.pack(anchor="w", padx=8, pady=4)

        # Pokedex
        self.v_pokedex = tk.StringVar()
        frm, _ = row_text(self.form, "Pokedex", self.v_pokedex); frm.pack(anchor="w", padx=8, pady=4)

        # Generation
        self.v_generation = tk.StringVar()
        frm, _ = row_number(self.form, "Generation", self.v_generation); frm.pack(anchor="w", padx=8, pady=4)

        # Flags（テキスト or 後でチェック群に差し替え可能）
        self.v_flags = tk.StringVar()
        frm, _ = row_text(self.form, "Flags", self.v_flags); frm.pack(anchor="w", padx=8, pady=4)

        # WildItemCommon / Uncommon / Rare（アイテムから選択）
        self.v_wild_c = tk.StringVar(); self.v_wild_u = tk.StringVar(); self.v_wild_r = tk.StringVar()
        frm, _ = row_combo(self.form, "WildItemCommon", self.v_wild_c, []); frm.pack(anchor="w", padx=8, pady=4)
        frm, _ = row_combo(self.form, "WildItemUncommon", self.v_wild_u, []); frm.pack(anchor="w", padx=8, pady=4)
        frm, _ = row_combo(self.form, "WildItemRare", self.v_wild_r, []); frm.pack(anchor="w", padx=8, pady=4)

        # 進化を編集（ボタン）
        evofrm = ttk.Frame(self.form); evofrm.pack(anchor="w", padx=8, pady=4)
        ttk.Button(evofrm, text="進化を編集…", command=self.edit_evolutions).pack(side=tk.LEFT)

        # RivalSpecies
        self.v_rival = tk.StringVar()
        frm, _ = row_combo(self.form, "RivalSpecies", self.v_rival, []); frm.pack(anchor="w", padx=8, pady=4)

        # SpeciesSOS
        self.v_soss = tk.StringVar()
        frm, _ = row_combo(self.form, "SpeciesSOS", self.v_soss, []); frm.pack(anchor="w", padx=8, pady=4)

        # CallRateSOS
        self.v_callrate = tk.StringVar()
        frm, _ = row_number(self.form, "CallRateSOS", self.v_callrate); frm.pack(anchor="w", padx=8, pady=4)

        # 動作ボタン（下部）
        btns = ttk.Frame(self.form); btns.pack(anchor="w", padx=8, pady=8)
        ttk.Button(btns, text="このポケモンだけ保存", command=self.save_current).pack(side=tk.LEFT)
        ttk.Button(btns, text="全体を書き出し", command=self.export_all).pack(side=tk.LEFT, padx=8)

    # ----------------- rsc 読み込み -----------------
    def choose_rsc(self):
        d = filedialog.askdirectory(title="rscフォルダを選択")
        if not d: return
        self.rsc_dir = d

        # moves*.txt → 技候補
        self.moves_list = self._load_rsc_pairs_multi(prefix="moves")
        # items.txt → アイテム（Incense/野生アイテム）
        self.items_pairs = self._load_rsc_pairs_single("items.txt")
        self.items_id2jp = {k:v for k,v in self.items_pairs}
        self.items_jp2id = {v:k for k,v in self.items_pairs}
        incense_jp = [v for k,v in self.items_pairs if k.upper().endswith("INCENSE")]
        self.cmb_incense["values"] = incense_jp if incense_jp else [v for _,v in self.items_pairs]
        item_vals = [v for _,v in self.items_pairs]
        for cmb in (self._get_combo("WildItemCommon"), self._get_combo("WildItemUncommon"), self._get_combo("WildItemRare")):
            cmb["values"] = item_vals

        # abilities.txt / abilities_unique.txt / abilities_shiny.txt
        self.abilities_pairs = self._load_rsc_pairs_single("abilities.txt")
        self.uniq_pairs      = self._load_rsc_pairs_single("abilities_unique.txt")
        self.shiny_pairs     = self._load_rsc_pairs_single("abilities_shiny.txt")

        self.abilities_id2jp = {k:v for k,v in self.abilities_pairs}
        self.abilities_jp2id = {v:k for k,v in self.abilities_pairs}
        self.uniq_id2jp      = {k:v for k,v in self.uniq_pairs}
        self.uniq_jp2id      = {v:k for k,v in self.uniq_pairs}
        self.shiny_id2jp     = {k:v for k,v in self.shiny_pairs}
        self.shiny_jp2id     = {v:k for k,v in self.shiny_pairs}

        # 種族候補（PBS 読み込み後に反映）
        self._refresh_species_combos()

        messagebox.showinfo("rsc", f"rsc を読み込みました：\n{d}")

    def _load_rsc_pairs_single(self, filename):
        path = os.path.join(self.rsc_dir, filename)
        if not (self.rsc_dir and os.path.isfile(path)): return []
        return self._read_pairs_any(path)

    def _load_rsc_pairs_multi(self, prefix):
        res = {}
        if not (self.rsc_dir and os.path.isdir(self.rsc_dir)): return []
        for nm in os.listdir(self.rsc_dir):
            low = nm.lower()
            if low.startswith(prefix) and low.endswith(".txt"):
                for k,v in self._read_pairs_any(os.path.join(self.rsc_dir, nm)):
                    res[k] = v
        return sorted(res.items())

    def _read_pairs_any(self, path):
        pairs = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or line.startswith(";"): continue
                if line.startswith("[") and "]" in line and "=" in line:
                    # PBS形式 [ID] ... Name=日本語
                    if line.startswith("[") and line.endswith("]"):
                        cur_id = line.strip("[]").strip()
                        # 探索モード（簡易）
                        # 実用十分：別のセクションに到達するまで Name= を拾う
                        # ここでは簡易のため、直後に Name= の行が来たと仮定
                    continue
                # CSV/TSV/Colon のゆるい対応
                if ":" in line and "," not in line and "\t" not in line:
                    k, v = line.split(":", 1)
                elif "\t" in line and "," not in line:
                    k, v = line.split("\t", 1)
                else:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) < 2: continue
                    k, v = parts[0], parts[1]
                pairs.append((k.strip(), v.strip()))
        return pairs

    def _get_combo(self, label_text):
        # フォーム上の該当 row_combo の Combobox を簡易取得
        for child in self.form.winfo_children():
            # row_comboは (Frame, Combobox) を返している想定
            try:
                if isinstance(child, ttk.Frame):
                    lbls = [w for w in child.winfo_children() if isinstance(w, ttk.Label)]
                    if lbls and lbls[0].cget("text") == label_text:
                        combos = [w for w in child.winfo_children() if isinstance(w, ttk.Combobox)]
                        if combos:
                            return combos[-1]
            except:
                pass
        # 見つからなければダミー
        return ttk.Combobox(self.form)

    # ----------------- PBS 読み込み -----------------
    def open_pbs(self):
        path = filedialog.askopenfilename(
            title="PBSファイルを開く",
            filetypes=[("Text", "*.txt"), ("All", "*.*")]
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        self.original_text = txt

        secs = parsePBS(txt)
        self.sections = secs
        self.sec_by_id = {s["id"]: s for s in secs}

        # 左のリスト
        self.lb.delete(0, tk.END)
        for s in secs:
            name = s["kv"].get("Name", "")
            self.lb.insert(tk.END, f"{s['id']} — {name}")
        if secs:
            default = "BULBASAUR" if "BULBASAUR" in self.sec_by_id else secs[0]["id"]
            self.lb.select_set(0)
            self.load_section(default)

        # 種族候補を更新（Rival/Offspring/SOS）
        self._refresh_species_combos()

    def _refresh_species_combos(self):
        if not self.sec_by_id:
            return
        ids = list(self.sec_by_id.keys())
        self.species_pairs = [(sid, self.sec_by_id[sid]['kv'].get('Name','')) for sid in ids]
        disp = [f"{sid} — {self.sec_by_id[sid]['kv'].get('Name','')}" for sid in ids]
        self.cmb_offspring["values"] = disp
        self._get_combo("RivalSpecies")["values"] = disp
        self._get_combo("SpeciesSOS")["values"] = disp

    # ----------------- 選択反映 -----------------
    def on_select_id(self, event=None):
        i = self.lb.curselection()
        if not i: return
        sec = self.sections[i[0]]
        self.current_id = sec["id"]
        self._load_to_form(sec)

    def _id2jp(self, pairs, id_):
        return dict(pairs).get(id_, id_)

    def _split_idjp(self, s):
        # "ID:日本語" → (ID, 日本語)
        if ":" in s:
            a,b = s.split(":",1); return a.strip(), b.strip()
        return s.strip(), s.strip()

    def _load_to_form(self, sec):
        kv = sec["kv"]; g = kv.get

        self.v_name.set(g("Name",""))
        self.v_form.set(g("FormName",""))

        # Types
        t = (g("Types","") or "").split(",")
        t1 = t[0].strip() if len(t)>0 else ""
        t2 = t[1].strip() if len(t)>1 else ""
        jp1 = next((n for i,n in TYPES if i==t1), t1 or "—")
        jp2 = next((n for i,n in TYPES if i==t2), t2 or "—")
        self.v_type1.set(f"{t1}:{jp1}" if t1 else "—")
        self.v_type2.set(f"{t2}:{jp2}" if t2 else "—")

        # BaseStats
        bs = (g("BaseStats","") or "").split(",")
        for idx in range(6):
            self.v_bs[idx].set(bs[idx].strip() if idx < len(bs) else "")

        # Gender / Growth
        self.v_gender.set(f"{g('GenderRatio','')}:" + next((v for k,v in GENDER if k==g("GenderRatio","")), g("GenderRatio","")))
        self.v_growth.set(f"{g('GrowthRate','')}:" + next((v for k,v in GROWTH if k==g("GrowthRate","")), g("GrowthRate","")))

        self.v_baseexp.set(g("BaseExp",""))

        # EVs
        ev_map = {"HP":0,"ATTACK":1,"DEFENSE":2,"SPECIAL_ATTACK":3,"SPECIAL_DEFENSE":4,"SPEED":5,"ATK":1,"DEF":2,"SPA":3,"SPD":4,"SPE":5}
        for j in range(6): self.v_evs[j].set("")
        parts = (g("EVs","") or "").replace(",", " ").split()
        for k, v in zip(parts[::2], parts[1::2]):
            kk = k.strip().upper(); idx = ev_map.get(kk, None)
            if idx is not None: self.v_evs[idx].set(v.strip())

        self.v_happy.set(g("Happiness",""))

        # Abilities
        self.v_abilities.set(g("Abilities",""))
        self.v_hidden.set(g("HiddenAbilities",""))
        self.v_unique.set(g("UniqueAbilities",""))
        self.v_shiny.set(g("ShinyUnique",""))

        # EggGroups
        eg = [x.strip() for x in (g("EggGroups","") or "").split(",") if x.strip()]
        self.v_egg1.set(eg[0] if len(eg)>0 else "")
        self.v_egg2.set(eg[1] if len(eg)>1 else "")

        self.v_hatch.set(g("HatchSteps",""))

        # Incense / Offspring
        self.v_incense.set(self.items_id2jp.get(g("Incense",""), g("Incense","")))
        off = g("Offspring","")
        self.v_offspring.set(next((f"{sid} — {nm}" for sid,nm in self.species_pairs if sid==off), off))

        # Height/Weight
        self.v_height.set(g("Height",""))
        self.v_weight.set(g("Weight",""))

        # Color/Shape/Habitat
        self.v_color.set(f"{g('Color','')}:" + next((v for k,v in COLORS if k==g("Color","")), g("Color","")))
        self.v_shape.set(f"{g('Shape','')}:" + next((v for k,v in SHAPES if k==g("Shape","")), g("Shape","")))
        self.v_habitat.set(f"{g('Habitat','')}:" + next((v for k,v in HABITATS if k==g("Habitat","")), g("Habitat","")))

        self.v_category.set(g("Category",""))
        self.v_pokedex.set(g("Pokedex",""))
        self.v_generation.set(g("Generation",""))

        self.v_flags.set(g("Flags",""))

        # Wild Items
        self.v_wild_c.set(self.items_id2jp.get(g("WildItemCommon",""), g("WildItemCommon","")))
        self.v_wild_u.set(self.items_id2jp.get(g("WildItemUncommon",""), g("WildItemUncommon","")))
        self.v_wild_r.set(self.items_id2jp.get(g("WildItemRare",""), g("WildItemRare","")))

        # Rival/SOS
        self.v_rival.set(next((f"{sid} — {nm}" for sid,nm in self.species_pairs if sid==g("RivalSpecies","")), g("RivalSpecies","")))
        self.v_soss.set(next((f"{sid} — {nm}" for sid,nm in self.species_pairs if sid==g("SpeciesSOS","")), g("SpeciesSOS","")))

        self.v_callrate.set(g("CallRateSOS",""))

        # Movesは別ダイアログで編集、ここでは保持しない（元テキストを使う想定）

    # ----------------- 反映（フォーム → セクション） -----------------
    def apply_to_current(self):
        if not self.current_id: return
        sec = self.sec_by_id[self.current_id]
        kv = sec["kv"]

        def setkv(k, v):
            v = ("" if v is None else str(v)).strip()
            if v == "": kv.pop(k, None)
            else: kv[k] = v

        setkv("Name", self.v_name.get())
        setkv("FormName", self.v_form.get())

        # Types
        t1 = self._split_idjp(self.v_type1.get())[0] if self.v_type1.get() and self.v_type1.get()!="—" else ""
        t2 = self._split_idjp(self.v_type2.get())[0] if self.v_type2.get() and self.v_type2.get()!="—" else ""
        setkv("Types", ",".join([x for x in (t1, t2) if x]))

        # BaseStats
        bs = ",".join(v.get().strip() for v in self.v_bs)
        setkv("BaseStats", bs)

        # Gender/Growth
        setkv("GenderRatio", self._split_idjp(self.v_gender.get())[0])
        setkv("GrowthRate", self._split_idjp(self.v_growth.get())[0])

        setkv("BaseExp", self.v_baseexp.get())

        # EVs
        ev_keys = ["HP","ATTACK","DEFENSE","SPECIAL_ATTACK","SPECIAL_DEFENSE","SPEED"]
        ev_parts = []
        for lab, var in zip(ev_keys, self.v_evs):
            val = var.get().strip()
            if val and val != "0":
                ev_parts.append(f"{lab},{val}")
        setkv("EVs", " ".join(ev_parts))

        setkv("Happiness", self.v_happy.get())

        # Abilities など（今はテキスト/自由入力。将来コンボ化可）
        setkv("Abilities", self.v_abilities.get())
        setkv("HiddenAbilities", self.v_hidden.get())
        setkv("UniqueAbilities", self.v_unique.get())
        setkv("ShinyUnique", self.v_shiny.get())

        # EggGroups
        eg1 = self._split_idjp(self.v_egg1.get())[0] if self.v_egg1.get() else ""
        eg2 = self._split_idjp(self.v_egg2.get())[0] if self.v_egg2.get() else ""
        setkv("EggGroups", ",".join([x for x in (eg1, eg2) if x]))

        setkv("HatchSteps", self.v_hatch.get())

        # Incense/Offspring
        inc_id = self.items_jp2id.get(self.v_incense.get().strip(), self.v_incense.get().strip())
        setkv("Incense", inc_id)
        off = self.v_offspring.get().strip()
        off_id = off.split("—",1)[0].strip() if "—" in off else off
        setkv("Offspring", off_id)

        # Height/Weight
        setkv("Height", self.v_height.get())
        setkv("Weight", self.v_weight.get())

        # Color/Shape/Habitat
        setkv("Color", self._split_idjp(self.v_color.get())[0])
        setkv("Shape", self._split_idjp(self.v_shape.get())[0])
        setkv("Habitat", self._split_idjp(self.v_habitat.get())[0])

        # Category / Pokedex / Generation
        setkv("Category", self.v_category.get())
        setkv("Pokedex", self.v_pokedex.get())
        setkv("Generation", self.v_generation.get())

        # Flags
        setkv("Flags", self.v_flags.get())

        # Wild Items
        setkv("WildItemCommon", self.items_jp2id.get(self.v_wild_c.get().strip(), self.v_wild_c.get().strip()))
        setkv("WildItemUncommon", self.items_jp2id.get(self.v_wild_u.get().strip(), self.v_wild_u.get().strip()))
        setkv("WildItemRare", self.items_jp2id.get(self.v_wild_r.get().strip(), self.v_wild_r.get().strip()))

        # Rival/SOS
        rv = self.v_rival.get().strip(); setkv("RivalSpecies", rv.split("—",1)[0].strip() if "—" in rv else rv)
        ss = self.v_soss.get().strip(); setkv("SpeciesSOS", ss.split("—",1)[0].strip() if "—" in ss else ss)

        # CallRateSOS
        setkv("CallRateSOS", self.v_callrate.get())

    # ----------------- 保存 -----------------
    def save_current(self):
        if not self.current_id:
            messagebox.showinfo("保存", "ポケモンが選択されていません。"); return
        self.apply_to_current()
        sec = self.sec_by_id[self.current_id]
        block = stringify_section(sec)
        path = filedialog.asksaveasfilename(
            title="このポケモンだけ保存",
            defaultextension=".txt",
            initialfile=f"{self.current_id}.pbs.txt",
            filetypes=[("Text","*.txt"),("All","*.*")]
        )
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write(block.rstrip("\n") + "\n")
        messagebox.showinfo("保存", "書き出しました。")

    def export_all(self):
        if not self.original_text:
            messagebox.showinfo("書き出し", "先にPBSファイルを開いてください。"); return
        if self.current_id:
            self.apply_to_current()
        text = self.original_text
        for s in self.sections:
            snap = self.sec_by_id.get(s["id"])
            if snap:
                text = replace_section_in_text(text, snap)
        path = filedialog.asksaveasfilename(
            title="全体ファイルを書き出し",
            defaultextension=".txt",
            initialfile="pokemon_Gen1_edited.txt",
            filetypes=[("Text","*.txt"),("All","*.*")]
        )
        if not path: return
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("保存", "全体を書き出しました。")

    # ----------------- ダイアログ（わざ/進化） -----------------
    def edit_level_moves(self):
        if not self.moves_list:
            messagebox.showwarning("moves", "先に rsc で moves*.txt を読み込んでください。")
            return
        # 既存文字列はセクションから取り直す
        cur = self.sec_by_id[self.current_id]["kv"].get("Moves","") if self.current_id else ""
        dlg = MovesDialog(self, [m for _,m in self.moves_list], title="レベル技の編集", with_level=True, initial=[p for p in cur.split() if p.strip()])
        self.wait_window(dlg)
        if dlg.result is not None:
            self.sec_by_id[self.current_id]["kv"]["Moves"] = " ".join(dlg.result)

    def edit_tutor_moves(self):
        if not self.moves_list:
            messagebox.showwarning("moves", "先に rsc で moves*.txt を読み込んでください。")
            return
        cur = self.sec_by_id[self.current_id]["kv"].get("TutorMoves","") if self.current_id else ""
        dlg = MovesDialog(self, [m for _,m in self.moves_list], title="教え技の編集", with_level=False, initial=[p for p in cur.split() if p.strip()])
        self.wait_window(dlg)
        if dlg.result is not None:
            self.sec_by_id[self.current_id]["kv"]["TutorMoves"] = " ".join(dlg.result)

    def edit_egg_moves(self):
        if not self.moves_list:
            messagebox.showwarning("moves", "先に rsc で moves*.txt を読み込んでください。")
            return
        cur = self.sec_by_id[self.current_id]["kv"].get("EggMoves","") if self.current_id else ""
        dlg = MovesDialog(self, [m for _,m in self.moves_list], title="タマゴ技の編集", with_level=False, initial=[p for p in cur.split() if p.strip()])
        self.wait_window(dlg)
        if dlg.result is not None:
            self.sec_by_id[self.current_id]["kv"]["EggMoves"] = " ".join(dlg.result)

    def edit_evolutions(self):
        if not self.sections:
            messagebox.showwarning("進化", "先に PBS を読み込んでください。"); return
        # 候補
        species_disp = [sid for sid,_ in self.species_pairs]  # EvoDialogはID配列でOK
        items_ids = [k for k,_ in self.items_pairs]
        moves_ids = [k for k,_ in self.moves_list]
        cur = self.sec_by_id[self.current_id]["kv"].get("Evolutions","") if self.current_id else ""
        dlg = EvoDialog(self,
                        species_list=species_disp,
                        items_list=items_ids,
                        moves_list=moves_ids,
                        title="進化の編集",
                        initial=[p for p in cur.split() if p.strip()])
        self.wait_window(dlg)
        if dlg.result is not None:
            self.sec_by_id[self.current_id]["kv"]["Evolutions"] = " ".join(dlg.result)

if __name__ == "__main__":
    App().mainloop()

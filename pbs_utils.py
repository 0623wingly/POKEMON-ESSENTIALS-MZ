# pbs_utils.py — PBSテキストの解析/整形/置換ユーティリティ
# 役割：
#   - parsePBS(text): PBSファイル文字列 → セクション配列([{id, kv, order}, ...])
#   - stringify_section(sec): セクションdict → PBSブロック文字列（[ID] 行から）
#   - replace_section_in_text(text, sec): 元テキスト内の当該セクションを丸ごと置換（堅牢版）

from __future__ import annotations
import re
import os
from typing import Dict, List, Tuple

# 区切り行（Essentials の PBS でよくあるやつ）
SEP_LINE = "#-------------------------------"


# ------------------------------------------------------------
# 低レベル：改行正規化
# ------------------------------------------------------------
def _to_lf(s: str) -> str:
    """CRLF/CR を LF に正規化"""
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _from_lf(s: str) -> str:
    """実行環境の改行コードに戻す（Windowsなら CRLF）"""
    if os.linesep != "\n":
        return s.replace("\n", os.linesep)
    return s


# ------------------------------------------------------------
# 解析：PBS → セクション配列
# ------------------------------------------------------------
def parsePBS(text: str) -> List[Dict]:
    """
    PBSライクなテキストを解析して、セクションの配列を返す。
    セクションは以下の構造:
      { "id": "BULBASAUR", "kv": {"Name": "フシギダネ", ...}, "order": ["Name","FormName",...] }

    前提フォーマット：
      #-------------------------------
      [ID]
      Key = Value
      Key2 = Value2
      ...
      #-------------------------------
      [NEXT_ID]
      ...
    """
    src = _to_lf(text)
    sections: List[Dict] = []

    # 先頭 or 改行 → 区切り行 → [ID] → 本文 → 次の区切り or EOF
    pat = re.compile(r"(?:^|\n)#-+\n\[([A-Z0-9_\-\.]+)\]([\s\S]*?)(?=(\n#-+\n\[|$))")

    for m in pat.finditer(src):
        sid = m.group(1).strip()
        body = m.group(2)
        kv: Dict[str, str] = {}
        order: List[str] = []

        for raw in body.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                kv[k] = v
                order.append(k)
        sections.append({"id": sid, "kv": kv, "order": order})
    return sections


# ------------------------------------------------------------
# 整形：セクションdict → PBSブロック文字列
# ------------------------------------------------------------
def stringify_section(sec: Dict) -> str:
    """
    セクションdict（{id,kv,order}）を PBS ブロック文字列に変換。
    [ID] の次に、元の order を尊重して Key = Value を並べ、
    その後に新規キー（orderに無いもの）を追加する。
    """
    lines: List[str] = [f"[{sec['id']}]"]
    kv: Dict[str, str] = sec.get("kv", {})
    seen = set()

    # まずは元の順番
    for k in sec.get("order", []):
        if k in kv and k not in seen:
            lines.append(f"{k} = {kv[k]}")
            seen.add(k)
    # 追加分（新規キー）
    for k, v in kv.items():
        if k not in seen:
            lines.append(f"{k} = {v}")
    return "\n".join(lines)


# ------------------------------------------------------------
# 置換：元テキスト中の当該セクションを丸ごと差し替え（堅牢）
# ------------------------------------------------------------
def replace_section_in_text(text: str, sec: Dict) -> str:
    """
    元テキスト内の [ID] セクション全体を置換。
    - 改行をLF化 → マッチ＆置換 → 余計な空行の圧縮 → 末尾は改行1つ → OSの改行へ戻す
    - セクションが見つからなければ末尾に追記
    """
    src = _to_lf(text)
    sid = re.escape(sec["id"])

    # 例：\n#----\n[ID] ... （次の区切り or EOF まで）
    pat = re.compile(rf"(?:^|\n)#-+\n\[{sid}\][\s\S]*?(?=(\n#-+\n\[|$))", re.DOTALL)

    block = stringify_section(sec).strip()
    replacement = f"\n{SEP_LINE}\n{block}\n"  # 末尾は改行1つ

    if pat.search(src):
        out = pat.sub(replacement, src, count=1)
    else:
        # 末尾追記時、改行を増やしすぎない
        out = re.sub(r"\n+$", "\n", src) + replacement

    # 連続3行以上の空行は2行に圧縮（お好みで調整可）
    out = re.sub(r"\n{3,}", "\n\n", out)
    # ファイル末尾は改行1つだけ
    out = out.rstrip("\n") + "\n"

    return _from_lf(out)

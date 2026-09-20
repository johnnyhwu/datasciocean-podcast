"""產生 show notes,並且當發布前的最後一道 gate。

素材全部是現成的:`episodes/<slug>/<lang>.json` 有逐字稿與章節標記,
`meta.json` 有集數層級的標題與重點,音檔長度加上 stitch.py 的停頓規則
就是時間戳記。時間戳記幾乎零成本,但部分平台會直接渲染成可點擊章節。

**gate 的部分才是重點。** Apple Podcasts 第 1.11 條要求 AI 生成的音訊
必須在「內容本身」與「metadata」兩處揭露。這支腳本檢查音訊那處確實存在,
並固定輸出 metadata 那處。漏掉的代價是整集下架,所以不通過就不產出檔案。

用法:uv run python pipeline/shownotes.py out/<slug>/<lang>
"""
import json
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from brand import (AUDIO_DISCLOSURE, FOOTER, META_DISCLOSURE, SHIP_RATE, SHOW)
from stitch import gap_for          # 停頓規則只有一份,時間戳才對得上音檔


def timeline(out_dir: Path, rows):
    """每段的起始秒數。

    優先讀 `MIX.json` —— 加了片頭音樂與章節轉場之後,時間軸整個往後推,
    自己重算一定會錯(片頭把所有東西推後約 6.5 秒,每次轉場再推 5.4 秒)。
    那份檔案是 `assemble.py` 混音時寫的,是唯一知道真實位置的來源。
    沒有混音成品時(還在驗證逐字稿的階段)才退回依 stitch.py 的規則重算。
    """
    mix = out_dir / "MIX.json"
    if mix.exists():
        d = json.loads(mix.read_text())
        rate = d.get("rate", 1.0)
        if abs(rate - SHIP_RATE) > 1e-9:
            raise SystemExit(
                f"✗ MIX.json 是 {rate}x 的時間軸,交付速度是 {SHIP_RATE}x。\n"
                f"  章節時間會差約 {abs(1 - rate / SHIP_RATE) * 100:.0f}%。\n"
                f"  重跑:assemble.py {out_dir} --intro … --rate {SHIP_RATE}")
        return d["marks"], d["total_s"]
    t, marks = 0.0, {}
    for r in rows:
        w = out_dir / f"{r['id']}.wav"
        if not w.exists():
            continue
        marks[r["id"]] = t
        info = sf.info(str(w))
        t += info.frames / info.samplerate + gap_for(r)
    return marks, t


def hhmmss(s: float) -> str:
    s = int(s)
    return f"{s//3600}:{s//60%60:02d}:{s%60:02d}" if s >= 3600 \
        else f"{s//60}:{s%60:02d}"


def main():
    out_dir = Path(sys.argv[1]).resolve()
    lang, slug = out_dir.name, out_dir.parent.name
    if lang not in SHOW:
        raise SystemExit(f"目錄最後一層要是語言(zh/en),讀到「{lang}」")

    ep_dir = Path(__file__).parent.parent / "episodes" / slug
    rows = json.loads((ep_dir / f"{lang}.json").read_text())
    meta = json.loads((ep_dir / "meta.json").read_text())
    m, show = meta[lang], SHOW[lang]

    # --- gate 1:音訊內揭露 -------------------------------------------
    ident = [r for r in rows if r.get("role") == "identity"]
    if not ident:
        raise SystemExit("✗ 找不到 identity beat,無法確認 AI 揭露")
    if not any(AUDIO_DISCLOSURE[lang].search(r["text"]) for r in ident):
        raise SystemExit(
            f"✗ identity beat 裡沒有 AI 揭露(Apple Podcasts 1.11)。\n"
            f"  現有內容:{ident[0]['text'][:60]}…\n"
            f"  改稿後要重新合成該段,不能只改 show notes。")

    # --- gate 2:章節 -------------------------------------------------
    chapters = [r for r in rows if r.get("chapter")]
    if len(chapters) < 4:
        raise SystemExit(f"✗ 只有 {len(chapters)} 個章節標記,至少要 4 個。"
                         f"在 beats 的 signpost 段加 \"chapter\" 欄位。")

    marks, total = timeline(out_dir, rows)
    url = show["post"].format(article=meta["article"])

    L = [f"# {m['title']}", "", m["summary"], ""]
    L += [f"**{'這集你會知道' if lang == 'zh' else 'In this episode'}**", ""]
    L += [f"- {b}" for b in m["bullets"]] + [""]
    L += [f"**{'章節' if lang == 'zh' else 'Chapters'}**", ""]
    for r in chapters:
        if r["id"] in marks:
            L.append(f"- {hhmmss(marks[r['id']])} {r['chapter']}")
    L += ["", f"**{'原文' if lang == 'zh' else 'Read the original'}**", "",
          f"{FOOTER[lang]}", "", f"{url}", "",
          "---", "", META_DISCLOSURE[lang], ""]

    dst = out_dir / "SHOWNOTES.md"
    dst.write_text("\n".join(L))

    # 標題在 app 列表裡會被截斷,所以直接把截斷後的樣子印出來 ——
    # 這比訂一個字數上限有用:重點不是「幾個字」,是「被切掉之後還剩什麼」。
    cut = 25 if lang == "zh" else 45
    print(f"{slug}/{lang}  {hhmmss(total)}  {len(chapters)} 章")
    print(f"  標題 {len(m['title'])} 字元:{m['title']}")
    if len(m["title"]) > cut:
        print(f"  列表只看得到:{m['title'][:cut]}…")
    print(f"  ✓ 音訊揭露  ✓ metadata 揭露  ✓ 原文連結 {url}")
    print(f"-> {dst}")


if __name__ == "__main__":
    main()

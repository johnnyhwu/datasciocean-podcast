"""改了正規化規則之後,拿 report.json 裡既有的轉錄結果重新算分。

存在的理由很單純:每次調整 verify.py 的正規化都要重跑一次 Whisper,
一集要十分鐘,而轉錄結果本身沒變 —— 重算的只是比對。

用法:
    uv run python pipeline/rescore.py <out_dir> [--write]

預設只印出差異;加 --write 才會寫回 report.json。
"""
import sys, json, difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify import spoken_form, detect_lang, SPEED


def main():
    d = Path(sys.argv[1])
    rows = json.loads((d / "report.json").read_text())
    lang = detect_lang([r.get("text", "") for r in rows])
    sp = SPEED[lang]

    moved = []
    for r in rows:
        if "transcribed" not in r:
            continue
        a, b = spoken_form(r["text"], lang), spoken_form(r["transcribed"], lang)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        new = round(sm.ratio(), 3)
        old = r.get("similarity")
        cps = r.get("chars_per_sec", 0)
        flags = []
        if cps and cps < sp["runaway"]:  flags.append("失控")
        elif cps > sp["high"]:           flags.append("過快")
        elif cps and cps < sp["low"]:    flags.append("偏慢")
        if new < 0.90:                   flags.append("STT差異大")
        if len(b) > len(a) * 1.15:       flags.append("疑似幽靈音")
        if old != new:
            moved.append((r["id"], old, new))
        r["similarity"], r["flags"] = new, flags
        r["diffs"] = [f"預期「{a[i1:i2]}」→實際「{b[j1:j2]}」"
                      for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"][:10]

    print(f"{d.name}[{lang}]:{len(moved)} 段分數變動")
    for i, o, n in sorted(moved, key=lambda x: x[2] - (x[1] or 0)):
        print(f"  {i:26s} {o} -> {n}")
    scored = [r for r in rows if "similarity" in r]
    clean = [r for r in scored if not r["flags"]]
    avg = sum(r["similarity"] for r in scored) / len(scored)
    print(f"=== {len(clean)}/{len(scored)} 無標記,平均 sim={avg:.3f} ===")
    bad = [r["id"] for r in scored if r["flags"]]
    if bad:
        print("需要人耳確認:", ", ".join(bad))
    if "--write" in sys.argv:
        (d / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        print("已寫回 report.json")


if __name__ == "__main__":
    main()

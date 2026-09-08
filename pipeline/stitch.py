"""把一集的 beat 片段拼接成完整音檔,beat 之間以靜音分隔。

對應 plan.md pipeline 步驟 [10]。用法:uv run python pipeline/stitch.py <out_dir>

這一步驗證的是「整集聽起來如何」,
而不只是單句 —— 節奏、停頓長度、語氣連貫性只有連續聽才判斷得出來。

停頓長度設計:
  hook 之後停久一點(讓問題沉澱),一般 beat 之間 0.6s,
  段落轉折 1.0s。這些值需要人耳驗證後調整。
"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf

# 取樣率由第一個片段決定
SR = None
GAP_DEFAULT = 0.6

# 停頓綁 role 而非 beat id。先前綁 id 的版本 key 全部拼錯(ep01_hook vs b00_hook),
# 導致整集 28 個接縫都是 0.6s — 連 hook 之後的沉澱停頓都沒發生。
# role 由 beat 自己宣告,拼錯會在下面的檢查中被抓出來。
GAP_BY_ROLE = {
    "hook": 1.2,
    "identity": 0.9,
    "turn": 1.0,
    "payoff": 1.0,
    "recap": 0.9,
    "promise": 1.0,    # 「你會學到什麼」講完要讓它沉澱
    "signpost": 0.4,   # 路標要接得緊,停久了反而斷
}


def gap_for(row):
    """取 beat 的停頓長度。role 缺漏時退回 id 前綴猜測,並回報。"""
    role = row.get("role")
    if role:
        if role not in GAP_BY_ROLE and role not in ("context", "mechanism",
                                                    "evidence", "critique",
                                                    "opinion", "outro",
                                                    "analogy", "promise"):
            print(f"  ⚠ 未知 role「{role}」({row['id']}),用預設停頓")
        return GAP_BY_ROLE.get(role, GAP_DEFAULT)
    for k, v in GAP_BY_ROLE.items():
        if k in row["id"]:
            return v
    return GAP_DEFAULT


def main():
    d = Path(sys.argv[1])
    rows = json.loads((d / "report.json").read_text())
    parts, total = [], 0.0
    marks = []
    sr_out = None
    for r in rows:
        w = d / f"{r['id']}.wav"
        if not w.exists():
            continue
        audio, sr = sf.read(str(w))
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr_out is None:
            sr_out = sr
        elif sr != sr_out:
            raise SystemExit(f"取樣率不一致:{w.name} 為 {sr},預期 {sr_out}")
        marks.append((total, r["id"], r.get("beat", "")))
        parts.append(audio)
        total += len(audio) / sr
        gap = gap_for(r)
        parts.append(np.zeros(int(gap * sr_out)))
        total += gap

    full = np.concatenate(parts)
    out = d / "FULL_EPISODE.wav"
    sf.write(out, full, sr_out)

    lines = ["# 拼接後的完整片段", "",
             f"總長 {total/60:.1f} 分鐘({total:.0f} 秒)", "",
             "| 時間 | beat | 內容 |", "|---|---|---|"]
    for t, bid, beat in marks:
        lines.append(f"| {int(t//60)}:{int(t%60):02d} | {bid} | {beat} |")
    (d / "TIMELINE.md").write_text("\n".join(lines))

    print(f"-> {out}  ({total/60:.1f} 分鐘)")
    print(f"-> {d / 'TIMELINE.md'}")


if __name__ == "__main__":
    main()

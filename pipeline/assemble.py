"""把片頭音樂、人聲、片尾音樂混成一集。

用法:
    uv run python pipeline/assemble.py <out_dir> --intro a.wav --outro b.wav

為什麼不用 pydub:它要 ffmpeg,而這個專案刻意沒有系統依賴。
混音在數學上只有兩件事 —— 淡入淡出是乘一條窗函數,疊加是對齊後相加。

三個設計決定:

**輸出 44.1 kHz 單聲道。** 人聲是 24 kHz,音樂是 44.1 kHz。把音樂降到 24 kHz
會讓 Nyquist 掉到 12 kHz,鼓組的空氣感整個沒了;把人聲升到 44.1 kHz 不會變好
但也不會變差,所以往上對齊。單聲道是因為旁白本來就是單聲道,而 `master.py`
的 -19 LUFS 是單聲道的標準(立體聲要 -16)。音樂降混成單聲道有相位抵消的風險,
`fold_loss_db` 會量出來。

**音樂的響度對齊到人聲,而不是對齊到峰值。** 峰值對齊會讓密度高的曲子聽起來
大聲很多。兩邊都用 BS.1770 積分響度量,再把音樂推到「人聲 + MUSIC_REL」。

**交接用 duck 而不是硬接。** 片頭音樂在人聲進來前壓低 DUCK_DB 並淡出,
人聲的第一個字疊在音樂尾巴上 —— 這是廣播的標準做法,因為完全沒有重疊時
中間那道縫會聽成「上一段結束了」而不是「節目開始了」。
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from scipy.ndimage import maximum_filter1d, minimum_filter1d

sys.path.insert(0, str(Path(__file__).parent))
from master import integrated_lufs, limit_true_peak, TARGET_LUFS
from stitch import gap_for

SR = 44100
OVERLAP = 1.5      # 人聲的第一個字往前疊進片頭音樂的秒數
DUCK_DB = -15.0    # 重疊期間音樂壓低多少
MUSIC_REL = 0.0    # 音樂的積分響度相對人聲(dB)
OUTRO_PRE = 3.0    # 片尾音樂在人聲結束前多久就進來
OUTRO_RISE = 0.8   # 人聲結束後音樂升回全音量的時間
STING_REL = -3.0   # 章節轉場相對人聲的積分響度
STING_PAD = 0.7    # 轉場前後的靜音,取代原本那個 beat 的停頓
MIN_PER_STING = 9.0  # 大約每幾分鐘一次轉場


def load(path, sr=SR):
    """讀檔、降混單聲道、重取樣到 sr。回傳 (訊號, 降混損失 dB)。"""
    x, s = sf.read(str(path), dtype="float64")
    loss = 0.0
    if x.ndim > 1:
        # 降混損失:和訊號的能量 vs 各聲道能量平均。負得多代表左右相位在打架。
        m = x.mean(axis=1)
        e_ch = (x ** 2).mean()
        e_m = (m ** 2).mean()
        loss = 10 * np.log10(e_m / e_ch) if e_ch > 0 else 0.0
        x = m
    if s != sr:
        from math import gcd
        g = gcd(int(s), int(sr))
        x = resample_poly(x, sr // g, s // g)
    return x, loss


def gain_to(x, target_lufs, sr=SR):
    l = integrated_lufs(x, sr)
    return x * 10 ** ((target_lufs - l) / 20), l


def soft_limit(x, sr, ceiling, lookahead=0.005, release=0.06):
    """前瞻峰值限幅,只用在音樂上。

    為什麼需要它:曲庫的曲子峰值餘裕差很多(實測 11.5 到 19.9 dB)。把它們
    對齊到同一個積分響度之後,餘裕大的那首峰值會衝到 +4 dBTP,於是整個混音
    被等比壓下來近 2 dB —— 那會讓那首在盲測裡「聽起來比較小聲」,變成不公平
    的比較。限幅只作用在音樂,人聲不碰(壓人聲會改變語氣)。

    做法:取 |x| 的滑動最大值當偵測包絡,算出需要的增益衰減,再對衰減取
    前瞻區間的滑動最小值(讓增益在峰值抵達前就先降下來),最後單極平滑避免
    增益本身變成新的失真源。
    """
    la = max(1, int(lookahead * sr))
    env = maximum_filter1d(np.abs(x), size=2 * la + 1, mode="nearest")
    gr = np.minimum(1.0, ceiling / np.maximum(env, 1e-12))
    gr = minimum_filter1d(gr, size=2 * la + 1, mode="nearest")
    a = np.exp(-1.0 / (release * sr))          # 只平滑「放開」方向
    out = np.empty_like(gr); g = 1.0
    for i, v in enumerate(gr):
        g = v if v < g else a * g + (1 - a) * v
        out[i] = g
    return x * out


def fade_out(n):
    """等功率淡出(cos²),不是線性 —— 線性淡出在中段聽起來會掉太快。"""
    return np.cos(np.linspace(0, np.pi / 2, n)) ** 2


def place(canvas, y, at, gain=None):
    """把 y 疊加到 canvas 的 at 樣本處,長度不足自動補。"""
    i = int(at)
    if i < 0:
        y = y[-i:]; i = 0
    need = i + len(y) - len(canvas)
    if need > 0:
        canvas = np.concatenate([canvas, np.zeros(need)])
    canvas[i:i + len(y)] += y * (1.0 if gain is None else gain)
    return canvas


def intro_envelope(n, sr, overlap=OVERLAP, duck_db=DUCK_DB):
    """片頭音樂的音量包絡:全音量 → 壓低 → 在重疊區淡到零。"""
    g = np.ones(n)
    ov = int(overlap * sr)
    ramp = int(0.35 * sr)                      # 壓低的過渡,太快會聽成「被切掉」
    d = 10 ** (duck_db / 20)
    s = max(0, n - ov - ramp)
    g[s:s + ramp] = np.linspace(1, d, ramp)
    g[s + ramp:] = d * fade_out(n - s - ramp)
    return g


def outro_envelope(n, sr, pre=OUTRO_PRE, rise=OUTRO_RISE, duck_db=DUCK_DB):
    """片尾音樂的音量包絡:壓低進來墊在最後一句話底下 → 人聲結束後升回全音量。"""
    g = np.ones(n)
    d = 10 ** (duck_db / 20)
    p, r = int(pre * sr), int(rise * sr)
    g[:min(p, n)] = d
    if p < n:
        k = min(r, n - p)
        g[p:p + k] = np.linspace(d, 1, k)
    return g


def consonant_power(y, sr=SR):
    """1-4 kHz 的平均功率。子音帶決定聽不聽得懂,遮蔽要看這一帶而不是寬頻。"""
    from scipy.signal import stft as _stft
    f, t, Z = _stft(y, sr, nperseg=2048, noverlap=1024)
    m = (f >= 1000) & (f < 4000)
    return float((np.abs(Z[m]) ** 2).sum(axis=0).mean())


def duck_for(music, voice, sr=SR, overlap=OVERLAP, target_db=-22.0, base=DUCK_DB):
    """算出這首曲子在交接時該壓多少,讓子音帶的音樂/人聲比不高於 target_db。

    為什麼不能固定 -15 dB:寬頻壓 15 dB 不代表子音帶也降 15 dB —— 曲子的頻譜
    形狀不同,實測同樣的 duck 會落在 -14 到 -30 dB 之間。密度高的曲子會正好
    蓋住第一句話,而那是聽眾決定要不要繼續聽的地方。固定值會讓盲測比到的是
    我的混音失誤,不是曲子本身。
    """
    ov = int(overlap * sr)
    got = 10 * np.log10(consonant_power(music[-ov:] * 10 ** (base / 20))
                        / max(consonant_power(voice[:ov]), 1e-30))
    return base + min(0.0, target_db - got)


def build(voice, intro=None, outro=None, sr=SR, music_rel=MUSIC_REL,
          overlap=OVERLAP, outro_pre=OUTRO_PRE, duck_db=None, verbose=True):
    """voice 已經是拼好的整段人聲。回傳 (成品, 資訊 dict)。"""
    v_lufs = integrated_lufs(voice, sr)
    info = {"voice_lufs": round(v_lufs, 2), "voice_s": round(len(voice) / sr, 2)}
    canvas = np.zeros(0)
    v_at = 0

    v_ceil = float(np.max(np.abs(voice)))      # 音樂的峰值不超過人聲的峰值

    if intro is not None:
        intro, info["intro_lufs"] = gain_to(intro, v_lufs + music_rel, sr)
        intro = soft_limit(intro, sr, v_ceil)
        d = duck_for(intro, voice, sr, overlap) if duck_db is None else duck_db
        info["duck_db"] = round(d, 1)
        intro = intro * intro_envelope(len(intro), sr, overlap, d)
        canvas = place(canvas, intro, 0)
        v_at = max(0, len(intro) - int(overlap * sr))
        info["intro_s"] = round(len(intro) / sr, 2)

    canvas = place(canvas, voice, v_at)
    info["voice_at"] = round(v_at / sr, 3)
    v_end = v_at + len(voice)

    if outro is not None:
        outro, info["outro_lufs"] = gain_to(outro, v_lufs + music_rel, sr)
        outro = soft_limit(outro, sr, v_ceil)
        # 片尾墊在最後一句話底下,用同一條判準
        do = (duck_for(outro[::-1], voice[::-1], sr, outro_pre)
              if duck_db is None else duck_db)
        info["duck_out_db"] = round(do, 1)
        outro = outro * outro_envelope(len(outro), sr, outro_pre, duck_db=do)
        canvas = place(canvas, outro, v_end - int(outro_pre * sr))
        info["outro_s"] = round(len(outro) / sr, 2)

    y, tp, cut = limit_true_peak(canvas, sr)
    y, _ = gain_to(y, TARGET_LUFS, sr)
    y, tp, cut = limit_true_peak(y, sr)
    info.update(total_s=round(len(y) / sr, 2), lufs=round(integrated_lufs(y, sr), 2),
                true_peak=round(tp, 2))
    if verbose:
        print(f"  人聲 {info['voice_lufs']} LUFS / {info['voice_s']}s"
              f" → 成品 {info['lufs']} LUFS / {info['true_peak']} dBTP / {info['total_s']}s")
    return y, info


def stitch_voice(d, sr=SR, ids=None):
    """從 out_dir 讀 report.json,依 role 加停頓拼成人聲。ids 可只取部分 beat。"""
    rows = json.loads((Path(d) / "report.json").read_text())
    parts = []
    for r in rows:
        if ids is not None and r["id"] not in ids:
            continue
        w = Path(d) / f"{r['id']}.wav"
        if not w.exists():
            continue
        a, _ = load(w, sr)
        parts += [a, np.zeros(int(gap_for(r) * sr))]
    if not parts:
        raise SystemExit("沒有可用的 beat")
    return np.concatenate(parts[:-1])


def sting_count(total_s, lo=2, hi=5):
    """依整集長度決定要放幾次轉場。

    大約每 9 分鐘一次。三十分鐘的一集就是三次 —— 八個章節點全放的話
    平均不到四分鐘一次,轉場會從「這裡換段落了」退化成背景噪音。
    下限 2 是因為一次聽起來像意外,上限 5 是因為再多就變成節目的節奏本身。
    """
    return int(min(hi, max(lo, round(total_s / 60 / MIN_PER_STING))))


def pick_sting_points(cands, total_s, n):
    """挑 n 個章節點,讓「最長一段沒有標點的區間」最短。

    第一版是取等距目標的最近鄰,結果在 ep003 上把三次轉場全擠在前 18 分鐘,
    最後 11 分鐘一次都沒有 —— 那一段的章節點本來就稀疏,最近鄰會一直往前挑。
    改成直接對目標最佳化:枚舉組合,取最大間隔最小的那一組,平手再取間隔
    變異數最小的。章節點只有十幾個,枚舉完全負擔得起。
    """
    from itertools import combinations
    if n <= 0 or not cands:
        return []
    n = min(n, len(cands))
    best = None
    for c in combinations(range(len(cands)), n):
        gaps = np.diff([0.0] + [cands[i][1] for i in c] + [total_s])
        key = (round(float(gaps.max()), 1), float(np.var(gaps)))
        if best is None or key < best[0]:
            best = (key, c)
    return [cands[i][0] for i in best[1]]


def episode(out_dir, intro=None, outro=None, sting=None, n_stings=None,
            sr=SR, sting_rel=STING_REL, rate=1.0, verbose=True):
    """混一整集:人聲 + 章節轉場 + 片頭 + 片尾。回傳 (成品, 資訊)。

    轉場插在章節 beat 的前面,取代該處原本的停頓 —— 不是疊在停頓上,
    不然那個縫會變成 0.7 + 原停頓 + 0.7,聽起來像斷線。
    第一個章節點(b00_hook)不放,那是開場,前面已經有片頭音樂了。

    `rate` > 1 是加速版本。**只加速人聲,音樂保持原速** —— WSOLA 是靠找相似
    波形重疊接起來的,拉伸語音很乾淨,拉伸音樂會打散它的週期性,產生顆粒感與
    節奏抖動。所以加速要在混音**之前**做:每段人聲各自拉伸、停頓按比例縮短,
    片頭片尾與轉場再用原速疊上去。先混完再整段加速就毀了音樂。
    """
    if rate != 1.0:
        from speedup import wsola
    out_dir = Path(out_dir)
    lang, slug = out_dir.name, out_dir.parent.name
    rows = json.loads((out_dir / "report.json").read_text())
    spec_path = Path(__file__).parent.parent / "episodes" / slug / f"{lang}.json"
    spec = json.loads(spec_path.read_text())
    chapter_of = {r["id"]: r["chapter"] for r in spec if r.get("chapter")}

    segs, t = [], 0.0
    for r in rows:
        w = out_dir / f"{r['id']}.wav"
        if not w.exists():
            continue
        a, _ = load(w, sr)
        g = gap_for(r)
        if rate != 1.0:
            a, g = wsola(a, rate), g / rate
        segs.append((r["id"], a, g))
        t += len(a) / sr + g
    if not segs:
        raise SystemExit("沒有可用的 beat")

    # 先在「沒有轉場」的時間軸上挑點,誤差只有幾秒,但少一輪相互依賴
    starts, acc = {}, 0.0
    for sid, a, g in segs:
        starts[sid] = acc
        acc += len(a) / sr + g
    cands = [(sid, starts[sid]) for sid, _, _ in segs if sid in chapter_of][1:]
    n = sting_count(acc) if n_stings is None else n_stings
    pts = set(pick_sting_points(cands, acc, n)) if (sting is not None and n) else set()

    parts, marks, at = [], {}, 0.0
    sting_at = []
    for i, (sid, a, g) in enumerate(segs):
        if sid in pts and parts:
            parts.pop()                      # 丟掉前一段的停頓
            at -= segs[i - 1][2]
            for blk in (np.zeros(int(STING_PAD * sr)), sting,
                        np.zeros(int(STING_PAD * sr))):
                if blk is sting:
                    sting_at.append(round(at, 2))
                parts.append(blk)
                at += len(blk) / sr
        marks[sid] = at
        parts.append(a)
        at += len(a) / sr
        parts.append(np.zeros(int(g * sr)))
        at += g
    voice = np.concatenate(parts[:-1])

    if sting is not None and pts:
        # 人聲的響度只算人聲,不能把還沒調整的轉場算進去 —— 那會互相污染
        v_lufs = integrated_lufs(np.concatenate([a for _, a, _ in segs]), sr)
        # 轉場的響度對齊到人聲,不是對齊到片頭 —— 它夾在兩段話之間
        k = 10 ** ((v_lufs + sting_rel - integrated_lufs(sting, sr)) / 20)
        voice = np.concatenate([p if p is not sting else p * k for p in parts[:-1]])
        sting = sting * k

    y, info = build(voice, intro, outro, sr=sr, verbose=verbose)
    off = info.get("voice_at", 0.0)
    info["marks"] = {k2: round(v + off, 2) for k2, v in marks.items()}
    info["stings"] = dict(count=len(pts), at=[round(x + off, 2) for x in sting_at],
                          beats=[sid for sid, _, _ in segs if sid in pts],
                          chapters=[chapter_of[sid] for sid, _, _ in segs if sid in pts],
                          rel_db=sting_rel)
    if verbose and pts:
        print(f"  轉場 {len(pts)} 次(整集 {acc/60:.0f} 分,每 {MIN_PER_STING:.0f} 分一次):")
        for sid in [s2 for s2, _, _ in segs if s2 in pts]:
            print(f"    {int(info['marks'][sid]//60)}:{int(info['marks'][sid]%60):02d}"
                  f"  {sid}  {chapter_of[sid]}")
    return y, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--intro"); ap.add_argument("--outro"); ap.add_argument("--sting")
    ap.add_argument("--stings", type=int, default=None,
                    help="轉場次數,預設依整集長度決定(約每 9 分鐘一次)")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--rate", type=float, default=1.0,
                    help="加速倍率。只加速人聲,音樂保持原速")
    ap.add_argument("--music-rel", type=float, default=MUSIC_REL)
    ap.add_argument("--duck", type=float, default=None)
    a = ap.parse_args()
    d = Path(a.out_dir)
    intro = load(a.intro)[0] if a.intro else None
    outro = load(a.outro)[0] if a.outro else None
    sting = load(a.sting)[0] if a.sting else None
    y, info = episode(d, intro, outro, sting, n_stings=a.stings, rate=a.rate)
    tag = "" if a.rate == 1.0 else f"_x{a.rate:g}"
    out = Path(a.output) if a.output else d / f"FULL_EPISODE_mixed{tag}.wav"
    sf.write(str(out), y, SR)
    print(f"-> {out}")
    if a.rate == 1.0:      # 時間戳只有原速那份有意義,show notes 用它
        (d / "MIX.json").write_text(json.dumps(info, ensure_ascii=False, indent=1,
                                               default=float))
        print(f"-> {d / 'MIX.json'}  ({len(info['marks'])} 段的最終時間戳)")


if __name__ == "__main__":
    main()

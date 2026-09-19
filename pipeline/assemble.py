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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--intro"); ap.add_argument("--outro")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--music-rel", type=float, default=MUSIC_REL)
    ap.add_argument("--duck", type=float, default=None)
    a = ap.parse_args()
    d = Path(a.out_dir)
    voice = stitch_voice(d)
    intro = load(a.intro)[0] if a.intro else None
    outro = load(a.outro)[0] if a.outro else None
    y, info = build(voice, intro, outro, music_rel=a.music_rel, duck_db=a.duck)
    out = Path(a.output) if a.output else d / "FULL_EPISODE_mixed.wav"
    sf.write(str(out), y, SR)
    print(f"-> {out}")
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()

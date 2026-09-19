"""從授權原曲切出片頭、章節轉場、片尾三個品牌音檔。

用法:uv run python music/cut.py

原曲:Jonas Blakewood / Presentation(Pixabay,見 docs/MUSIC.md 的授權存證)。
放在 music/source/ 進版控,因為沒有它就沒辦法重切,也沒辦法證明來源。

三個位置都是 Johnny 盲測選的,不要自己改:

    片頭  小節 0-1    0.65s 起 8.0 秒(兩小節)
    轉場  小節 14    56.51s 起 4.0 秒(一小節)—— 留白之後鼓回來的那一小節
    片尾  小節 31-32  124.46s 起 7.0 秒,含原曲的自然衰減

為什麼一定要貼小節線:切在小節中間,耳朵會把它聽成「被打斷」而不是「結束」。
這首 60 BPM,一小節 3.99 秒,所以長度只能是 4 的倍數 —— 這也是為什麼片頭是
8 秒而不是 10 秒。相位 0.65s 是從起音包絡量出來的,不是猜的。
"""
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

SRC = Path(__file__).parent / "source" / "jonasblakewood-presentation-524137.mp3"
SR = 44100
BAR, PHASE = 3.99, 0.650
LEAD_IN = 0.02          # 只為了不爆音,不是淡入

CUTS = {
    "intro": dict(at=PHASE,             bars=2, tail=0.0, fade_out=1.6),
    "sting": dict(at=PHASE + 14 * BAR,  bars=1, tail=0.0, fade_out=0.8),
    "outro": dict(at=PHASE + 31 * BAR,  bars=1, tail=3.0, fade_out=0.9),
}


def load_source():
    x, sr = sf.read(str(SRC), dtype="float64")
    m = x.mean(axis=1) if x.ndim > 1 else x
    # 去掉 mp3 解碼在頭尾補的靜音,不然所有時間都會偏移
    hop = int(0.02 * sr)
    e = 10 * np.log10((m[:len(m) // hop * hop] ** 2).reshape(-1, hop).mean(axis=1) + 1e-12)
    on = np.where(e > -55)[0]
    x = x[int(on[0] * 0.02 * sr):int((on[-1] + 1) * 0.02 * sr)]
    if sr != SR:
        from math import gcd
        g = gcd(int(sr), SR)
        x = resample_poly(x, SR // g, sr // g, axis=0)
    return x


def cut(x, at, bars, tail, fade_out):
    a = int(at * SR)
    b = int(min(len(x), (at + bars * BAR + tail) * SR))
    y = x[a:b].copy()
    n = int(LEAD_IN * SR)
    y[:n] *= np.linspace(0, 1, n)[:, None] if y.ndim > 1 else np.linspace(0, 1, n)
    n = min(int(fade_out * SR), len(y))
    w = np.cos(np.linspace(0, np.pi / 2, n)) ** 2      # 等功率淡出
    y[-n:] *= w[:, None] if y.ndim > 1 else w
    return y


def main():
    x = load_source()
    out = Path(__file__).parent
    for name, p in CUTS.items():
        y = cut(x, **p)
        sf.write(str(out / f"{name}.wav"), y, SR, subtype="PCM_16")
        print(f"{name:6} {p['at']:7.2f}s 起 {len(y) / SR:5.2f}s -> music/{name}.wav")


if __name__ == "__main__":
    main()

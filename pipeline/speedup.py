"""音訊變速(不改音高)—— WSOLA 時域波形相似疊加。

環境裡沒有 ffmpeg / sox / rubberband(本專案刻意避開這些系統依賴),
所以用 numpy + scipy 自己實作。

原理:把音訊切成重疊的小段,重新以較短的間隔疊回去。關鍵在於每一段
不是硬切,而是在目標位置附近搜尋「波形最接近前一段自然延續」的位置,
這樣接縫落在波形相位一致的地方,不會產生金屬感或回音。

單純重採樣(改播放速率)會連音高一起變,聽起來像花栗鼠,所以不能用。

用法:
    uv run python pipeline/speedup.py <輸入.wav> 1.1 1.2 1.3 1.4 1.5
"""
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import correlate

FRAME = 1024      # 24kHz 下約 43ms,語音 WSOLA 的常用尺度
TOL = 256         # 搜尋半徑約 10ms


def wsola(x: np.ndarray, rate: float, n: int = FRAME, tol: int = TOL) -> np.ndarray:
    if abs(rate - 1.0) < 1e-6:
        return x.copy()
    hs = n // 2                      # 合成側固定半段重疊
    ha = int(round(hs * rate))       # 分析側依速率跨得更遠
    win = np.hanning(n).astype(np.float32)
    out_len = int(len(x) / rate) + 2 * n
    out = np.zeros(out_len, dtype=np.float32)
    norm = np.zeros(out_len, dtype=np.float32)

    out[:n] += x[:n] * win
    norm[:n] += win
    nat = x[hs:hs + n]               # 前一段的「自然延續」,拿它當比對模板
    ana, syn = ha, hs

    while ana + n + tol < len(x) and syn + n < out_len:
        lo = max(0, ana - tol)
        hi = min(len(x) - n, ana + tol)
        if hi <= lo:
            best = min(ana, len(x) - n)
        else:
            region = x[lo:hi + n]
            c = correlate(region, nat, mode="valid", method="fft")
            best = lo + int(np.argmax(c))
        seg = x[best:best + n]
        if len(seg) < n:
            break
        out[syn:syn + n] += seg * win
        norm[syn:syn + n] += win
        nat = x[best + hs:best + hs + n]
        if len(nat) < n:
            break
        ana += ha
        syn += hs

    end = syn + n
    out, norm = out[:end], norm[:end]
    return np.divide(out, norm, out=np.zeros_like(out), where=norm > 1e-6)


def main():
    src = Path(sys.argv[1])
    rates = [float(r) for r in sys.argv[2:]] or [1.1, 1.2, 1.3, 1.4, 1.5]
    x, sr = sf.read(str(src), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    print(f"原檔 {src.name}  {len(x)/sr/60:.1f} 分鐘  {sr} Hz\n")
    for r in rates:
        y = wsola(x, r)
        peak = np.max(np.abs(y))
        if peak > 0.999:                       # 疊加後偶爾會頂到,壓回來
            y = y * (0.999 / peak)
        dst = src.with_name(f"{src.stem}_x{r:g}.wav")
        sf.write(str(dst), y, sr)
        print(f"  x{r:g}  {len(y)/sr/60:5.1f} 分鐘  (實際 {len(x)/len(y):.3f} 倍)  -> {dst.name}")


if __name__ == "__main__":
    main()

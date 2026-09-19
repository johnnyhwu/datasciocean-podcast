"""音量正規化 —— ITU-R BS.1770-4 響度量測 + 增益 + true peak 保護。

環境裡沒有 ffmpeg(本專案刻意避開系統依賴),PLAN.md 5.2 寫的
`ffmpeg loudnorm` 不能用,所以整套 BS.1770 用 numpy + scipy 自己實作。

為什麼不是看波形最大值:peak 跟人耳感受幾乎無關。一段全程平穩的旁白,
和一段大部分很小聲、只有一聲頂到滿的錄音,peak 一樣但聽起來差很多。
LUFS 量的是感知響度 —— 先過 K-weighting 濾波器模擬人耳對 2-4kHz
(講話頻段)特別敏感,再切塊平均,而且**把安靜的塊丟掉再平均**(gating)。
最後那步是關鍵:podcast 有大量停頓,靜音一起平均會把數字拉低,
結果就是把節目推得過大聲。

True peak 要 4 倍以上過取樣才量得到 —— 取樣點「之間」的真實波形會衝更高,
壓成 AAC 時那些點會被還原出來。留 1dB 餘裕就是為了這個。

用法:
    uv run python pipeline/master.py <輸入.wav> [-o 輸出.wav]
    uv run python pipeline/master.py <輸入.wav> --measure   # 只量不改
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import lfilter, resample_poly

TARGET_LUFS = -19.0    # 單聲道 podcast 標準(立體聲才是 -16)
TARGET_TP = -1.0       # dBTP,壓縮成 AAC 前要留的餘裕
ABS_GATE = -70.0       # BS.1770 絕對閘門
REL_GATE = -10.0       # 相對閘門,低於平均 10 LU 的塊不計入


def _biquad_shelf(sr, fc, q, gain_db):
    """K-weighting 第一級:high-shelf,模擬頭部對高頻的繞射增益。

    這不是 RBJ 那條 high-shelf 公式 —— 用 RBJ 推出來的係數跟 BS.1770-4
    表 1 對不起來(997Hz 差 0.26 dB,超出 ±0.1 的容差)。這裡用的是能
    原樣重現表 1 的形式,注意 Vh 是 10^(G/20) 而不是 RBJ 的 10^(G/40)。
    """
    k = np.tan(np.pi * fc / sr)
    vh = 10 ** (gain_db / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b = np.array([vh + vb * k / q + k * k, 2 * (k * k - vh),
                  vh - vb * k / q + k * k]) / a0
    a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return b, a


def _biquad_hpf(sr, fc, q):
    """K-weighting 第二級:high-pass,砍掉人耳不當成響度的低頻。

    分子固定 [1, -2, 1](在 Nyquist 歸一),與表 2 一致。
    """
    k = np.tan(np.pi * fc / sr)
    a0 = 1 + k / q + k * k
    a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return np.array([1.0, -2.0, 1.0]), a


def k_weight(x, sr):
    """套 K-weighting。係數依取樣率當場推導,不寫死 48kHz 的那組。"""
    b, a = _biquad_shelf(sr, 1681.974450955533, 0.7071752369554196,
                         3.999843853973347)
    y = lfilter(b, a, x, axis=0)
    b, a = _biquad_hpf(sr, 38.13547087602444, 0.5003270373238773)
    return lfilter(b, a, y, axis=0)


def _block_power(y, sr, block_s, step_s):
    """逐塊的均方功率,用 cumsum 一次算完,不要逐塊迴圈。

    多聲道時把各聲道的功率**相加**(BS.1770 對 L/R 的通道加權都是 1.0),
    不是先降混再量 —— 左右不同的素材在降混時會互相抵消,音樂很常見,
    那樣量出來會偏低。人聲是單聲道,走的是同一條路徑。
    """
    bn, sn = int(round(block_s * sr)), int(round(step_s * sr))
    y = np.asarray(y, dtype=np.float64)
    if y.ndim == 1:
        y = y[:, None]
    if len(y) < bn:
        return np.array([])
    c = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, axis=0)])
    starts = np.arange(0, len(y) - bn + 1, sn)
    return ((c[starts + bn] - c[starts]) / bn).sum(axis=1)


def _lufs(z):
    """z 是已經跨聲道加總過的功率。功率為 0 的塊要擋掉,不然 log10 會炸。"""
    z = np.asarray(z, dtype=np.float64)
    out = np.full(np.shape(z), -np.inf)
    np.log10(z, out=out, where=z > 0)
    return -0.691 + 10 * out


def integrated_lufs(x, sr):
    """整合響度。兩段 gating:先丟掉靜音,再丟掉明顯低於平均的塊。"""
    z = _block_power(k_weight(x, sr), sr, 0.400, 0.100)
    if z.size == 0:
        return -np.inf
    z = z[_lufs(z) > ABS_GATE]
    if z.size == 0:
        return -np.inf
    thr = _lufs(z.mean()) + REL_GATE
    z = z[_lufs(z) > thr]
    return float(_lufs(z.mean())) if z.size else -np.inf


def loudness_range(x, sr):
    """LRA —— 最大聲與最小聲的差距。只是報告用,不做修正。

    用 3 秒的 short-term 塊(不是 integrated 的 0.4 秒),相對閘門也不同
    (-20 LU),最後取第 10 與第 95 百分位的差。語音類約 5-8 算正常。
    """
    l = _lufs(_block_power(k_weight(x, sr), sr, 3.0, 1.0))
    l = l[l > ABS_GATE]
    if l.size < 2:
        return 0.0
    l = l[l > _lufs(np.mean(10 ** ((l + 0.691) / 10))) - 20.0]
    if l.size < 2:
        return 0.0
    return float(np.percentile(l, 95) - np.percentile(l, 10))


def true_peak_db(x, sr):
    """過取樣到 ≥192kHz 再量。直接看樣本最大值會低估,那正是 AAC 爆音的來源。"""
    up = max(4, int(np.ceil(192000 / sr)))
    p = float(np.max(np.abs(resample_poly(x, up, 1, axis=0))))
    return 20 * np.log10(p) if p > 0 else -np.inf


def limit_true_peak(y, sr, ceiling=TARGET_TP):
    """整段等比壓回天花板。不做動態壓縮 —— 那會改變語氣。"""
    tp = true_peak_db(y, sr)
    if tp <= ceiling:
        return y, tp, 0.0
    cut = ceiling - tp
    return y * 10 ** (cut / 20), ceiling, cut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--target", type=float, default=TARGET_LUFS)
    ap.add_argument("--peak", type=float, default=TARGET_TP)
    ap.add_argument("--measure", action="store_true", help="只量測,不輸出檔案")
    args = ap.parse_args()

    x, sr = sf.read(str(args.src), dtype="float64", always_2d=False)
    if x.ndim > 1:
        x = x.mean(axis=1)

    lufs, lra, tp = integrated_lufs(x, sr), loudness_range(x, sr), true_peak_db(x, sr)
    print(f"{args.src.name}  {len(x)/sr/60:.1f} 分鐘  {sr} Hz")
    print(f"  現況  {lufs:7.2f} LUFS   {tp:6.2f} dBTP   LRA {lra:.1f}")

    if not np.isfinite(lufs):
        raise SystemExit("整段都在閘門以下(近乎無聲),不做正規化。")
    if lra > 9:
        print(f"  ⚠ LRA {lra:.1f} 偏大,語音類通常 5-8。可能有某幾段明顯過小聲。")

    if args.measure:
        return

    gain = args.target - lufs
    y, tp2, cut = limit_true_peak(x * 10 ** (gain / 20), sr, args.peak)
    if cut < 0:
        print(f"  ⚠ 增益 {gain:+.2f} dB 會讓 true peak 超標,再壓 {cut:.2f} dB;"
              f"實際響度會落在 {args.target + cut:.2f} LUFS")

    out = args.out or args.src.with_name(f"{args.src.stem}_norm.wav")
    sf.write(str(out), y, sr, subtype=sf.info(str(args.src)).subtype)
    print(f"  增益  {gain + cut:+.2f} dB")
    print(f"  結果  {integrated_lufs(y, sr):7.2f} LUFS   {tp2:6.2f} dBTP")
    print(f"-> {out}")


if __name__ == "__main__":
    main()

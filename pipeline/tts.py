"""透過 OpenRouter 的 /audio/speech 逐段合成,輸出 pipeline/verify.py 吃得下的格式。

OpenRouter 只接受 model / input / voice / response_format 四個欄位,
**不支援** voice cloning、pronunciation_dict、emotion、speed、language_boost ——
語氣一律靠 spec 裡每段自己的 `style` 提示表達。

用法:
    uv run python pipeline/tts.py episodes/<slug>/zh.json out/<slug>/zh \
        --model google/gemini-3.1-flash-tts-preview --voice Zubenelgenubi --pcm \
        [--resume] [--only b00_hook,b01_identity]
"""
import os, sys, re, json, time, argparse, subprocess, tempfile
from pathlib import Path
for _l in (Path(__file__).parent.parent / ".env").read_text().splitlines():
    if "=" in _l and not _l.strip().startswith("#"):
        _k, _v = _l.split("=", 1); os.environ.setdefault(_k.strip(), _v.strip())
import requests, soundfile as sf

URL = "https://openrouter.ai/api/v1/audio/speech"
SR = 24000   # Gemini TTS 的裸 PCM 就是這個取樣率,stitch.py 直接拼不轉換


def to_wav(mp3: bytes, dst: Path):
    """mp3 -> 24k 單聲道 wav。用 macOS 內建 afconvert,不引入 ffmpeg 依賴。"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(mp3); tmp = f.name
    subprocess.run(["afconvert", "-f", "WAVE", "-d", f"LEI16@{SR}", "-c", "1",
                    tmp, str(dst)], check=True, capture_output=True)
    os.unlink(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("out")
    ap.add_argument("--model", required=True)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--only", default="")
    ap.add_argument("--resume", action="store_true",
                    help="已存在的 wav 直接沿用,只補缺的")
    ap.add_argument("--pcm", action="store_true",
                    help="模型只支援 pcm 時使用(例如 Gemini TTS)")
    a = ap.parse_args()

    key = os.environ["OPENROUTER_API_KEY"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    items = json.loads(Path(a.spec).read_text())
    if a.only:
        keep = set(a.only.split(","))
        items = [x for x in items if x["id"] in keep]

    print(f"model={a.model}  voice={a.voice}  {len(items)} 段\n", flush=True)
    rows, chars, failed = [], 0, []
    for i, it in enumerate(items, 1):
        w0 = out / f"{it['id']}.wav"
        if a.resume and w0.exists():
            arr, sr = sf.read(str(w0))
            rows.append({**it, "duration_s": round(len(arr)/sr, 2),
                         "chars_per_sec": round(len(it["text"])/(len(arr)/sr), 2),
                         "model": a.model, "voice": it.get("voice") or a.voice})
            continue
        fmt = "pcm" if a.pcm else "mp3"
        # Gemini 的風格控制是把指示寫進 input 前綴,模型會照做但不會唸出來
        # (實測 s2_style_en:指示沒有出現在轉錄裡)。指示不計入比對文字,
        # 否則相似度會被指示本身拉低。
        # 風格提示相對正文太長時,Gemini 會穩定回 502 空音訊(實測:45 字提示
        # 配 24 字正文必掛,同樣提示配 60 字正文正常)。所以準備一組由長到短的
        # 提示,失敗就降級,最後一級是完全不帶提示 —— 寧可少一點語氣也要有音檔。
        # 降級後的提示必須跟原提示同語言:英文稿掉到中文指示會直接改掉口音,
        # 那比沒有語氣還糟。所以句號、骨幹句、保底指示都跟著提示的語言走。
        st = it.get("style") or ""
        ladder = [st] if st else [""]
        if st:
            zh = bool(re.search(r"[一-鿿]", st))
            eos = "。" if zh else "."
            head = st.split(eos)[0].strip() + eos      # 只留骨幹那句
            floor = "請用台灣口音說。" if zh else "Speak in a neutral American accent."
            ladder += [head, floor, ""]
        ladder = list(dict.fromkeys(ladder))     # 去重且保序
        v = it.get("voice") or a.voice           # spec 可逐筆指定音色
        body = {"model": a.model, "input": it["text"], "response_format": fmt}
        if v:
            body["voice"] = v
        t0 = time.time()
        # Gemini 偶發回傳空音訊(官方文件承認需要重試邏輯),且沒有 seed
        # 可用,所以重試就是重骰 —— 這是正式 pipeline 也必須有的一層。
        ok = False
        for lvl, stl in enumerate(ladder):
            body["input"] = (stl + "\n\n" + it["text"]) if stl else it["text"]
            for attempt in range(2):
                r = requests.post(URL, headers={"Authorization": f"Bearer {key}",
                                                "Content-Type": "application/json"},
                                  json=body, timeout=300)
                ok = (r.status_code == 200 and len(r.content) > 2000
                      and not r.headers.get("content-type", "").startswith("application/json"))
                if ok:
                    break
                time.sleep(2)
            if ok:
                if lvl:
                    print(f"    提示降級到第 {lvl} 級({len(stl)} 字)才成功", flush=True)
                break
        if not ok:
            print(f"    ✗ {it['id']} 全部降級都失敗,跳過", flush=True)
            failed.append(it["id"])
            continue
        w = out / f"{it['id']}.wav"
        if a.pcm:
            # 裸 PCM 無檔頭:Gemini TTS 為 24kHz / 16-bit / 單聲道
            import numpy as np
            sf.write(str(w), np.frombuffer(r.content, dtype="<i2"), SR)
        else:
            to_wav(r.content, w)
        arr, sr = sf.read(str(w))
        dur = len(arr) / sr
        cps = len(it["text"]) / dur if dur else 0
        chars += len(it["text"])
        print(f"[{i}/{len(items)}] {it['id']:24s} {dur:5.1f}s {cps:4.1f}字/秒 "
              f"(gen {time.time()-t0:.0f}s)", flush=True)
        rows.append({**it, "duration_s": round(dur, 2),
                     "chars_per_sec": round(cps, 2), "model": a.model,
                     "voice": v})

    (out / "report.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    if failed:
        print(f"\n⚠ {len(failed)} 段失敗:{', '.join(failed)}")
    print(f"\n約 {chars} 字元 -> {out}")
    print(f"下一步:uv run python pipeline/verify.py {out}")


if __name__ == "__main__":
    main()

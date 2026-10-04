"""STT 回轉驗證 —— 合成完的音檔用 Whisper 轉錄,跟輸入逐字稿比對。

這是整條 pipeline 的品質關卡。原則:**STT 是篩選器,不是判官。**
Whisper 自己也會聽錯,所以低分只代表「這一段需要人耳確認」,
不代表 TTS 一定唸錯。

比對前會做正規化,把跟發音無關的差異排除掉(簡繁、中英文數字寫法、
標點、百分比與小數點的寫法),否則分數會被系統性低估。

語言由稿子自動判斷(中文字比例),中英文各有一套正規化與語速門檻。

用法:
    uv run python pipeline/verify.py <out_dir> [--lang zh|en]

會就地更新該目錄的 report.json,補上 transcribed / similarity / diffs / flags。
"""
import sys, json, difflib, re
from pathlib import Path

STT_MODEL = "openai/whisper-large-v3-turbo"

# 正常語速區間(字元/秒)與失控下限。中文 Gemini 實測落在 4.5-6.5;
# 英文因為字元密度低得多(一個音節平均 3 個字母以上),整組門檻要放大約 2.8 倍,
# 對應每分鐘 140-200 字的正常口說速度。
SPEED = {"zh": {"low": 4.0, "high": 9.5, "runaway": 3.5},
         "en": {"low": 11.0, "high": 20.0, "runaway": 9.0}}

# 報表上的速度單位標籤,只影響顯示。
UNIT = {"zh": "字/秒", "en": "字元/秒"}

_CC = None


def detect_lang(texts) -> str:
    """看中文字佔比決定語言。英文稿裡也可能夾少量中文,所以用 15% 當界線。"""
    joined = "".join(texts)
    if not joined:
        return "zh"
    zh = len(re.findall(r"[一-鿿]", joined))
    return "zh" if zh / len(joined) > 0.15 else "en"


def _to_trad(s: str) -> str:
    """Whisper 有時輸出簡體,轉成繁體再比對,避免簡繁差異被誤判為發音錯誤。"""
    global _CC
    if _CC is None:
        from opencc import OpenCC
        _CC = OpenCC("s2twp")
    return _CC.convert(s)


_NUM_ZH = {"零": "0", "一": "1", "二": "2", "兩": "2", "三": "3", "四": "4",
           "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}


def _zh_num_to_digits(s: str) -> str:
    """把中文數字轉成阿拉伯數字,雙向統一。
    逐字稿寫「十五」而 STT 常寫「15」,這不是發音錯誤。"""
    def rep(m):
        t = m.group(0)
        if t == "十":
            return "10"
        if t.startswith("十"):
            return "1" + _NUM_ZH.get(t[1], "")
        if t.endswith("十"):
            return _NUM_ZH.get(t[0], "") + "0"
        if "十" in t:
            a, b = t.split("十")
            return _NUM_ZH.get(a, "") + _NUM_ZH.get(b, "")
        return "".join(_NUM_ZH.get(c, c) for c in t)
    s = re.sub(r"[零一二兩三四五六七八九]?十[零一二兩三四五六七八九]?|[零一二兩三四五六七八九]+", rep, s)
    s = s.replace("百分之", "%").replace("點", ".")
    return s


_NUM_ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
             "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
             "nineteen": 19}
_NUM_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
             "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}

# 不規則序數。規則的(fourth/sixth/twentieth…)由下面的字尾規則處理。
_ORD_IRREG = {"first": "one", "second": "two", "third": "three",
              "fifth": "five", "eighth": "eight", "ninth": "nine",
              "twelfth": "twelve"}


def _ord_to_card(w: str) -> str:
    """序數詞還原成基數詞,ninety-fifth -> ninety five -> 95。"""
    if w in _ORD_IRREG:
        return _ORD_IRREG[w]
    if w.endswith("ieth"):
        return w[:-4] + "y"
    if w.endswith("th") and w[:-2] in _NUM_ONES | _NUM_TENS:
        return w[:-2]
    return w


_SCALE = {"hundred": 100, "thousand": 1000, "million": 10 ** 6,
          "billion": 10 ** 9}


def _fold_scales(s: str) -> str:
    """把量級詞併進數字:nine thousand nine hundred -> 9900、six hundred -> 600。

    Whisper 一律寫阿拉伯數字(9,900),稿子為了唸得對寫成英文詞,
    兩邊要拉齊。只有整段裡真的出現量級詞才折疊,否則
    「the last 10 messages」這種單純數字會被誤併。
    """
    toks = re.split(r"(\s+)", s)
    out, run = [], []

    def flush():
        if not run:
            return
        words = [t for t in run if not t.isspace()]
        if not any(w.lower().rstrip(".,") in _SCALE for w in words):
            out.extend(run)                      # 沒有量級詞就原樣放回
            return
        total = cur = 0
        for w in words:
            k = w.lower().rstrip(".,")
            if k in _SCALE:
                v = _SCALE[k]
                if v == 100:
                    cur = max(cur, 1) * v      # hundred 併進當前的位數
                else:
                    total += max(cur, 1) * v   # thousand 以上結算成一段
                    cur = 0
            elif k in ("a", "an"):
                cur = 1
            elif k != "and":
                cur = int(k)
        # 末尾的標點要留著:折疊掉的是數字,不是句號。掉了會讓兩邊
        # 一邊有句點一邊沒有,而句點接在數字後面不會被後面的標點規則清掉。
        punct = re.match(r".*?([.,]*)$", words[-1]).group(1)
        out.append(str(total + cur) + punct)
        if run[-1].isspace():
            out.append(run[-1])

    for t in toks:
        k = t.lower().rstrip(".,")
        if t.isspace() and run:
            run.append(t)
        elif k.isdigit() or k in _SCALE or k in ("a", "an", "and"):
            run.append(t)
        else:
            flush(); run = []; out.append(t)
    flush()
    return "".join(out)


def _en_num_to_digits(s: str) -> str:
    """英文數字詞統一成阿拉伯數字。

    R3 規則把「Stage 2」改寫成「Stage two」送進 TTS,但 Whisper 聽到之後
    多半寫回「Stage 2」。這不是發音錯誤,若不統一會系統性低估分數 ——
    對 Mem zero、GPT four o mini 這類詞尤其嚴重。

    英文集數實測補上的三類(都是 Whisper 寫數字、稿子寫詞):
      ninety-fifth percentile -> 95th、twenty-four percent -> 24%、five percent -> 5%
    """
    s = re.sub(r"(?<=\d),(?=\d)", "", s)   # Whisper 寫 9,900,先把千分位拿掉
    words = "|".join(list(_ORD_IRREG) + [w + "th" for w in _NUM_ONES | _NUM_TENS]
                     + [w[:-1] + "ieth" for w in _NUM_TENS])
    s = re.sub(r"\b(" + words + r")\b",
               lambda m: _ord_to_card(m.group(0).lower()), s, flags=re.I)

    # 複合數字要先處理,否則 twenty-four 會被拆成 20 和 4。
    s = re.sub(r"\b(" + "|".join(_NUM_TENS) + r")[\s-]+(" + "|".join(_NUM_ONES) + r")\b",
               lambda m: str(_NUM_TENS[m.group(1).lower()]
                             + _NUM_ONES[m.group(2).lower()]), s, flags=re.I)
    allnum = _NUM_ONES | _NUM_TENS
    s = re.sub(r"\b(" + "|".join(allnum) + r")\b",
               lambda m: str(allnum[m.group(0).lower()]), s, flags=re.I)

    s = _fold_scales(s)
    # 數字後的序數字尾與 percent 兩邊拉齊(95th -> 95,5 percent -> 5%)。
    s = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", s, flags=re.I)
    s = re.sub(r"\s*\bpercent\b", "%", s, flags=re.I)
    return s


def norm_for_compare(s: str, lang: str = "zh") -> str:
    """比對前正規化:去標點空白、統一大小寫與數字寫法。

    目的是讓相似度只反映『字有沒有唸對』,排除與發音無關的差異:
      1. 簡繁(Whisper 有時輸出簡體)—— 僅中文
      2. 中文數字 vs 阿拉伯數字(十五 / 15)—— 僅中文
      3. 英文數字詞 vs 阿拉伯數字(two / 2)—— 兩者都要
      4. 標點與空白

    英文稿不能跑 OpenCC:s2twp 是簡繁詞彙對應表,對純英文是白花時間,
    而且會連帶把稿子裡少數的中文專有名詞改掉,製造假差異。
    """
    if lang == "zh":
        s = _to_trad(s)
    # Mem0 為了讓耳朵分辨得出來,稿子一律寫成「Mem zero」,但 Whisper 會
    # 寫回原本的 Mem0 / Memzero。這是刻意的改寫,不是唸錯。
    s = re.sub(r"\bmem\s*zero\b", "Mem0", s, flags=re.I)
    s = _en_num_to_digits(s)   # 必須在移除空白前,否則 \b 詞邊界失效
    # 小數點要保留:先拿掉「非數字之間」的句點,再清其餘標點,
    # 否則 48.7% 會被壓成 487%,與「百分之四十八點七」對不起來。
    s = re.sub(r"(?<!\d)\.(?!\d)", "", s)
    s = re.sub(r"[,,。、!!??::;;()()\[\]「」『』\"'\s—~]", "", s)
    s = re.sub(r"[-負]", "", s)   # 連字號與「負」一律去掉,兩邊同等對待
    if lang == "zh":
        s = _zh_num_to_digits(s)
    # 「百分之四十八點七」會變成 %48.7,但 Whisper 寫的是 48.7% —— 統一成後綴,
    # 否則正規化過的稿子會被系統性低估(n08 曾因此從 1.000 掉到 0.892)。
    s = re.sub(r"%(\d+(?:\.\d+)?)", r"\1%", s)
    return s.lower()


def spoken_form(s: str, lang: str = "zh") -> str:
    """把輸入文字轉成『預期被唸出來的樣子』。
    L.L.M. 唸出來 STT 會寫成 LLM,點要先去掉。"""
    return norm_for_compare(s, lang)

def leaks_prompt(style: str, got: str, expected: str, lang: str) -> bool:
    """轉錄裡是否出現風格提示的句子 —— TTS 把指示唸出來了。

    這跟「疑似幽靈音」不同:幽靈音常是 Whisper 自己編的,這個是提示的原句
    逐字出現在轉錄裡,而且稿子本身沒有那句話,所以一定是 TTS 的問題,
    不用看語速,直接重骰。可能出現在開頭(ep003 b21)也可能在結尾。
    """
    st = spoken_form(style, lang)
    if not st:
        return False
    m = difflib.SequenceMatcher(None, st, got, autojunk=False) \
        .find_longest_match(0, len(st), 0, len(got))
    return m.size >= min(8 if lang == "zh" else 20, len(st)) \
        and st[m.a:m.a + m.size] not in expected


def _load_stt():
    from mlx_audio.stt.utils import load_model
    print(f"載入 STT: {STT_MODEL}", flush=True)
    return load_model(STT_MODEL)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0])
    rows = json.loads((d / "report.json").read_text())

    lang = None
    if "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]
    lang = lang or detect_lang([r.get("text", "") for r in rows])
    sp, unit = SPEED[lang], UNIT[lang]
    print(f"語言:{lang}(語速正常區間 {sp['low']}-{sp['high']} {unit})")

    stt = _load_stt()

    out = []
    for i, r in enumerate(rows, 1):
        w = d / f"{r['id']}.wav"
        if not w.exists():
            print(f"[{i:2d}/{len(rows)}] {r['id']:26s} 缺音檔,跳過", flush=True)
            continue
        # temperature 固定 0.0(關掉 fallback 取樣)+ condition_on_previous_text=False
        # + hallucination_silence_threshold —— 這三個合起來才有效,任一個漏掉都不夠。
        # 起因:預設 temperature 是 (0.0, 0.2, ..., 1.0) 的 fallback tuple,Whisper
        # 對音檔尾端的短暫低能量段沒信心時會往上調溫度重試,調高溫度就是在取樣,
        # 同一個音檔重跑三次會編出三種不同的幻覺文字(親眼測過:同一份 wav,
        # 幻覺過「請訂閱轉發打賞」這種 YouTube 片尾語,也幻覺過別的亂碼)。
        # 這代表「疑似幽靈音」這個警示以前有不小比例是 STT 自己編的,不是 TTS
        # 真的講錯——之前 ep002 因此重骰了好幾段其實沒問題的音檔,白花了成本。
        # 固定 temperature=0.0 讓解碼可重現,同一份音檔重跑結果一致。
        res = stt.generate(str(w), language=lang, temperature=0.0,
                           condition_on_previous_text=False,
                           hallucination_silence_threshold=2.0)
        got = res.text if hasattr(res, "text") else str(res)

        a, b = spoken_form(r["text"], lang), spoken_form(got, lang)
        # autojunk=False 是必要的:difflib 預設對長度 >200 的序列,把出現頻率
        # 超過 1% 的元素當成雜訊剔除。逐字比對時英文的 e/t/a、中文的「的」
        # 全部符合,整段分數會直接崩掉(b42 只少了開頭一句卻算出 0.058)。
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ratio = sm.ratio()
        diffs = [f"預期「{a[i1:i2]}」→實際「{b[j1:j2]}」"
                 for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]

        cps = r.get("chars_per_sec", 0)
        flags = []
        if cps and cps < sp["runaway"]:  flags.append("失控")
        elif cps > sp["high"]:           flags.append("過快")
        elif cps and cps < sp["low"]:    flags.append("偏慢")
        if ratio < 0.90:             flags.append("STT差異大")
        if len(b) > len(a) * 1.15:   flags.append("疑似幽靈音")
        if leaks_prompt(r.get("style", ""), b, a, lang):
            flags.append("提示洩漏")

        mark = "○" if not flags else "⚠ " + ",".join(flags)
        print(f"[{i:2d}/{len(rows)}] {r['id']:26s} {cps:5.1f}{unit} sim={ratio:.3f} {mark}",
              flush=True)
        if diffs and ratio < 0.95:
            for x in diffs[:4]:
                print(f"           {x}", flush=True)
        out.append({**r, "transcribed": got, "similarity": round(ratio, 3),
                    "diffs": diffs[:10], "flags": flags})

    (d / "report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    clean = [r for r in out if not r["flags"]]
    avg = sum(r["similarity"] for r in out) / len(out) if out else 0
    print(f"\n=== {d.name}: {len(clean)}/{len(out)} 無標記,平均 sim={avg:.3f} ===")
    bad = [r["id"] for r in out if r["flags"]]
    if bad:
        print("需要人耳確認:", ", ".join(bad))


if __name__ == "__main__":
    main()

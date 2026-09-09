"""beats.json 的結構檢查 —— 在合成之前擋下問題,對應 plan.md 原則二「fail fast」。

合成一集要 30 分鐘,所以所有能靠讀稿子發現的問題都必須在這一步攔下來。

語言由稿子自動判斷。中英文的字元密度差約 2.8 倍(英文一個音節平均 3 個字母
以上),所以長度、語速、重複句偵測的門檻都要各有一套,不能共用。

用法:
    uv run python pipeline/validate.py episodes/<slug>/zh.json
"""
import sys, json, re, statistics, collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify import detect_lang   # 語言判準只有一份,避免兩支腳本各判各的
from brand import AUDIO_DISCLOSURE, AUDIO_DISCLOSURE_SUGGESTED

ROLES = {"hook", "identity", "promise", "signpost", "context", "mechanism",
         "analogy", "evidence", "turn", "recap", "critique", "opinion",
         "payoff", "outro"}
BODY = {"context", "mechanism", "evidence", "analogy"}

# Gemini 實測:提示相對正文太長會穩定回 502 空音訊。
# 45 字提示配 24 字正文必掛,配 32 字正文正常。留 2.0 倍的安全邊際。
MIN_TEXT_RATIO = 2.0

# 各語言的門檻。cpm 是每分鐘字元數,只用來估算集數長度;
# short/stdev 是「節奏夠不夠參差」的下限;overlap 是相鄰段重複句的判定長度。
LANG = {
    "zh": {"cpm": (260, 330), "short": 60,  "stdev": 40,  "overlap": 8},
    "en": {"cpm": (760, 950), "short": 170, "stdev": 110, "overlap": 5},
}


def norm(s):
    return re.sub(r"[,,。、!!??::;;()()「」『』\s—~]", "", s)


def check(items, lang):
    cfg = LANG[lang]
    errs, warns = [], []
    ids = [x["id"] for x in items]

    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        errs.append(f"重複的 id:{dup}")

    for x in items:
        if x.get("role") not in ROLES:
            errs.append(f"{x['id']}:未知 role「{x.get('role')}」")
        if not x.get("text", "").strip():
            errs.append(f"{x['id']}:text 是空的")

    # --- 相鄰 beat 的重複句 ---
    # 實測踩過的坑:先寫完內文、事後插入 signpost,結果路標把內文第一句
    # 又講了一遍。聽起來像跳針,而 STT 驗證完全抓不到(兩段各自都正確)。
    # 中文比字元、英文比詞:英文一個詞平均 5 個字母,用字元數當門檻會把
    # "the memory" 這種無意義的碎片也算成重複。
    for a, b in zip(items, items[1:]):
        if lang == "zh":
            tail, head = norm(a["text"])[-40:], norm(b["text"])[:40]
            unit = "字"
        else:
            tail = re.findall(r"[a-z0-9']+", a["text"].lower())[-12:]
            head = re.findall(r"[a-z0-9']+", b["text"].lower())[:12]
            unit = "詞"
        best, seg = 0, None
        for n in range(cfg["overlap"], min(len(tail), len(head)) + 1):
            for i in range(len(tail) - n + 1):
                chunk = tail[i:i + n]
                if (chunk in head if lang == "zh"
                        else any(head[j:j + n] == chunk for j in range(len(head) - n + 1))):
                    if n > best:
                        best, seg = n, chunk
        # 專有名詞跨段重複是正常的(「Mem zero」在相鄰段都出現很合理),
        # 中文另外要求重疊片段本身含有足夠的中文,才算是「整句講了兩遍」。
        if seg is not None and best >= cfg["overlap"]:
            if lang == "zh" and len(re.findall(r"[一-鿿]", seg)) < 4:
                continue
            shown = seg if lang == "zh" else " ".join(seg)
            errs.append(f"{a['id']} 結尾與 {b['id']} 開頭重複「{shown}」({best} {unit})"
                        f" —— 插了路標就要修剪下一段的開頭")

    # --- 連續解說段落 ---
    run, chain = 0, []
    for x in items:
        if x["role"] in BODY:
            run += 1
            chain.append(x["id"])
            if run > 4:
                errs.append(f"連續 {run} 段解說無喘息:{' -> '.join(chain[-run:])}"
                            f" —— 在中間插 signpost 或 recap")
        else:
            run, chain = 0, []

    # --- 提示 / 正文比例 ---
    thin = []
    for x in items:
        st = len(x.get("style", ""))
        tx = len(x["text"])
        if st and tx < st * MIN_TEXT_RATIO:
            thin.append(x["id"])

    if thin:
        warns.append(f"{len(thin)} 段正文短於提示的 {MIN_TEXT_RATIO} 倍,"
                     f"Gemini 可能回空音訊 —— tts.py 會自動降級提示因應,"
                     f"通常不用處理:{', '.join(thin[:6])}"
                     + (" ..." if len(thin) > 6 else ""))

    # 開場四段是固定結構:hook -> identity -> promise -> roadmap。
    # b02 / b03 很容易在改稿時被吃掉,而它們正是「要不要投資 30 分鐘」
    # 這個決定的依據,所以列為硬性錯誤。
    opening = [x.get("role") for x in items[:4]]
    if opening != ["hook", "identity", "promise", "signpost"]:
        errs.append(f"開場四段的 role 應為 hook/identity/promise/signpost,"
                    f"實際是 {'/'.join(str(r) for r in opening)}")

    # AI 揭露。Apple Podcasts 第 1.11 條要求音訊內與 metadata 兩處都要有,
    # 漏掉可能整集下架。開場白每集由 TTS 重新生成,措辭可以跟當集主題呼應,
    # 但「聲音是 AI 合成」這個事實不能不見 —— 所以驗事實不驗逐字。
    ident = [x for x in items if x.get("role") == "identity"]
    if not any(AUDIO_DISCLOSURE[lang].search(x["text"]) for x in ident):
        errs.append("identity beat 缺 AI 揭露(Apple Podcasts 1.11)。"
                    f"建議措辭:{AUDIO_DISCLOSURE_SUGGESTED[lang]}")

    # 章節標記給 show notes 的時間戳用。標在 signpost 上,聽眾看得懂的說法,
    # 不要用 beat 欄位那種內部描述(「路標 — 第一站」對聽眾沒有意義)。
    ch = [x for x in items if x.get("chapter")]
    if len(ch) < 4:
        warns.append(f"只有 {len(ch)} 個 chapter 標記,show notes 的章節會太少;"
                     f"在主要的 signpost 段加 \"chapter\" 欄位(建議 6-10 個)")

    c = collections.Counter(x["role"] for x in items)
    L = [len(x["text"]) for x in items]
    if c["recap"] < 2:
        errs.append(f"recap 只有 {c['recap']} 個,至少要 2 個")
    if c["signpost"] < 3:
        errs.append(f"signpost 只有 {c['signpost']} 個,至少要 3 個")
    if sum(1 for l in L if l < cfg["short"]) < 3:
        warns.append(f"短 beat(<{cfg['short']} 字元)少於 3 個,節奏會太平均")
    if len(L) > 1 and statistics.stdev(L) < cfg["stdev"]:
        warns.append(f"beat 長度標準差 {statistics.stdev(L):.0f} < {cfg['stdev']},長度太均勻")
    if len(set(x.get("style", "") for x in items)) < 5:
        warns.append("語氣提示種類太少,整集會聽起來很平")

    return errs, warns, c, L, cfg


def main():
    p = Path(sys.argv[1])
    items = json.loads(p.read_text())
    lang = sys.argv[2] if len(sys.argv) > 2 else detect_lang(
        [x.get("text", "") for x in items])
    errs, warns, c, L, cfg = check(items, lang)

    tot = sum(L)
    lo, hi = cfg["cpm"]
    print(f"{p.name}[{lang}]:{len(items)} beats,{tot} 字元,"
          f"預估 {tot/hi:.0f}-{tot/lo:.0f} 分鐘,約 US${tot/1e6:.3f}")
    print(f"長度 平均{statistics.mean(L):.0f} 標準差{statistics.stdev(L):.0f} "
          f"最短{min(L)} 最長{max(L)}")
    print("role:", dict(c))
    for w in warns:
        print(f"  ⚠ {w}")
    for e in errs:
        print(f"  ✗ {e}")
    print("\n通過" if not errs else f"\n{len(errs)} 個問題必須修正")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()

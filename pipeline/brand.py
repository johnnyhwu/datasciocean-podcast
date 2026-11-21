"""節目的固定字串 —— 名稱、網址、簡介。

單獨一支的理由:這些字串會被 validate.py(擋稿)、shownotes.py(產出)
以及日後的 RSS 腳本同時用到。散在各處就會漂移。

中英是**兩個獨立節目**,不是同一個節目的兩種語言 —— RSS 的 <language>
是節目層級的單一欄位,混語言會被 Apple 以「Incorrect Language」退件。
"""
import json
import re
from pathlib import Path

SITE = "https://datasciocean.com"

# 交付速度(人聲的播放倍率),各語言各有預設,單集可在 meta.json 用
# `ship_rate` 覆寫(一個數字,或 {"zh": 1.1})。目前中英都是 1.0,不加速。
#
# 不是 1.0 時:`assemble.py` 只拉伸人聲,片頭、轉場、片尾維持原速;
# 章節時間戳來自交付速度的 `MIX.json`。`assemble.py`、`shownotes.py`、
# `validate.py` 都透過 `ship_rate()` 取值,所以改預設或覆寫不需要動別處。
#
# app 的倍速是疊在檔案本身之上的:交付 1.1 之後想聽 1.2 的人拿到的是 1.32。
SHIP_RATE = {"zh": 1.0, "en": 1.0}
ROOT = Path(__file__).resolve().parent.parent


def ship_rate(lang: str, slug: str | None = None) -> float:
    """這一集這個語言的交付速度:meta.json 的 ship_rate 優先,否則用 SHIP_RATE。"""
    if slug:
        meta = ROOT / "episodes" / slug / "meta.json"
        if meta.exists():
            r = json.loads(meta.read_text()).get("ship_rate")
            r = r.get(lang) if isinstance(r, dict) else r
            if r is not None:
                return float(r)
    return SHIP_RATE[lang]

# 節目簡介 —— RSS 的節目層級欄位,也是上架平台填的那一段。
# Johnny 自己寫的,不要改寫成比較「工整」的版本:開場從聽眾的焦慮切入、
# 痛點寫得具體(20 頁論文、被術語擋在門外)、海洋的比喻同時扣住節目名與封面
# (封面上那顆在深水中發光的鉛錘就是「探照燈」)。這些是它有效的原因。
#
DESCRIPTION = {
    "zh": """AI 與數據技術像一片深不見底的大洋,每天都有看不完的新進展。面對資訊洪流,你是否也感到焦慮?

啃完一篇 20 頁的論文往往要耗掉大半天;翻開頂尖科技公司的 Engineering Blog,又常被滿紙架構術語擋在門外。好不容易看懂了,才發現很多數字是精挑細選過的「包裝」,實際落地滿是地雷。

DataSci Ocean 想做的,是你在這片深海裡的探照燈。我會替你讀完那些複雜的論文與技術文章,徹底消化後再用好懂的語言拆解:

💡 講清技術本質:不賣弄術語,帶你看懂這個模型或架構到底為了解決什麼痛點。
💡 說論文沒說的真話:哪些實驗設計有洞?哪些限制被刻意略過?幫你過濾炒作泡沫。
💡 關注對你的啟發:不只是學術玩具,更關乎工程實踐與落地可能。

節目長度隨主題自然呼吸——有時是 15 分鐘的關鍵輕解讀,有時是近一小時的徹底深潛。

不必再對著複雜的 PDF 孤單發呆。戴上耳機,這一次有人陪你一起下潛。

我是 Johnny。內容改編自我個人的研讀筆記。完整的架構圖、Prompt 範例與程式碼在部落格:https://datasciocean.com/""",
    # 英文版是**重寫不是翻譯**。中文版的結構沿用(痛點 -> 定位 -> 收尾 -> 揭露),
    # 但英文市場同類節目多一個量級,所以差異化(「論文沒說的部分」)提前到
    # 定位句就講完,不鋪陳。海洋的比喻對齊封面 —— 封面上就是一盞被垂降到
    # 深水裡的燈,不是岸上掃射的探照燈。
    # 沒有直譯「你是否也感到焦慮」:那在英文裡是明顯的翻譯腔,改成用事實
    # 製造焦慮而不用「焦慮」這個字。
    "en": """Every week brings another paper you're told you have to read. A 20-page PDF eats an afternoon, and the headline number usually turns out to have been carefully chosen.

I read them properly and take them apart in plain language — including the parts the authors left out: which experiments have holes, which limitations got quietly skipped.

You don't have to stare at another PDF alone. This time someone's going down there with you.

I'm Johnny. Adapted from my own notes. Diagrams and code: https://datasciocean.com/en/""",
}

# 節目名的念法。複製聲音會把「DataSci Ocean」念糊(ep010 被 Whisper 聽成
# 「DataShare」,Ocean 不見)。2026-11-21 試了重骰、加空格、拼音式拼法與加提示
# 四種,Johnny 耳聽選了「加提示」:正文不動,在 identity 段的 style 後面接這句。
# validate.py 會檢查 identity 段有沒有帶。
NAME_HINT = {"zh": "「DataSci Ocean」是節目名，用英文清楚地念，Data 和 Sci 分開。"}

SHOW = {
    "zh": {
        "name": "DataSci Ocean",
        "language": "zh-TW",          # 不是 zh-CN,填錯會影響平台分類
        "site": SITE,
        # {category} 預設 paper-intro(舊集數 meta.json 沒有 category 欄位時的
        # 相容值)。部落格的文章目錄不是全部都在 paper-intro 底下
        # (例如 ai-concept/),meta.json 要填 category 才能組對原文連結。
        "post": SITE + "/{category}/{article}/",
    },
    "en": {
        "name": "DataSci Ocean [English]",
        "language": "en",
        "site": SITE + "/en/",
        "post": SITE + "/en/{category}/{article}/",
    },
}

# Spotify 的節目簡介上限是 600 字元,超過會被截斷,在匯入時就擋掉。
DESCRIPTION_MAX = 600
for _lang, _text in DESCRIPTION.items():
    if _text is not None and len(_text) > DESCRIPTION_MAX:
        raise ValueError(
            f"節目簡介({_lang})有 {len(_text)} 字元,超過 {DESCRIPTION_MAX} 上限。"
            f"平台會截斷。請先縮短。")

# 不揭露 AI 語音(2026-11-21 Johnny 的決定):節目改用他自己的複製聲音,
# 音訊與 show notes 都不提 AI 合成。他知道 Apple Podcasts 1.11 的要求,
# 目前只上 Spotify,風險由他承擔。日後要上 Apple 前請先跟他重新確認。

FOOTER = {
    "zh": "這集提到的架構圖和實驗數據，用聽的實在沒辦法。完整的筆記我寫在部落格上：",
    "en": "The architecture diagrams and the experiment tables just don't "
          "work in audio. The full write-up is on the blog:",
}

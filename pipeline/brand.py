"""節目的固定字串 —— 名稱、網址、AI 揭露。

單獨一支的理由:這些字串會被 validate.py(擋稿)、shownotes.py(產出)
以及日後的 RSS 腳本同時用到。散在各處就會漂移,而揭露那句話漂移的代價
是整集下架(Apple Podcasts 第 1.11 條)。

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
# **最後一行的 AI 揭露不能刪。** Apple Podcasts 第 1.11 條要求音訊與 metadata
# 兩處都要揭露,音訊端在 b01_identity,metadata 端就是這裡。用「合成」不用
# 「演繹」—— 後者可能被讀成在描述表演風格而不是在揭露技術。
DESCRIPTION = {
    "zh": """AI 與數據技術像一片深不見底的大洋,每天都有看不完的新進展。面對資訊洪流,你是否也感到焦慮?

啃完一篇 20 頁的論文往往要耗掉大半天;翻開頂尖科技公司的 Engineering Blog,又常被滿紙架構術語擋在門外。好不容易看懂了,才發現很多數字是精挑細選過的「包裝」,實際落地滿是地雷。

DataSci Ocean 想做的,是你在這片深海裡的探照燈。我會替你讀完那些複雜的論文與技術文章,徹底消化後再用好懂的語言拆解:

💡 講清技術本質:不賣弄術語,帶你看懂這個模型或架構到底為了解決什麼痛點。
💡 說論文沒說的真話:哪些實驗設計有洞?哪些限制被刻意略過?幫你過濾炒作泡沫。
💡 關注對你的啟發:不只是學術玩具,更關乎工程實踐與落地可能。

節目長度隨主題自然呼吸——有時是 15 分鐘的關鍵輕解讀,有時是近一小時的徹底深潛。

不必再對著複雜的 PDF 孤單發呆。戴上耳機,這一次有人陪你一起下潛。

我是 Johnny。內容改編自我個人的研讀筆記,由 AI 語音合成。完整的架構圖、Prompt 範例與程式碼在部落格:https://datasciocean.com/""",
    # 英文版是**重寫不是翻譯**。中文版的結構沿用(痛點 -> 定位 -> 收尾 -> 揭露),
    # 但英文市場同類節目多一個量級,所以差異化(「論文沒說的部分」)提前到
    # 定位句就講完,不鋪陳。海洋的比喻對齊封面 —— 封面上就是一盞被垂降到
    # 深水裡的燈,不是岸上掃射的探照燈。
    # 沒有直譯「你是否也感到焦慮」:那在英文裡是明顯的翻譯腔,改成用事實
    # 製造焦慮而不用「焦慮」這個字。
    "en": """Every week brings another paper you're told you have to read. A 20-page PDF eats an afternoon, and the headline number usually turns out to have been carefully chosen.

I read them properly and take them apart in plain language — including the parts the authors left out: which experiments have holes, which limitations got quietly skipped.

You don't have to stare at another PDF alone. This time someone's going down there with you.

I'm Johnny. Adapted from my own notes; the voice is AI-generated. Diagrams and code: https://datasciocean.com/en/""",
}

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

# Spotify 的節目簡介上限是 600 字元。超過會被截斷,而被截斷的位置正好是
# 最後一行 —— 也就是 Apple 1.11 要求的 metadata 端 AI 揭露。所以這不是
# 排版問題,是合規問題,在匯入時就擋掉。
DESCRIPTION_MAX = 600
for _lang, _text in DESCRIPTION.items():
    if _text is not None and len(_text) > DESCRIPTION_MAX:
        raise ValueError(
            f"節目簡介({_lang})有 {len(_text)} 字元,超過 {DESCRIPTION_MAX} 上限。"
            f"平台會截斷,而被切掉的是結尾的 AI 揭露。請先縮短。")

# 音訊內的揭露。每集由 TTS 重新生成,所以只驗「必須出現的事實」而不是
# 逐字比對 —— 措辭可以跟當集主題呼應,但「聲音是 AI 合成」這件事不能不見。
# 「這是 AI 的聲音」這件事必須出現。措辭可以換,事實不能掉。
# 主詞收 聲音/音訊/語音,動詞收 合成/生成 —— 放寬過一次,因為原本只收
# 「聲音…合成」,而「本集音訊交由 AI 語音合成」這種寫法會被誤判成漏揭露。
AUDIO_DISCLOSURE = {
    "zh": re.compile(r"(聲音|音訊|語音).{0,10}AI.{0,8}(合成|生成)"),
    "en": re.compile(r"(voice|audio|speech).{0,40}AI[\s-]?generated"
                     r"|AI[\s-]?generated.{0,25}(voice|audio|speech)", re.I),
}

# 給寫稿用的建議措辭(不強制逐字,但「聲音是 AI 合成」一定要在)。
#
# 揭露到哪為止:**只揭露語音**。1.11 管的是「聽眾以為在聽真人」,
# 不管來源素材怎麼寫的。論文是 Johnny 自己讀的、筆記是他跟 AI 共同撰寫並
# 掛名發表的 —— 那就是他的筆記,寫作過程不在揭露範圍,也不是業界會揭露的事。
#
# 但要用「改編**自**我的筆記」而不是「內容**就是**我的筆記」:
# 在 podcast 的語境裡「內容」會被聽成「這一集」,而這集的逐字稿確實是
# 從筆記改寫來的。一字之差,而且比原本更準確。
AUDIO_DISCLOSURE_SUGGESTED = {
    "zh": "這個節目的聲音是 AI 合成的,內容改編自我自己讀論文寫的筆記。",
    "en": "The voice you're hearing is AI generated. The content is adapted "
          "from my own notes, written while I read the paper.",
}

# metadata 端的揭露。這是文字、不會被聽,所以固定一份,好稽核。
#
# 語氣是 Johnny 自己定的:**要像人講話,不要像法務聲明。** show notes 的
# 最後一句還是節目的一部分,制式的句子會把前面建立的語氣掐掉。
# 「因為本人比較害羞」是玩笑,但它不影響揭露 —— 後半句把事實講得很清楚,
# 而 1.11 要的是聽眾不會誤以為在聽真人,不是要一段嚴肅的聲明。
META_DISCLOSURE = {
    "zh": "因為本人比較害羞,本集音訊交由 AI 語音合成。"
          "Podcast 內容主要基於我自己讀論文時寫的筆記。",
    "en": "I'm a little shy, so this episode's audio is AI-generated speech. "
          "The content is based on notes I wrote while reading the paper myself.",
}

# 改上面那兩段措辭時,這個檢查會擋下「改到把事實改掉」的情況。
# 放在 import 時跑:揭露壞了就不該有任何東西跑得起來。
for _lang, _text in META_DISCLOSURE.items():
    if not AUDIO_DISCLOSURE[_lang].search(_text):
        raise AssertionError(
            f"META_DISCLOSURE[{_lang!r}] 沒有通過 AUDIO_DISCLOSURE 的檢查 —— "
            f"「這是 AI 合成的聲音」這個事實不見了。Apple Podcasts 1.11 要求"
            f"音訊與 metadata 兩處都揭露,漏掉可能整集下架。\n  現況:{_text}")

FOOTER = {
    "zh": "這集提到的架構圖和實驗數據,用聽的實在沒辦法。完整的筆記我寫在部落格上:",
    "en": "The architecture diagrams and the experiment tables just don't "
          "work in audio. The full write-up is on the blog:",
}

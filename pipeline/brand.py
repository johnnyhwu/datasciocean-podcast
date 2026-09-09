"""節目的固定字串 —— 名稱、網址、AI 揭露。

單獨一支的理由:這些字串會被 validate.py(擋稿)、shownotes.py(產出)
以及日後的 RSS 腳本同時用到。散在各處就會漂移,而揭露那句話漂移的代價
是整集下架(Apple Podcasts 第 1.11 條)。

中英是**兩個獨立節目**,不是同一個節目的兩種語言 —— RSS 的 <language>
是節目層級的單一欄位,混語言會被 Apple 以「Incorrect Language」退件。
"""
import re

SITE = "https://datasciocean.com"

SHOW = {
    "zh": {
        "name": "DataSci Ocean",
        "language": "zh-TW",          # 不是 zh-CN,填錯會影響平台分類
        "site": SITE,
        "post": SITE + "/paper-intro/{article}/",
    },
    "en": {
        "name": "DataSci Ocean [English]",
        "language": "en",
        "site": SITE + "/en/",
        "post": SITE + "/en/paper-intro/{article}/",
    },
}

# 音訊內的揭露。每集由 TTS 重新生成,所以只驗「必須出現的事實」而不是
# 逐字比對 —— 措辭可以跟當集主題呼應,但「聲音是 AI 合成」這件事不能不見。
AUDIO_DISCLOSURE = {
    "zh": re.compile(r"聲音.{0,8}AI.{0,6}合成"),
    "en": re.compile(r"voice.{0,40}AI[\s-]?generated|AI[\s-]?generated.{0,25}voice",
                     re.I),
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

# metadata 的揭露相反 —— 這是文字、不會被聽,固定反而更明確、更好稽核。
META_DISCLOSURE = {
    "zh": "本集音訊由 AI 語音合成,內容改編自 Johnny 讀論文寫的筆記。",
    "en": "This episode's audio is AI-generated speech. The content is "
          "adapted from Johnny's own notes on the paper.",
}

FOOTER = {
    "zh": "這集提到的架構圖和實驗數據,用聽的實在沒辦法。完整的筆記我寫在部落格上:",
    "en": "The architecture diagrams and the experiment tables just don't "
          "work in audio. The full write-up is on the blog:",
}

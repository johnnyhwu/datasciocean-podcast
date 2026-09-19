"""節目的固定字串 —— 名稱、網址、AI 揭露。

單獨一支的理由:這些字串會被 validate.py(擋稿)、shownotes.py(產出)
以及日後的 RSS 腳本同時用到。散在各處就會漂移,而揭露那句話漂移的代價
是整集下架(Apple Podcasts 第 1.11 條)。

中英是**兩個獨立節目**,不是同一個節目的兩種語言 —— RSS 的 <language>
是節目層級的單一欄位,混語言會被 Apple 以「Incorrect Language」退件。
"""
import re

SITE = "https://datasciocean.com"

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
    # 英文版**重寫,不翻譯** —— 英文市場同類節目多得多,差異化的講法要換一套。
    # 故意留 None:之後的 RSS 腳本讀到會直接炸掉,而不是靜靜發布一段空簡介。
    "en": None,
}

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

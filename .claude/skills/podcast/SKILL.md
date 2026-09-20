---
name: podcast
description: 把 Johnny 部落格的一篇技術文章做成完整的 podcast,中文版與英文版各一集。使用者說「我想把 XXX 文章轉成 podcast」「做一集 XXX」「做個英文版」時使用。涵蓋讀文章、寫 beats.json 逐字稿、Gemini TTS 合成、Whisper 驗證、混入片頭轉場片尾、輸出交付檔與 show notes。
---

# 製作一集 podcast

**預設出中英兩版。** 使用者只講文章、沒指定語言時,就是兩版都要,
而且**兩版都要跑完整的 validate 與 verify** —— 不要只驗中文那版。
使用者若只要其中一版,他會明講。

一集用一個 slug,格式是 `ep<三位數>-<短名>`(例如 `ep001-mem0`)。
短名通常就是部落格文章的目錄名。

```
episodes/<slug>/zh.json   episodes/<slug>/en.json   episodes/<slug>/meta.json
out/<slug>/zh/            out/<slug>/en/
```

**這個路徑形狀是有意義的,不要自己改。** `assemble.py` 與 `shownotes.py`
都從 `out/<slug>/<lang>` 反推 slug 與語言,再去讀 `episodes/<slug>/<lang>.json`。
把輸出放到別的地方,它們會找不到逐字稿。

**每一步做完先回報再繼續**,不要一路衝到底 ——
逐字稿是使用者最在意的部分,他會想在合成前看過。

---

## 步驟 1:讀文章

文章在 `~/Desktop/johnnyhwu.github.io/content/posts/paper-intro/<slug>/index.zh-tw.md`。

使用者可能給 slug、標題關鍵字、或整個 URL。找不到就用
`find ~/Desktop/johnnyhwu.github.io/content -name "*.zh-tw.md" | grep -i <關鍵字>`。

**整篇讀完再動筆。** 特別注意:
- 圖表裡的數字(`{{< image >}}` 的 `alt` 與 `caption` 常含關鍵數據)
- 作者自己的評論與質疑(這些是 `opinion` / `critique` beat 的素材)
- 論文沒解釋、但你能推論的地方(這是最有價值的內容,但**必須標明是推論**)

## 步驟 2:讀判準

寫稿前**一定要讀**這個 skill 目錄底下的 `reference/NARRATION.md` 和
`reference/NORMALIZATION.md`(絕對路徑:`.claude/skills/podcast/reference/`)。
要出英文版就再讀 NARRATION.md 的**第十節**(為什麼不能翻譯、門檻換算表)。
它們是從實際踩過的坑長出來的,不是通則。

## 步驟 3:寫中文版 `episodes/<slug>/zh.json`

```json
[{"id": "b00_hook", "role": "hook", "beat": "簡短說明這段的作用",
  "style": "<風格提示,見下>", "text": "<逐字稿>"}]
```

### role 與風格提示

`style` 是固定骨幹加一句 role 語氣。**不要超過 50 字** ——
提示相對正文太長,Gemini 會回空音訊(見 GEMINI-TTS.md)。

骨幹(中文):`請用台灣人的口音說話,像台北的科技 podcast 主持人那樣。`
骨幹(英文):`Speak in a neutral American accent, like the host of a tech podcast.`

| role | 中文語氣 | 英文語氣 |
|---|---|---|
| `hook` | 語氣好奇,帶點困惑,像在丟一個謎題。 | Sound curious, a little puzzled, like you're laying out a riddle. |
| `identity` | 語氣親切清楚,像在自我介紹。 | Sound warm and clear, like you're introducing yourself. |
| `promise` | 語氣有精神,像在告訴朋友這集值得聽。 | Sound energetic, like you're telling a friend this one is worth their time. |
| `signpost` | 語氣俐落,像在標一個路標。 | Sound crisp and brisk, like you're planting a signpost. |
| `context` | 語氣平穩清楚,把背景交代好。 | Sound steady and clear, laying out the background. |
| `mechanism` | 語氣耐心而清楚,像在解釋一個機制。 | Sound patient and precise, like you're explaining how something works. |
| `analogy` | 語氣輕鬆,像在打一個生活化的比方。 | Sound relaxed, like you're reaching for an everyday comparison. |
| `evidence` | 語氣篤定,就事論事地報數字。 | Sound matter-of-fact, just reporting the numbers. |
| `turn` | 語氣帶點驚訝和好笑,像在揭曉意外。 | Sound a little surprised and amused, like you're revealing a twist. |
| `recap` | 語氣沉穩,幫聽眾把剛剛的東西收攏。 | Sound calm and grounded, pulling the last stretch together. |
| `critique` | 語氣存疑,若有所思。 | Sound skeptical and thoughtful. |
| `opinion` | 語氣坦率,像在講自己的真心話。 | Sound candid, like you're saying what you actually think. |
| `payoff` | 語氣篤定,慢慢把答案講出來。 | Sound certain, delivering the answer slowly. |
| `outro` | 語氣溫暖,收尾。 | Sound warm, wrapping up. |

**提示語言必須跟正文一致** —— tts.py 的降級階梯跟著提示的語言走,
混語言會讓降級後的口音跑掉。

### 篇幅

**寧願講清楚也不要蜻蜓點水。** 20-40 分鐘都可以,必要時更長。
中文約 300 字元 / 分鐘(30 分鐘 ≈ 9,000 字元),
英文約 850 字元 / 分鐘(30 分鐘 ≈ 26,000 字元)。兩者都是 65-70 個 beat。

### 開場的固定結構(validate.py 會擋)

前四段的 role 必須是 `hook` → `identity` → `promise` → `signpost`:

| id | role | 固定 or 每集不同 |
|---|---|---|
| `b00_hook` | `hook` | 每集不同,不劇透 |
| `b01_identity` | `identity` | **前半固定**(節目名 + AI 揭露)+ 後半每集不同(主題預告) |
| `b02_promise` | `promise` | 每集不同,聽完會拿到哪 2-3 樣東西 |
| `b03_roadmap` | `signpost` | 每集不同,這集會走幾站 |

**b02 和 b03 很容易在改稿時被吃掉**,但它們正是聽眾決定「要不要投資
30 分鐘」的依據,所以列為硬性錯誤。細節看 NARRATION.md 第一節。

### ⚠️ AI 揭露是硬性合規要求

Apple Podcasts 第 1.11 條:AI 生成的音訊必須在**內容本身**與 **metadata**
兩處揭露,漏掉可能整集下架。開場白每集由 TTS 重新生成(不用固定音檔 ——
b01 的固定半句與變動半句在同一句裡,拆開接會有聽得出來的接縫),
所以措辭可以跟當集主題呼應,但「聲音是 AI 合成」這個事實不能不見。

建議措辭在 `pipeline/brand.py` 的 `AUDIO_DISCLOSURE_SUGGESTED`:

> 這個節目的聲音是 AI 合成的,內容改編自我自己讀論文寫的筆記。

**揭露到語音為止就好。** 1.11 管的是「聽眾以為在聽真人」,不管來源素材
怎麼寫的。論文是 Johnny 自己讀的,筆記是他跟 AI 共同撰寫並掛名發表的
—— 那就是他的筆記,寫作過程不在揭露範圍,**不要主動加上去**。

但要用「改編**自**我的筆記」,不要寫成「內容**就是**我的筆記」:
在 podcast 的語境裡「內容」會被聽成「這一集」,而這集的逐字稿確實是
從筆記改寫來的。

### chapter 欄位

在主要的 `signpost` 段加 `"chapter": "<章節名>"`,建議 6-10 個,
`shownotes.py` 會配上時間戳。中英兩版標記的段落要一對一對齊。

章節標題的寫法:

- **不要用 `beat` 欄位那種內部描述**(「路標 — 第一站」對聽眾沒有意義)
- **不要帶「第一站 / 第二站」前綴。** 那是講稿裡的敘事裝置,聽眾在音訊裡
  會聽到;寫在 show notes 上只是把最珍貴的前幾個字吃掉 —— podcast app
  的列表會截斷標題
- **寫成人話。** 「收束」「總結」「結語」這種書面語台灣人不會講,
  改成「所以,我們到底學到了什麼」。最後一章尤其容易寫成術語
- 用問句或懸念比用名詞好:「加上知識圖譜的那個版本」勝過「進階架構」

### ⚠️ 最容易犯的錯

先寫完內文、事後插入路標,結果路標把下一段的第一句又講了一遍。
**插完路標一定要把相鄰兩段連起來讀一次,修剪重複。**
`validate.py` 只抓字面重複,換句話說的重複要靠自己讀。

## 步驟 4:寫英文版 `episodes/<slug>/en.json`

**骨架沿用、內容重寫。** `id` / `role` / `beat` / `chapter` 跟中文版
一對一對齊(`chapter` 的文字要翻成英文,標記的段落必須相同),
`text` 重寫不翻譯,`style` 換英文骨幹。
為什麼、以及要換掉哪些東西(文化性類比、中文詞義解釋),見 NARRATION.md 第十節。

## 步驟 5:驗證結構(兩版都要)

```bash
uv run python pipeline/validate.py episodes/<slug>/zh.json
uv run python pipeline/validate.py episodes/<slug>/en.json
```

語言自動判斷,不用下參數;語速、短 beat、重複判定的門檻會跟著切換。

有 `✗` 就必須修到過。`⚠` 是提醒,通常可以放行
(「正文短於提示」那條是已知的,tts.py 會自動降級處理)。

**這一步過了再給使用者看逐字稿,等他確認後才合成。**

## 步驟 6:合成(兩版各跑一次)

```bash
uv run python pipeline/tts.py episodes/<slug>/zh.json out/<slug>/zh \
    --model google/gemini-3.1-flash-tts-preview --voice Zubenelgenubi --pcm
```

- 69 段約需 **30-40 分鐘**,用 `run_in_background` 跑,不要卡住對話。
- 成本:中文約 **US$0.01**,英文約 **US$0.03**(同樣內容英文字元數約 3 倍),
  先跟使用者講。
- **音色兩版共用 `Zubenelgenubi`**,不需要另外挑。
- 中斷後加 `--resume` 續跑,已存在的音檔會沿用。
- 腳本內建重試與提示降級,單段失敗會記錄後跳過,不會中斷整集。

## 步驟 7:驗證與修補(兩版都要)

```bash
uv run python pipeline/verify.py out/<slug>/zh
```

**STT 是篩選器,不是判官。** 看到標記先讀 `report.json` 的 `transcribed`
判斷是真的唸錯,還是 Whisper 自己聽錯:

| 現象 | 處理 |
|---|---|
| 結尾冒出無關字詞(幽靈音) | **刪掉該段 wav,加 `--resume` 重跑**(沒有 seed,重跑就是重骰) |
| 專有名詞唸錯 | 同上先重骰;連兩次都錯就改 beats.json 的寫法 |
| 同音字差異(在/再、記/計) | **誤報,不用理** |
| 簡繁、數字寫法差異 | **誤報**,比對時已正規化,還出現代表規則有漏 |
| 英文數字詞 vs 阿拉伯數字、`arXiv` 轉成 "Archive" | **誤報**,verify.py 已折算 |
| 標記「偏慢」或「過快」(中文 4.0-9.5,英文 11.0-20.0 字元/秒) | 請使用者用耳朵確認,刻意留白的金句可以慢 |
| 標記「**失控**」(中文 < 3.5,英文 < 9.0 字元/秒) | **不要問使用者,直接重骰。** 音檔長度遠超過文字量,通常是尾巴掛了一段幻聽或長靜音 |

改了 `verify.py` 的正規化規則之後,用
`uv run python pipeline/rescore.py <out_dir> --write` 重算,不要重跑 STT;
並且**順手 rescore 另一個語言那版**,確認新規則沒把它弄壞。

## 步驟 8:混音與輸出(兩版都要)

```bash
uv run python pipeline/stitch.py out/<slug>/zh          # 先聽純人聲,確認節奏
uv run python pipeline/assemble.py out/<slug>/zh \
  --intro music/intro.wav --outro music/outro.wav --sting music/sting.wav
uv run python pipeline/assemble.py out/<slug>/zh \
  --intro music/intro.wav --outro music/outro.wav --sting music/sting.wav --rate 1.0
afconvert -f m4af -d aac -b 128000 \
  out/<slug>/zh/FULL_EPISODE_mixed_x1.1.wav out/<slug>/zh/<slug>-zh.m4a
```

**交付速度是 1.1x,不是 1.0x。** `--rate` 的預設值就是 `brand.py` 的
`SHIP_RATE`,所以第一行不用帶參數。第二行的 1.0 是存檔母帶,不是交付物。
**只留這兩個倍率** —— app 的倍速是疊在檔案之上的,交付 1.1 之後聽眾再選 1.2
拿到的是 1.32,那是預期行為,不需要預先燒好每個倍率。

**加速必須在混音之前。** `--rate` 只拉伸人聲、停頓按比例縮短,音樂維持原速。
WSOLA 靠找相似波形重疊接起來,拉伸語音很乾淨,拉伸音樂會打散週期性,
產生顆粒感與節奏抖動。對混完的成品加速就是把音樂一起毀掉。

`assemble.py` 一次做完混音與正規化,輸出 44.1 kHz 單聲道、**-19 LUFS**、
true peak ≤ **-1 dBTP**。所以**不需要再跑 master.py**;要單獨量用
`master.py <檔> --measure`。留那 1 dB 是因為取樣點之間的波形更高,
AAC 編碼會把它推上來 —— ep001 實測吃掉 0.2-0.4 dB。

**兩版都要跑。** 兩版的原始響度不一樣(ep001:中文 -15.4、英文 -16.9),
不正規化的話聽眾切換版本會感覺到音量跳動。英文版有時會停在 -19.05 而不是
剛好 -19.00 —— 峰值天花板先到了,**保峰值優先,不要為此調高目標**。

**轉場次數是算出來的,不要手填。** 約每 9 分鐘一次、下限 2 上限 5,
由整集長度決定(ep001 29.6 分 → 3 次)。放哪幾個章節點是枚舉組合、取
「最長一段沒有標點的區間」最短的那一組。要覆寫才用 `--stings <n>`。

產出:

| 檔案 | 用途 |
|---|---|
| `<slug>-<lang>.m4a` | **上傳用**(128k AAC,1.1x) |
| `FULL_EPISODE_mixed_x1.1.wav` | 交付母帶,無損 |
| `FULL_EPISODE_mixed.wav` | 1.0 存檔母帶,**不交付** |
| `FULL_EPISODE.wav` | 純人聲,只用來試聽節奏 |
| `MIX.json` | 交付速度那份的時間戳,show notes 讀它 |

檔名容易搞混,**判準是有沒有 `_x1.1`**。沒有後綴的那個不是成品。

### 已知現象:Gemini 的輸出本來就觸頂

TTS 回傳的 PCM16 有少量樣本頂在滿刻度(ep001 中文版 69 段裡有 53 段,
合計 3,158 個樣本,佔 0.007%)。**這是 TTS 來源就有的,修不掉**,
量太小聽不出來,而且正規化是往下降,不會惡化。不用為此重錄。

## 步驟 9:show notes(兩版都要)

先寫 `episodes/<slug>/meta.json`。六個欄位都是必要的,缺一個會 KeyError:

```json
{
  "number": 1,
  "article": "mem0",
  "zh": { "title": "…", "summary": "…", "bullets": ["…", "…", "…"] },
  "en": { "title": "…", "summary": "…", "bullets": ["…", "…", "…"] }
}
```

`article` 是部落格文章的目錄名,用來組原文連結,**不是 slug** ——
`ep001-mem0` 的 `article` 是 `mem0`。`number` 目前只印出來給上架時填,
腳本不拿它做事,但要跟 slug 的編號一致。

```bash
uv run python pipeline/shownotes.py out/<slug>/zh
uv run python pipeline/shownotes.py out/<slug>/en
```

產出 `SHOWNOTES.md`,含章節時間戳、原文連結、固定的 metadata 揭露文字。

**時間戳讀 `MIX.json`**,不是自己重算 —— 片頭音樂把所有東西往後推約 6.5 秒,
每次章節轉場再推 5.4 秒。所以 show notes 一定要在步驟 8 之後跑;
還沒混音時它會退回依停頓規則估算,那份數字只能拿來檢查稿子,不能發布。

### 標題與文案:要吸引人,不要誇大

這一節是使用者親自改過 ep001 之後定下來的。他的原話是
**「不要是誇大的標題,這樣不符合我的 podcast 風格」** —— 所以下面的規則
不是「怎麼寫得更聳動」,而是**怎麼在不說謊的前提下寫得更想點**。

#### 界線在哪:一條可以驗的判準

看他改出來的標題:

```
【Mem0 深度拆解】知識圖譜輸了論文卻不說？AI Agent 長期記憶只要 4 個動作
```

它很有張力,但**每一個鉤子都是這一集裡可以指出時間點的事實**:
知識圖譜版本真的輸了兩類、論文真的沒解釋、記憶管理真的只有四個動作。

**所以判準是:每個標題與每條重點,都要能說出它在第幾分鐘被兌現。
說不出來就是誇大,不管用詞多克制。**

反過來,誇大不是「語氣太強」,而是三個具體動作:

| 誇大的做法 | 為什麼不行 | 改成 |
|---|---|---|
| 絕對化:「徹底顛覆」「你不知道的」「最強」 | 沒有一集做得到,而且不可驗證 | 講具體差異:「輸了兩類問題」 |
| 用情緒代替內容:「太扯了」「震驚」 | 情緒是聽眾的反應,不是節目的內容 | 把讓你驚訝的那件事直接寫出來 |
| 承諾大於內容:「看完就會自己實作」 | 一集 30 分鐘的導讀做不到 | 降到真的做得到:「聽完知道它只有四個動作」 |

一句話:**具體勝過強烈。** 數字、專有名詞、真實的矛盾,張力自己會出來。

#### 標題的三個零件

1. **【方括號裡放關鍵字】** —— 論文名或技術名擺最前面。這是聽眾搜尋時
   實際會打的字(`Mem0`、`RAG`、`LoRA`),也是列表被截斷時唯一保證看得到的。
2. **一個懸念,用問號** —— 給缺口,不給結論。陳述句會讓人以為已經知道了。
   懸念必須是這一集真的會回答的問題。
3. **一個具體收穫,帶數字** —— 「只要 4 個動作」。數字讓抽象題目有了尺寸,
   而且暗示了節目的密度。

> **這條規則改過。** 原本寫「論文名放後半」,理由是前幾個字最珍貴。
> 前半句錯了:前幾個字確實最珍貴,但**最該放在那裡的就是論文名** ——
> 那是搜尋時打的字。

除了方括號裡的主關鍵字,標題裡還要有**一個範疇關鍵字**
(ep001 是「AI Agent 長期記憶」)。主關鍵字接住已經知道這篇論文的人,
範疇關鍵字接住只知道自己遇到什麼問題的人 —— 後者多得多。

**不要**退化成「第 5 集:某某論文解讀」:沒有關鍵字、沒有懸念、沒有收穫。

**不要跟部落格標題一模一樣。** 同一個關鍵字要共用,但兩邊的標題各自針對
不同的介面(搜尋結果 vs podcast 列表)。做成同一句只是讓自己跟自己競爭。

#### 截斷比字數重要

`shownotes.py` 會印「列表只看得到」那一行(中文前 25 字、英文前 45 字)。
**看那一行,不要看總字數。** 重點是切掉之後還剩什麼。

**英文要特別小心**:同樣的意思英文約吃三倍字元。ep001 的英文版 132 字元,
「4 Operations」那個收穫落在第 100 字之後,列表裡完全看不到。
英文版通常得把收穫往前挪,或是放棄第三個零件。

#### 摘要(`meta.json` 的 `summary`)

**第一句要能單獨站著。** app 的預覽通常只顯示兩行,而搜尋引擎抓的也是開頭。
所以第一句必須同時做到:含主關鍵字、講出這集的矛盾或缺口。

不要用「這集我們要來聊聊…」開場 —— 那句話零資訊,而它正好佔掉預覽的位置。
ep001 的做法是直接從事實切入:「同一個團隊做了兩個版本,一個簡單、
一個用知識圖譜。」

#### 重點條列(`bullets`,3-5 條)

- **每條開頭放名詞或現象,不要放「我們會討論」。** 掃的人只看前幾個字。
- **每條都是一個可以兌現的承諾**,對應得到某一段。寫不出對應段落就砍掉。
- **可以放一條「這集沒有做什麼」。** 例如「這是導讀,不是實作教學」。
  這種話看起來在扣分,實際上是最強的信任訊號,而且擋掉會失望的聽眾。

#### 章節標題也是 SEO

部分平台會把章節渲染成可點的清單,也會被索引。所以章節標題用**人話 + 關鍵字**,
不要用內部描述。寫法規則在步驟 3 的「chapter 欄位」那節,兩邊要一致。

原文連結由 `brand.py` 依語言組出來:

```
中文  https://datasciocean.com/paper-intro/<article>/
英文  https://datasciocean.com/en/paper-intro/<article>/
```

這支腳本是**發布前的最後一道 gate**,音訊揭露不在就不產出檔案。

## 交付時要告訴使用者

**兩版分開講**:總長、通過率與平均相似度、**哪幾段需要他用耳朵確認以及為什麼**、
實際花費、以及交付檔的路徑(那個 `.m4a`)。

要他在手機上試聽就壓小一點發成 artifact:

```bash
afconvert -f m4af -d aac -b 32000 <in>.wav <out>.m4a
```

30 分鐘的 WAV 約 150 MB,超過 artifact 的 16 MB 上限;32 kbps 單聲道
對語音夠用。**音樂或混音要比較的時候不要用 32k** —— 那個碼率會把差異抹掉,
用 96k 以上,並且把音檔當 artifact 的附帶檔案發,不要塞成 base64。

## 已知還沒做的事

只剩 **Spotify for Creators 帳號**(兩個獨立的 show)與**授權條款快照**,
兩件都不是技術問題,使用者知道,不用主動補。音樂、封面、混音都已定案。

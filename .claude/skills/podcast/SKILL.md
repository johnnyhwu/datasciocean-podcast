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

## 工作模式:預設一路做完

**預設從頭做到尾**,只在兩個時間點停下來說話:
1. **花錢之前**(步驟 6 合成)先講預估成本;
2. **全部做完之後**給一份總結(見最後一節「交付時要告訴使用者」)。

使用者明講「逐步確認」「逐字稿先給我看」時,才切回逐步模式:
每步做完先回報,逐字稿通過 validate 後等他確認才合成。

一路做完不代表可以跳過檢查 —— validate、verify 的 `✗` 與標記照樣要處理。

---

## 步驟 1:讀文章

**先更新部落格,再讀文章**(每一集開工前都要做):

```bash
git submodule update --init --remote blog
```

部落格是本 repo 的 submodule(`blog/`,指向 `johnnyhwu/johnnyhwu.github.io` 的 main,淺層 clone),
這行會拉到遠端最新版。**只有已經推上 GitHub 的文章讀得到** ——
找不到文章時,先問使用者是不是還沒 push,不要去讀別處的本機副本。

文章在 `blog/content/posts/<category>/<slug>/index.zh-tw.md`。
`<category>` 多半是 `paper-intro`,也有 `ai-concept` 等 —— 這個目錄名要填進
`meta.json` 的 `category`,原文連結才組得對。

使用者可能給 slug、標題關鍵字、或整個 URL。找不到就用
`find blog/content -name "*.zh-tw.md" | grep -i <關鍵字>`。

**整篇讀完再動筆。** 特別注意:
- 圖表裡的數字(`{{< image >}}` 的 `alt` 與 `caption` 常含關鍵數據)。
  **稿裡要念出來的關鍵數字,回頭對文章目錄裡的原圖**(表格 png 用 Read 就能看),
  圖說跟圖本身不一定一致
- 作者自己的評論與質疑(這些是 `opinion` / `critique` beat 的素材)
- 論文沒解釋、但你能推論的地方(這是最有價值的內容,但**必須標明是推論**)

### 原文有疑慮的地方:不放進 podcast

你只有部落格原文,沒有論文全文,所以**不要自己去裁決**原文哪裡對、哪裡錯。
遇到**原文自己的矛盾** —— 同一個數字前後不同、圖說跟正文對不上、
結論跟表格對不上、圖與文字不一致 —— 稿裡就**刻意不講那一點**
(只講沒有爭議的部分),避免有疑慮的內容進入節目。

- 作者原文的批評與質疑**不算疑慮**,照常講,那是節目的賣點
- **自己的推測可以講**,但一定要明說「這是我自己的推測」(見 NARRATION.md 第六節)
- 略過了什麼要**記下來**,做完時在總結裡列出,讓使用者決定要不要回頭修部落格。
  不要悄悄拿掉,也不要去改他的部落格

## 步驟 2:讀判準

寫稿前**一定要讀**這個 skill 目錄底下的 `reference/NARRATION.md` 和
`reference/NORMALIZATION.md`(絕對路徑:`.claude/skills/podcast/reference/`)。
要出英文版就再讀 NARRATION.md 的**第十節**(為什麼不能翻譯、門檻換算表)。
寫 show notes(步驟 9)前再讀 `reference/COLD-READ.md`。
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
- **要過新手測試**(見步驟 9):不要出現論文裡的內部名詞(層級名、角色名、技術縮寫),
  除非那個詞已經在標題或摘要裡被白話定義過。章節標題只是標籤,事後修改不影響音訊

### ⚠️ 最容易犯的錯

先寫完內文、事後插入路標,結果路標把下一段的第一句又講了一遍。
**插完路標一定要把相鄰兩段連起來讀一次,修剪重複。**
`validate.py` 只抓字面重複,換句話說的重複要靠自己讀。

## 步驟 4:寫英文版 `episodes/<slug>/en.json`

**骨架沿用、內容重寫。** `id` / `role` / `beat` / `chapter` 跟中文版
一對一對齊(`chapter` 的文字要翻成英文,標記的段落必須相同),
`text` 重寫不翻譯,`style` 換英文骨幹。
為什麼、以及要換掉哪些東西(文化性類比、中文詞義解釋),見 NARRATION.md 第十節。

**英文版的 show notes 同樣適用步驟 9 的新手測試與冷讀**(人設與 prompt 見
`reference/COLD-READ.md`),差別只有:標點用半形、列表只看得到前 45 字、
標題前 45 字要收完第一個子句。英文版的冷讀流程**還沒實測過**,第一次用時要記錄
它跟中文版有什麼差異。

## 步驟 5:驗證結構(兩版都要)

```bash
uv run python pipeline/validate.py episodes/<slug>/zh.json
uv run python pipeline/validate.py episodes/<slug>/en.json
```

語言自動判斷,不用下參數;語速、短 beat、重複判定的門檻會跟著切換。
第一行印的是**依交付速度換算的長度**與**合成成本**(約 US$0.03/分鐘音訊)。

有 `✗` 就必須修到過。`⚠` 是提醒,通常可以放行
(「正文短於提示」那條是已知的,tts.py 會自動降級處理)。

通過後直接進步驟 6(逐步模式才先給使用者看逐字稿)。

## 步驟 6:合成(兩版各跑一次)

```bash
uv run python pipeline/tts.py episodes/<slug>/zh.json out/<slug>/zh \
    --model google/gemini-3.1-flash-tts-preview --voice Zubenelgenubi --pcm
```

- 69 段約需 **30-40 分鐘**,**背景啟動**(`nohup … &` 或 `run_in_background`),
  不要卡住對話。
- **成本:** 輸出音訊長度才是大頭,約 **US$0.03/分鐘音訊**,跟輸入文字多寡無關
  (為什麼見 `reference/GEMINI-TTS.md`)。開跑前先講估計(validate 第一行有),
  並用 `curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"`
  記下**開跑前的 `total_usage`**,合成後再查一次,差額就是實際花費,總結時回報。
  實測:ep003 中文 31 分鐘 US$0.956。
- **進度:每 15 分鐘看一次**,使用者已授權。背景跑
  `sleep 900; ls out/<slug>/<lang>/b*.wav | wc -l; tail -3 out/<slug>/tts_<lang>.log`
  (時間到會喚醒你)。**只用這類唯讀指令**,不要寫輪詢迴圈,也不要為了看進度
  開 `dangerouslyDisableSandbox`。把 log 導到 `out/<slug>/tts_<lang>.log`
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
| 標記「**提示洩漏**」,或 `transcribed` 裡逐字出現風格提示(「請用台灣人的口音說話…」) | **一定是 TTS 把指示唸出來了**,不論位置(ep003 的 `b21` 出在開頭)、不論語速 —— **刪掉該段 wav,加 `--resume` 重跑**(沒有 seed,重跑就是重骰) |
| 結尾冒出無關字詞(幽靈音),但 `chars_per_sec` 在正常區間 | **大機率是 Whisper 自己幻覺出來的,不是 TTS 講錯**——音檔長度跟預期文字量對得上,幾百毫秒塞不下那麼多亂碼字。見 `reference/GEMINI-TTS.md` 第五節。不用急著重骰 |
| 結尾冒出無關字詞(幽靈音),而且 `chars_per_sec` 明顯偏慢或失控 | 這才是音檔真的比預期長,**刪掉該段 wav,加 `--resume` 重跑** |
| 專有名詞唸錯 | 先重骰;連兩次都錯就改 beats.json 的寫法 |
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
uv run python pipeline/stitch.py out/<slug>/zh          # 選用:先聽純人聲,確認節奏
uv run python pipeline/assemble.py out/<slug>/zh \
  --intro music/intro.wav --outro music/outro.wav --sting music/sting.wav
```

一行指令做完:混音、正規化、`MIX.json`、`.wav`、128k AAC 的 `.m4a`
(用內建的 `afconvert`,不需要再手動轉檔)。

**交付速度由 `brand.py` 的 `SHIP_RATE` 決定,中英各有預設,目前都是 1.0。**
單集要不同就在 `meta.json` 加 `"ship_rate": 0.9`(或 `{"zh": 0.9}`);
`assemble.py`、`shownotes.py`、`validate.py` 都從同一處取值,**不要自己帶 `--rate`**
—— 帶了非交付速度的值只會產出試聽檔,不會寫 `MIX.json`。
舊集數(ep001、ep002)的 `meta.json` 記著 `ship_rate: 1.1`。

**加速必須在混音之前**(速度不是 1.0 時才相關)。`--rate` 只拉伸人聲、停頓按比例縮短,
音樂維持原速。WSOLA 靠找相似波形重疊接起來,拉伸語音很乾淨,拉伸音樂會打散
週期性,產生顆粒感。對混完的成品加速就是把音樂一起毀掉。

輸出 44.1 kHz 單聲道、**-19 LUFS**、true peak ≤ **-1 dBTP**,所以**不需要再跑
master.py**;要單獨量用 `master.py <檔> --measure`。留那 1 dB 是因為取樣點之間的波形更高,
AAC 編碼會把它推上來,實測吃掉 0.2-0.4 dB。

**兩版都要跑。** 兩版的原始響度不一樣(ep001:中文 -15.4、英文 -16.9),
不正規化的話聽眾切換版本會感覺到音量跳動。英文版有時會停在 -19.05 而不是
剛好 -19.00 —— 峰值天花板先到了,**保峰值優先,不要為此調高目標**。

**轉場次數是算出來的,不要手填。** 約每 9 分鐘一次、下限 2 上限 5,
由整集長度決定(31 分 → 3 次)。放哪幾個章節點是枚舉組合、取
「最長一段沒有標點的區間」最短的那一組。要覆寫才用 `--stings <n>`。

產出(都在 `out/<slug>/<lang>/`):

| 檔案 | 用途 |
|---|---|
| `<slug>-<lang>.m4a` | **上傳用** |
| `<slug>-<lang>.wav` | 交付母帶,無損,**給使用者在編輯器裡試聽** |
| `MIX.json` | 時間戳,show notes 讀它 |
| `FULL_EPISODE.wav` | 純人聲(stitch.py),只用來試聽節奏 |
| `FULL_EPISODE_mixed_x<倍率>.wav` | 只有手動帶了非交付速度的 `--rate` 才有,試聽用,**不交付** |

**判準是檔名等於 `<slug>-<lang>`。** 其他都不是成品。

### 已知現象:Gemini 的輸出本來就觸頂

TTS 回傳的 PCM16 有極少量樣本頂在滿刻度(ep001:佔 0.007%)。這是來源就有的,
聽不出來,正規化是往下降不會惡化,**不用為此重錄**。

## 步驟 9:show notes(兩版都要)

先寫 `episodes/<slug>/meta.json`:

```json
{
  "number": 3,
  "article": "wikiskill",
  "category": "paper-intro",
  "ship_rate": 1.0,
  "zh": { "title": "…", "summary": "…", "bullets": ["…", "…", "…"] },
  "en": { "title": "…", "summary": "…", "bullets": ["…", "…", "…"] }
}
```

- `number`、`article`、要出的語言那一份 `title/summary/bullets` 是必要的。
  **只出單一語言時,另一個語言的區塊可以省略**(`shownotes.py` 只讀要出的那個)。
- `article` 是部落格文章的目錄名,用來組原文連結,**不是 slug** ——
  `ep001-mem0` 的 `article` 是 `mem0`。`number` 只印出來給上架時填,要跟 slug 的編號一致。
- `category` 是文章在部落格的上層目錄(`paper-intro`、`ai-concept`…),
  省略時當作 `paper-intro`。
- `ship_rate` 選填,省略就用 `brand.py` 的預設(見步驟 8)。

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

#### 第二道關卡:新手測試

上面那條判準管的是**不說謊**。另一道獨立的關卡管**聽不聽得懂**:

> 標題、摘要、重點、章節標題,每一處都要能被「會用 ChatGPT、沒讀過論文、沒做過
> 相關開發」的人讀懂。判準不是詞彙難不難,而是**這句話有沒有假設聽眾已經知道某件事**。

兩道都要過。ep003 的舊標題通過了第一道(每個鉤子都說得出分鐘數),卻完全沒過第二道:
「Agent Skill 自動演化多一層 wiki」每個詞都是黑話,「最想證明的那件事」是空的指涉。
**這道關卡用冷讀驗證,不要靠自己判斷** —— 作者讀自己的稿子永遠覺得看得懂。
流程、上限與 prompt 範本在 `reference/COLD-READ.md`,**預設要跑**。

#### 標題的寫法

1. **【名稱】放頭端。** 論文名或技術名放在最前面的方括號,這是聽眾搜尋時實際會打的字
   (`Mem0`、`RAG`、`WikiSkill`),也是節目的品牌慣例。括號裡**只放名稱**,
   不加「論文」「解析」之類的字 —— ep003 冷讀時,讀者點名「論文」讓人覺得艱深。
2. **接一個聽眾自己會問的問題,用白話。** 例如「AI 老是重複犯錯?」,而不是論文
   裡的說法。懸念必須是這一集真的會回答的問題。
3. **不要把反轉放進標題。** 「給錯人反而變差」這類半句,沒有鋪墊就是謎語,ep003 的
   讀者全看不懂。反轉放摘要。
4. **數字要帶基準,否則拿掉。** 「進步 15 個百分點」沒說從哪到哪,讀者反而覺得不厲害。
   標題塞不下基準就不放數字,放到摘要。
5. **不要用論文裡的角色名或內部名詞**(「改手冊的人」「三層架構」)。

**一個取捨,要知道:** 名稱放頭端,對不認識它的新聽眾是一道門檻。ep003 冷讀時,
點名這個前綴的讀者有 4 位,而且他們都建議挪到後面或換成通用說法。使用者選了放頭端
(搜尋與品牌優先),所以補救放在別處:**摘要的前兩句必須說清楚這個名稱是什麼**,
而且名稱後面立刻接白話問題,不接另一個術語。

除了名稱,標題或摘要第一段要有**一個範疇關鍵字**(ep001 的「AI Agent 長期記憶」)。
名稱接住已經知道這篇論文的人,範疇關鍵字接住只知道自己遇到什麼問題的人,後者多得多。

**不要**退化成「第 5 集:某某論文解讀」。**不要跟部落格標題一模一樣**:兩邊針對不同的
介面(搜尋結果 vs podcast 列表),做成同一句只是讓自己跟自己競爭。

#### 截斷比字數重要

`shownotes.py` 會印「列表只看得到」那一行(中文前 25 字、英文前 45 字)。
**看那一行,不要看總字數。** 把開頭的【名稱】略過之後,**第一個子句要在這個範圍內收尾**,
否則聽眾在列表上看到的是半句話(腳本會提醒)。

**英文要特別小心**:同樣的意思英文約吃三倍字元。ep001 的英文版 132 字元,
「4 Operations」那個收穫落在第 100 字之後,列表裡完全看不到。
英文版通常得把收穫往前挪,或是放棄第三個零件。

#### 摘要(`meta.json` 的 `summary`)

依序寫,每一步都要讓沒背景的人跟得上:

1. **第一句講現象或疑問,白話,而且能單獨站著。** app 的預覽通常只顯示兩行,
   搜尋引擎抓的也是開頭。**不要用論文術語開場**,也不要用「這集我們要來聊聊…」
   —— 那句零資訊,卻佔掉預覽的位置。
2. **第二、三句把答案講出來,不要吊胃口。** 標題問「有用嗎」,摘要就要答,
   而且要講到「有什麼前提」。吊胃口的前提(「有個前提」但不說是什麼)讀者只覺得被耍。
   **同時說清楚標題裡的【名稱】是什麼。**
3. **用一句話定義這集用到的最少術語。** 專有名詞第一次出現就補白話,
   (論文裡叫 skill)這種括號夠用。
4. **校正期待。** 明講這集不是什麼 —— 讀者很容易把「AI 老是犯錯」讀成
   「教我怎麼讓自己的 ChatGPT 少犯錯」。
5. **最後一句交代先備知識**:需不需要讀過論文、需不需要會寫程式。

數字要帶基準與範圍(「平均答對率從 48.7%(沒有筆記時)升到 63.7%」)。
**列範圍就列全**:「數學、試算表、問答等四類」讀者會數,數出三類就失去信任 ——
四類就把四類寫出來,不要用「等」。

#### 重點條列(`bullets`,3-5 條)

- **每條開頭放現象或問題,不要放「我們會討論」,也不要放名詞。** 掃的人只看前幾個字。
- **每條都是一個可以兌現的承諾**,對應得到某一段。寫不出對應段落就砍掉。
- **一條裡不要同時出現兩個以上沒解釋的新詞。** 內部術語(角色名、層級名)不進重點,
  除非同一條前面已經定義。
- **最後一條放「這集沒有做什麼」**,例如「不是教你怎麼叫 ChatGPT 記筆記,也不是實作教學」。
  這種話看起來在扣分,實際上是最強的信任訊號,而且擋掉會失望的聽眾。

#### 章節標題也是 SEO,也要過新手測試

部分平台會把章節渲染成可點的清單,也會被索引。章節標題用**人話**,
**不要出現論文裡的內部名詞**(wiki、skill、三層架構、呼叫次數)。
寫法規則在步驟 3 的「chapter 欄位」那節。章節標題**要一起放進冷讀的完整頁測試**。

#### 標點

- **中文 show notes 一律全形標點:`，。？！：；（）`。** 時間戳(`2:14`)、小數點(`48.7%`)、
  網址不在此限。我寫中文時習慣用半形標點,所以 `shownotes.py` 會在中文旁邊出現半形
  `,?!:;()` 時提醒。
- **英文 show notes 用半形標點**,出現全形標點同樣會提醒。
- **逐字稿(`zh.json` 的 `text`)不在這條規則內**,它是念給 TTS 的稿,不要為了標點去改它
  —— 改了就得重新合成。`chapter` 欄位只是標籤,不會被念出來,可以安全修改。

原文連結由 `brand.py` 依語言組出來:

```
中文  https://datasciocean.com/<category>/<article>/
英文  https://datasciocean.com/en/<category>/<article>/
```

這支腳本是**發布前的最後一道 gate**,音訊揭露不在就不產出檔案。

## 步驟 10:收尾 —— 清乾淨,再講哪個是成品

做完把**自己產生的實驗與暫存檔刪掉**,讓 repo 乾淨:

- 包裝腳本、一次性測試腳本、`credits_before.json`、`tts_*.log` 之類
- 重複的母帶(例如與 `<slug>-<lang>.wav` 內容相同的檔)
- `.DS_Store`(根目錄的 `.gitignore` 已排除,但有就刪)

**不要刪:** `out/<slug>/<lang>/b*.wav`(單段重骰要用)、`report.json`、`MIX.json`、
`SHOWNOTES.md`,以及別人的集數與檔案。刪之前先 `ls` 看過每一個目標。
最後 `git status` 應該只剩這一集該 commit 的東西(`episodes/<slug>/` 與有意修改的程式與文件)。
**commit 要等使用者確認。**

## 交付時要告訴使用者

總結用中文,**兩版分開講**:
- **最終交付檔是哪一個**:`.m4a`(上傳用)與 `.wav`(試聽用)的完整路徑、總長、響度
- 合成通過率與平均相似度,**哪幾段需要他用耳朵確認以及為什麼**
- **實際花費**(合成前後 credits 的差額)
- **略過了什麼**:原文的疑慮與你因此沒講的地方(見步驟 1)
- 過程中遇到的問題,以及 skill / CLAUDE.md 可以怎麼改進

要他在手機上試聽就壓小一點發成 artifact:

```bash
afconvert -f m4af -d aac -b 32000 <in>.wav <out>.m4a
```

30 分鐘的 WAV 約 150 MB,超過 artifact 的 16 MB 上限;32 kbps 單聲道
對語音夠用。**音樂或混音要比較的時候不要用 32k** —— 那個碼率會把差異抹掉,
用 96k 以上,並且把音檔當 artifact 的附帶檔案發,不要塞成 base64。

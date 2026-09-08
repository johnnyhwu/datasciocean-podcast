---
name: podcast
description: 把 Johnny 部落格的一篇技術文章做成完整的 podcast,中文版與英文版各一集。使用者說「我想把 XXX 文章轉成 podcast」「做一集 XXX」「做個英文版」時使用。涵蓋讀文章、寫 beats.json 逐字稿、Gemini TTS 合成、Whisper 驗證、拼接、輸出加速版本。
---

# 製作一集 podcast

**預設出中英兩版。** 使用者只講文章、沒指定語言時,就是兩版都要,
而且**兩版都要跑完整的 validate 與 verify** —— 不要只驗中文那版。
使用者若只要其中一版,他會明講。

一集用一個 slug(例如 `ep003-mem0`):

```
episodes/<slug>/zh.json   episodes/<slug>/en.json
out/<slug>/zh/            out/<slug>/en/
```

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

寫稿前**一定要讀** `reference/NARRATION.md` 和 `reference/NORMALIZATION.md`。
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

### 開場必備

`hook`(不劇透)→ `identity`(含 AI 揭露)→ `promise`(聽完會學到什麼)
→ 路線圖(`signpost`)。細節看 NARRATION.md。

### ⚠️ 最容易犯的錯

先寫完內文、事後插入路標,結果路標把下一段的第一句又講了一遍。
**插完路標一定要把相鄰兩段連起來讀一次,修剪重複。**
`validate.py` 只抓字面重複,換句話說的重複要靠自己讀。

## 步驟 4:寫英文版 `episodes/<slug>/en.json`

**骨架沿用、內容重寫。** `id` / `role` / `beat` 跟中文版一對一對齊,
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
| 語速超出區間(中文 4.0-9.5,英文 11.0-20.0 字元/秒) | 請使用者用耳朵確認,刻意留白的金句可以慢 |

改了 `verify.py` 的正規化規則之後,用
`uv run python pipeline/rescore.py <out_dir> --write` 重算,不要重跑 STT;
並且**順手 rescore 另一個語言那版**,確認新規則沒把它弄壞。

## 步驟 8:拼接與輸出(兩版都要)

```bash
uv run python pipeline/stitch.py out/<slug>/zh
uv run python pipeline/speedup.py out/<slug>/zh/FULL_EPISODE.wav 1.1 1.2 1.3 1.4 1.5
```

產出:
- `FULL_EPISODE.wav` —— 原速
- `FULL_EPISODE_x1.1` ~ `x1.5` —— 五個加速版本(WSOLA,音高不變)
- `TIMELINE.md` —— 時間軸,可跳段
- `report.json` —— 每段的驗證結果

## 交付時要告訴使用者

**兩版分開講**:總長與各加速版本長度、通過率與平均相似度、
**哪幾段需要他用耳朵確認以及為什麼**、實際花費。

想在手機上試聽,可以壓成 AAC 再發成 artifact:
`afconvert -f m4af -d aac -b 32000 <in>.wav <out>.m4a`
(原始 WAV 約 67 MB,超過 artifact 的 16 MB 上限;
32 kbps 單聲道對語音夠用,壓完約 5.6 MB)。

## 已知還沒做的事

片頭片尾音效、BGM、封面、RSS 發布、show notes。
規劃在 `docs/plan.md` 第六、七、九章。使用者知道,不用主動補。

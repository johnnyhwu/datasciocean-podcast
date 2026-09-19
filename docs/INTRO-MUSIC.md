# 片頭曲:生成紀錄

用 ACE-Step 1.5 在本機生成,**授權 MIT**(GitHub LICENSE `Copyright (c) 2026 ACEStep`,
HF 模型卡 `license: mit`,查證日 2026-09-09)。MIT 沒有營收上限、沒有地區限制、
產出不需標示歸屬,是 `docs/MUSIC-GENERATION-RESEARCH.md` 裡授權最乾淨的一個。

**環境是一次性的,選定後整包刪除**(`~/.cache/acestep-trial/`,含 venv、權重、
HF 快取)。所以這份紀錄是唯一的重現依據 —— 同樣的 caption + seed 可以重生。
podcast repo 自己的 venv 沒有被裝進 torch。

生成參數(十首共用):

| | |
|---|---|
| 模型 | `acestep-v15-turbo` + `acestep-5Hz-lm-1.7B` |
| 後端 | DiT 走 MPS,LM 走 MLX(Apple Silicon 原生) |
| duration | 15 秒(下限是 10;生 15 秒讓旋律有完整起落,之後裁成 8-12 秒) |
| inference_steps / shift | 8 / 3.0(turbo 的建議值) |
| instrumental | True,lyrics = `[Instrumental]` |
| 耗時 | 每首約 35 秒(M5 24GB) |

負面提示:

```
vocals, singing, choir, epic cinematic trailer, orchestral swell,
aggressive drums, distorted guitar, fade-out ending
```

骨幹句(接在每個 caption 前面):

```
Intro sting for a technology podcast. Instrumental only.
Ends on a clean resolved note.
```

方向依 `plan.md` 附錄 B 的 A / B / C 展開,另加兩個混血與一個極簡 logo sting。
其中 **07 是針對附錄 B 自己指出的風險**(方向 C「可能過慢過柔,開場缺乏推進感」)
加上穩定脈動的版本。

## 十首候選

| # | 方向 | BPM | 調 | seed | 原始 LUFS | 特徵 |
|---|---|---|---|---|---|---|
| 01 | A 好奇心 | 108 | C Major | 1001 | -16.1 | Curious and playful electronic, warm analog synth arpeggio, … |
| 02 | A 好奇心 | 116 | D Major | 1002 | -14.7 | Quirky and bright, plucked synth motif, bouncy but restraine… |
| 03 | A 好奇心 | 120 | A Minor | 1003 | -18.5 | Minimal IDM, crisp glitch percussion, an arpeggio that unfol… |
| 04 | B 溫暖 | 88 | F Major | 1004 | -15.9 | Warm lo-fi electronic, acoustic guitar plucks, soft Rhodes p… |
| 05 | B 溫暖 | 92 | Bb Major | 1005 | -15.0 | Warm and thoughtful, vibraphone melody, soft upright bass, b… |
| 06 | C 海洋 | 80 | D Major | 1006 | -14.4 | Ambient electronic with depth and space, soft synth pads, a … |
| 07 | C 海洋 | 100 | E Major | 1007 | -15.1 | Ambient electronic with a steady gentle pulse underneath, de… |
| 08 | 混血 A+C | 104 | G Major | 1008 | -20.4 | Bright marimba arpeggio riding over a deep ambient pad, a fe… |
| 09 | 混血 A+B | 96 | C Major | 1009 | -12.9 | Lo-fi keys with a repeating arpeggio motif, tape warmth, sof… |
| 10 | 極簡 | 90 | C Major | 1010 | -14.0 | Extremely minimal logo sting. One memorable four-note motif … |

完整 caption 在 `out/brand/intro-candidates/GENERATION-LOG.json`(gitignore,
環境刪掉前會複製一份到這裡)。

## 試聽時做了什麼

原始輸出的響度差了將近 **9 dB**(-12.9 到 -20.4 LUFS)。A/B 比較時大聲的
無條件聽起來比較好,所以試聽前用 `pipeline/master.py` 全部推到 -19 LUFS。
唯一例外是 **08**,它動態太大,推到 -19 會讓 true peak 超標,停在 -20.5。

為此把 `master.py` 的響度量測改成支援立體聲 —— BS.1770 對 L/R 的通道加權
都是 1.0,是**兩聲道功率相加**,不是先降混再量(降混會讓左右不同的素材
互相抵消)。單聲道路徑不變,ep003 的母帶重量仍是 -19.00。

## 選定之後要做的事

1. 裁成 8-12 秒,結尾加淡出
2. 用同一個 seed 生變體微調
3. 混音:片頭音樂淡出時與人聲重疊 1-2 秒(音樂降到約 -30 dB 當背景)
4. **對混完的成品重跑一次 `master.py`** —— 加了音樂之後整體響度會變
5. `rm -rf ~/.cache/acestep-trial`

## 一個著作權上的注意事項

美國著作權局 2025-01-29 的報告結論是「完全由 AI 生成的作品不可著作權登記,
單純選擇 prompt 不構成人類創作」。這**不影響你使用**這段音樂,但可能影響你
主張「別人不得抄襲你的片頭」。裁切、混音、加層這些人為編輯會增加人類創作
成分 —— 我們本來就要做第 1、3 步,順便解決了一部分。

---

# 第二輪:盲測

第一輪 Johnny 選了 **04 / 06 / 09 / 10**。四首裡有三首帶「重複的短動機」,
偏好是溫暖、有明確動機、不吵。

他自己說「音樂不是我的領域,很難用描述的說我喜歡什麼」—— 所以第二輪改成
**盲測**,並且把變化設計成**一次只動一個變數**,讓選出來的結果自己指出答案:

| 軸 | 動什麼 | 想知道什麼 |
|---|---|---|
| 重骰 | 只換 seed,caption / bpm / key 完全不動 | 同一個描述的隨機幅度有多大 |
| 速度調性 | 只動 bpm 與 keyscale,seed 沿用 | 快一點 / 亮一點是不是比較好 |
| 配器 | 只換樂器詞,seed 沿用 | 喜歡的是音色還是旋律 |
| 情緒 | 只換情緒詞,seed 沿用 | 溫暖 vs 明亮 vs 深沉 |

四個基礎 × 四個變體 = 16,加上原本那四首當對照 = 20 首。
順序用固定亂數種子 `20260910` 打亂,可重現。

## 盲測編號對照

| 盲測 | 來源 | 基礎 | 軸 | BPM | 調 | seed |
|---|---|---|---|---|---|---|
| 01 | A3-instr | 04 | 配器 | 88 | F Major | 1004 |
| 02 | B3-instr | 06 | 配器 | 80 | D Major | 1006 |
| 03 | C3-instr | 09 | 配器 | 96 | C Major | 1009 |
| 04 | A4-mood | 04 | 情緒 | 82 | F Major | 1004 |
| 05 | D4-mood | 10 | 情緒 | 86 | D Major | 1010 |
| 06 | C1-reroll | 09 | 重骰 | 96 | C Major | 2091 |
| 07 | C2-tempo | 09 | 速度調性 | 104 | D Major | 1009 |
| 08 | D3-instr | 10 | 配器 | 90 | C Major | 1010 |
| 09 | D2-tempo | 10 | 速度調性 | 100 | G Major | 1010 |
| 10 | 06-ocean-bell | 06 | 原始 | 80 | D Major | 1006 |
| 11 | 04-lofi-rhodes | 04 | 原始 | 88 | F Major | 1004 |
| 12 | A1-reroll | 04 | 重骰 | 88 | F Major | 2041 |
| 13 | B2-tempo | 06 | 速度調性 | 92 | A Major | 1006 |
| 14 | D1-reroll | 10 | 重骰 | 90 | C Major | 2101 |
| 15 | C4-mood | 09 | 情緒 | 96 | C Major | 1009 |
| 16 | B4-mood | 06 | 情緒 | 80 | D Major | 1006 |
| 17 | A2-tempo | 04 | 速度調性 | 96 | G Major | 1004 |
| 18 | 09-lofi-arp | 09 | 原始 | 96 | C Major | 1009 |
| 19 | B1-reroll | 06 | 重骰 | 80 | D Major | 2061 |
| 20 | 10-four-note-logo | 10 | 原始 | 90 | C Major | 1010 |

## 已知的兩個瑕疵(不影響盲測)

- **19(B1-reroll)只有 4.3 秒。** 不是被裁壞,它本身就是一段很短的 sting,收得乾淨。
- **12(A1-reroll)結尾被硬切在 15 秒**,尾端峰值還有整體的 25%,沒有收乾淨。

兩者都能重生解決,所以留在盲測裡,並請 Johnny **只判斷旋律與音色**,
不要因為長度或結尾排除掉好的旋律。

二十首一樣全部推到 **-19 LUFS**,響度不構成偏誤。

---

# 第二輪的結論

Johnny 從 20 首留下 9 首。把 caption 的詞跟取捨對起來數:

| 詞 | 留 | 汰 |
|---|---|---|
| Rhodes | **5** | 0 |
| guitar | **4** | 0 |
| vibraphone / celesta / marimba | 3 | 1 |
| **synth bell** | 0 | **3** |
| bell(全部) | 1 | **7** |
| **soft dusty beat** | 0 | **4** |
| arpeggio | 1 | 4 |

**判準是「樂器有沒有音頭」,不是旋律動機。** 留下的是敲擊/撥弦的真實樂器
(Rhodes、吉他、鐵琴、鋼片琴、馬林巴),淘汰的是持續音的合成器
(pad、synth bell、氛圍質地)。

佐證:09 那組唯一活下來的 C4,就是把 `soft dusty beat` 換成 `clean` +
`gentle pulse` 的那一個;同組 C3 加了馬林巴卻仍被淘汰,因為它留著 dusty beat。

**這推翻了第一輪的推測。** 當時看他選的四首有三首帶重複動機,推測他喜歡動機
—— 但 `arpeggio` 是留 1 汰 4。還好變體是一次只動一個變數,錯的假設沒污染結果。

另一個發現:**06 / 09 / 10 的原始版本(第一輪他親自挑的)這次全被淘汰**,
只有 04 撐住。第一輪是在比五個差很遠的方向,第二輪是在比二十個接近的東西,
參照點不同。結論:**只有 04 是禁得起盲測的偏好。**

base 04 拿了 5/5,代表「留/汰」對這個家族已經沒有鑑別力,第三輪改用兩兩對決。

# 第三輪:對決 + 長度實驗

12 首,順序用種子 `20260910` 打亂,一樣全部 -19 LUFS。

**負面提示加了 `synth bell` 與 `drum kit`**(第二輪證實這兩類全滅),
生成長度從 15 降到 14 留餘裕 —— 第二輪那個「結尾被硬切」的問題沒有重現,
12 首尾端殘留都只有 0.1%。

## 長度:ACE-Step 的 duration 下限是 10 秒

生不出 6 秒。做法是 `duration=10` 加上 prompt 明講
「Six-second logo sting… state the motif once and resolve immediately, then stop」,
讓它自己提早解決,再裁掉尾端靜音。**有效**:四首短版長出 6.5 / 9.5 / 6.6 / 8.2 秒,
三首落在 6-8 秒。長版平均 11.9 秒。

短版刻意做成長版的**同內容同 seed**,所以對決結果能直接分離出「長度」這個變數。

| 名稱 | 家族 | 長短 | 生成 | 實際 | BPM | 調 | seed |
|---|---|---|---|---|---|---|---|
| E1-rhodes-clean | 04 領地 | 長 | 14.0s | 12.1s | 88 | F Major | 3001 |
| E2-rhodes-vibes | 04 領地 | 長 | 14.0s | 13.7s | 88 | F Major | 3002 |
| E3-rhodes-celesta | 04 領地 | 長 | 14.0s | 11.9s | 90 | F Major | 3003 |
| E4-rhodes-marimba | 04 領地 | 長 | 14.0s | 11.4s | 92 | G Major | 3004 |
| F1-musicbox | 新基底 | 長 | 14.0s | 12.2s | 84 | C Major | 3011 |
| F2-nylon-felt | 新基底 | 長 | 14.0s | 11.1s | 86 | D Major | 3012 |
| F3-pizz-harp | 新基底 | 長 | 14.0s | 12.2s | 96 | G Major | 3013 |
| F4-muted-wurli | 新基底 | 長 | 14.0s | 10.6s | 100 | C Major | 3014 |
| S1-rhodes-clean | 04 領地 | 短 | 10.0s | 6.5s | 88 | F Major | 3001 |
| S2-rhodes-vibes | 04 領地 | 短 | 10.0s | 9.5s | 88 | F Major | 3002 |
| S3-musicbox | 新基底 | 短 | 10.0s | 6.6s | 84 | C Major | 3011 |
| S4-pizz-harp | 新基底 | 短 | 10.0s | 8.2s | 96 | G Major | 3013 |

---

# 第三輪的結論

Johnny 的前六名:

| 名次 | | 家族 | 長短 |
|---|---|---|---|
| 1 | E2-rhodes-vibes | 04 領地 | 長 |
| 2 | E4-rhodes-marimba | 04 領地 | 長 |
| 3 | F2-nylon-felt | 新基底 | 長 |
| 4 | S1-rhodes-clean | 04 領地 | **短** |
| 5 | E1-rhodes-clean | 04 領地 | 長 |
| 6 | E3-rhodes-celesta | 04 領地 | 長 |

## 判準要再修正一次:不是「有沒有音頭」,是「暖還是亮」

第二輪的結論是「要有音頭的真實樂器」。但第三輪的音樂盒與撥奏弦樂+豎琴
**都極有音頭,卻都沒進前六**。真正的軸是三個槌擊樂器的排名:

| 樂器 | 質地 | 名次 |
|---|---|---|
| 鐵琴 vibraphone | 最暖、木質、柔 | **1** |
| 馬林巴 marimba | 中間 | **2** |
| 鋼片琴 celesta | 最亮、玻璃質、金屬 | **6** |

**由暖到亮,名次由高到低。** 同理,唯一擠進前六的新基底 F2(尼龍弦吉他 +
氈化直立鋼琴)是溫暖中低音域近距離房間感;落榜的音樂盒、撥奏弦樂、豎琴
全是明亮纖細高音域。

=> **音頭是必要條件,真正的軸是「溫暖 / 中低音域 / 木質」對「明亮 / 高音域 / 玻璃質」。**

## 長度:兩對打平,所以長度不是決定因素

同內容同 seed 的兩對:

| seed | 長版 | 短版 | 誰贏 |
|---|---|---|---|
| 3001 | E1 #5 | S1 **#4** | 短 |
| 3002 | E2 **#1** | S2 未進前六 | 長 |

一比一。**內容才是決定因素,長度可以純粹依製作需求決定**
(`plan.md` 6.1 建議 8-12 秒),不必為了討好耳朵而妥協。

# 第四輪:決選

配方固定為 E2:`Soft Rhodes piano with light vibraphone accents, tape warmth,
gentle and unhurried, warm and friendly, no percussion.`,88 BPM,F 大調。

負面提示新增 `celesta` / `music box` / `glassy bright bell`,把「明亮玻璃質」
那一側直接擋掉。

**這是重骰終於有意義的時候。** 第二輪證明重骰救不了弱基底(0/3),
但 E2 是強基底,現在要找的是同配方裡最好的那次運氣。
四個純重骰 + 四個微調(把第 2、3 名的元素混進第 1 名),
**加上原本的 E2 當對照** —— 沒有對照就分不出新的有沒有真的比較好。

| 名稱 | 類型 | 改了什麼 | BPM | 調 | seed | 秒 |
|---|---|---|---|---|---|---|
| G1-take | 新 | 純重骰 | 88 | F Major | 4001 | 11.5 |
| G2-take | 新 | 純重骰 | 88 | F Major | 4002 | 11.2 |
| G3-take | 新 | 純重骰 | 88 | F Major | 4003 | 11.3 |
| G4-take | 新 | 純重骰 | 88 | F Major | 4005 | 14.0 |
| G5-vibes-marimba | 新 | 加馬林巴 | 88 | F Major | 3002 | 11.5 |
| G6-room | 新 | 換成 F2 的房間感 | 88 | F Major | 3002 | 11.1 |
| G7-nylon | 新 | 加尼龍弦吉他 | 88 | F Major | 3002 | 12.6 |
| G8-slower | 新 | 放慢到 84 | 84 | F Major | 3002 | 11.6 |
| E2-control | 對照 | —(第三輪冠軍) | 88 | F Major | 3002 | 13.7 |

`G4-take` 原本的 seed 4004 被硬切在 14 秒(尾端殘留 54.8%),換 seed 4005 重生。
瑕疵不是好壞問題,放進盲測會被冤枉淘汰。

---

# 診斷輪:`use_cot_caption` 這個預設值

第三輪之後 Johnny 反映「有些音質沒有很好,有些旋律有點混亂」。
查日誌發現一件影響很大的事。

## 發現:LM 會把 caption 整個改寫掉

`use_cot_caption` **預設是 True**,5Hz LM 會用 CoT 重寫使用者的 caption
再餵給 DiT。實際送出:

> Soft Rhodes piano with light vibraphone accents, tape warmth, gentle and
> unhurried, warm and friendly, **no percussion**.

LM 改寫成(日誌原文):

> A **chillhop** instrumental with a relaxed **neo-soul groove** … jazzy
> **electric guitar** chords shimmering over **atmospheric pads** before settling
> into a steady **boom-bap drum machine beat** and a smooth melodic **bassline** …
> **two guitars**, one chordal stabs while another weaving lead melodies …
> A brief **breakdown section** … before **rebuilding momentum**.

Rhodes 不見、鐵琴不見、`no percussion` 變成 boom-bap 鼓機,
負面提示裡的 `drum kit` 也沒攔住。bpm 與調性有被遵守(88、F Major 照抄)。

**所以第一到第三輪的 prompt 層級歸因全部不可信。** Johnny 的排名是真的
(他聽的是真實音檔),但「鐵琴 > 馬林巴 > 鋼片琴,由暖到亮」那個解釋站不住 ——
caption 既然被換掉,那個順序更可能是 seed 的運氣。E2/E4/E3 的 seed 也不同。

## 但關掉它讓結果變糟 —— 這是反直覺的部分

六段同 seed(3002)同 prompt、只改生成設定的盲測排名:

| 名次 | | DiT | LM 改寫 |
|---|---|---|---|
| 1 | R0(= 第三輪的 E2) | 2B | **開** |
| 2 | Q3 | XL | 關 |
| 3 | Q4(+ 改寫過的 prompt) | XL | 關 |
| 4 | P2 | XL | 開 |
| 5 | Q2 | 2B | 不用 LM |
| 6 | Q1 | 2B | **關** |

- **R0 兩度奪冠**(第三輪 12 首、診斷輪 6 段,兩次都第一)。偏好可重現。
- **最後兩名都是拿掉 LM 的 2B。** 關掉改寫在 2B 上是災難。
- 三段 XL 都在前四,但都沒贏過 R0。

**結論:改寫不是元兇,它在幫忙。** 我們的 caption 太短太乾,而 DiT 訓練時
吃的是完整編曲描述;LM 的膨脹反而更接近它熟悉的輸入。改寫的代價是
**失去樂器控制權**,換到的是**音樂性**。

**所以不要關掉 `use_cot_caption`。** 正確做法是**用 LM 自己的文體寫 caption**
—— 長篇、點名主奏樂器與其角色、點名伴奏樂器與其角色、描述編曲隨時間的形狀、
最後講情緒。這樣改寫趨近恆等變換,控制權與音樂性都拿得到。

## 兩個被推翻的中間結論(留著避免重犯)

1. **「該換成 `acestep-v15-sft` 提高音質」是錯的。** Best Practices 那段說
   「用 base 模型提品質」,但 Model Zoo 的逐模型評級表寫 turbo 是 **Very High**、
   sft 是 High、base 是 Medium。**評級表才是權威**,換過去會更差。
2. **「關掉改寫讓頻寬變滿 = 音質變好」是量測假影。** 用峰值 1e-4 當截止門檻
   量到 24 kHz(Nyquist),但 20-24 kHz 的能量全在 **-65 dB 以下,聽不到**,
   且與音樂起伏相關性低 —— 那是底噪延伸。真正聽得到的 16-20 kHz 反而是
   R0 最高(-40 dB,比其他高 11 dB)。**頻譜量不出音質,只能靠耳朵。**

## 順帶確認的事

- **AAC 128k 不是音質瓶頸。** 解回 WAV 比對:高頻只掉 0.64 dB、截止 17.6k
  vs 原始 18.5k、整段誤差 -30.5 dB。之後試聽仍改用 256k,把這個變數移掉。
- **`acestep-5Hz-lm-4B` 指定了卻不會自動下載也不報錯**,會悄悄沿用已存在的
  1.7B。要用它必須先確認 `checkpoints/` 底下真的有那個目錄。
- 生成耗時:2B 不用 LM **14 秒**、2B 開 LM 84 秒、XL 約 170-390 秒。

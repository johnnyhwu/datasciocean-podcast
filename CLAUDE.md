# DataSci Ocean Podcast

把 Johnny 的中文技術部落格文章,做成 20-40 分鐘的單人旁白 podcast。
**每篇文章出兩集:中文版給華人聽眾,英文版給外國聽眾。**

**要做一集時,直接呼叫 `podcast` skill** —— 完整步驟、指令與判準都在那裡,
這份文件只講「整個專案長什麼樣、哪些事不能做」。

## 一句話流程

文章 → beats.json(結構化逐字稿)→ `validate` 擋錯 → Gemini TTS 逐段合成 →
Whisper 回轉驗證 → 拼接加停頓 → (需要時)人聲變速 → 混入片頭/轉場/片尾 +
響度正規化 → show notes。中英兩版各走一次,**兩版都要驗證**。

## 環境

- **絕不弄髒系統。** 一律 `uv run`,套件記在 `pyproject.toml`,
  Python 版本由 `.python-version` 指定。**不要 `pip install`。**
- **部落格原文一律讀 `blog/`(submodule),開工前先 `git submodule update --init --remote blog`。**
  不要去讀 `~/Desktop` 上別處的本機副本 —— 那份可能比遠端新或舊,
  而 podcast 的原文連結指向的是已發布的版本。
- **不要引入系統依賴。** 這個專案刻意沒有 ffmpeg / sox / rubberband / pydub。
  響度、變速、混音全部是 numpy + scipy 自己實作,格式轉換用內建的 `afconvert`。
  看到任何要 ffmpeg 的方案就換掉,不要「先裝一下」。
- 模型權重放 `~/.cache/huggingface`(預設位置),讓其他專案共用。
  **選型定案後要刪掉落選的權重**,不然幾 GB 躺在那裡沒人知道能不能刪。
- 金鑰放 `.env`(已 gitignore),腳本自動讀。需要 `OPENROUTER_API_KEY`。

## 目錄

```
pipeline/            十支檔案,就是整條流程。每支的檔頭註解就是它的文件
  validate.py        beats.json 結構檢查 —— 合成前擋錯
  tts.py             Gemini TTS 合成
  verify.py          Whisper 回轉驗證(中英各一套門檻,自動判斷語言)
  rescore.py         改了正規化規則後重算分數,不必重跑 STT
  stitch.py          拼接 + 依 role 加停頓(只用來試聽節奏)
  assemble.py        混音 + 正規化:人聲 + 片頭 + 章節轉場 + 片尾。
                     交付速度預設 1.0x;變速在混音前做,只拉伸人聲
  master.py          BS.1770-4 響度量測與正規化(純 numpy,含 --measure)
  speedup.py         WSOLA 實作。assemble.py import 它,它的 CLI 是一次性用途
  shownotes.py       show notes + 發布前的 AI 揭露 gate
  brand.py           節目層級常數:名稱、網址、揭露措辭、簡介、各語言的交付速度
.claude/skills/podcast/
  SKILL.md           做一集的完整步驟與指令
  reference/         寫稿與調校的判準,**寫稿前必讀**。跟 skill 放在一起是因為
                     它們是 skill 步驟 2 的前置條件,不是可以跳過的背景
    NARRATION.md     怎麼寫給只能用聽的聽眾(第十節專講英文版)
    NORMALIZATION.md 哪些詞要改寫、哪些不要
    GEMINI-TTS.md    TTS 實測結論與已知陷阱
blog/                部落格原文,git submodule(johnnyhwu.github.io 的 main,淺層)
episodes/<slug>/     一集一個目錄,中英兩份 spec 放在一起
  meta.json          集數、對應文章、中英各一份標題/摘要/重點;可選 ship_rate
  zh.json  en.json   逐字稿。`ep001-mem0/zh.json` 是參考範例
out/<slug>/{zh,en}/  該集的所有產出(gitignore)
music/               片頭、轉場、片尾的成品(進版控,品牌資產)
                     source/ 是授權原曲,cut.py 可以重切
thumbnail/           節目封面,中英共用。cover-3000.jpg 是上傳用的
docs/                給人讀的,執行流程不需要
  PLAN.md            原始規劃書。**只剩第七章(發布合規)與第九章(上線)還有用**
  RESEARCH-HISTORY.md  TTS / STT 選型過程,含三次被推翻的判斷
  MUSIC.md           音樂的選擇、裁切位置、授權存證、為什麼不鋪底 BGM
  COVER-ART.md       封面的概念、prompt、縮圖驗收方式
  TTS-VENDOR-SURVEY.md   商用 TTS 市場調查(Johnny 做的,已定案)
  MUSIC-MODEL-SURVEY.md  自架音樂模型調查(Johnny 做的,**這條路已放棄**)
  TTS-TEST-SUITE.md  中英夾雜測試集,換引擎時才需要
```

## 定案的技術選擇(不要重新評估)

| | 選擇 | 為什麼 |
|---|---|---|
| TTS | `google/gemini-3.1-flash-tts-preview`(走 OpenRouter) | 八個引擎實測分數最高,**$1/百萬字元**,比次便宜的低 15 倍 |
| 音色 | `Zubenelgenubi` | 人耳挑選,中英共用 —— Gemini 的 prebuilt voice 與語言無關 |
| STT | `openai/whisper-large-v3-turbo`(走 `mlx_audio`) | 輸出繁體、精度足夠、不需要 torch |
| 音樂 | Jonas Blakewood / Presentation(Pixabay) | 三輪盲測。片頭/轉場/片尾同源,見 `docs/MUSIC.md` |
| 響度 | -19 LUFS 單聲道、true peak ≤ -1 dBTP | -16 是**立體聲**的值。AAC 編碼會把峰值推上來,實測吃掉 0.2-0.4 dB |
| 交付速度 | 中英預設都是 1.0x(`brand.py` 的 `SHIP_RATE`,各語言各一個值;單集用 `meta.json` 的 `ship_rate` 覆寫) | Johnny 聽過 0.9 與 1.0 後選定。非 1.0 時只變速人聲,音樂原速 |

**四個不要:**

- **不要用 `mlx-whisper` 套件** —— 它會拉進 torch 並要求 ffmpeg。
- **不要考慮 Breeze-TTS-2** —— 權重非商業授權,podcast 一旦營利就違約。
- **不要再試 voice cloning** —— 克隆傳得了音色、傳不了口音,三個引擎都證實過。
- **不要重建 ACE-Step 環境** —— 自己生成音樂跑了五輪盲測,人耳否決,
  29 GB 環境已整包刪除。理由與五個仍然有用的技術發現在 `docs/MUSIC.md` 最後一節。

## 中文版與英文版的關係

**共用骨架,不共用逐字稿。** `id` / `role` / `beat` 一對一對齊,
`text` 和 `style` 重寫 —— 逐句翻譯會壞掉(中英夾雜的定錨消失、
類比是文化性的、中文詞義解釋對英文聽眾是雜訊)。

**兩版是兩個獨立節目,不是一個節目的兩種語言。** RSS 的 `<language>`
是節目層級的單一欄位,混語言會被 Apple 以「Incorrect Language」退件。
判準與門檻換算表在 `.claude/skills/podcast/reference/NARRATION.md` 第十節。

## 開場的固定結構

前四段是固定骨架,`validate.py` 會擋:

```
b00_hook      hook      鉤子,不劇透
b01_identity  identity  節目名 + AI 揭露(固定)+ 這集主題預告(每集不同)
b02_promise   promise   這集能學到什麼
b03_roadmap   signpost  路線圖
b04 之後                正文
```

**開場白每集由 TTS 重新生成,不用固定音檔。** b01 的固定半句與變動半句
在同一句話裡,拆成兩個 beat 去接會留下聽得出來的接縫。品牌識別靠片頭音樂
(那才是固定音檔),人聲的韻律微差聽眾不會註冊成「不同節目」。

代價是揭露句可能漂移,所以 `validate.py`(合成前)與 `shownotes.py`(發布前)
兩處都驗 —— 措辭可以跟當集主題呼應,但「聲音是 AI 合成」這個事實不能不見。
**Apple Podcasts 第 1.11 條,漏掉可能整集下架。**

## 四個設計原則

1. **Single source of truth** —— beats.json 的 `text` 就是最終逐字稿,
   不要在下游再改寫。要改寫就改 beats.json 然後重新合成那一段。
2. **Fail fast** —— 合成一集要 30 分鐘,所有能靠讀稿發現的問題
   都必須在 `validate.py` 擋下來。
3. **結構性約束優於 prompt** —— 不要在提示裡寫「請講得生動一點」,
   而是讓 schema 逼出變化(role 制度、連續解說上限、recap 下限)。
4. **檢查點越早越好** —— 驗證在每一段合成後就做,不要等整集拼完。

## 跟使用者互動

- 使用者用**繁體中文**溝通,回覆也用繁體中文。
- **他的耳朵是最終判準。** STT 分數、頻譜、相關係數都只是篩選器。
  量測可以說明「為什麼」,不能推翻「好不好聽」 —— 音樂選型三輪都是這樣收斂的。
- **預設一路做完**,只在花錢前(講預估成本)與全部完成後(總結)停下來;
  他說「逐步確認」才改成每步回報。背景合成**每 15 分鐘查一次進度**,他已授權。
- 花錢的操作(TTS API)**先講預估成本再跑**。成本幾乎完全由輸出音訊長度
  決定(約 US$0.03/分鐘音訊),跟輸入文字多寡無關 —— 一集約 30-40 分鐘音訊,
  實際約 US$1-1.5。合成前後各查一次 OpenRouter credits 對帳(細節見 skill 步驟 6)。
- **部落格原文自己有矛盾的地方,podcast 裡不講。** 我們只有原文、沒有論文全文,
  不替原文裁決;略過了什麼在總結裡列出。自己的推測可以講,但要明說是推測。
- 做完要**清掉這次的實驗與暫存檔**,並明確告訴他最終交付檔是哪一個(skill 步驟 10)。
- 給他比較用的東西就做成真的情境。片段脫離上下文聽不出差別,
  音樂是放進完整節目裡比才選得出來的。

## 還沒做的

只有兩件,**都不是技術問題**:

- **Spotify for Creators 帳號** —— 兩個獨立的 show。`PLAN.md` 7.1 的結論是
  初期手動上傳,它自動產生的 feed 可直接提交給 Apple,一份 hosting 兩邊通用。
- **授權條款快照** —— 把 `docs/MUSIC.md` 裡三個 Pixabay 網址各存一份當天的
  截圖或 PDF。網址指向現行版本,條款改版後就證明不了下載當天的內容。

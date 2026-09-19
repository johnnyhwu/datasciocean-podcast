# DataSci Ocean Podcast

把 Johnny 的中文技術部落格文章,做成 20-40 分鐘的單人旁白 podcast。
**每篇文章出兩集:中文版給華人聽眾,英文版給外國聽眾。**

## 一句話流程

文章 → beats.json(結構化逐字稿)→ Gemini TTS 逐段合成 →
Whisper 回轉驗證 → 拼接加停頓 → 音量正規化 →
輸出原速 + 5 個加速版本 → show notes。
中英兩版各走一次,**兩版都要驗證**。

**要做一集時,直接呼叫 `podcast` skill。** 它有完整的步驟與判準。

## 中文版與英文版的關係

**共用骨架,不共用逐字稿。** `id` / `role` / `beat` 一對一對齊,
`text` 和 `style` 重寫 —— 逐句翻譯會壞掉(中英夾雜的定錨消失、
類比是文化性的、中文詞義解釋對英文聽眾是雜訊)。
音色兩版共用同一個 `Zubenelgenubi`,Gemini 的 prebuilt voice 與語言無關。

理由、門檻換算表、正規化差異全部在 `reference/NARRATION.md` 第十節。

## 環境

- **絕不弄髒系統。** 一律 `uv run`,套件記在 `pyproject.toml`,
  Python 版本由 `.python-version` 指定。不要 `pip install`。
- **不要引入系統依賴。** 這個專案刻意沒有 ffmpeg / sox / rubberband,
  音訊處理用 numpy + scipy 自己實作(`pipeline/speedup.py`),
  格式轉換用 macOS 內建的 `afconvert`。
- 模型權重放 `~/.cache/huggingface`(預設位置),讓其他專案共用。
- 金鑰放 `.env`(已 gitignore),腳本會自動讀取。需要 `OPENROUTER_API_KEY`。

## 文章來源

`~/Desktop/johnnyhwu.github.io` —— Hugo repo,文章在
`content/posts/paper-intro/<slug>/index.zh-tw.md`,約 110 篇。

## 目錄

```
pipeline/                 九支檔案,就是整條流程
  validate.py             beats.json 結構檢查(合成前擋錯)
  tts.py                  Gemini TTS 合成
  verify.py               Whisper 回轉驗證(中英文各一套門檻,自動判斷語言)
  rescore.py              改了正規化規則後重算分數,不必重跑 STT
  stitch.py               拼接 + 依 role 加停頓
  master.py               音量正規化(BS.1770-4 LUFS + true peak,純 numpy)
  shownotes.py            show notes + 發布前的 AI 揭露 gate
  brand.py                節目固定字串(名稱、網址、揭露措辭)
  speedup.py              產生加速版本(WSOLA,不改音高)
reference/                寫稿與調校的判準,寫稿前必讀
  NARRATION.md            怎麼寫給只能用聽的聽眾(第十節:英文版)
  NORMALIZATION.md        哪些要改寫、哪些不要
  GEMINI-TTS.md           TTS 實測結論與已知陷阱
episodes/<slug>/          一集一個目錄,中英兩份 spec 放在一起
  meta.json               集數層級的發布資訊(標題、摘要、重點、對應文章 slug)
  zh.json  en.json        ep003-mem0/zh.json 是參考範例。它的 validate 會回一個
                          ✗(b22b_sp 與 b23_four_ops 重複句)—— 這是真的缺陷,
                          使用者決定這集不重錄,而音檔已依現稿生成,
                          改稿就會與音檔脫節。**新的一集不可以帶著 ✗ 就去合成。**
out/<slug>/{zh,en}/       該版的所有產出(gitignore)
docs/                     給人讀的,執行流程不需要
  plan.md                 原始規劃書。還沒做的部分(封面、RSS、上線)在這裡;
                          第三、四章與附錄 A 已被取代,章首有警示
  RESEARCH-HISTORY.md     TTS / STT 選型過程的完整紀錄
  INTRO-MUSIC.md          片頭曲的 prompt、seed、各輪盲測結果與結論
  MUSIC-GENERATION-RESEARCH.md  音樂模型選型與授權盡職調查(Johnny 做的)
  vendor-research.md      商用 TTS 市場調查(Johnny 做的,已定案)
  TTS-TEST-SUITE.md       中英夾雜測試集,換引擎時才需要
archive/                  Johnny 的錄音(gitignore,克隆已放棄,留著備查)
```

## 定案的技術選擇(不要重新評估)

| | 選擇 | 為什麼 |
|---|---|---|
| TTS | `google/gemini-3.1-flash-tts-preview`(走 OpenRouter) | 八個引擎實測分數最高,且 **$1/百萬字元**,比次便宜的低 15 倍 |
| 音色 | `Zubenelgenubi` | 人耳挑選,中英文共用 |
| STT | `openai/whisper-large-v3-turbo`(走 `mlx_audio`) | 輸出繁體、精度足夠、不需要 torch |

**不要用 `mlx-whisper` 套件** —— 它會拉進 torch 並要求 ffmpeg。
**不要考慮 Breeze-TTS-2** —— 權重是非商業授權,podcast 一旦營利就違約。
**不要再試 voice cloning** —— 克隆傳得了音色,傳不了口音,三個引擎都證實過。
詳細比較見 `docs/RESEARCH-HISTORY.md`。

## 四個設計原則

1. **Single source of truth** —— beats.json 的 `text` 就是最終逐字稿,
   不要在下游再改寫。要改寫就改 beats.json。
2. **Fail fast** —— 合成一集要 30 分鐘,所有能靠讀稿發現的問題
   都必須在 `validate.py` 擋下來。
3. **結構性約束優於 prompt** —— 不要在提示裡寫「請講得生動一點」,
   而是讓 schema 逼出變化(role 制度、連續解說上限、recap 下限)。
4. **檢查點越早越好** —— 驗證在每一段合成後就做,不要等整集拼完。

## 跟使用者互動

- 使用者用**繁體中文**溝通,回覆也用繁體中文。
- 使用者會親自試聽並給具體回饋,**他的耳朵是最終判準**。
  STT 分數只是篩選器,不是判官。
- 花錢的操作(TTS API)先講清楚預估成本再跑。
  一集中文約 US$0.01,英文約 US$0.03。

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

代價是揭露句可能漂移,所以 `validate.py` 與 `shownotes.py` 兩處都驗
—— 措辭可以跟當集主題呼應,但「聲音是 AI 合成」這個事實不能不見。
Apple Podcasts 第 1.11 條,漏掉可能整集下架。

## 還沒做的部分

- **片頭曲**:進行中。用 ACE-Step 1.5 本機生成(MIT 授權),已跑三輪盲測,
  方向收斂到「Rhodes 電鋼 + 暖的木質敲擊 accent」。過程與 seed 見
  `docs/INTRO-MUSIC.md`。**環境是拋棄式的**(`~/.cache/acestep-trial/`),
  定案後整包刪除,刪除方式見該目錄的 `TEARDOWN.md`。
- **片尾曲 / 混音腳本 / BGM**:未做。混音要自己用 numpy 做
  (淡出是乘窗函數、疊加是對齊相加),**不要用 pydub**,它要 ffmpeg。
  混完之後要對成品重跑一次 `master.py`,因為加了音樂響度會變。
- **封面、RSS 發布、上線**:未做。規劃在 `docs/plan.md` 第六、七、九章。

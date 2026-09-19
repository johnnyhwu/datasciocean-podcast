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
pipeline/                 十支檔案,就是整條流程
  validate.py             beats.json 結構檢查(合成前擋錯)
  tts.py                  Gemini TTS 合成
  verify.py               Whisper 回轉驗證(中英文各一套門檻,自動判斷語言)
  rescore.py              改了正規化規則後重算分數,不必重跑 STT
  stitch.py               拼接 + 依 role 加停頓
  assemble.py             片頭音樂 + 人聲 + 片尾音樂混成一集(純 numpy)
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
thumbnail/                節目封面。cover-3000.jpg 是上傳用的成品,
                          v4.png 是生成母帶。中英兩個節目共用同一張
docs/                     給人讀的,執行流程不需要
  plan.md                 原始規劃書。還沒做的部分(RSS、上線)在這裡;
                          第三、四章與附錄 A 已被取代,章首有警示
  RESEARCH-HISTORY.md     TTS / STT 選型過程的完整紀錄
  INTRO-MUSIC.md          片頭曲的 prompt、seed、各輪盲測結果與結論
  COVER-ART.md            封面的概念、prompt、縮圖驗收方式與踩過的坑
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

- **片頭 / 片尾曲**:改用授權曲庫的現成片段,**不再自己生成**。
  ACE-Step 1.5 跑了五輪盲測,結果 Johnny 不滿意,環境(29 GB)已整包移除
  —— 不要再重建。但那五輪定出了規格,挑曲子時照這個對:
  **Rhodes 電鋼或尼龍弦吉他的獨奏質地、無鼓無貝斯、8-12 秒、
  單一動機不發展、低調不搶話**;被明確淘汰的是「敲擊樂器一問一答」的結構。
  過程與量測見 `docs/INTRO-MUSIC.md`。授權要留存證(來源網址、授權條款、
  下載日期),CC0 / CC-BY 都要記,商用 podcast 出事是授權出事。
- **混音腳本**:✅ `pipeline/assemble.py`。純 numpy,沒有 pydub(它要 ffmpeg)。
  輸出 44.1 kHz 單聲道 −19 LUFS,交接的壓低量逐首反推(見檔頭註解)。
- **全程鋪底 BGM**:**不做**,有量測依據。音樂壓到寬頻 −20 dB 時,1–4 kHz 的
  子音帶其實只低 18.6 dB,而子音決定聽不聽得懂;加上 1.1–1.5× 的加速版本會把
  音樂一起 WSOLA 拉伸,產生顆粒感。音樂只當標點:片頭、章節轉場、片尾。
- **封面**:✅ 已完成,`thumbnail/cover-3000.jpg`(3000×3000、RGB、中英共用)。
  做法與踩過的坑見 `docs/COVER-ART.md`。**任何視覺素材的驗收都是縮到
  150 px 和 55 px 看** —— 細於全寬 1% 的元素在那個尺寸不會存在。
- **RSS 發布、上線**:未做,但**不需要寫程式**。`plan.md` 7.1 的結論是初期
  手動上傳 Spotify for Creators,它自動產生的 feed 可直接提交給 Apple,
  一份 hosting 兩邊通用。卡在帳號,不卡在技術。

# 自架、可商用 AI 開場音樂(intro sting)方案完整調查(2026 年 9 月）

> **⚠️ 這條路已經放棄(2026-09-20)。** 本文是 Johnny 做的自架音樂模型調查,
> 它的結論(用 ACE-Step 1.5)照著做了五輪盲測,**結果人耳不滿意**,
> 改用 Pixabay 的授權曲。定案與過程見 `MUSIC.md`。
>
> 留著的唯一理由是:如果哪天要重新考慮自架,不用從零查一遍授權
> —— 尤其 MusicGen(CC-BY-NC)那類商用地雷。
> **但先讀 `MUSIC.md` 最後一節**,那裡寫了為什麼自架生成的品質沒有過關。
> 不需要這份參考的話可以整份刪掉,內容在 git 歷史裡。


## TL;DR（30 秒結論）
- **首選:ACE-Step 1.5（自架、MIT 授權）。** 它是目前唯一同時滿足「授權最乾淨（MIT,無營收上限、無地區限制、無需標示歸屬）+ 官方原生支援 Apple Silicon（MLX 後端）+ 能生成有旋律的完整音樂而非只是音效」的方案,生成後把片段裁成 8–12 秒即可一次性使用。
- **次選:Stable Audio Open Small / 1.0。** 專為短素材設計、最貼合「開場 sting」用途,但授權是 Stability AI Community License（年營收 < 100 萬美元免費商用、需標示「Powered by Stability AI」),且輸出偏音效/氛圍質地,旋律性較弱。
- **一句話:** 要旋律好聽又授權最無牽掛,用 ACE-Step 1.5;要最省事、專門做短音效,用 Stable Audio Open——兩者都能在你的 M5 24GB Mac 上跑。

## Key Findings
- **可商用的自架開源選項比你清單上多。** 除了 Stable Audio Open 與 ACE-Step,還有 **ACE-Step 1.5**（2026 年新版,MIT）、**YuE**（Apache 2.0）、**DiffRhythm / DiffRhythm 2**（Apache 2.0,但 VAE 部分受 Stability 授權牽制）、**Magenta RealTime / RT2**（Apache 程式碼 + CC-BY-4.0 權重)、**MiniMax Music 3**（社群授權,免費商用門檻 2000 萬美元但有地區限制)、以及較舊的 **Riffusion v1**（OpenRAIL-M）。
- **MusicGen（Meta)確定排除。** 權重為 CC-BY-NC 4.0,非商用;程式碼雖為 MIT 但權重限制使生成物不可商用。
- **授權「乾淨度」排序（對你這種未來可能有業配收入的個人 podcast）:** MIT / Apache 2.0（ACE-Step 1.5、ACE-Step v1、YuE、DiffRhythm 主體、Magenta RT）> Stability Community License（有 100 萬美元營收門檻 + 強制標示）> MiniMax 社群授權（有地區排除 + 強制標示）> OpenRAIL-M（Riffusion）> CC-BY-NC（MusicGen,不可用）。
- **Apple Silicon 支援差異巨大。** ACE-Step 1.5 與 Magenta RT2 有官方原生 Apple Silicon 路徑;Stable Audio Open 需手動改 `cuda`→`mps`;YuE 與 MiniMax 官方只支援 NVIDIA CUDA,Mac 只能靠社群 fork。
- **你的用途（一次性生成 8–12 秒、之後重複使用)其實對硬體與速度幾乎沒要求。** 就算在 M5 上一次生成要一兩分鐘,也完全不影響,因為只跑一次。真正的決策軸是「授權」與「輸出是否有旋律性」。

## Details（各方案逐一查證,授權查證時間為 2026 年 9 月 9 日）

### 1. ACE-Step 1.5（★ 首選,自架）
- **授權:** 官方 GitHub repo 的 LICENSE 檔為 **MIT License（Copyright (c) 2026 ACEStep）**。Hugging Face 模型卡明確寫「You can strictly use the generated music for commercial purposes」,並說明訓練資料為「授權音樂 + 公有領域/免版稅音樂」。MIT 無營收門檻、無地區限制、無強制標示歸屬（僅需保留版權聲明於軟體本身,不涉及你產出的音訊)。查證日 2026-09-09。
- **來源:** github.com/ace-step/ACE-Step-1.5/blob/main/LICENSE;huggingface.co/ACE-Step/Ace-Step1.5
- **自架 / Apple Silicon:** 官方 repo 標題即宣稱「supporting Mac, AMD, Intel, and CUDA devices」,提供 `start_gradio_ui_macos.sh`,macOS 腳本自動設定 `ACESTEP_LM_BACKEND=mlx` 走 Apple 原生 MLX 加速。社群實測在 M2 MacBook Air 可跑（需設 `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`),生成約 5–10 分鐘;M2 Max 約每分鐘音訊 26 秒。你的 M5 24GB 記憶體足夠（建議用 2B 或 0.6B LM 變體以避免 OOM;16GB+ 系統會自動關閉 CPU offload）。
- **輸出:** 完整旋律音樂（非音效),可控制時長,最長約 10 分鐘,支援 50+ 語言、純器樂或含人聲。生成後裁切成 8–12 秒即可。
- **成本:** 全本機、免費、無額度限制。首次需下載模型權重（2B 權重約 4.7GB,一次性)。
- **注意:** Mac 上 LoRA 微調受限（MLX DiT 不支援 LoRA、訓練易 OOM),但你的用途不需要微調,不受影響。

### 2. Stable Audio Open Small / Stable Audio Open 1.0（★ 次選,自架）
- **授權:** **Stability AI Community License,最後更新日 2024-07-05。** 經查證原始授權條文:年營收 **低於 100 萬美元（US$1,000,000)** 的個人或組織可免費用於商業目的;超過門檻則授權終止、需另向 Stability 申請。**產出的音訊（Outputs)歸你所有**——授權第 IV(c)(iii) 條寫「You own any outputs generated from the Models... to the extent permitted by applicable law」,且「Derivative Work」定義明確以「but do not include the output of any Model」排除模型輸出,即你的音訊與模型權重分開處理。但第 IV(a) 條要求:若你散布模型或衍生作品,需保留授權副本並「prominently display『Powered by Stability AI』」。查證日 2026-09-09。
- **來源:** stability.ai/community-license-agreement;huggingface.co/stabilityai/stable-audio-open-1.0/blob/main/LICENSE.md;stability.ai/license
- **重要更正:** 部分二手部落格（如 SiliconANGLE 2024、Apatero)仍稱 Stable Audio Open 是「non-commercial、禁止商用」——這是舊資訊或誤讀。官方模型卡與授權原文明確允許 100 萬美元以下商用。以官方 License 為準。
- **自架 / Apple Silicon:** 非 CUDA 環境預設 fallback 到 CPU;需手動把 `stable_audio_tools` 內 `device="cuda"` 改為 `mps` 才能用 Apple Silicon 加速。開發者實測（finetuned 3 秒模型)MPS 約 17 秒/次 vs CPU 51 秒/次。Hugging Face 討論串確認 Stable Audio Open 1.0 可在 M2 Mac 上跑（CPU fallback,較慢);而新版 Small 在 CPU 上可能卡住。官方 GitHub Issue #79 顯示 MPS 支援仍屬社群需求、非官方保證。
- **效能與規格:** Stable Audio Open Small 為 341M 參數模型,官方（Stability AI 2025 新聞稿)稱其借助 Arm KleidiAI 可「produce up to 11 seconds of audio on a smartphone in less than 8 seconds」,在 NVIDIA H100 上生成 12 秒音訊僅需 75 毫秒(Stability AI/Arm arXiv 論文,arxiv.org/abs/2505.08175）。
- **輸出:** 官方 Hugging Face 模型卡:「Stable Audio Open Small generates variable-length (up to 11s) stereo audio at 44.1kHz from text prompts」;**1.0 最長 47 秒;Small 最長 11 秒**。官方警告僅支援英文 prompt、無法生成擬真人聲或高品質完整歌曲(訓練資料偏西方)。偏向鼓組 loop、foley、樂器 riff、氛圍質地等「音效/製作素材」,旋律性弱於 ACE-Step。
- **成本:** 全本機、免費、無額度限制。需在 Hugging Face 同意授權後下載權重。
- **對你用途的評語:** 「11 秒短素材」的設計和你「8–12 秒 sting」需求完美吻合,是最省事的選擇;唯一取捨是它比較像「音效」而非「有記憶點的旋律開場」,以及那個 100 萬美元門檻 + 標示義務。

### 3. ACE-Step v1 3.5B（自架,舊版）
- **授權:** Apache 2.0（GitHub LICENSE 與 Hugging Face 模型卡一致),明確允許商用、無門檻。查證日 2026-09-09。
- **來源:** github.com/ace-step/ACE-Step/blob/main/LICENSE;huggingface.co/ACE-Step/ACE-Step-v1-3.5B
- **自架 / Apple Silicon:** 支援 MPS;社群有 Apple Silicon fork。最低 8GB VRAM,是清單中最輕量、消費級硬體可跑的。
- **輸出:** 完整旋律音樂,可控時長,最長約 4 分鐘,支援 17 種語言。
- **成本:** 全本機免費。
- **評語:** 已被 1.5 取代;若要用 ACE 系列,直接用 1.5（授權更明確為 MIT,Mac 支援更成熟)。

### 4. YuE（自架）
- **授權:** **Apache 2.0（含權重),2025-01-30 起。** 官方鼓勵商業使用與變現,唯一要求是標示「**YuE by HKUST/M-A-P**」。查證日 2026-09-09。
- **來源:** github.com/multimodal-art-projection/YuE/blob/main/LICENSE
- **自架 / Apple Silicon:** **官方只支援 CUDA 11.8+ 與 FlashAttention 2,無第一方 Mac/MPS 路徑**（截至 2026 年 4 月)。單段生成需約 16GB VRAM,完整歌曲建議 80GB 級 GPU。Mac 只能靠社群 fork / CPU / 雲端。
- **輸出:** 歌詞轉完整歌曲（含人聲 + 伴奏),最長約 5 分鐘。是最接近 Suno 的開源模型,但偏「完整帶人聲歌曲」,對純器樂短 sting 是殺雞用牛刀,且 Mac 支援差。
- **評語:** 授權好但硬體與用途都不適合你。排除。

### 5. DiffRhythm / DiffRhythm 2（自架）
- **授權:** 程式碼與 DiT 權重為 **Apache 2.0**;但 **VAE 由 Stable Audio Open 微調而來,因此該部分受 Stability AI Community License 約束**（即又回到 100 萬美元門檻議題)。查證日 2026-09-09。
- **來源:** github.com/ASLP-lab/DiffRhythm;huggingface.co/ASLP-lab/DiffRhythm-vae/blob/main/LICENSE.md
- **輸出:** 完整歌曲（人聲 + 伴奏),最長約 4分45秒。偏完整歌曲。
- **評語:** 授權因 VAE 而變複雜,且偏完整歌曲,對短 sting 不理想。

### 6. Magenta RealTime / RealTime 2（Google,自架）
- **授權:** **程式碼 Apache 2.0,權重 CC-BY-4.0（允許商用,需標示歸屬)**。Google 聲明對你的產出不主張任何權利。查證日 2026-09-09。
- **來源:** huggingface.co/google/magenta-realtime;huggingface.co/google/magenta-realtime-2
- **規格:** Magenta RealTime 為 800M 參數自迴歸 Transformer,官方 Hugging Face 卡載明「trained on ~190k hours of stock music from multiple sources, mostly instrumental」,輸出 48kHz 立體聲,RTF≈0.625（每 2 秒音訊生成需 1.25 秒);RT2 訓練資料約 71k 小時 stock music。
- **自架 / Apple Silicon:** RT2 官方提供 MLX 後端與 C++ 推理引擎,可在 Apple Silicon 原生低延遲跑;`magenta-rt` 函式庫支援 JAX 與 MLX。
- **輸出:** 即時、連續的器樂音訊（instrumental only),由文字 prompt 或音訊範例引導。設計用於即時互動演出,而非「生成一段固定檔案」,對一次性 sting 稍微綁手綁腳,但技術上可行且授權乾淨。
- **評語:** 授權與 Apple Silicon 支援都很好,是可行的備案,尤其若你想要氛圍/器樂質地。

### 7. MiniMax Music 3（自架/開放權重）
- **授權:** **MiniMax Community License（非 OSI 開源)**。年營收 **低於 2000 萬美元** 可免費商用,超過需書面授權;**強制在商業產品介面顯示「MiniMax-Music3」**;且有**地區排除——美國、歐盟、英國、南韓為 Excluded Territories**,這些地區用開放權重需另外申請授權(雲端 API 政策不同)。查證日 2026-09-09。
- **來源:** huggingface.co/MiniMaxAI（模型卡);comfy.org/minimax/license
- **自架 / Apple Silicon:** 官方只支援 NVIDIA CUDA;社群有 MLX 版與 ComfyUI CMF 版,據報可在 Apple M4/M5 上跑。
- **輸出:** 完整歌曲（含人聲),最長 5 分鐘,32kHz 立體聲。品質據評約等於 Suno V3.5。
- **評語:** 地區排除條款是大地雷——若你或聽眾在美/歐/英/韓,用開放權重商用需另申請授權。強制標示也麻煩。不推薦作首選。

### 8. Riffusion v1（自架,舊）
- **授權:** CreativeML OpenRAIL-M。明確允許「use the model commercially and/or as a service」,Riffusion 不主張產出權利,但你散布時需附帶相同使用限制並提供授權副本。查證日 2026-09-09。
- **來源:** huggingface.co/riffusion/riffusion-model-v1/blob/main/README.md
- **輸出:** 以 spectrogram 影像方式生成音樂,品質偏低、偏舊。
- **評語:** 授權可商用,但音質已落後 2026 年的模型,不推薦。

### 9. MusicGen（Meta)—— 確定排除
- **授權:** 程式碼 MIT,但**權重 CC-BY-NC 4.0（非商用)**。因此生成物不可商業使用。查證日 2026-09-09。
- **來源:** huggingface.co/facebook/musicgen-small（README license: cc-by-nc-4.0);github.com/facebookresearch/audiocraft/issues/198
- **評語:** 列出以避免誤踩。**不要用於任何可能商業化的 podcast。**

### 雲端付費服務（供對照,非本任務重點）
- **Suno Pro / Udio Standard 等:** 付費訂閱期間生成的內容才有商用授權;免費版一律不可商用。DiffRhythm.ai、acemusic.ai 等官方託管站有各自的商業方案。這些不符合你「免費/極低成本 + 自架」的偏好,僅在你想完全免安裝時考慮,且務必看付費層級的 ToS。

## 比較表

| 方案 | 授權 | 免費商用? | 營收/地區限制 | 需標示歸屬? | 自架 Apple Silicon | 輸出長度 | 音樂類型 | 適合短 sting? |
|---|---|---|---|---|---|---|---|---|
| **ACE-Step 1.5** | MIT | ✅ | 無 | ❌ 不需 | ✅ 官方 MLX 原生 | 至多約 10 分,可控 | 完整旋律,可器樂/人聲 | ★★★★★ |
| **Stable Audio Open Small** | Stability Community | ✅ | < 100 萬美元 | ✅ Powered by Stability AI | ⚠️ 需改 mps | 至多 11 秒 | 音效/氛圍/loop | ★★★★☆ |
| **Stable Audio Open 1.0** | Stability Community | ✅ | < 100 萬美元 | ✅ Powered by Stability AI | ⚠️ 需改 mps | 至多 47 秒 | 音效/氛圍/riff | ★★★★☆ |
| ACE-Step v1 3.5B | Apache 2.0 | ✅ | 無 | ❌ | ✅ MPS | 至多約 4 分 | 完整旋律 | ★★★★☆ |
| YuE | Apache 2.0 | ✅ | 無 | ✅ YuE by HKUST/M-A-P | ❌ 官方僅 CUDA | 至多約 5 分 | 完整歌曲+人聲 | ★★☆☆☆ |
| DiffRhythm 2 | Apache 2.0（VAE 受 Stability) | ✅ | VAE 部分 < 100 萬美元 | 視 VAE | ⚠️ | 至多約 4分45秒 | 完整歌曲+人聲 | ★★☆☆☆ |
| Magenta RT2 | Apache + CC-BY-4.0 | ✅ | 無 | ✅ 需 CC-BY 標示 | ✅ 官方 MLX | 即時連續 | 器樂 | ★★★☆☆ |
| MiniMax Music 3 | MiniMax Community | ✅ | < 2000 萬美元 + **排除美/歐/英/韓** | ✅ MiniMax-Music3 | ❌ 官方僅 CUDA(社群 MLX) | 至多 5 分 | 完整歌曲+人聲 | ★★☆☆☆ |
| Riffusion v1 | OpenRAIL-M | ✅ | 無 | 需附授權副本 | ⚠️ | 短片段 | 舊、音質低 | ★★☆☆☆ |
| MusicGen | 權重 CC-BY-NC | ❌ **不可** | — | — | ✅ | 至多約 30 秒 | 器樂 | ❌ 排除 |

## Recommendations（具體行動建議）
1. **直接用 ACE-Step 1.5 生成你的 sting。** 步驟:在 M5 上 `git clone github.com/ace-step/ACE-Step-1.5` → `uv sync` → 執行 `start_gradio_ui_macos.sh`（自動走 MLX）→ 開 localhost Gradio UI → 以純器樂 prompt(例如「short upbeat electronic intro sting, bright synth, no vocals, 12 seconds」)生成幾個版本 → 在任何免費 DAW(GarageBand/Audacity)裁成 8–12 秒、加淡出 → 匯出成你固定的開場檔。因為只做一次,生成慢(數分鐘)完全無所謂。理由:MIT 授權最乾淨(無營收上限、無地區限制、產出不需標示),旋律性最好,Apple Silicon 官方支援。若 24GB 記憶體吃緊,改用 0.6B 或 2B LM 變體(避開建議 ≥20GB VRAM 的 XL/4B)。
2. **若你想要「專門做短音效」的最省事路線,改用 Stable Audio Open Small（11 秒)或 1.0(47 秒)。** 但務必:(a) 確認你 podcast 年營收 < 100 萬美元(對絕大多數個人 podcast 顯然成立);(b) 在你的節目網站或說明頁放一行「Powered by Stability AI」以符合標示義務。這條路適合你想要氛圍/質地型開場、而非明確旋律時。
3. **保留 Magenta RT2 作為器樂備案**——授權(CC-BY,只需標示)與 Apple Silicon 原生支援都好,但它是「即時串流」設計,要額外把輸出錄成固定檔,稍麻煩。
4. **明確避開:** MusicGen(不可商用)、MiniMax Music 3(地區排除美/歐/英/韓)、YuE(Mac 支援差且偏完整人聲歌曲)。
5. **改變建議的門檻:** 若你的 podcast 年營收未來會超過 100 萬美元 → Stable Audio Open 就需另購 Stability 商業授權,此時 ACE-Step 1.5(MIT)的「無上限」優勢更關鍵,應鎖定 MIT/Apache 方案。若你完全不想碰命令列 → 才考慮付費雲端(Suno Pro/Udio),並只在訂閱有效期內生成。

## Caveats（尚未查清、需你自行再確認的事項）
- **AI 生成音樂的著作權可否登記,各國不同,且對「純 AI 生成」多半不利。** 美國著作權局 2025-01-29 發布《Copyright and Artificial Intelligence, Part 2: Copyrightability》報告,明確結論「Human authorship is a bedrock of copyrightability, and thus works entirely generated by AI are not copyrightable」,且「mere selection of prompts…does not itself yield a copyrightable work」。這不影響你「使用」該音訊做 sting 的合法性,但可能影響你「主張他人不得抄襲你的 sting」的能力。若這對你重要,建議在生成後做人為編輯(裁切、混音、加層)以增加人類創作成分,並諮詢當地法律。
- **授權條款變動快。** 本報告所有授權查證時間點為 **2026 年 9 月 9 日**。Stability 的 Community License 標示「最後更新 2024-07-05」;ACE-Step 1.5 為 MIT(2026)。發布前請再開一次官方 LICENSE / 模型卡確認未變動。
- **Stable Audio Open 的 Apple Silicon 速度** 我只找到「3 秒 finetuned 模型 MPS 約 17 秒」這個社群數據,以及「1.0 可在 M2 上跑但較慢」的確認;完整 47 秒生成在 M5 上的實際耗時沒有官方 benchmark,需你自行實測。但因是一次性任務,速度不構成阻礙。
- **ACE-Step 1.5 在 24GB 記憶體上的穩定性** 社群多在 16GB(M2 Air)與 64GB(M2 Max)實測;你的 24GB 介於中間,XL(4B)變體官方建議 ≥20GB VRAM,可能吃緊,建議先用 2B/0.6B 變體並觀察記憶體壓力。
- **「訓練資料是否乾淨」是另一層風險。** 據 TechCrunch(2025)報導,Stability 宣稱 Stable Audio Open Small「training set is made up entirely of songs from the royalty-free audio libraries Free Music Archive and Freesound」,以對比 Suno、Udio 訓練集含受版權內容的 IP 風險;ACE-Step 1.5 亦宣稱使用授權/免版稅/公有領域資料。但這些皆為廠商自述,無第三方稽核。若日後有業配且金額大,建議保留你的 prompt 與生成紀錄作為佐證。
- **強制標示的實務位置** Stability 要求「prominently display」Powered by Stability AI——放在 podcast show notes / 網站頁尾應足夠,但「prominently」的標準模糊,若要百分百保險可諮詢法律。
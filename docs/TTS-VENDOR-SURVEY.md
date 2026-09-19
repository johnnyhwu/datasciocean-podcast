# 商用 TTS 服務窮盡式市場調查:DataSci Ocean 中文科技 Podcast 語音方案選型

> **現況(2026-09-16 由 Claude 補):已定案,本文是決定之前的市場調查。**
> 最後選的是 `google/gemini-3.1-flash-tts-preview`(走 OpenRouter),
> 音色 `Zubenelgenubi`。決策過程見 `RESEARCH-HISTORY.md`。
> 本文留著的價值是授權與價格的比對紀錄 —— 日後要換供應商時不用重查一遍。


## TL;DR
- **以「中英混雜品質 + 台灣腔」為第一權重,最適合的正式方案是雲端的 MiniMax Speech 2.8(HD)**:2026 年台灣腔實測第一名,且在「同事 sync 一下明天的 schedule」這類中英夾雜句中連英文字都能帶台灣腔;若要自架且商用授權乾淨,首選 **CosyVoice3 0.5B(Apache 2.0,Mac MLX 可跑、RTF≈0.5、可懂度最佳)**,用一段台灣腔參考音檔做 zero-shot 克隆。
- **使用者原本的兩個領先候選都要重新定位,且都不是「開箱即用」的最佳解**:Qwen3-TTS 中英混讀確實流暢(「无明显切换卡顿」)但內建音色是大陸腔、無台灣腔;IndexTTS-2/2.5 技術指標最強(WER 6.75、說話人相似度 73.18 為多語冠軍)但**授權是 bilibili 非商用授權,商用須寄信 indexspeech@bilibili.com 另外取得付費授權**,對「正式商用」是紅旗。
- **中國廠商 API 可從台灣合法申請**:走阿里雲/MiniMax 的「國際站(新加坡節點)」用台灣 +886 門號 + 國際信用卡/PayPal 即可註冊付款,不需大陸門號或大陸實名(阿里雲官方:實名驗證為選填,只有買大陸境內部署服務才強制);但資料落地在境外新加坡,仍有法遵與供應鏈風險需自評。

## Key Findings

**中英混雜是可量化的難題,而且使用者遇到的三種失敗模式在學術界有正式對應。** 一篇 2026 年台灣導向研究 BlueMagpie-TTS(arXiv 2607.06054)幾乎逐字描述了本使用者的情境:「A single spoken sentence in Taiwan often mixes Mandarin with English words, abbreviations, and proper nouns... At the switch point, the tokenizer fragments the boundary, the language model cannot plan the prosody transition, and the TTS distorts the English span or breaks the surrounding Mandarin prosody.」另一個 CS3-Bench(Heyang Liu 等,arXiv 2510.07881)在 7 個主流模型上量到「a relative performance drop of up to 66% in knowledge-intensive question answering」,並用 Chain-of-Recognition + Keyword-Highlighting 把知識準確率從 25.14% 提升到 46.13%。這證明失敗模式 1(英文發音不清/口音重)、失敗模式 2(英文接數字斷句錯)、失敗模式 3(縮寫唸法奇怪)是系統性問題,而非個別工具 bug。

**最關鍵的排序結論**:對「台灣腔 + 中英混雜」同時滿足的需求,真正能打的只有兩類——(a) 支援 zero-shot 克隆的模型(餵一段台灣腔音檔:IndexTTS-2、CosyVoice、MiniMax clone、F5-TTS、Fish-Speech 屬此類),或 (b) 原生台灣腔服務(Azure zh-TW、Yating 雅婷、ATEN 優聲學、MediaTek BreezyVoice)。國際大廠(ElevenLabs、OpenAI、Google 生成式)與純大陸腔服務(Qwen3-TTS 內建音色、火山引擎、訊飛)在「台灣腔」這一項先天弱勢,除非它們支援克隆。

**Mac M5 24GB 本地推論可行性(重要更正)**:網路上常見「Qwen3-TTS 需要 NVIDIA、不支援 Mac」的說法(texttolab:「you need an NVIDIA GPU with at least 6GB VRAM. No Mac」)只對「官方 CUDA 參考實作」成立;實際上 Qwen3-TTS 0.6B/1.7B、CosyVoice3 0.5B、IndexTTS v1.5/2.0 都已有社群 MLX(Apple Silicon)移植版可跑。M 系列實測(Soniqo benchmark):CosyVoice3 0.5B 4-bit RTF≈0.59、round-trip WER 3.25%(可懂度最佳);Qwen3-TTS 1.7B 4-bit RTF 0.79;F5-TTS 16-step RTF 0.57;IndexTTS2 clone RTF≈1.0、佔用約 3.0GB。這些在 24GB 記憶體上綽綽有餘(1.7B 量化後約 2.3–3.5GB,0.5B 約 1.9GB)。

## Details:五大類別逐項評估

### 類別一:國際大廠雲端 TTS

**Microsoft Azure AI Speech(建議列為正式方案的「保底」候選)**
- 台灣腔:原生支援 zh-TW 三個神經語音——曉臻(HsiaoChen,女)、曉雨(HsiaoYu,女)、雲哲(YunJhe,男),是市面上少數原生台灣腔的國際大廠。
- 中英混雜:官方明言「所有神經語音都是多語系,而且可流利地使用其自己的語言和英文」,句中英文可直接朗讀;缺點是嵌入英文帶中文口音,術語縮寫(LLM、MCP)與「英文+數字」仍需靠 SSML 的 `<say-as>`/`<sub>`/自訂 lexicon 逐一校正,否則會出現失敗模式 2、3。
- Pipeline 適配:完整支援 SSML、REST 與各語言 SDK,逐段(beat-by-beat)呼叫穩定,固定音色跨段一致性佳,非常適合 beats.json 流程。
- 定價:標準 Neural 每百萬字元 16 美元、新一代 Neural HD 每百萬 22 美元(2026 年 3 月由 30 降至 22);F0 免費層每月 50 萬字元。以每月約 3–4 萬字元(含重試 QA)計,幾乎落在免費額度內,付費也僅約每月 0.5 美元。
- 從台灣申請:完全可以。
- 結論:**最穩、最便宜、合規最單純的「保底正式方案」**,但台灣腔英文發音平淡,不是中英混雜表現最好的。

**ElevenLabs(不建議作為主力,尤其對中英混雜)**
- 台灣腔:v3 有標註 Taiwanese Mandarin 的具名音色(如 Yi Min、James),Audrey 2026 實測「tone and accuracy are pretty good」,但選 v3 時「it somehow switched to a different person's voice?!」音色不穩。
- 中英混雜:多方實測指出致命問題——長文本會「randomly switches accents or languages mid-sentence」,且「expect accent bleeding and pronunciation issues with numbers, dates, and proper nouns」,甚至把「200000」唸成「20 thousand thousand」。這正中失敗模式 2。另有評測指出失敗生成也照樣扣點數,實際成本約標示的 2.8 倍。
- 定價:Creator 方案每月 22 美元含 121k credits(首月促銷 11 美元)。
- 結論:自然度高、克隆最強,但**在「英文+數字」與長文本語言漂移上正是你淘汰過的失敗模式**,不建議當中英混雜主力。

**OpenAI TTS(gpt-4o-mini-tts,不建議作為主力)**
- 台灣腔:內建音色皆以英文為主訓練,官方明言「built-in voices are optimized for English」,無法選台灣腔;Audrey 實測「couldn't find any way to select a different accent」。
- 中英混雜:可切語言,中文只是「reasonable pronunciation」;新版 gpt-4o-mini-tts-2025-12-15 在 Common Voice/FLEURS 上 WER 降約 35%、中文(Mandarin)特別強是加分;但輸入上限 2,000 tokens、長文本(>1–2 分鐘)有隨機停頓/抖動。
- 定價:按 token/音訊時長計費,用量每月低個位數美元。
- 結論:音色非台灣腔是硬傷,只適合快速原型或英文為主節目。

**Google Cloud TTS(Chirp 3: HD / Neural2 / WaveNet,中段候選)**
- 台灣腔:傳統 Neural2/WaveNet/Standard 有 cmn-TW/zh-TW 台灣音色;最新 Chirp 3: HD 生成式音色語言表以 cmn-CN(大陸普通話)為主,台灣/香港中文屬 Preview,台灣腔要退回舊版 Neural2/WaveNet。
- 中英混雜:支援 SSML 與 custom_pronunciations(可用 X-SAMPA 音標覆寫發音,對修正 LLM、MCP、Stage 2 這類特別有用);但舊版台灣音色的中英混雜自然度不如新一代 LLM-based 模型。
- 定價:WaveNet/Neural2 約每百萬字元 16 美元;用量每月約 0.5 美元或落在免費額度。
- 結論:custom_pronunciations 是修正術語發音的利器,但台灣腔只在舊版音色、生成式新音色又偏大陸腔,取捨尷尬。

**Amazon Polly / IBM Watson TTS(淘汰)**:Polly 中文以 cmn-CN(Zhiyu)為主,無台灣腔神經語音,中英混雜弱;IBM Watson 無台灣中文。兩者皆不符第一優先需求。

### 類別二:TTS 新創/專門服務商

**MiniMax(Hailuo)Speech 2.8 / speech-02 / speech-2.5(強烈建議,雲端主力候選)**
- 台灣腔 + 中英混雜:2026 年 Audrey 的台灣腔實測「MiniMax Speech 2.8 leapfrogs the field on Taiwanese-accent naturalness」拿下第一(10,000 人盲測 86.2% approval);更關鍵的是她測中英夾雜句「咦?好我晚點跟同事 sync 一下明天的 schedule」時「it captures that unique, subtle Taiwanese accent even on the English words」——這正是你要的,而且是三種失敗模式裡最難的那類句子。官方另稱 Speech-2.8 在盲測 MOS「ties with ElevenLabs Turbo v2.5」。
- Pipeline 適配:T2A v2 REST API,支援 `<#x#>` 停頓標記、字幕、流式;固定音色或克隆音色跨段一致;逐段合成穩定。
- 定價(已更正):speech-02-hd 約每千字元 0.10 美元(每百萬 100 美元)、Turbo 約每百萬 60 美元;官方稱「at half the cost of ElevenLabs」。你的用量(約 3 萬字/月)每月約 2–3 美元(HD)或約 1.8 美元(Turbo)。
- 從台灣申請:走國際站 api.minimax.io / minimax.io,以國際信用卡付款可用;但 MiniMax 為上海公司,資料落地與法遵須自評。
- 結論:**中英混雜 + 台灣腔的綜合最佳雲端方案**,取捨是中國廠商的合規與資料落地疑慮。

**Cartesia Sonic-3**:15 種語言含普通話,延遲業界最低(40–90ms),但 Audrey 實測「couldn't find anything that indicates a Taiwanese accent」,情感控制也弱,不適合台灣腔旁白。

**PlayHT / Resemble AI / Murf / WellSaid / Deepgram Aura / LMNT / Hume AI**:這幾家主打英文與即時語音代理,中文(尤其台灣腔)與中英混雜非其強項,demo 與社群佐證稀少;WellSaid、Murf、LMNT、Deepgram Aura 中文支援有限或無台灣腔;Hume AI 主打情感英文;Resemble/PlayHT 有克隆但台灣腔中英混雜缺乏可信實測。整體列為次要,不建議作為第一優先。

### 類別三:中國廠商商用 TTS

**阿里雲 Qwen3-TTS-Flash / Qwen-Audio-3.0-TTS(百煉 / DashScope,建議雲端候選之一)**
> 命名須釐清:**Qwen3-TTS** 是開源(Apache 2.0)自架模型家族(0.6B/1.7B,見類別五);**Qwen-Audio-3.0-TTS Flash/Plus** 是另一個 2026 年 7 月發布的閉源、只提供 API 的雲端模型。多數文章把兩者混為一談。
- 中英混雜:社群實測「中英混读流畅自然,无明显『切换卡顿』」,官方 demo 直接示範「這個 feature 真的很 smart!」;10 語種、支援句中多語言混合輸入。是失敗模式 1 表現相對好的一家。
- 台灣腔:內建 49 音色 + 9 種中文方言,但屬大陸普通話腔,**無台灣腔**;雲端版不支援克隆(只能選內建音色),無法用克隆補台灣腔。
- Pipeline 適配:REST/WebSocket、支援 SSML 與流式;逐段呼叫穩定;固定音色跨段一致。
- 定價:Qwen-Audio-3.0-TTS Flash 約每百萬字元 15 美元(OpenRouter、EmpirioLabs 一致;Plus 約 20–27.59 美元,資料源有出入);開通後有 100 萬字元/90 天免費額度、國際站(新加坡)每月 100 萬字免費額度。你的用量幾乎全在免費額度內。
- 從台灣申請:阿里雲「國際站」用非大陸門號(台灣 +886 可)+ Visa/Mastercard/PayPal 註冊,官方文件明言「real-name verification is optional」,只有買大陸境內部署服務才需大陸實名;呼叫時選新加坡地域 API Key,資料落地新加坡。
- 結論:中英混雜佳、幾乎免費、台灣可合法申請,**但缺台灣腔是相對本使用情境的硬傷**;可作為「英文術語密集但可接受大陸腔」時的備援。

**火山引擎(字節跳動)豆包語音 Doubao-Seed-TTS 2.0**:2025 年 10 月發布,官方音色列表明言「支援中文及中英文混合場景」,情感/旁白風格豐富(narrator、professional 等),低延遲流式;但音色為大陸腔,無台灣腔,且台灣申請需火山引擎帳號(實名與跨境金流較 MiniMax/阿里國際站麻煩)。中英混雜成熟,台灣腔缺席。

**騰訊雲 / 百度智能雲 / 訊飛(科大訊飛)開放平台**:三者中英混雜與情感語音技術成熟,但 (a) 皆為大陸腔、無台灣腔;(b) 帳號多需大陸手機號 + 大陸實名 + 大陸金流,台灣申請門檻高、法遵疑慮大。除非用其國際/海外站否則不建議。訊飛超擬人語音合成品質高但同受帳號與腔調限制。

### 類別四:台灣本土廠商/本地化服務(對台灣腔最對症)

**Yating 雅婷(中研院技轉,建議台灣腔候選)**
- 台灣腔:官方明言「提供台灣口音」,是台灣本土最知名的 TTS/STT 團隊;TTS 有雅婷、意晴(女)、家豪(男)三音色。
- 中英混雜:API 音色模型命名為 `zh_en_female_2` 等,明確主打中英雙語;雅婷 STT 端以能辨識「晶晶體」(中英夾雜)著稱,TTS 端中英混雜相對友善,但術語縮寫與「英文+數字」仍需實測。
- Pipeline 適配:REST API,支援 speed/pitch/energy 參數、回傳 base64 音檔,逐段呼叫可行;SSML 支援程度需查其開發者文件。
- 定價:需向雅婷洽詢 TTS API 商用報價(逐字稿 STT 每小時 100 元,TTS 另計)。
- 結論:**台灣腔最道地的本土雲端選項之一**,建議實測中英混雜與術語發音後決定。

**ATEN 優聲學(宏正,建議台灣腔候選)**
- 台灣腔:宏正自研 AI 神經網路 TTS,主打「最擬真、最自然的台灣口音」,6 位聲優(男女聲)。
- 中英混雜:官方宣傳「一個模型完美生成中英文夾雜的句子」,並可自定義破音字讀音、插入停頓、調語速語調——對修正 CLAUDE.md、Stage 2、LLM 這類發音有用。
- Pipeline 適配:提供雲端及離線一站式方案、API 串接與 SDK。
- 定價:免費版每月 2,500 字(不可下載高音質);個人標準版每月 499 元約 3 萬字(約 4 部影片);企業體驗版每月 14,900 元無限量 + 客製聲音克隆。你的用量(約 3 萬字/月)剛好落在個人標準版邊緣。
- 結論:**台灣腔 + 明確主打中英夾雜 + 可調破音字**,是本土最對症的商用方案;取捨是個人標準版字數上限貼近你的用量,重試/QA 重合成可能超額,需觀察或升企業版。

**其他台灣本土**:中華電信有語音合成但偏企業客服整合、自助 API 較不透明;台語 TTS App 與 iMyfone VoxBox 等偏消費端工具,不適合 API pipeline。

### 類別五:可商用開源/自架 TTS(Mac M5 24GB 可行性)

**CosyVoice 3 / CosyVoice 2(自架首選——授權乾淨 + Mac 可懂度最佳)**
- 授權:CosyVoice2-0.5B 開源(Apache 2.0);CosyVoice3 有 Fun-CosyVoice3-0.5B 開放權重(注意:雲端 cosyvoice-v3.5 非開放權重)。對正式商用是乾淨的。
- 中英混雜:阿里通義出品,15 萬小時訓練,跨語言合成強;CS3-Bench 論文即用 CosyVoice2 合成中英混雜語料,顯示其被視為代表性中英模型。
- 台灣腔:大陸腔,靠 zero-shot 克隆補台灣腔。
- Mac 可行性:**Fun-CosyVoice3-0.5B 有 MLX 版,M2 Max RTF≈0.5、M 系列 4-bit round-trip WER 3.25%(受測開源 TTS 中可懂度最佳)**,約 1.9GB,24GB 充足。
- 結論:**Mac 上速度與可懂度最佳、授權最乾淨的自架方案**,建議作為自架主力。

**F5-TTS(自架備選——但商用授權須改用 OpenF5 變體)**
- 中英混雜:官方與多方實測強調「seamless code-switching between English and Chinese within a single generation」,10 萬小時多語;Audrey 2026 列為開源追蹤重點,克隆體驗「lightning fast」。
- 台灣腔:靠 zero-shot 克隆(約 10 秒台灣腔參考音檔)。
- **授權(重要更正)**:原始碼 MIT,但**預訓練權重因用了 Emilia 資料集而是 CC-BY-NC(非商用)**,官方 GitHub 明言「The pre-trained models are licensed under the CC-BY-NC license due to the training data Emilia」。正式商用**不能直接用官方權重**,須改用 Apache 2.0 的 `mrfakename/OpenF5-TTS-Base` 或自行以商用資料重訓。
- Mac 可行性:有 MLX 版,M 系列 16-step RTF≈0.57(快於即時),24GB 充足。
- 基準:論文 LibriSpeech-PC WER 2.42(32 NFE)。
- 結論:中英切換佳、Mac 可跑,但**官方權重非商用**是關鍵陷阱;要商用請務必改用 OpenF5-TTS-Base(Apache 2.0)。

**IndexTTS-2 / IndexTTS-2.5(使用者候選,技術最強但授權是致命前提)**
- 中英混雜:IndexTTS-2 支援中英,社群實測情感遷移驚豔;IndexTTS 2.5 用 GRPO(以 ASR 的 WER 當 reward 微調)降低多語/混語發音錯誤。但技術解讀指出其「指令引導生成」在「中英混說」場景「指令可能有點冗餘,用处不大」。
- 台灣腔:原生大陸腔,靠 zero-shot 克隆(3–15 秒音檔)帶入台灣腔。
- **授權(紅旗)**:IndexTTS 採 bilibili「Model Use License Agreement」,官方 FAQ 明言「Supports non-commercial use; commercial use requires separate commercial license」,商用須寄信 indexspeech@bilibili.com 另談付費授權。對正式商用 podcast 必須先取得商用授權,否則有法律風險。
- Mac 可行性:官方 repo 支援 macOS 的 CPU/MPS(「CUDA is not available on macOS... functionality is preserved」,但較慢);另有社群 mlx-indextts(涵蓋 v1.5、v2.0)。IndexTTS-2.5 的 HF 卡以 NVIDIA 6GB VRAM 為推薦路徑。
- 基準:IndexTTS 2.5 技術報告「lowest average WER (6.75) and the best average speaker similarity (73.18)」為多語冠軍,RL 版再到 WER 6.00 / 相似度 73.63(CV3-Eval),勝過 CosyVoice2、F5-TTS、Qwen3-TTS 1.7B、VoxCPM2、Moss-TTS 1.5;但 WER 上仍略輸 Fish Audio S2 Pro(4B,5.94 WER)。
- 結論:**指標最強,但非商用授權是對正式商用的致命前提**;若願付費取得 bilibili 商用授權且能接受 Mac 上較慢的 MPS 推論,它是品質天花板。

**Qwen3-TTS(開源 0.6B/1.7B,使用者候選)**
- 授權:**Apache 2.0(可商用,最乾淨)**,1.7B 佔 4.54GB、0.6B 佔 2.52GB。
- 中英混雜:與雲端版同源,中英混讀流暢;開源版台灣腔仍需靠參考音檔(須確認其克隆支援),內建音色為大陸腔。
- Mac 可行性:官方 CUDA 導向(texttolab:「No Mac」),但社群 MLX 版(mlx-audio、mlx-audio-plus)已可在 Apple Silicon 跑,M 系列實測 1.7B 4-bit RTF 0.79、round-trip WER 3.47%;0.6B 4-bit 可懂度差(WER 15.58%),建議用 1.7B。
- 結論:授權最乾淨 + Mac 可跑,但台灣腔仍是弱點;作為 Apache 授權的自架備援。

**MediaTek BreezyVoice(台灣本土開源,概念最對症)**
- 台灣腔 + 中英混雜:聯發創新基地專為台灣腔調校,HF 卡明言「BreezyVoice excels at code-switching scenarios」且「outperforms competing commercial services in terms of naturalness」,以注音(bopomofo)輔助發音控制。
- 授權:Apache 2.0(可商用)。
- Mac 可行性:可在筆電上跑,但衍生自 CosyVoice 一代、架構較舊,社群反映「slow and not SOTA」、開頭可能有兩秒靜音、跟不上最新成果。
- 結論:**唯一「台灣腔 + 中英混雜 + Apache 商用」三合一的開源模型**,概念上最對症,但品質/速度落後 CosyVoice3、F5-TTS,建議實測比較。

**其他開源(多數不建議作為主力)**:
- GPT-SoVITS:克隆強、社群大,中英混雜可,但授權/訓練資料合規較模糊,穩定性吃調校。
- Fish-Speech(fishaudio):中英日,論文克隆 WER 6.89 優於 F5/CosyVoice,但**授權為 CC-BY-NC-SA(非商用)**,自架不可商用——淘汰(自架商用),要商用只能付費用其雲端。
- XTTS-v2(Coqui):Coqui 已停運,授權非標準商用,中英混雜一般,不建議。
- Kokoro:輕量、Mac 上 RTF 0.17 最快,Apache 授權,但中文/中英混雜/台灣腔弱,適合純英文。
- Bark、Parler-TTS、StyleTTS2、OpenVoice、ChatTTS、Spark-TTS、MeloTTS:中英混雜或台灣腔皆非強項,或授權/穩定性不足,列為次要。

## 總結比較表(依「中英混雜表現」為第一排序)

| 排名 | 方案 | 中英混雜 | 台灣腔 | 失敗模式風險 | 授權/商用 | Mac M5 24GB | 每月約成本(~3萬字) | 台灣可申請 |
|---|---|---|---|---|---|---|---|---|
| 1 | **MiniMax Speech 2.8 HD**(雲端) | 極佳(實測連英文帶台灣腔) | 佳(實測第一) | 低 | 商用 API | 不需本地 | ~US$2–3 | 國際站可 |
| 2 | **CosyVoice3 0.5B**(自架,克隆) | 佳 | 靠克隆 | 中低 | **Apache 2.0** | ✅ MLX RTF≈0.5,WER 3.25% | 電費 | 直接下載 |
| 3 | **ATEN 優聲學**(台灣本土雲端) | 佳(主打中英夾雜、可調破音字) | 極佳(原生) | 低 | 商用訂閱 | 不需本地 | NT$499(3萬字) | ✅ 台灣廠商 |
| 4 | **F5-TTS / OpenF5**(自架,克隆) | 佳(seamless 中英) | 靠克隆 | 中低 | 官方權重 **CC-BY-NC**;商用須用 OpenF5(Apache) | ✅ MLX RTF≈0.57 | 電費 | 直接下載 |
| 5 | **Azure zh-TW**(雲端保底) | 中(需 SSML 校正縮寫/數字) | 極佳(原生 zh-TW) | 中(需 SSML) | 商用 API | 不需本地 | ~US$0.5 或免費 | ✅ |
| — | Qwen3-TTS(開源/Qwen-Audio-3.0 API) | 佳 | 弱(大陸腔) | 低 | Apache 2.0 / API | ✅ MLX 1.7B | 免費額度內 | 國際站可 |
| — | IndexTTS-2.5(自架) | 佳(指標最強) | 靠克隆 | 低 | **非商用,商用需另談付費** | ⚠️ MPS 慢/NVIDIA 佳 | 電費+授權費 | 直接下載 |
| — | ElevenLabs v3 | 差(語言漂移、數字唸錯) | 有具名音色但不穩 | **高(正中失敗模式2)** | 商用 API | 不需本地 | ~US$22 | ✅ |
| — | OpenAI gpt-4o-mini-tts | 中(中文改善但英文音色) | 無 | 中 | 商用 API | 不需本地 | 低個位數美元 | ✅ |
| — | BreezyVoice(台灣開源) | 佳(官方稱 excels) | 極佳(原生) | 低 | Apache 2.0 | ✅ 但慢 | 電費 | 直接下載 |

## Recommendations(分階段、可執行)

**第 0 階段(1 天,建立評測夾具)**:把既有的 Whisper 回轉驗證流程直接當成「中英混雜正確率」的自動評測。用 5–10 個代表句(含「Stage 2」「fallback 到 BERT」「一份被 checked in 的 CLAUDE.md」「rm -rf」「ρ = -0.44」「LLM/MCP/RLHF/SFT/CoT」)對每個候選各合成一次,用 Whisper STT 回轉算字錯率 + 人耳確認三種失敗模式。這是選型的黃金標準,勝過任何廠商宣傳。

**第 1 階段(平行實測 3 雲端 + 2 自架)**:
- 雲端:MiniMax Speech 2.8 HD(國際站)、Qwen-Audio-3.0-TTS Flash(阿里新加坡節點,免費額度)、ATEN 優聲學(個人標準版試用)。
- 自架:CosyVoice3 0.5B(MLX)、OpenF5-TTS-Base(MLX);兩者各餵一段你有合法使用權的台灣腔參考音檔。
- 全部用第 0 階段夾具跑同一批句子,比對 Whisper 回轉字錯率與失敗模式命中數。

**第 2 階段(決策)**:
- 若「商用合規單純 + 最省事 + 台灣腔英文最好」最重要 → **選 MiniMax Speech 2.8 HD**,先做資料落地/法遵確認(內容是公開部落格文章,敏感度低,通常可接受)。
- 若「資料不出境 + 授權乾淨 + 長期壓成本」最重要 → **選 CosyVoice3 0.5B 自架**(Apache 2.0,Mac 上最快最可懂),用固定台灣腔參考音檔確保跨集音色一致;F5-TTS 僅在改用 OpenF5(Apache)權重時才可商用。
- 若「要台灣廠商、開發票、在地支援」最重要 → **選 ATEN 優聲學**(注意 3 萬字/月上限貼近用量,重試多會超額,必要時升企業版)或洽 Yating 雅婷商用報價。
- **保底**:無論選哪個,都以 **Azure zh-TW + SSML 自訂發音詞典** 作為 fallback,術語(LLM、MCP、RLHF)一律進 lexicon 強制發音。

**會改變建議的門檻**:
- 若 MiniMax 的資料落地/法遵無法通過你的內部要求 → 降級到 CosyVoice3 自架。
- 若 CosyVoice3/OpenF5 克隆的台灣腔在 Whisper 回轉字錯率 > 5% 或英文縮寫命中失敗模式 3 → 改用 ATEN 優聲學(原生台灣腔 + 破音字自訂)。
- 若你願意付費取得 bilibili 商用授權 → IndexTTS-2.5 的品質天花板值得重新評估(多語 WER 6.00 幾乎全場最低,僅略輸 Fish Audio S2 Pro 的 5.94)。

## Caveats
- **中英混雜品質高度吃「輸入端正規化」**:即使最好的模型,LLM、MCP、Stage 2、rm -rf、ρ = -0.44、SC@64 這類 token 都建議在 beats.json 階段先做正規化(縮寫改成模型友善拼寫、數字明確標注、希臘字母/符號改寫),再交給 TTS,能大幅降低三種失敗模式,這比換模型更有效。
- **台灣腔在多數國際/大陸方案是靠克隆補的**:MiniMax、IndexTTS、CosyVoice、F5-TTS、Fish-Speech 的「台灣腔」品質取決於你提供的參考音檔;務必用一段乾淨、道地、你有合法使用權的台灣腔音檔。
- **授權紅旗**:IndexTTS-2/2.5 為非商用授權(商用須寄信另談付費)、**F5-TTS 官方預訓練權重為 CC-BY-NC(非商用,商用須改用 OpenF5-TTS-Base 的 Apache 權重)**、Fish-Speech 為 CC-BY-NC-SA(自架不可商用)、XTTS-v2/Coqui 授權非標準商用——這幾者切勿在未取得授權下用於正式商用 podcast。相對地,CosyVoice2/3、Qwen3-TTS、BreezyVoice 為 Apache 2.0 可放心商用。
- **中國廠商合規**:即使走國際站(新加坡)可從台灣申請付款,資料仍落地境外,服務條款、可用性、跨境金流政策可能變動,簽約前確認 SLA 與資料處理條款。
- **價格與模型版本變動快**:TTS 領域半年一大改(Audrey 語:「三年 AI 進展 ≈ 九年前 AI 世界」),本報告價格與版本以 2026 年 9 月可得資料為準,採購前請以各廠商官方定價頁最終確認。MiniMax 各轉售平台單價有出入($0.05–0.10/千字元皆有見),以官方為準。
- **部分數據為廠商自報**:Qwen-Audio-3.0-TTS 的 WER 3.87、說話人相似度 82.75 等為廠商自報未經獨立驗證;IndexTTS/F5/Fish 的數字來自 arXiv 論文較可信,但各家測試集與 ASR 評測工具(FunASR vs Whisper-large-v3)不同,跨論文數字不可直接對比。
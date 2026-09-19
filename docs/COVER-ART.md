# 節目封面

**已定案。** 中英兩個節目共用同一張。

```
thumbnail/cover-3000.jpg   3000×3000 · RGB · 3.2 MB · 上傳用這個
thumbnail/v4.png           1254×1254 · 生成原檔,唯一的母帶
```

需要無損的 3000px PNG 時重建(不進版控,13.6 MB):

```bash
uv run --with pillow --no-project python -c "
from PIL import Image
Image.open('thumbnail/v4.png').convert('RGB').resize((3000,3000), Image.LANCZOS)\
     .save('thumbnail/cover-3000.png','PNG',optimize=True)"
```

規格要求:**3000×3000、正方形、RGB**(Apple 明確要求,不能 CMYK)、JPG 或 PNG。
Apple 與 Spotify 通用。

---

## 唯一有意義的驗收:縮到 150 px 和 55 px 看

podcast app 裡封面多半以 **55–150 px** 顯示。在 3000 px 好看不算數。

```bash
uv run --with pillow --no-project python -c "
from PIL import Image
im=Image.open('thumbnail/v4.png')
for px in (150,55): im.resize((px,px), Image.LANCZOS).save(f'/tmp/t{px}.png')"
```

現況:150 px 標題清楚可讀;55 px 標題成輪廓,但金色光點辨識度仍強
(那個尺寸下沒有任何 podcast 封面的字讀得出來,不是缺點)。

## 概念

一條鉛垂線垂入分層的水中,末端的黃銅錘像一盞燈,光往四周水層暈開。

選它不是為了扣節目名裡的 Ocean,而是**扣節目的姿態**:差異化在於誠實指出
論文沒說清楚的地方、自己下去量一遍實際有多深,而不是相信宣稱的數字。
測深線就是「實際量一次」這個動作。

配色刻意沿用片頭曲盲測選出來的性格 —— **暖的木質與氈質,不是亮的玻璃感**,
所以是暖奶油、水藍、青綠、黃銅琥珀,不是科技藍或霓虹。封面與片頭曲是同一套
感官語言。

## 最終 prompt

```
A square 1:1 screen-printed risograph poster illustration of the deep sea,
warm and inviting rather than sombre.

The top third of the poster is a calm band of warm cream paper. Printed
across it in deep teal ink, in a clean geometric sans-serif with generous
letter spacing, are the words "DataSci Ocean" — set as part of the print,
with the same halftone grain and slight ink misregistration as the artwork,
never as a crisp digital overlay.

Below the title, horizontal bands of water descend from bright aqua through
warm teal to a deep but never black blue-green at the bottom. A slender
brass plumb line drops from the title area down into the water. At its end
hangs a small brass weight that glows like a lantern. Its light is a soft,
diffuse, volumetric halo of warm amber that bleeds outward into the
surrounding bands of water and warms them from within, fading gradually
into the teal. The glow has no hard edges and no visible beams.

Flat bold shapes, limited palette of warm cream, aqua, teal, deep blue-green
and brass amber. Visible halftone dots, paper grain, slight ink
misregistration. Few elements, strong contrast, generous margins, calm,
warm, optimistic.

The only text in the image is "DataSci Ocean", spelled exactly that way.
No bubbles. No light rays, no starburst, no sunbeams, no lens flare, no
sparkles. No other words, no letters, no numbers, no logo, no people. Not
photorealistic, no 3D render, no glowing circuitry, no neural network
diagram, no robot, no brain.
```

最後那段否定詞不是裝飾。AI 生成的「科技 podcast 封面」預設會給你發光大腦、
電路板、神經網路節點圖 —— 那類最沒有辨識度,而且細節多,縮小就變成一團雜訊。

---

## 三輪踩到的坑(都會在下次做視覺素材時重演)

### 一、細線在縮圖會直接消失

第一版的鉛垂線寬度是**全寬的 0.40%**。換算:

| 顯示尺寸 | 線寬 |
|---|---|
| 3000 px | 12 px ✓ |
| 150 px | **0.6 px** |
| 55 px | **0.22 px** |

55 px 時完全不見。**任何細於全寬 1% 的元素都不要指望它在縮圖存在。**
最終版改成靠「深水中一顆金色光點」當識別記號,那個在 55 px 依然成立。

### 二、紙邊框的兩種情況,判斷相反

- **第一版**:米色是包在滿版插圖外面的**空框**,平台滿版顯示又加圓角,
  它會被讀成裁切失誤 → **要裁掉**。
- **最終版**:米色是**標題印在上面的紙**,是版面的一部分,而且那圈約 4.5%
  的邊距正好把標題擋在圓角裁切區之外 → **要留著**。

判準不是「有沒有邊框」,是「那塊留白有沒有在做事」。

### 三、自己排字會跟插圖打架

第一版把 Avenir 疊在插圖上,看起來很突兀。原因不是選錯字型 ——
**整張圖都有油墨顆粒、網點、套印偏移,只有字是完美銳利的數位字。**
那個質感落差才是違和感的來源。

所以最後讓圖像模型**把字一起印出來**,字自動帶到同樣的油墨質感
(最終版的標題帶著紅色套印偏移邊,和插圖同一次印刷)。

代價是**拼字風險**:`DataSci Ocean` 常見錯誤是拆成 `Data Sci`、大小寫跑掉、
多一個字母。**每次重生都要逐字看過。**

若堅持自己排字,關鍵不是選字型,是**別讓字太乾淨** —— 疊一層很淡的顆粒,
或把不透明度降到 92% 左右讓紙紋透出來。

### 四、`rays` 這個字會生出星芒

第三版寫了 `radiates outward in gentle rays`,結果生出**幾何星芒**。
問題是風格不一致:整張圖是大氣式的柔和漸層,星芒是海報圖形語彙,
而且光在水裡是體積式擴散,不會打出硬邊輻條。

改成 `soft, diffuse, volumetric halo … no hard edges and no visible beams`,
並把 `no light rays, no starburst, no sunbeams, no lens flare` 加進否定清單。

### 五、加元素之前先想因果

第三版加了氣泡想讓畫面活潑,結果 Johnny 覺得「有點好笑」。
原因是**鉛錘是一塊惰性金屬,它不會冒泡** —— 看起來像它在打嗝。
而且氣泡沿繩排成一列、大小規律,像一串珍珠而不是水裡自然的氣泡。

活潑感最後是靠**調色**達成的(整體提亮一階、最深層從近黑改深青綠、
上層推到亮水藍),不需要多加元素。

---

## 中英兩版

**共用同一張,不做兩張。** 兩個節目在平台上靠節目名與描述區分,封面同源
反而幫忙建立識別 —— 聽眾看得出是同一個作者。

(`<language>` 是 RSS 節目層級的單一欄位,所以必須開兩個獨立節目,
這是平台限制,與封面無關。見 `plan.md` 第八章。)

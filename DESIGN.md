---
name: 运河人物志
description: 墨染运河——宣纸白、黛绿、松烟墨构成的沉浸式人物河图
colors:
  paper: "#faf7f2"
  paper-deep: "#f4f1ea"
  surface: "rgba(250, 247, 242, 0.86)"
  ink: "#2b2b2b"
  ink-soft: "#6f6a63"
  teal: "#2c5e5a"
  teal-deep: "#1e423f"
  line: "rgba(44, 94, 90, 0.15)"
typography:
  display:
    fontFamily: "Source Han Serif SC, Noto Serif SC, Songti SC, STSong, serif"
    fontSize: "clamp(32px, 4.1vw, 58px)"
    fontWeight: 700
    lineHeight: 1.16
    letterSpacing: "0.12em"
  title:
    fontFamily: "Source Han Serif SC, Noto Serif SC, Songti SC, STSong, serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.16
    letterSpacing: "0.04em"
  body:
    fontFamily: "system-ui, -apple-system, Segoe UI, PingFang SC, Microsoft YaHei, Noto Sans SC, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.8
  label:
    fontFamily: "system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  control: "8px"
  card: "12px"
  segmented: "10px"
  pill: "999px"
  portrait: "50%"
shadows:
  paper: "2px 2px 0 rgba(44, 94, 90, 0.05), 5px 5px 0 rgba(44, 94, 90, 0.03)"
  float: "3px 3px 0 rgba(44, 94, 90, 0.06), 8px 8px 0 rgba(44, 94, 90, 0.04)"
components:
  button-primary:
    backgroundColor: "{colors.teal}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    height: "42px"
  surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    border: "{colors.line}"
  inspector:
    backgroundColor: "rgba(250, 247, 242, 0.82)"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    width: "min(470px, calc(100% - 44px))"
---

# Design System: 运河人物志 · 墨染运河

## Overview

**Creative North Star: “可进入的墨染河图”**

运河人物志是一册建立在真实地理上的沉浸式河图。经过古风降饱和处理的高德地图是入口，一条连续的黛绿运河线路先建立空间叙事；苏轼、陈瑄、张伯行不是目录卡片，而是落在徐州、淮安、苏州真实地点上的人物门扉。用户先读河、再发现人、选择一人，最后进入只属于该人物与地点的私密对话。

视觉世界由宣纸白、黛绿与松烟墨构成。地图保持历史厚重感，界面用温润的纸质表面、细若游丝的墨线边框与克制的双层硬阴影模拟纸张重叠；进入聊天后，人物身份、地点与会话保持锁定，不把地图页的多人选择带进对话。

**Key Characteristics:**

- 真实高德地图经过浅色样式与宣纸晕染处理，突出运河水系而非现代道路网络。
- 一条连续黛绿水路连接三个真实地点，圆形纪实肖像承担人物识别。
- 印章、选中点与错误状态统一使用黛绿，不引入第二强调色。
- 宋体标题与无衬线正文分层：古典韵味留在姓名与标题，功能文字保持现代易读。
- 地图和单人物聊天是两个清晰状态，通过 URL hash 保留可直接进入的人物身份。

## Colors

宣纸背景与带墨意的中性色构成安静的地理底盘；黛绿是唯一的交互强调与印章级点缀。

### Primary

- **黛绿**：用于连续河线、选中状态、图标、焦点和主要动作。
- **深黛绿**：用于主按钮悬停端与高对比交互面。

### Neutral

- **宣纸白**：全屏环境底色与主要背景。
- **宣纸深**：次级表面与地图瓦片加载前的底色。
- **纸面半透明**：毛玻璃质感的内容表面，配合发丝墨线与细白边使用。
- **松烟墨**：主要文字、标题与品牌标记的基础色。
- **松烟灰**：次级文字、地点说明、占位符与未选中控制。
- **发丝墨线**：低对比边框，承担结构分隔而非强调。
**The One Teal Rule.** 路线、选中、主动作、印章与焦点只使用黛绿家族，不引入第二强调色。

**The Map Stays Quiet Rule.** 地图瓦片降低饱和度与对比度并偏向宣纸色，使地名仍可定位，但不会压过人物和运河线路。

## Typography

**Display Font:** Source Han Serif SC / Noto Serif SC，回退至 Songti SC、STSong 与系统衬线；用于地图主标题、人物姓名和对话中的人物引语。

**Body Font:** 系统无衬线栈，用于正文、标签、控件、地址与地图署名，保证现代感与微型可读性。

**Character:** 宋体标题 + 无衬线正文；人物消息使用宋体以呈现书信质感，用户消息使用无衬线以区分现代阅读侧。

### Hierarchy

- **Display**（700，流体 32–58px，1.16，0.12em）：地图主标题；短行、加宽字距。
- **Title**（700，24–27px，1.16）：人物姓名；移动端降至 23px / 21px。
- **Body**（400，14px，1.8）：连续对话与说明文字。
- **Label**（600，11px）：地点、朝代、模式与按钮。

**The Names Lead Rule.** 人物姓名与地点关系先于朝代、别号和解释文本；不用英文大写微标签制造伪编辑感。

## Layout

桌面地图页使用 100dvh 双行框架：18px 外框、56px 顶栏与 12px 间隙，其余空间交给真实地图。地图标题位于左上，人物检视器固定在左下，检视器宽度不超过 470px。

聊天页桌面采用 3:5 双栏：左栏约 34% 展示人物画像、生平纪略与当前足迹，右栏约 66% 承载对话流；对话列最大宽度约 680px，形成信笺式排版。背景使用毛玻璃宣纸，让水墨背景自然过渡到视觉中心。

在 900px 以下，聊天双栏收为单列，人物上下文缩为紧凑顶栏；在 760px 以下，地图与聊天移除外框和壳体圆角，顶栏贴边，检视器缩为底部单卡。420px 以下进一步收紧，320px 为最小支持宽度。

**The One Inspector Rule.** 第一视口只允许一个选中人物检视器和一个进入动作；其余人物保持地图标记，不变成卡片网格。

## Elevation & Depth

系统采用“扁平纸叠”的深度。不用现代弥散投影，改用 2px / 5px 或 3px / 8px 的双层硬阴影模拟纸张重叠；毛玻璃只属于导航、检视器、人物卡与对话壳，不把静态内容切成多层玻璃卡片。

### Shadow Vocabulary

- **纸叠**（`2px 2px 0 … , 5px 5px 0 …`）：顶栏、消息、输入器等常规表面。
- **悬浮纸叠**（`3px 3px 0 … , 8px 8px 0 …`）：选中人物检视器。

## Shapes

系统以 8–12px 圆角为常态：按钮与地图小控件 8px，主要表面 12px，分段控件 10px，推荐问题胶囊 999px。圆形只用于地图人物肖像、印章点与加载点。用户与人物消息使用不对称 4px / 12px 角，轻微指向发言一侧。

## Components

### Real Canal Map

- 使用高德 JS API 2.0，地点数据统一采用 GCJ-02 `[lng, lat]`，不做坐标体系混用。
- 运河以 14px 浅黛绿底线叠加 4px 黛绿主线绘制，保持一条从徐州经淮安、苏州继续向南的连续水路。
- 地图叠加宣纸色晕染与内收暗角；高德原生缩放与品牌标识始终保留。

### Character Marker

- 58px 圆形纪实肖像连接带姓名和城市的 8px 圆角标签；三位人物独立可发现、可点击并可键盘聚焦。
- 选中标记通过黛绿双环和深黛绿标签表达；姓名和城市始终可读。

### Character Inspector

- 桌面为 470px 以内的两列宣纸面板，包含 138px × 184px 肖像、姓名、朝代、城市、人物引语、真实地点和地址。
- 唯一主按钮位于信息列底部，使用黛绿纯色，并明确进入当前人物的锁定会话。

### Character Context

- 聊天页左栏展示 74px × 92px 微缩画像、黛绿印章、人物 active_time、两条生平纪略与当前足迹。
- 当前足迹以黛绿圆点 + 宋体地点名表达，附真实地址。

### Buttons

- **Primary:** 8px 圆角、白字、黛绿纯色；悬停切换为深黛绿。
- **Ghost:** 透明底与黛绿文字；悬停以浅黛绿底和深黛绿文字回应。
- **Focus:** 所有按钮使用 2px 深黛绿外轮廓、3px 偏移；地图标记使用 2px 轮廓、4px 偏移。
- **Disabled:** 发送按钮降至 45% 不透明度，并移除指针暗示。

### Mode Switch

- 双列黛绿浅底分段控制，外层 10px、内按钮 8px；选中项为黛绿和白字。
- 移动端压缩至 126px；切换模式会重置当前人物的会话，不改变人物身份。

### Messages

- 人物消息为宣纸白底加发丝墨线，用户消息为黛绿纯色；两者通过不对称圆角区分方向。
- 回复只渲染受限 Markdown：普通段落、以 `>` 开头的引用和 `**…**` 粗体。禁止注入原始 HTML 或通用 Markdown 解释器。
- 忙碌态使用三个黛绿小点；错误使用克制的黛绿提示，不扩展为模态框。

### Suggestions and Composer

- 推荐问题是 28px 高、横向可滚动的宣纸胶囊短按钮，不占用消息阅读空间。
- 输入器桌面最小高度 64px，内含无边框 textarea 和 46px 方形发送按钮；`focus-within` 提升边线。移动端分别降至 58px 和 42px。

### Navigation and Routing

- 地图顶栏只承载品牌与“京杭大运河人物图”语境；聊天顶栏只承载返回地图、居中品牌和新会话。
- 聊天路由使用 `#chat/{character-id}`，直接打开时恢复对应人物；聊天内部不提供切换其他人物的入口。

## Do's and Don'ts

### Do:

- **Do** 让真实地图、连续运河、三位地点人物、一个选中检视器和一个主动作共同定义第一视口。
- **Do** 把每位人物绑定到可验证地点，并让地图数据统一使用 GCJ-02 `[lng, lat]`。
- **Do** 用宋体承载人物姓名、标题与人物消息，用无衬线承载功能文字与用户消息。
- **Do** 提供可见焦点、语义标签、减少动态效果和减少透明度回退。
- **Do** 保持单人物会话锁定，并用安全的有限 Markdown 渲染回复。

### Don't:

- **Don't** 用人物卡片目录、仪表盘或静态示意图替代真实河图入口。
- **Don't** 让检视器遮住必需人物、运河线路、缩放控件或地图署名。
- **Don't** 在聊天页直接切换人物，或让一个会话混合多个人物身份与记忆。
- **Don't** 使用第二强调色、装饰性渐变文字、超大圆角、大面积弥散阴影或无功能的玻璃装饰。
- **Don't** 隐藏原始地图归属信息、依赖纯颜色表达选择，或在减少动态效果时保留飞入动画。

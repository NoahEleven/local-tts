---
name: local-tts
version: 1.1.0
description: 文本转语音（TTS）。三条通道：edge-tts（微软神经网络语音，免费无需 key，15 个中文音色可用）、Azure Speech 官方 API（75 个中文音色全解锁，含晓秋/晓辰/HD/MAI，50 万字符/月免费）、pyttsx3（Windows SAPI 离线兜底）。当用户/agent 需要把文本转成语音文件（mp3/wav）、生成语音播报、配音、解锁被 edge-tts 封锁的音色时使用。
---

# Local TTS（文本转语音）

把任意文本转成本地音频文件，给 agent 或脚本调用。

> ⚠️ **默认行为**：不传任何参数 = **联网 edge-tts + 晓晓女声**（`zh-CN-XiaoxiaoNeural`）。只有显式加 `--offline` 才走离线引擎。这是唯一默认。

> 📌 **选型原则（2026-08-10 定稿）**：**只用云端托管 TTS，免费无需注册优先**。不部署任何本地开源模型（Kokoro/CosyVoice 等一律不装），pyttsx3 仅作断网最后兜底。

> ☁️ **Azure 通道（2026-09-18 打通）**：edge-tts 拿不到的音色（晓秋/晓辰/晓涵等）走 Azure 官方 API，**75 个中文音色全通**。凭据见「Azure 官方通道」章节。

## 三条通道

| 通道 | 音色数 | 音质 | 联网 | 成本 | 何时用 |
|---|---|---|---|---|---|
| **edge-tts**（默认） | 15 个中文可用 | ⭐⭐⭐ 神经网络 | 需要 | 免费无 key | 默认、通用播报 |
| **Azure 官方** | **75 个中文全通** | ⭐⭐⭐~⭐⭐⭐⭐⭐（含 HD） | 需要 | 50 万字符/月免费 | 要 edge-tts 封锁的音色 / HD / 情感风格 |
| **pyttsx3**（`--offline`） | 1 个（Huihui） | ⭐ 老式合成音 | 完全离线 | 免费 | 断网兜底 |

## 用法（edge-tts / 离线）

```bash
# 基础用法：edge-tts 神经网络语音（默认晓晓女声），未指定 -o 则存 tts_output/
python scripts/tts.py "要合成的文本" -o 输出路径.mp3

# 生成后自动播放（转 wav 用 winsound 同步播放，阻塞到播完，不弹窗）
python scripts/tts.py "文本" -o out.mp3 --play

# 指定音色 / 语速 / 音量（倍率 0.5~1.5）
python scripts/tts.py "文本" -o out.mp3 -v zh-CN-YunxiNeural -r 1.1 --volume 1.2

# 强制离线引擎（断网可用）
python scripts/tts.py "文本" -o out.wav --offline

# 列出 edge-tts 全部可用音色
python scripts/tts.py --list-voices
```

## ☁️ Azure 官方通道（2026-09-18 打通）

**用途**：edge-tts 免费通道对较新一批中文音色做了封锁（返回 `NoAudioReceived`），
Azure 官方 API 是**唯一解锁路径**，且音色库大 5 倍。

### 凭据位置（保密，勿外传）

按优先级查找，任选一处即可：
1. 环境变量 `AZURE_SPEECH_KEYS_FILE` 指向的路径
2. `scripts/keys.env`（脚本同目录）
3. skill 根目录 `keys.env`
4. `~/.workbuddy/azure_speech.env`（全局兜底）

文件格式：
```
AZURE_SPEECH_KEY=<密钥>
AZURE_SPEECH_REGION=eastasia
```

> 🔒 **保密铁律**：`keys.env` 不进版本控制、不写入可对外文件、不发第三方。本仓库已加 `.gitignore` 防呆。

### 用法

```bash
# 单条
python scripts/azure_tts.py --text "要合成的文本" \
    --voice zh-CN-XiaoqiuNeural --out out.mp3

# 批量（JSON 结构：{"segments":[{"text":"第 1 段"},{"text":"第 2 段"}]}，
# 也兼容 slides 数组及 narration/vo 字段，输出 01.mp3 ~ N.mp3）
python scripts/azure_tts.py --json script.json --voice zh-CN-XiaoqiuNeural --outdir audio_out

# 列全部 75 个中文音色（含官方标签与风格）
python scripts/azure_tts.py --list-zh
python scripts/azure_tts.py --list-zh --voice xiaoqiu    # 只看某个

# 语速/音调/音量/情感风格（SSML prosody + mstts:express-as）
python scripts/azure_tts.py --text "..." --out o.mp3 --rate +10% --pitch +0Hz --style newscast
```

### 关键事实（实测）

- **终结点必须用区域终结点**：`https://{region}.tts.speech.microsoft.com/cognitiveservices/v1`
  - ⚠️ 门户给的 Foundry 终结点（形如 `https://xxx.services.ai.azure.com/`）**不能用于标准 TTS 调用**，这是最容易踩的坑
- **请求头**：`Ocp-Apim-Subscription-Key` + `Content-Type: application/ssml+xml` + `X-Microsoft-OutputFormat`
- **免费额度**：F0 层 **50 万字符/月**（每月重置）。**只算朗读字符**——实测 1800 字脚本文档配音约 1000 字 → 额度够约 500 期
- **计费分档**：标准音色（`*Neural`）在免费额度内；**DragonHD 系列与 MAI-Voice-2 系列按量计费，不在免费额度内**，用前先确认
- **75 个中文音色分档**：标准版 38 · 多语言版 8 · DragonHD 闪电版 21 · MAI-Voice-2 8

### 知性女声推荐

| 音色 ID | 标签 | 备注 |
|---|---|---|
| `zh-CN-XiaoqiuNeural` | Calm, Engaging, Soothing | **晓秋**，知性治愈，无风格标签（靠 prosody 调） |
| `zh-CN-XiaoxiaoNeural` | Warm, Well-Rounded | 晓晓，**20 种风格**（newscast/calm/gentle…） |
| `zh-CN-XiaochenNeural` | Friendly, Casual, Upbeat | 晓辰 |
| `zh-CN-XiaohanNeural` | Gentle, Warm, Emotional | 晓涵，10 种情感 |
| `zh-CN-XiaomoNeural` | Deep, Casual, Calm | 晓墨，低沉知性 |
| `zh-CN-XiaoruiNeural` | Confident, Emotional, Hoarse | 晓睿，沙哑质感 |
| `zh-CN-XiaozhenNeural` | Calm, Serious, Confident | 晓臻，沉稳 |

## 🔈 自动播放方案（`--play`）

> ⚠️ **内容红线**：语音只播报**最终总结/结论内容**。**严禁**播放思考过程、执行过程、工具调用过程、中间日志。若任务无总结，则不播。

**播放链路（已固化）**：文本 → 生成 mp3/wav →（mp3 则 ffmpeg 静默转 wav 到系统 temp）→ `winsound` **同步**播放（阻塞到播完）→ 清理 → 退出。

**技术要求**：
- 统一 mp3→wav 静默转码（imageio-ffmpeg 隔离版）→ winsound **同步**播放
- **不用** `SND_ASYNC`：agent 调用是「生成即退」短进程，异步播放会在进程退出时被掐断 → 听不到声音
- **不检查** `winsound.PlaySound` 返回值（成功返回 `None`，失败抛异常）
- 不弹窗、不残留临时文件（转码走系统 temp 的 `local_tts_play.wav`）

**三种触发方式**：
- **A · 单次播报** → 命令加 `--play`（已实现）
- **B · 会话级语音回复** → 用户说"用语音回复"，agent 每次回复末尾对**总结段落**带 `--play`；只播总结不播过程；启停由会话约定，不写死进脚本
- **C · 定时任务播报** → automation 执行完对**摘要文本**（不是执行日志）TTS + `--play`

## 🚨 音色可用性：双通道对照（2026-09-18 实测）

**`--list-voices` 返回的音色 ≠ 实际能合成的音色。** edge-tts 服务端对较新一批中文音色做了封锁（返回 `NoAudioReceived`）。
**先查下表，别照 list 盲选**；要用的音色在右列被封锁 → 直接走 Azure 通道。

### ✅ edge-tts 可用（15 个）

| 音色 ID | 说明 |
|---|---|
| `zh-CN-XiaoxiaoNeural` | 晓晓，女，万金油 |
| `zh-CN-XiaoyiNeural` | 晓伊，女，活泼 |
| `zh-CN-XiaoxuanNeural` | 晓萱，女 |
| `zh-CN-YunxiNeural` | 云希，**男**（网文常误写为女声，注意） |
| `zh-CN-YunjianNeural` | 云健，男，浑厚 |
| `zh-CN-YunyangNeural` | 云扬，男，新闻播报 |
| `zh-CN-YunxiaNeural` | 云夏，男，少年 |
| `zh-CN-liaoning-XiaobeiNeural` | 晓北，女，东北话 |
| `zh-CN-shaanxi-XiaoniNeural` | 晓妮，女，陕西话 |
| `zh-HK-HiuGaaiNeural` / `HiuMaanNeural` / `WanLungNeural` | 粤语（女/女/男） |
| `zh-TW-HsiaoChenNeural` / `HsiaoYuNeural` / `YunJheNeural` | 台湾国语（女/女/男） |

### ❌ edge-tts 被拒（14 个 → 走 Azure）

`Xiaochen` `Xiaohan` `Xiaomeng` `Xiaomo` `Xiaoqiu` `Xiaorui` `Xiaoshuang` `Xiaoyan`
`Xiaoyou` `Xiaozhen` `Yunfeng` `Yunhao` `Yunye` `Yunze`

**规律**：可用 = 较早期一批；被拒 = 较新一批。上列 14 个**在 Azure 通道全部可用**（Azure 共 75 个中文音色全通）。

### ⚠️ 间歇性限流（edge-tts）

即使是可用音色也可能**临时被拒**：实测云希 `+35%` 成功、`+0%` 连试 3 次全败。
→ **务必保留退避重试**（脚本已内置），别因单次失败就换音色。Azure 通道无此问题。

### 音色自检脚本

```bash
python scripts/probe_voices.py              # 探测内置快照清单（edge-tts）
python scripts/probe_voices.py --all-zh     # 探测全部 zh-* 音色（慢）
python scripts/probe_voices.py --voice zh-CN-XiaochenNeural   # 只测一个
python scripts/azure_tts.py --list-zh       # Azure 端权威音色清单
```

## 环境

- 依赖：`pip install pyttsx3 edge-tts imageio-ffmpeg`（Azure 通道零第三方依赖，纯标准库）
- **模块级 `import` 延迟到函数内**：`--list-voices`/`--offline` 等场景不会因缺依赖而整体崩溃

## 输出文件规范（agent 调用时遵守）

- **输出路径**：调用方显式指定 `-o`；未指定时固定生成到 **本 skill 目录下 `tts_output/`**（用脚本 `__file__` 定位，与调用时工作目录无关）
- **命名**：建议语义化命名（如 `20260918_新闻早报.mp3`），不用乱码/序号
- **格式**：联网引擎 → `.mp3`；离线引擎 → `.wav`
- **临时转码文件**：`--play` 的转码 wav 放系统临时目录，**不会**留在工作区
- **测试产物**：不把测试音频留在工作区根目录；确认后清理

## 坑

- **edge-tts 需能访问微软服务器**；失败时自动降级 pyttsx3 离线引擎（多抽 15 秒左右）
- **Azure Foundry 终结点不能用于标准 TTS**（最高频踩坑）：必须用 `{region}.tts.speech.microsoft.com` 区域终结点
- **Azure 音色列表响应约 600KB**，流式 `json.load(response)` 偶发 `IncompleteRead` → 脚本已改为「先读完整 bytes 再 `json.loads`」并带退避重试
- **Azure 401/403 不重试**（凭据问题重试无意义，直接 break 并打印原因）
- `--play` 播放细节见「🔈 自动播放方案」；转码用 imageio-ffmpeg 隔离版（装于 venv 内）
- 脚本输出**绝对路径到 stdout**，方便 agent 直接捕获

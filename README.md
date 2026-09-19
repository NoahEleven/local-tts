# Local TTS（本地文本转语音）

把任意文本转成本地音频文件（mp3/wav），供 agent 或脚本调用。

- **edge-tts（默认）**：微软神经网络语音，音质自然，需联网，免费无需 key，15 个中文音色可用
- **Azure Speech（进阶）**：官方 API，75 个中文音色全解锁（含 HD / 情感风格），50 万字符/月免费额度
- **pyttsx3（离线）**：Windows SAPI 引擎，完全断网可用，自动兜底

## 安装

```bash
pip install pyttsx3 edge-tts imageio-ffmpeg
# Azure 通道零第三方依赖（纯 Python 标准库），无需额外安装
```

## 用法

```bash
# 默认：edge-tts + 晓晓女声（zh-CN-XiaoxiaoNeural）
python scripts/tts.py "要合成的文本" -o 输出.mp3

# 指定音色
python scripts/tts.py "文本" -o out.mp3 -v zh-CN-YunxiNeural

# 强制离线引擎（断网可用）
python scripts/tts.py "文本" -o out.wav --offline

# 生成后自动播放（仅 Windows，winsound 同步播放不弹窗）
python scripts/tts.py "文本" -o out.mp3 --play

# 列出 edge-tts 全部可用音色
python scripts/tts.py --list-voices

# 语速/音量（0.5~1.5）
python scripts/tts.py "文本" -o out.mp3 -r 1.1 --volume 1.2
```

## Azure 通道（v1.1.0 新增）

edge-tts 对较新一批中文音色做了服务端封锁（返回 `NoAudioReceived`），Azure 官方 API 是唯一解锁路径：

```bash
# 先配置凭据（任选其一：环境变量 AZURE_SPEECH_KEYS_FILE / scripts/keys.env / skill 根目录 keys.env / ~/.workbuddy/azure_speech.env）
#   AZURE_SPEECH_KEY=<密钥>
#   AZURE_SPEECH_REGION=eastasia

# 单条合成（解锁晓秋/晓辰/晓涵等 75 个中文音色）
python scripts/azure_tts.py --text "要合成的文本" --voice zh-CN-XiaoqiuNeural --out out.mp3

# 批量配音（JSON：{"segments":[{"text":"..."}]}，输出 01.mp3 ~ N.mp3）
python scripts/azure_tts.py --json script.json --voice zh-CN-XiaoqiuNeural --outdir audio_out

# 列出全部 75 个中文音色（含官方标签与情感风格）
python scripts/azure_tts.py --list-zh

# 语速/音调/情感风格（SSML prosody + mstts:express-as）
python scripts/azure_tts.py --text "..." --out o.mp3 --rate +10% --style newscast
```

> ⚠️ 必须用区域终结点（`{region}.tts.speech.microsoft.com`），门户的 Foundry 终结点不能用于标准 TTS。DragonHD / MAI-Voice-2 系列按量计费，不在免费额度内。

## 特性

- 联网失败自动降级到离线引擎（edge-tts → pyttsx3）
- Azure 通道 401/403 不重试（凭据问题直接报原因），5xx/限流带指数退避
- 未指定 `-o` 时输出到本 skill 目录 `tts_output/`
- `--play` 播放统一 mp3→wav 静默转码（imageio-ffmpeg）→ winsound 同步播放，不弹窗不残留临时文件
- 模块级 import 延迟到函数内，缺依赖不整体崩溃
- 内置音色可用性对照表（SKILL.md）：edge-tts 实际可用 15 个中文音色，被封锁的 14 个走 Azure

## 平台说明

- 文本合成（edge-tts / Azure / pyttsx3）：跨平台
- `--play` 播放：仅 Windows（依赖 winsound）

## License

MIT

# Local TTS（本地文本转语音）

把任意文本转成本地音频文件（mp3/wav），供 agent 或脚本调用。

- **edge-tts（默认）**：微软神经网络语音，音质自然，需联网，免费无需 key，中文 20+ 音色
- **pyttsx3（离线）**：Windows SAPI 引擎，完全断网可用，自动兜底

## 安装

```bash
pip install pyttsx3 edge-tts imageio-ffmpeg
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

# 列出全部中文音色
python scripts/tts.py --list-voices

# 语速/音量（0.5~1.5）
python scripts/tts.py "文本" -o out.mp3 -r 1.1 --volume 1.2
```

## 特性

- 联网失败自动降级到离线引擎（edge-tts → pyttsx3）
- 未指定 `-o` 时输出到本 skill 目录 `tts_output/`
- `--play` 播放统一 mp3→wav 静默转码（imageio-ffmpeg）→ winsound 同步播放，不弹窗不残留临时文件
- 模块级 import 延迟到函数内，缺依赖不整体崩溃

## 平台说明

- 文本合成（edge-tts / pyttsx3）：跨平台
- `--play` 播放：仅 Windows（依赖 winsound）

## License

MIT

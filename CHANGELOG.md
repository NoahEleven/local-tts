# Changelog

## [1.0.0] - 2026-08-10

### Added
- 初始发布
- edge-tts 神经网络语音（默认晓晓女声 zh-CN-XiaoxiaoNeural），免费无需 key
- pyttsx3 离线引擎兜底（断网自动降级 / `--offline` 强制）
- 可选 `--play` 自动播放：mp3→wav 静默转码（imageio-ffmpeg）+ winsound 同步播放（仅 Windows）
- `--list-voices` 列出全部中文音色
- 语速/音量调节（`-r` / `--volume`）
- 未指定 `-o` 时输出到 skill 目录 `tts_output/`

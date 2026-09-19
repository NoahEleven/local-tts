# Changelog

## [1.1.0] - 2026-09-18

### Added
- **Azure Speech 官方通道**（`scripts/azure_tts.py`）：解锁被 edge-tts 封锁的 14 个中文音色，共 75 个全通（含 HD / MAI-Voice-2 / 情感风格）
  - 区域终结点调用（`{region}.tts.speech.microsoft.com`），SSML prosody + `mstts:express-as`
  - 语速/音调/音量/情感风格可调（`--rate` / `--pitch` / `--style`）
  - 批量配音：`--json` 读取 `{"segments":[{"text":...}]}` 结构，输出 01.mp3 ~ N.mp3
  - `--list-zh` 列出全部中文音色（含官方标签）
  - 零第三方依赖（纯标准库 urllib），密钥按 4 级优先级自动查找（环境变量 → scripts/keys.env → skill 根 keys.env → ~/.workbuddy/azure_speech.env）
- **音色探测脚本**（`scripts/probe_voices.py`）：实测音色可用性，支持单测/全量/快照清单三种模式
- SKILL.md 新增「音色可用性双通道对照表」（2026-09-18 实测）：edge-tts 实际可用 15 个、被封锁 14 个的完整清单

### Fixed
- Azure 音色列表响应（约 600KB）流式解析偶发 `IncompleteRead` → 改为先读完整 bytes 再 `json.loads`，带退避重试
- Azure 401/403 凭据错误不再重试，直接报错并提示配置方法

## [1.0.0] - 2026-08-10

### Added
- 初始发布
- edge-tts 神经网络语音（默认晓晓女声 zh-CN-XiaoxiaoNeural），免费无需 key
- pyttsx3 离线引擎兜底（断网自动降级 / `--offline` 强制）
- 可选 `--play` 自动播放：mp3→wav 静默转码（imageio-ffmpeg）+ winsound 同步播放（仅 Windows）
- `--list-voices` 列出全部中文音色
- 语速/音量调节（`-r` / `--volume`）
- 未指定 `-o` 时输出到 skill 目录 `tts_output/`

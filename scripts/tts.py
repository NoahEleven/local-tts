#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local TTS - 本地文本转语音（agent 可调用）

用法:
  python tts.py "文本" [-o 输出.mp3] [-v 音色] [-r 语速] [--volume 音量] [--offline] [--play] [--list-voices]

默认: 联网 edge-tts + 晓晓女声 (zh-CN-XiaoxiaoNeural)；--offline 走 pyttsx3 断网兜底。
--play: 生成后统一转 wav 用 winsound 同步播放（阻塞到播完，不弹窗）。
"""
import argparse
import asyncio
import sys


def parse_args():
    p = argparse.ArgumentParser(description="Local TTS")
    p.add_argument("text", nargs="?", default=None, help="要合成的文本")
    p.add_argument("-o", "--out", default=None, help="输出文件路径（.mp3 或 .wav）")
    p.add_argument("-v", "--voice", default="zh-CN-XiaoxiaoNeural", help="edge-tts 音色")
    p.add_argument("-r", "--rate", type=float, default=1.0, help="语速倍率 0.5~1.5（1.0 正常）")
    p.add_argument("--volume", type=float, default=1.0, help="音量倍率 0.5~1.5（1.0 正常）")
    p.add_argument("--offline", action="store_true", help="强制用离线引擎 pyttsx3（断网兜底）")
    p.add_argument("--play", action="store_true", help="生成后自动播放（统一转 wav 用 winsound 同步播放，不弹窗不阻塞等待播完）")
    p.add_argument("--list-voices", action="store_true", help="列出 edge-tts 中文音色")
    return p.parse_args()


def list_voices():
    import edge_tts
    voices = asyncio.run(edge_tts.list_voices())
    zh = [v for v in voices if v["Locale"].startswith("zh")]
    for v in sorted(zh, key=lambda x: x["ShortName"]):
        print(f"{v['ShortName']}  {v['Gender']}  {v.get('FriendlyName','')}")
    print(f"\n共 {len(zh)} 个中文音色，其他语言用 --list-voices 自行查看或访问微软文档")


def edge_synth(text, out, voice, rate, volume):
    import edge_tts

    async def _run():
        # edge-tts 语速/音量格式为百分比字符串：1.0 -> +0%, 1.1 -> +10%, 0.8 -> -20%
        rate_pct = f"{int(round((rate - 1.0) * 100)):+d}%"
        vol_pct = f"{int(round((volume - 1.0) * 100)):+d}%"
        tts = edge_tts.Communicate(text, voice, rate=rate_pct, volume=vol_pct)
        await tts.save(out)

    try:
        asyncio.run(_run())
        return True
    except Exception as e:
        # 清理可能生成的半截文件
        import os
        if os.path.exists(out):
            try:
                os.remove(out)
            except Exception:
                pass
        print(f"[local-tts] edge-tts 失败（{type(e).__name__}: {e}），降级到离线引擎", file=sys.stderr)
        return False


def offline_synth(text, out):
    import os
    import pyttsx3

    eng = pyttsx3.init()
    voices = eng.getProperty("voices")
    zh = [v for v in voices if "zh" in v.id.lower() or "Chinese" in v.name]
    if zh:
        eng.setProperty("voice", zh[0].id)
    eng.setProperty("rate", 180)
    # pyttsx3 只输出 wav；用 os.path.splitext 安全替换扩展名（目录含点也不会切错）
    if not out.lower().endswith(".wav"):
        out = os.path.splitext(out)[0] + ".wav"
    eng.save_to_file(text, out)
    eng.runAndWait()
    return out


def main():
    args = parse_args()
    if args.list_voices:
        list_voices()
        return

    if not args.text:
        print("用法: python tts.py \"文本\" [-o 输出.mp3] [--offline] [-v 音色]", file=sys.stderr)
        sys.exit(2)

    # 未指定输出路径时：固定存到本 skill 目录 tts_output/ 下（语义化时间戳命名）
    # 用 __file__ 定位 skill 根目录，不依赖调用时的工作目录
    out = args.out
    if not out:
        import os as _os
        from datetime import datetime
        skill_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        out_dir = _os.path.join(skill_root, "tts_output")
        _os.makedirs(out_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = ".wav" if args.offline else ".mp3"
        out = _os.path.join(out_dir, f"tts_{ts}{suffix}")
        print(f"[local-tts] 未指定 -o，输出到: {out}", file=sys.stderr)

    if args.offline:
        out = offline_synth(args.text, out)
    else:
        if not edge_synth(args.text, out, args.voice, args.rate, args.volume):
            out = offline_synth(args.text, out)

    # 自动播放
    if args.play:
        play_audio(out)

    import os
    print(os.path.abspath(out))


def play_audio(path):
    """播放音频：统一转 WAV 后 winsound 同步播放（阻塞到播完）。
    必须用同步（不带 SND_ASYNC）：agent 调用是"生成即退出"的短进程，
    异步播放会在进程退出时被终止导致听不到声音。
    mp3 先用 ffmpeg（imageio-ffmpeg 隔离版）转 wav 到临时目录。
    """
    import os
    try:
        if not path.lower().endswith(".wav"):
            # mp3 -> wav 静默转码
            import imageio_ffmpeg
            import tempfile
            ff = imageio_ffmpeg.get_ffmpeg_exe()
            tmp_wav = os.path.join(tempfile.gettempdir(), "local_tts_play.wav")
            subprocess_check(ff, "-y", "-i", path, tmp_wav)
            path = tmp_wav
        import winsound
        # 注意：winsound.PlaySound 成功时返回 None，失败时抛异常，不要检查返回值
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        print(f"[local-tts] 已播放完毕（同步，无弹窗）: {os.path.abspath(path)}")
    except Exception as e:
        print(f"[local-tts] 播放失败（{type(e).__name__}: {e}），文件已生成: {path}", file=sys.stderr)


def subprocess_check(*cmd):
    import subprocess
    r = subprocess.run(list(cmd), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{r.stderr[:300]}")


if __name__ == "__main__":
    main()

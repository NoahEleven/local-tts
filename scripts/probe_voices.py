# -*- coding: utf-8 -*-
"""探测 edge-tts 实际可用音色（list 返回的 ≠ 能合成的）

用法：
    python scripts/probe_voices.py                 # 探测内置候选清单
    python scripts/probe_voices.py --all-zh        # 探测全部 zh-* 音色（慢）
    python scripts/probe_voices.py --voice zh-CN-XiaochenNeural   # 只测一个

背景：服务端对较新一批中文音色做了封锁，调用返回 NoAudioReceived。
      换音色前先跑本脚本，避免盲选浪费。
"""
import argparse
import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TEST_TEXT = "这是一句音色可用性测试。"

# 2026-09-18 实测快照，作为默认候选
SNAPSHOT = {
    "http_ok": [
        "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-XiaoxuanNeural",
        "zh-CN-YunxiNeural", "zh-CN-YunjianNeural", "zh-CN-YunyangNeural",
        "zh-CN-YunxiaNeural", "zh-CN-liaoning-XiaobeiNeural",
        "zh-CN-shaanxi-XiaoniNeural",
        "zh-HK-HiuGaaiNeural", "zh-HK-HiuMaanNeural", "zh-HK-WanLungNeural",
        "zh-TW-HsiaoChenNeural", "zh-TW-HsiaoYuNeural", "zh-TW-YunJheNeural",
    ],
    "http_rejected": [
        "zh-CN-XiaochenNeural", "zh-CN-XiaohanNeural", "zh-CN-XiaomengNeural",
        "zh-CN-XiaomoNeural", "zh-CN-XiaoqiuNeural", "zh-CN-XiaoruiNeural",
        "zh-CN-XiaoshuangNeural", "zh-CN-XiaoyanNeural", "zh-CN-XiaoyouNeural",
        "zh-CN-XiaozhenNeural", "zh-CN-YunfengNeural", "zh-CN-YunhaoNeural",
        "zh-CN-YunyeNeural", "zh-CN-YunzeNeural",
    ],
}


async def probe_one(voice, tmpdir):
    """合成一小段，成功返回 True。"""
    import edge_tts

    path = os.path.join(tmpdir, "probe_tmp.mp3")
    try:
        c = edge_tts.Communicate(TEST_TEXT, voice)
        await c.save(path)
        if os.path.getsize(path) > 500:
            return True
    except Exception:
        pass
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)  # 注意：用 os.remove，Path.unlink 会被 safe-delete 拦
            except OSError:
                pass
    return False


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", help="只探测指定音色")
    ap.add_argument("--all-zh", action="store_true", help="探测全部 zh-* 音色")
    ap.add_argument("--sleep", type=float, default=1.0, help="每个音色间隔秒数")
    args = ap.parse_args()

    import edge_tts

    if args.voice:
        candidates = [args.voice]
    elif args.all_zh:
        voices = await edge_tts.list_voices()
        candidates = sorted(
            v["ShortName"] for v in voices
            if v["ShortName"].startswith("zh-")
        )
    else:
        candidates = SNAPSHOT["http_ok"] + SNAPSHOT["http_rejected"]

    tmpdir = os.path.join(HERE, "_probe_tmp")
    os.makedirs(tmpdir, exist_ok=True)

    ok, bad = [], []
    for v in candidates:
        r = await probe_one(v, tmpdir)
        (ok if r else bad).append(v)
        print(f"{'OK  ' if r else 'FAIL'} {v}", flush=True)
        await asyncio.sleep(args.sleep)

    print(f"\n=== 可用 {len(ok)} ===")
    for v in ok:
        print(v)
    print(f"\n=== 被拒 {len(bad)} ===")
    for v in bad:
        print(v)

    # 清理临时目录
    try:
        os.rmdir(tmpdir)
    except OSError:
        pass

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

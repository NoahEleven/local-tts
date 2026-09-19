#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Azure Speech 官方 TTS 引擎（edge-tts 被封锁音色的解锁通道）

用法:
    # 单条
    python azure_tts.py --text "你好，这是一段测试语音。" --voice zh-CN-XiaoqiuNeural --out out.mp3

    # 从 JSON 文件批量（多段配音）
    python azure_tts.py --json _build/ep13.json --voice zh-CN-XiaoqiuNeural --outdir audio_ep13

    # 列全部中文音色（75 个，含官方标签与风格）
    python azure_tts.py --list-zh

凭据从 keys.env 读取，不硬编码。keys.env 查找顺序：
    1. 环境变量 AZURE_SPEECH_KEYS_FILE 指定的路径
    2. 本脚本同目录 keys.env
    3. 本 skill 根目录 keys.env
    4. ~/.workbuddy/azure_speech.env（全局兜底）
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)

ENDPOINT_TPL = "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"


def _candidate_key_files():
    """按优先级返回可能的凭据文件路径。"""
    cands = []
    envp = os.environ.get("AZURE_SPEECH_KEYS_FILE")
    if envp:
        cands.append(envp)
    cands.append(os.path.join(HERE, "keys.env"))
    cands.append(os.path.join(SKILL_ROOT, "keys.env"))
    cands.append(os.path.join(os.path.expanduser("~"), ".workbuddy", "azure_speech.env"))
    return cands


def find_keys_file():
    for p in _candidate_key_files():
        if os.path.isfile(p):
            return p
    return None


def load_keys(path=None):
    """读 keys.env，返回 (key, region)。找不到则 SystemExit 并给出修复指引。"""
    if path is None:
        path = find_keys_file()
    if not path:
        raise SystemExit(
            "找不到 Azure 凭据文件。请把 keys.env 放到以下任一位置（按优先级）：\n"
            "  " + "\n  ".join(_candidate_key_files()) + "\n"
            "内容格式：\n"
            "  AZURE_SPEECH_KEY=<你的密钥>\n"
            "  AZURE_SPEECH_REGION=eastasia\n"
            "（也可用环境变量 AZURE_SPEECH_KEYS_FILE 指定任意路径）"
        )
    cfg = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    key = cfg.get("AZURE_SPEECH_KEY")
    region = cfg.get("AZURE_SPEECH_REGION", "eastasia")
    if not key:
        raise SystemExit(f"{path} 里缺少 AZURE_SPEECH_KEY")
    return key, region


def ssml_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_ssml(text, voice, rate=None, pitch=None, volume=None, style=None):
    parts = []
    if rate:
        parts.append(f'rate="{rate}"')
    if pitch:
        parts.append(f'pitch="{pitch}"')
    if volume:
        parts.append(f'volume="{volume}"')
    inner = ssml_escape(text)
    if parts:
        inner = f"<prosody {' '.join(parts)}>{inner}</prosody>"
    if style:
        return (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="zh-CN">'
            f'<voice name="{voice}"><mstts:express-as style="{style}">'
            f"{inner}</mstts:express-as></voice></speak>"
        )
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="zh-CN"><voice name="{voice}">{inner}</voice></speak>'
    )


def synth(text, voice, out_path, key=None, region=None, rate=None, pitch=None,
          volume=None, style=None, retries=3, timeout=60):
    """合成单条，带退避重试。返回 (成功?, 字节数)。"""
    if key is None or region is None:
        key, region = load_keys()
    url = ENDPOINT_TPL.format(region=region)
    data = build_ssml(text, voice, rate, pitch, volume, style).encode("utf-8")
    hdrs = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": OUTPUT_FORMAT,
        "User-Agent": "workbuddy-local-tts",
    }
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                audio = r.read()
            if len(audio) < 500:
                raise RuntimeError(f"返回音频过小：{len(audio)}B")
            d = os.path.dirname(os.path.abspath(out_path))
            if d:
                os.makedirs(d, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(audio)
            return True, len(audio)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:200]
            last_err = f"HTTP {e.code}: {body}"
            if e.code in (401, 403):
                break  # 凭据问题，重试无意义
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        if attempt < retries - 1:
            time.sleep(1.5 * (attempt + 1))
    print(f"  [FAIL] {voice} -> {last_err}", file=sys.stderr)
    return False, 0


def extract_segments(json_path):
    """从 JSON 文件提取配音文本列表，返回 [(序号, 文本)]。"""
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    segs = d.get("segments") or d.get("slides") or []
    texts = []
    for i, s in enumerate(segs, 1):
        for k in ("text", "voice", "narration", "vo"):
            if isinstance(s.get(k), str) and s[k].strip():
                texts.append((i, s[k].strip()))
                break
    return texts


def count_chars(text):
    """统计计费字符（汉字 + 字母 + 数字）。"""
    return len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


def fetch_json(url, headers, retries=3, timeout=60):
    """GET 并解析 JSON。音色列表响应可达 600KB，直接 json.load(response)
    偶发 IncompleteRead，改为「先完整读 bytes 再 loads」，并退避重试。"""
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()  # 一次性读完，避免流式解析被截断
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise SystemExit(f"拉取音色列表失败：{last_err}")


def cmd_list_zh(key, region, voice_filter=None):
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
    voices = fetch_json(url, {"Ocp-Apim-Subscription-Key": key})
    zh = [v for v in voices if v["Locale"].startswith("zh-")]
    if voice_filter:
        zh = [v for v in zh if voice_filter.lower() in v["ShortName"].lower()]
    print(f"共 {len(zh)} 个中文音色（区域 {region}）：")
    print(f"共 {len(zh)} 个中文音色（区域 {region}）：")
    for v in sorted(zh, key=lambda x: x["ShortName"]):
        tag = v.get("VoiceTag", {})
        cats = ",".join(tag.get("ContentCategories") or [])
        pers = ",".join(tag.get("VoicePersonalities") or [])
        styles = ",".join(v.get("StyleList") or [])
        print(f"  {v['ShortName']:44s} {v['Gender']:6s} {cats:24s} {pers:30s} styles={styles}")
    return len(zh)


def main():
    ap = argparse.ArgumentParser(description="Azure Speech TTS 合成")
    ap.add_argument("--text", help="单条文本")
    ap.add_argument("--json", help="批量：JSON 配音脚本路径（{"segments":[{"text":...}]}）")
    ap.add_argument("--voice", default="zh-CN-XiaoqiuNeural", help="音色 ID")
    ap.add_argument("--out", help="单条输出文件")
    ap.add_argument("--outdir", help="批量输出目录")
    ap.add_argument("--rate", help="语速，如 +10%%")
    ap.add_argument("--pitch", help="音调，如 +0Hz")
    ap.add_argument("--volume", help="音量，如 +0%%")
    ap.add_argument("--style", help="情感风格，如 newscast")
    ap.add_argument("--list-zh", action="store_true", help="列出全部中文音色")
    args = ap.parse_args()

    key, region = load_keys()

    if args.list_zh:
        cmd_list_zh(key, region)
        return

    if args.text:
        if not args.out:
            raise SystemExit("--text 模式需要 --out")
        t0 = time.time()
        ok, n = synth(args.text, args.voice, args.out, key, region,
                      args.rate, args.pitch, args.volume, args.style)
        if ok:
            print(f"OK {args.out}  {n}B  {count_chars(args.text)}字符  "
                  f"{(time.time()-t0)*1000:.0f}ms")
        else:
            sys.exit(1)
        return

    if args.json:
        if not args.outdir:
            raise SystemExit("--json 模式需要 --outdir")
        segs = extract_segments(args.json)
        total_chars = sum(count_chars(t) for _, t in segs)
        print(f"共 {len(segs)} 段，合计 {total_chars} 字符（音色 {args.voice}）")
        t0 = time.time()
        done = 0
        for idx, text in segs:
            out = os.path.join(args.outdir, f"{idx:02d}.mp3")
            ok, n = synth(text, args.voice, out, key, region,
                          args.rate, args.pitch, args.volume, args.style)
            if ok:
                done += 1
                print(f"  [{idx:02d}/{len(segs)}] {n:7d}B  {text[:24]}...")
        print(f"完成 {done}/{len(segs)}，耗时 {time.time()-t0:.1f}s，"
              f"消耗 {total_chars} 字符")
        sys.exit(0 if done == len(segs) else 1)

    ap.print_help()


if __name__ == "__main__":
    main()

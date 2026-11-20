"""把真实运行记录渲染成终端风格截图，便于贴进报告附录。"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT = ROOT / "experiments" / "demo_transcript.txt"
OUTPUT = ROOT / "experiments" / "run_demo.png"
FULL_OUTPUT = ROOT / "experiments" / "run_demo_full.png"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"

WIDTH = 1500
MARGIN = 36
LINE_HEIGHT = 30
FONT_SIZE = 21


def wrap_line(text: str, font, draw, max_width: int):
    """按像素宽度折行，避免长命令被截断。"""
    if not text:
        return [""]
    lines = []
    current = ""
    for char in text:
        trial = current + char
        if draw.textlength(trial, font=font) > max_width and current:
            lines.append(current)
            current = char
        else:
            current = trial
    lines.append(current)
    return lines


def condense(raw: list[str]) -> list[str]:
    """只保留命令和顶层关键输出，避免 A4 页面上文字过小。"""
    result = []
    in_json = False
    for line in raw:
        if line.startswith("$"):
            in_json = True
            result.append(line)
            continue
        if in_json and line.strip().startswith('"similar_comments"'):
            result.append("  ... 相似消息列表已省略，完整输出见 demo_run.md")
            in_json = False
            continue
        if in_json:
            stripped = line.strip()
            if stripped.startswith(('"label"', '"confidence"', '"action"', '"reason"', '"input"', '{', '}')):
                result.append(line)
    return result


def select_full_case(raw: list[str]) -> list[str]:
    """截取低置信度样例的完整命令与 JSON 输出。"""
    start = None
    for i, line in enumerate(raw):
        if line.startswith("$ ") and "Nokia phone is lovly.." in line:
            start = i
            break
    if start is None:
        raise ValueError("运行记录中未找到低置信度样例")
    return raw[start:]


def main() -> None:
    raw = TRANSCRIPT.read_text(encoding="utf-8").splitlines()
    full_mode = "--full" in sys.argv
    if full_mode:
        raw = select_full_case(raw)
        output = FULL_OUTPUT
        header = "Terminal - 短消息审核 Agent 完整 JSON 输出"
    else:
        raw = condense(raw)
        output = OUTPUT
        header = "Terminal - 短消息审核 Agent 运行演示"
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    probe = Image.new("RGB", (WIDTH, 100), "white")
    draw = ImageDraw.Draw(probe)
    max_width = WIDTH - 2 * MARGIN

    wrapped = []
    for line in raw:
        wrapped.extend(wrap_line(line, font, draw, max_width))

    header_height = 54
    height = header_height + len(wrapped) * LINE_HEIGHT + 2 * MARGIN
    img = Image.new("RGB", (WIDTH, height), "#1E1E1E")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, header_height], fill="#2D2D2D")
    draw.text((MARGIN, 14), header, font=font, fill="#FFFFFF")
    draw.ellipse([WIDTH - 100, 18, WIDTH - 84, 34], fill="#FF5F56")
    draw.ellipse([WIDTH - 72, 18, WIDTH - 56, 34], fill="#FFBD2E")
    draw.ellipse([WIDTH - 44, 18, WIDTH - 28, 34], fill="#27C93F")

    y = header_height + MARGIN
    for line in wrapped:
        color = "#7EE787" if line.startswith("$") else "#D4D4D4"
        draw.text((MARGIN, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    img.save(output)
    print(f"运行截图已生成：{output}（{WIDTH}x{height}）")


if __name__ == "__main__":
    main()

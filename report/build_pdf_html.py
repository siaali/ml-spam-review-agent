"""把 Pandoc 生成的正文 HTML 加上封面和运行截图，供 WeasyPrint 打印成 PDF。"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BODY = ROOT / "报告正文.html"
OUTPUT = ROOT / "报告.html"
SCREENSHOT = ROOT.parent / "experiments" / "run_demo.png"

COVER = """
<div class="cover">
  <h1>“机器学习”课程期末报告</h1>
  <table class="cover-table">
    <tr><td>题&nbsp;&nbsp;目</td><td>基于词袋模型与朴素贝叶斯的垃圾短消息审核 Agent</td></tr>
    <tr><td>学&nbsp;&nbsp;院</td><td>电子电气工程学院</td></tr>
    <tr><td>专&nbsp;&nbsp;业</td><td>计算机科学与技术</td></tr>
    <tr><td>学号</td><td>[学号]</td></tr>
    <tr><td>姓名</td><td>[姓名]</td></tr>
    <tr><td>组员及分工</td><td>无（个人独立完成）</td></tr>
    <tr><td>课程教师</td><td>[课程教师]</td></tr>
    <tr><td>完成日期</td><td>2026年11月27日</td></tr>
  </table>
</div>
<div class="page-break"></div>
"""

CSS = """
<style>
@page { size: A4; margin: 2.5cm; }
body { font-family: "Songti SC", "SimSun", serif; font-size: 12pt; line-height: 1.7; color: #000; }
.cover { text-align: center; margin-top: 5cm; }
.cover h1 { font-size: 24pt; font-weight: normal; margin-bottom: 2cm; }
.cover-table { width: 80%; margin: 0 auto; border-collapse: collapse; font-size: 14pt; }
.cover-table td { border-bottom: 1px solid #000; padding: 10px; text-align: center; }
.cover-table td:first-child { width: 30%; }
.page-break { page-break-after: always; }
h1 { font-size: 16pt; margin-top: 24pt; }
h2 { font-size: 14pt; margin-top: 18pt; }
table { border-collapse: collapse; width: 100%; margin: 12pt 0; }
th, td { border: 1px solid #666; padding: 6px; font-size: 10.5pt; }
code { font-family: "Courier New", monospace; font-size: 10pt; }
pre { background: #f5f5f5; padding: 10px; white-space: pre-wrap; }
.screenshot { text-align: center; margin: 12pt 0 4pt; }
.screenshot img { width: 100%; max-width: 16cm; border: 1px solid #666; }
.figcaption { text-align: center; font-size: 10.5pt; color: #333; margin: 0 0 10pt; }
</style>
"""


def screenshot_html() -> str:
    """生成内嵌截图 HTML，避免 WeasyPrint 读取本地文件路径失败。"""
    data = base64.b64encode(SCREENSHOT.read_bytes()).decode("ascii")
    return (
        '<p class="screenshot">'
        f'<img src="data:image/png;base64,{data}" alt="Agent 运行截图" />'
        "</p>"
        '<p class="figcaption">图 E-1 三条 Agent 命令的真实运行截图'
        "（完整 JSON 输出见 experiments/demo_run.md）</p>"
    )


def main() -> None:
    html = BODY.read_text(encoding="utf-8")
    if "</head>" in html:
        html = html.replace("</head>", CSS + "\n</head>", 1)
    else:
        html = CSS + html
    if "<body>" in html:
        html = html.replace("<body>", "<body>\n" + COVER, 1)
    else:
        html = COVER + html

    marker = "下图为真实运行的终端截图"
    pos = html.find(marker)
    if pos != -1:
        paragraph_end = html.find("</p>", pos)
        if paragraph_end != -1:
            insert_at = paragraph_end + len("</p>")
            html = html[:insert_at] + "\n" + screenshot_html() + html[insert_at:]
        else:
            html = html.replace("</body>", screenshot_html() + "\n</body>", 1)
    else:
        html = html.replace("</body>", screenshot_html() + "\n</body>", 1)

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"已生成：{OUTPUT}")


if __name__ == "__main__":
    main()

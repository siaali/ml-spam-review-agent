"""实际运行三条 Agent 命令，并把命令与真实输出保存为运行记录。"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT / "src" / "agent.py"
OUTPUT = ROOT / "experiments" / "demo_transcript.txt"

CASES = [
    "Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question",
    "Ok lar... Joking wif u oni...",
    "Nokia phone is lovly..",
]


def clean(stdout: str) -> str:
    """去掉 jieba 的词典加载日志，只留真正的 JSON 输出。"""
    keep = []
    for line in stdout.splitlines():
        if line.startswith(("Building prefix dict", "Loading model", "Prefix dict")):
            continue
        keep.append(line)
    return "\n".join(keep).strip()


def main() -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    lines = [
        "机器学习期末项目 - Agent 完整运行记录",
        "运行日期：2026-11-19",
        "",
    ]
    for text in CASES:
        lines.append(f"$ python src/agent.py \"{text}\"")
        result = subprocess.run(
            [sys.executable, str(AGENT), text],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"运行失败：{text}\n{result.stderr}")
        lines.append(clean(result.stdout))
        lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"运行记录已写入：{OUTPUT}")


if __name__ == "__main__":
    main()

"""mlopsarch_jd165 —— 把MLOps 平台架构师·量化位宽与精度回退切成可核查的片段并标出关键位置。

把输入按语义边界切成独立单元，逐单元核对MLOps 平台架构师·量化位宽与精度回退相关的特征并标出命中位置

定位：
  只做切分与定位，不做语义改写——判断依据全部落在可指认的位置上

岗位对应：
  目标岗位　百度 · 资深MLOps 平台架构师
  技能主线　MLOps、Kubernetes、Docker、Python
  领域标签　MLOps、AI基础设施

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python mlopsarch_jd165.py --help
    python mlopsarch_jd165.py --file input.txt
    python mlopsarch_jd165.py --text "示例内容"
    python mlopsarch_jd165.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：百度 · 资深MLOps 平台架构师
RULES: list[dict] = [
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·缺失",
        "why": "岗位要求「MLOps」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', 'MLOps'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·冲突",
        "why": "两处关于「Kubernetes」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', 'Kubernetes'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·越界",
        "why": "「Docker」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'Docker'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·退化",
        "why": "「Python」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', 'Python'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·泄漏",
        "why": "「AI基础设施」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', 'AI基础设施'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·重复",
        "why": "同一处「MLOps 平台架构师」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', 'MLOps 平台架构师'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·陈旧#2",
        "why": "「MLOps」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', 'MLOps'],
    },
    {
        "name": "MLOps 平台架构师·量化位宽与精度回退·不可核#2",
        "why": "关于「Kubernetes」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'Kubernetes'],
    },
]


def mlopsarch_jd165_split_units(text: str) -> list[str]:
    """把输入切成语义单元：优先按行，其次按句。"""
    units: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = re.split(r"(?<=[。！？；;])\s*|(?<=[.!?])\s+(?=[A-Z一-鿿])", line)
        for p in parts:
            p = p.strip()
            if p:
                units.append(p)
    return units


def mlopsarch_jd165_hit_any(text: str, keywords: list[str]) -> list[str]:
    """返回命中的关键词列表（去重、保序）。"""
    low = text.lower()
    out: list[str] = []
    for k in keywords:
        if k.lower() in low and k not in out:
            out.append(k)
    return out


def mlopsarch_jd165_scan_units(text: str) -> list[dict]:
    """逐单元套规则，产出命中记录。"""
    units = mlopsarch_jd165_split_units(text)
    findings: list[dict] = []
    for idx, unit in enumerate(units):
        for rule in RULES:
            hits = mlopsarch_jd165_hit_any(unit, rule["keywords"])
            if hits:
                findings.append({
                    "unit_index": idx,
                    "text": unit,
                    "rule": rule["name"],
                    "why": rule["why"],
                    "severity": rule["severity"],
                    "hits": hits,
                })
    return findings


def mlopsarch_jd165_analyze(text: str) -> dict:
    """主分析：返回单元数、命中与覆盖情况。"""
    units = mlopsarch_jd165_split_units(text)
    findings = mlopsarch_jd165_scan_units(text)
    by_rule: dict[str, int] = {}
    for f in findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    return {
        "unit_count": len(units),
        "findings": findings,
        "by_rule": by_rule,
        "unmatched": len(units) - len({f["unit_index"] for f in findings}),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"单元数：{result['unit_count']}")
    out.append(f"命中 {result['hit_count'] if 'hit_count' in result else sum(result['by_rule'].values())} 处")
    out.append("")
    for rule in RULES:
        n = result["by_rule"].get(rule["name"], 0)
        if not n:
            continue
        out.append(f"[{rule['name']}] {n} 处  ({rule['severity']})")
        for f in result["findings"]:
            if f["rule"] == rule["name"]:
                out.append(f"  #{f['unit_index']}: {f['text'][:100]}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="mlopsarch_jd165",
        description="把输入按语义边界切成独立单元，逐单元核对MLOps 平台架构师·量化位宽与精度回退相关的特征并标出命中位置（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python mlopsarch_jd165.py --file input.txt\n"
            "  python mlopsarch_jd165.py --text '示例内容'\n"
            "  python mlopsarch_jd165.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = mlopsarch_jd165_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

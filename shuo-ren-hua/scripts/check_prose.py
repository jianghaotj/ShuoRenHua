#!/usr/bin/env python3
# Retained upstream notice for this derived skill package, including its
# documentation and scripts.
# MIT License
#
# Copyright (c) 2026 Human Writing Skill contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""说人话：read-only diagnostics, never an independent semantic verdict.

Exit 0: no proven contract violation (warnings/gaps can remain).
Exit 1: a valid, source-bound literal contract was violated.
Exit 2: invalid input, arguments, configuration, or runtime failure.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

from check_contract import InputError, check_verbatim, text_hash, validate_contract
from prose_blocks import HAN_COUNT_VERSION, PARSER_VERSION, SourceMap, han_count, parse_markdown

DEFAULT_RULES = Path(__file__).resolve().parent.parent / "references" / "rules.json"
RULE_IDS = {"F01", "F02", "F03", "F04", "T01", "L01", "L02", "L03", "L04", "L05", "L06", "S01", "S02"}
SEMANTIC_LIMITS = [
    "F01 新增事实、来源支持和亲历真实性未核验",
    "F02 否定、条件、结论强度、责任和范围是否保留未核验",
    "F04 引用是否支持所在主张未核验；标识存在不等于支持关系成立",
    "T01 任务和必要内容是否完整未核验",
    "L02 指代对象是否唯一未核验；仅提示跨结构候选",
    "L03 术语是否适合读者未核验",
    "L04 逻辑关系与 L06 搭配是否准确未核验",
    "L05 同义重复和局部限定必要性未核验",
    "S02 改动是否必要未核验；允许清楚的原文保持不变",
]


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"JSON 字段重复: {key}")
        result[key] = value
    return result


def read_json(path: str | Path):
    return json.loads(Path(path).read_bytes().decode("utf-8"), object_pairs_hook=_strict_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"JSON 非有限数值: {value}")))


def validate_rules(config: dict) -> dict:
    if not isinstance(config, dict) or set(config) != {"schema_version", "profiles", "length_hints", "repetition", "style_markers", "rules"}:
        raise InputError("规则配置顶层字段无效")
    if config["schema_version"] != "2.0":
        raise InputError("规则 schema_version 必须是 2.0")
    profiles = config["profiles"]
    if not isinstance(profiles, dict) or not {"general", "professional", "narrative"} <= set(profiles):
        raise InputError("规则须包含 general、professional、narrative profiles")
    for name, settings in profiles.items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name) or not isinstance(settings, dict) or set(settings) != {"length_hints", "pronoun", "repetition", "style"}:
            raise InputError("profile 字段无效")
        if any(type(value) is not bool for value in settings.values()):
            raise InputError("profile 开关必须是布尔值")
    hints = config["length_hints"]
    if not isinstance(hints, dict) or set(hints) != {"clause_han_gt", "sentence_han_gt", "clause_count_gte", "calibrated", "auto_split"}:
        raise InputError("length_hints 字段无效")
    for key in ("clause_han_gt", "sentence_han_gt", "clause_count_gte"):
        if type(hints[key]) is not int or hints[key] < 1:
            raise InputError(f"{key} 必须是正整数")
    if hints["calibrated"] is not False or hints["auto_split"] is not False:
        raise InputError("当前检查器阈值未经校准，不支持 calibrated/auto_split=true")
    repetition = config["repetition"]
    if not isinstance(repetition, dict) or set(repetition) != {"minimum_occurrences", "phrases"}:
        raise InputError("repetition 字段无效")
    if type(repetition["minimum_occurrences"]) is not int or repetition["minimum_occurrences"] < 2:
        raise InputError("重复提醒次数必须是至少 2 的整数")
    for label, phrases in (("repetition.phrases", repetition["phrases"]), ("style_markers", config["style_markers"])):
        if not isinstance(phrases, list) or any(not isinstance(item, str) or not item.strip() for item in phrases):
            raise InputError(f"{label} 必须是非空字符串数组")
        if len(set(phrases)) != len(phrases):
            raise InputError(f"{label} 不得重复")
    rules = config["rules"]
    if not isinstance(rules, list):
        raise InputError("rules 必须是数组")
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"id", "normative_level", "detection_method", "report_level", "owner", "requires_semantic_review"}:
            raise InputError("规则元数据字段无效")
        identifier = rule["id"]
        if not isinstance(identifier, str) or identifier not in RULE_IDS or identifier in seen:
            raise InputError("规则 ID 无效或重复")
        seen.add(identifier)
        if rule["normative_level"] not in ("required", "default", "preference"):
            raise InputError("规则规范层级无效")
        if rule["detection_method"] not in ("semantic", "heuristic", "deterministic") or rule["report_level"] not in (None, "info", "warning", "error"):
            raise InputError("规则检测方式或严重性无效")
        if type(rule["requires_semantic_review"]) is not bool:
            raise InputError("requires_semantic_review 必须是布尔值")
        owner = rule["owner"]
        if not isinstance(owner, str) or not re.fullmatch(r"(?:references/[a-z0-9-]+\.md|SKILL\.md)", owner):
            raise InputError("规则 owner 必须是技能内的单一规范 Markdown 路径")
        if identifier == "F03":
            if (rule["normative_level"], rule["detection_method"], rule["report_level"], rule["requires_semantic_review"]) != ("required", "deterministic", "error", False):
                raise InputError("F03 必须是 required/deterministic/error，不可关闭")
        elif identifier in {"L01", "L02", "L05", "S01"}:
            if rule["detection_method"] != "heuristic" or rule["report_level"] not in ("info", "warning") or rule["requires_semantic_review"]:
                raise InputError("风格候选只能是 heuristic/info 或 warning，不得提升为 error")
        elif rule["detection_method"] != "semantic" or rule["report_level"] is not None or not rule["requires_semantic_review"]:
            raise InputError("语义规则必须声明 semantic、null 严重性和人工复核")
    if seen != RULE_IDS:
        raise InputError("规则注册表不完整")
    return config


def _matches(value: str, phrases: list[str]):
    if not phrases:
        return []
    pattern = "|".join(re.escape(phrase) for phrase in sorted(phrases, key=len, reverse=True))
    return list(re.finditer(pattern, value))


def _sentences(value: str):
    # Repeated Chinese/ASCII punctuation forms a single terminator.
    for match in re.finditer(r"[^。！？!?]+(?:[。！？!?]+|$)", value):
        start, end = match.span()
        while start < end and value[start].isspace():
            start += 1
        while end > start and value[end - 1].isspace():
            end -= 1
        if start < end:
            yield start, end, value[start:end]


def _pronoun(value: str):
    value = value.lstrip(" \t“‘\"'（(")
    if value.startswith(("其实", "其他", "其它", "其中", "其余", "尤其")):
        return None
    match = re.match(r"它们|他们|她们|这些|那些|这个|那个|这种|那种|这项|那项|这次|那次|此事|对此|这|那|它|他|她|其|该|此", value)
    if not match:
        return None
    word, tail = match.group(), value[match.end():]
    # Complete demonstrative noun phrases are conservatively excluded.
    # This lexical boundary is not a grammatical ambiguity proof.
    if word in {"这些", "那些", "这个", "那个", "这种", "那种", "这项", "那项", "这次", "那次", "该", "此"}:
        if tail and not re.match(r"(?:[，。！？；：、\s]|是|都|也|仍|还|已|更|很|会|能|应|要|可以|需要|可能|不能|不[是会能])", tail):
            return None
    if word in {"这", "那"} and re.match(r"[个位项种次份条台套张所名场本部家批]", tail):
        return None
    return word


def analyze(text: str, config: dict, profile: str = "general", original: str | None = None,
            contract: dict | None = None, input_path: str = "<memory>") -> dict:
    validate_rules(config)
    if profile not in config["profiles"]:
        raise InputError(f"未知 profile: {profile}")
    if contract is not None:
        if original is None:
            raise InputError("--contract 必须同时提供 --original")
        validate_contract(contract, original)
    parsed = parse_markdown(text)
    source = SourceMap(text)
    settings = config["profiles"][profile]
    rules = {rule["id"]: rule for rule in config["rules"]}
    issues, lengths = [], []
    repeats = collections.defaultdict(list)

    def issue(identifier, block, a, b, reason, action, details=None):
        start, end = block.span(a, b)
        item = {"rule_id": identifier, "severity": rules[identifier]["report_level"],
                "detection_method": "heuristic", "location": source.location(start, end),
                "excerpt": text[start:end], "reason": reason, "action": action}
        if details is not None:
            item["details"] = details
        issues.append(item)

    for block in parsed.blocks:
        if block.kind != "heading":
            for a, b, sentence in _sentences(block.text):
                clauses = [part for part in re.split(r"[，,；;]+", re.sub(r"[。！？!?]+$", "", sentence)) if part.strip()]
                metrics = {"han_count": han_count(sentence),
                           "visible_character_count": sum(not char.isspace() for char in sentence),
                           "latin_letter_count": len(re.findall(r"[A-Za-z]", sentence)),
                           "digit_count": sum(char.isdecimal() for char in sentence),
                           "clause_count": len(clauses),
                           "max_clause_han_count": max((han_count(clause) for clause in clauses), default=0)}
                start, end = block.span(a, b)
                lengths.append({"location": source.location(start, end), **metrics})
                hints, reasons = config["length_hints"], []
                if metrics["max_clause_han_count"] > hints["clause_han_gt"]:
                    reasons.append("分句汉字数超过诊断阈值")
                if metrics["han_count"] > hints["sentence_han_gt"]:
                    reasons.append("整句汉字数超过诊断阈值")
                if metrics["clause_count"] >= hints["clause_count_gte"]:
                    reasons.append("分句数达到诊断阈值")
                if settings["length_hints"] and reasons:
                    issue("L01", block, a, b, "；".join(reasons) + "；计数不证明句子难懂。",
                          "检查主干、独立任务、限定范围和回读位置；按实际逻辑决定是否修改，不自动拆句。", metrics)
        if settings["pronoun"] and block.after_structure and block.kind in ("paragraph", "quote"):
            word = _pronoun(block.text)
            if word:
                start = len(block.text) - len(block.text.lstrip(" \t“‘\"'（("))
                issue("L02", block, start, start + len(word), "结构边界后出现指代候选；尚未判断对象是否唯一。",
                      "结合前后对象、话题和动作核对指向；仅在确有歧义时补明对象。", {"candidate": word})
        if settings["repetition"]:
            for match in _matches(block.text, config["repetition"]["phrases"]):
                start, end = block.span(*match.span())
                repeats[match.group()].append({"location": source.location(start, end), "section": block.section,
                                               "context_excerpt": re.sub(r"\s+", " ", block.text[max(0, match.start() - 25):match.end() + 55]).strip(),
                                               "claim_summary": None})
        if settings["style"]:
            for match in _matches(block.text, config["style_markers"]):
                issue("S01", block, *match.span(), "词形命中语境候选；本义、术语或人物口吻可能完全正常。",
                      "检查这处表达是否传达具体信息；必要术语、物理本义和有意修辞可保留。")

    for phrase, occurrences in repeats.items():
        if len(occurrences) >= config["repetition"]["minimum_occurrences"]:
            issues.append({"rule_id": "L05", "severity": rules["L05"]["report_level"], "detection_method": "heuristic",
                           "location": occurrences[0]["location"], "excerpt": phrase,
                           "reason": f"相同短语出现 {len(occurrences)} 次；未判断是否同一主张或无新增信息。",
                           "action": "逐处核对对象、证据和独立阅读单元；保留改变该条结论的局部限制。",
                           "details": {"phrase": phrase, "occurrences": occurrences, "claim_summary_status": "not_run"}})

    comparison = None
    if original is not None:
        before = parse_markdown(original)
        old_targets = {item["target"] for item in before.citations}
        new_targets = {item["target"] for item in parsed.citations}
        for target in sorted(old_targets - new_targets):
            first = next(item for item in before.citations if item["target"] == target)
            issues.append({"rule_id": "F04", "severity": "warning", "detection_method": "heuristic", "location": None,
                           "original_location": first["location"], "excerpt": target,
                           "reason": "原文引用标识或链接目标未在修订稿中识别到；可能改写、获准省略或使用了未覆盖语法。",
                           "action": "核对省略授权及来源与当前主张的支持关系；此候选不证明事实错误。"})
        comparison = {"original_hash": text_hash(original), "text_identical": text == original,
                      "original_character_count": len(original), "revised_character_count": len(text),
                      "citation_targets_removed": sorted(old_targets - new_targets),
                      "semantic_fidelity": "not_run", "original_coverage_gaps": before.gaps}
    if contract is not None:
        issues.extend(check_verbatim(text, original, contract))
    unique = {}
    for item in issues:
        key = (item["rule_id"], json.dumps(item.get("location"), sort_keys=True), item["excerpt"])
        unique.setdefault(key, item)
    issues = sorted(unique.values(), key=lambda item: (item["location"]["start"]["offset"] if item["location"] else len(text) + 1, item["rule_id"]))
    prose = "\n".join(block.text for block in parsed.blocks)
    counts = collections.Counter(item["severity"] for item in issues)
    return {
        "schema_version": "2.0", "input_path": input_path, "input_hash": text_hash(text), "profile": profile,
        "coverage": {
            "parser": PARSER_VERSION, "position_unit": "unicode_code_point",
            "range_convention": "zero_based_half_open_offsets; one_based_line_column",
            "supported": ["paragraphs_and_soft_wraps", "atx_and_setext_headings", "backtick_and_tilde_fences_with_length", "inline_code",
                          "ordered_unordered_nested_list_items", "block_quotes", "pipe_tables_extension", "inline_link_labels_and_destinations",
                          "reference_links_and_definitions", "autolinks_and_bare_urls"],
            "limitations": ["保守子集，不声称完整 CommonMark/GFM 兼容", "复杂混合容器、制表符缩进和完整引用链接解析未覆盖",
                            "HTML、公式、前置元数据仅隔离并标记，不解析其语义", "表格单元格检查自然语言候选，事实和指代仍需语义核对",
                            "英文句点不用于拆句；主要面向中文句末标点", "汉字计数采用声明的 CJK 码位范围，范围中未分配码位也计入"],
            "protected_regions": parsed.protected, "gaps": parsed.gaps, "semantic_checks_not_run": SEMANTIC_LIMITS,
            "exact_contract": "checked" if contract is not None else "not_provided",
            "rule_scope": {"heuristic": ["L01", "L02", "L05", "S01"], "citation_presence_if_original": ["F04"], "deterministic_if_contract": ["F03"]},
        },
        "statistics": {"han_count": han_count(prose), "han_count_version": HAN_COUNT_VERSION,
                       "visible_character_count": sum(not char.isspace() for char in prose),
                       "block_counts": dict(collections.Counter(block.kind for block in parsed.blocks)), "sentences": lengths},
        "issues": issues, "summary": {"error": counts["error"], "warning": counts["warning"], "info": counts["info"]},
        "comparison": comparison,
        "contract_review": ({"operation": contract["operation"], "must_preserve_claims": contract.get("must_preserve_claims", []),
                             "allowed_omissions": contract.get("allowed_omissions", []), "unresolved_questions": contract.get("unresolved_questions", []),
                             "claims_review_status": "not_run"} if contract is not None else None),
        "semantic_review_status": "not_run",
    }


def read_text(path: str) -> str:
    return (sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()).decode("utf-8")


def render_text(report: dict) -> str:
    lines = [f"说人话检查 · {report['profile']} · 汉字 {report['statistics']['han_count']}",
             "仅列机器候选；语义审查 not_run。退出 0 不表示全文准确可用。"]
    for item in report["issues"]:
        location = item.get("location")
        where = f"{location['start']['line']}:{location['start']['column']}" if location else "原文位置/缺失项"
        lines.append(f"[{item['severity']}] {item['rule_id']} {where} {item['reason']}")
        lines.append("  核对动作：" + item["action"])
    if not report["issues"]:
        lines.append("未发现已覆盖的机器候选。")
    coverage = report["coverage"]
    lines.append(f"保护区域 {len(coverage['protected_regions'])}；未覆盖区域 {len(coverage['gaps'])}；逐字契约 {coverage['exact_contract']}。")
    for gap in coverage["gaps"]:
        point = gap["location"]["start"]
        lines.append(f"  coverage gap {point['line']}:{point['column']} {gap['kind']}")
    lines.extend("未检查：" + item for item in coverage["semantic_checks_not_run"])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="说人话：只读检查中文稿件；风格提醒不阻断，语义审查需另行完成")
    parser.add_argument("path", help="Markdown/文本文件，或 - 从标准输入读取")
    parser.add_argument("--profile", default="general", help="general / professional / narrative，或规则配置中的 profile")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--original", help="改写前的 UTF-8 原文，用于保真复核；不可用 -")
    parser.add_argument("--contract", help="显式保真契约 JSON，必须同时提供 --original")
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES, help="规则配置 JSON")
    args = parser.parse_args(argv)
    try:
        if args.original == "-":
            raise InputError("--original 请使用文件路径，标准输入仅用于待检查稿件")
        if args.contract and not args.original:
            raise InputError("--contract 必须同时提供 --original")
        config = validate_rules(read_json(args.rules))
        report = analyze(read_text(args.path), config, args.profile,
                         read_text(args.original) if args.original else None,
                         read_json(args.contract) if args.contract else None, args.path)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as error:
        if args.format == "json":
            print(json.dumps({"schema_version": "2.0", "status": "runtime_error", "error": str(error),
                              "semantic_review_status": "not_run"}, ensure_ascii=False))
        print(f"检查未完成：{error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else render_text(report))
    return 1 if report["summary"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate an explicit fidelity contract; only literal locks prove violations."""
from __future__ import annotations

import hashlib
import re

from prose_blocks import SourceMap


class InputError(ValueError):
    pass


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _string(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{label} 必须是非空字符串")
    return value


def validate_contract(contract: dict, original: str) -> dict:
    if not isinstance(contract, dict):
        raise InputError("契约必须是 JSON 对象")
    allowed = {"schema_version", "operation", "original_sha256", "must_preserve_claims",
               "verbatim_spans", "allowed_omissions", "unresolved_questions", "notes", "status"}
    if set(contract) - allowed:
        raise InputError("契约包含未知字段: " + ", ".join(sorted(set(contract) - allowed)))
    if contract.get("schema_version") != "2.0":
        raise InputError("契约 schema_version 必须是 2.0")
    if contract.get("operation") not in {"light_edit", "rewrite", "explain_rewrite", "summarize"}:
        raise InputError("契约 operation 无效")
    digest = contract.get("original_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise InputError("契约 original_sha256 必须是小写 SHA-256")
    if digest != text_hash(original):
        raise InputError("契约 original_sha256 与原文不符；请确认原文版本并显式更新契约")
    for key in ("must_preserve_claims", "verbatim_spans", "allowed_omissions", "unresolved_questions"):
        if not isinstance(contract.get(key, []), list):
            raise InputError(f"契约 {key} 必须是数组")
    seen_ids, seen_text = set(), set()
    for index, span in enumerate(contract.get("verbatim_spans", [])):
        if not isinstance(span, dict) or set(span) - {"id", "text", "minimum_occurrences"}:
            raise InputError(f"verbatim_spans[{index}] 字段无效")
        value = _string(span.get("text"), "逐字保留文本")
        count = span.get("minimum_occurrences", 1)
        if type(count) is not int or count < 1:
            raise InputError("minimum_occurrences 必须是正整数")
        if original.count(value) < count:
            raise InputError("逐字保留文本在原文中的非重叠出现次数不足；不得锁定原文没有的内容")
        if value in seen_text:
            raise InputError("逐字保留文本重复声明")
        seen_text.add(value)
        if "id" in span:
            identifier = _string(span["id"], "契约片段 id")
            if identifier in seen_ids:
                raise InputError("契约 id 重复")
            seen_ids.add(identifier)
    for index, claim in enumerate(contract.get("must_preserve_claims", [])):
        if not isinstance(claim, dict) or set(claim) - {"id", "source_excerpt", "meaning", "review"}:
            raise InputError(f"must_preserve_claims[{index}] 字段无效")
        excerpt = _string(claim.get("source_excerpt"), "主张 source_excerpt")
        _string(claim.get("meaning"), "主张 meaning")
        if excerpt not in original:
            raise InputError("主张 source_excerpt 不在原文中")
        if claim.get("review", "semantic") != "semantic":
            raise InputError("主张只支持 semantic 审查，不得伪装成逐字锁定")
        if "id" in claim:
            identifier = _string(claim["id"], "主张 id")
            if identifier in seen_ids:
                raise InputError("契约 id 重复")
            seen_ids.add(identifier)
    for key in ("allowed_omissions", "unresolved_questions"):
        for value in contract.get(key, []):
            _string(value, key)
    for key in ("notes", "status"):
        if key in contract and not isinstance(contract[key], str):
            raise InputError(f"契约 {key} 必须是字符串")
    return contract


def check_verbatim(revised: str, original: str, contract: dict) -> list[dict]:
    issues = []
    source = SourceMap(original)
    for index, span in enumerate(contract.get("verbatim_spans", [])):
        value = span["text"]
        expected = span.get("minimum_occurrences", 1)
        actual = revised.count(value)
        if actual < expected:
            start = original.index(value)
            issues.append({"rule_id": "F03", "severity": "error", "detection_method": "deterministic",
                           "location": None, "location_note": "修订稿缺失片段没有可靠位置；原文位置见 original_location",
                           "original_location": source.location(start, start + len(value)),
                           "excerpt": value, "reason": f"显式逐字契约要求至少 {expected} 次，修订稿实际 {actual} 次。",
                           "action": "恢复契约锁定的原文；若要求变化，请由用户更新契约。",
                           "details": {"span_id": span.get("id", f"span-{index + 1}"),
                                       "minimum_occurrences": expected, "actual_occurrences": actual}})
    return issues

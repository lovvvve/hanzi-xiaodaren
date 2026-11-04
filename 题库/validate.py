#!/usr/bin/env python3
"""校验题库 JSON 是否符合 README.md 中的 schema。

用法: python3 validate.py <file.json> [...]
  --part   分片文件：允许 seq 不从 1 开始（仍要求连续）
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TYPES = {"pinyin", "word_fill", "idiom_fill", "idiom_pick", "idiom_from_text", "char_meaning",
         "glyph", "poem_fill", "poem_link", "quote_context", "word_usage", "culture", "other"}
FORMATS = {"choice", "fill", "judge", "link"}
FLAGS = {"answer_missing", "answer_by_ai", "answer_doubt", "text_uncertain", "image_required"}
GRADES = {None, "4-5", "5", "附加"}
SET_KEYS = ["id", "title", "group", "level", "year", "date", "sources", "notes", "sections", "questions"]
Q_KEYS = ["id", "seq", "section", "no", "type", "format", "stem", "pinyin", "options", "answer",
          "answer_full", "analysis", "grade", "images", "source_page", "flags", "note"]


def check(path, part):
    errs = []
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:  # noqa: BLE001
        return [f"JSON 解析失败: {e}"]

    for k in SET_KEYS:
        if k not in d:
            errs.append(f"顶层缺字段 {k}")
    if errs:
        return errs
    if d["group"] not in ("真题", "模拟"):
        errs.append(f"group 非法: {d['group']}")
    if d["level"] not in ("市赛", "区赛", "模拟"):
        errs.append(f"level 非法: {d['level']}")
    sec_nos = set()
    for s in d["sections"]:
        for k in ("no", "title", "type", "format"):
            if k not in s:
                errs.append(f"section 缺字段 {k}: {s}")
        sec_nos.add(s.get("no"))
        if s.get("type") not in TYPES:
            errs.append(f"section {s.get('no')} type 非法: {s.get('type')}")
        if s.get("format") not in FORMATS:
            errs.append(f"section {s.get('no')} format 非法: {s.get('format')}")

    qs = d["questions"]
    if not qs:
        errs.append("questions 为空")
        return errs
    ids = set()
    start = qs[0].get("seq")
    if not part and start != 1:
        errs.append(f"seq 应从 1 开始，实际 {start}")
    for i, q in enumerate(qs):
        tag = f"q[{i}] {q.get('id')}"
        for k in Q_KEYS:
            if k not in q:
                errs.append(f"{tag} 缺字段 {k}")
        if any(k not in q for k in Q_KEYS):
            continue
        extra = set(q) - set(Q_KEYS)
        if extra:
            errs.append(f"{tag} 多余字段 {sorted(extra)}")
        if isinstance(start, int) and q["seq"] != start + i:
            errs.append(f"{tag} seq 不连续: {q['seq']}")
        exp_id = f"{d['id']}-{q['seq']:03d}" if isinstance(q["seq"], int) else None
        if q["id"] != exp_id:
            errs.append(f"{tag} id 应为 {exp_id}")
        if q["id"] in ids:
            errs.append(f"{tag} id 重复")
        ids.add(q["id"])
        if q["section"] not in sec_nos:
            errs.append(f"{tag} section {q['section']} 不在 sections 中")
        if q["type"] not in TYPES:
            errs.append(f"{tag} type 非法: {q['type']}")
        if q["format"] not in FORMATS:
            errs.append(f"{tag} format 非法: {q['format']}")
        if not isinstance(q["stem"], str) or not q["stem"].strip():
            errs.append(f"{tag} stem 为空")
        if q["grade"] not in GRADES:
            errs.append(f"{tag} grade 非法: {q['grade']}")
        if not isinstance(q["flags"], list) or set(q["flags"]) - FLAGS:
            errs.append(f"{tag} flags 非法: {q['flags']}")
        if q["type"] == "pinyin" and not q["pinyin"]:
            errs.append(f"{tag} pinyin 类缺 pinyin 字段")
        ans = q["answer"]
        if ans is None and "answer_missing" not in q["flags"]:
            errs.append(f"{tag} answer 为空但未标 answer_missing")
        if q["format"] == "choice":
            opts = q["options"]
            if not isinstance(opts, list) or len(opts) < 2:
                errs.append(f"{tag} choice 缺 options")
            else:
                keys = [o.get("key") for o in opts]
                if ans is not None:
                    for a in (ans if isinstance(ans, list) else [ans]):
                        if a not in keys:
                            errs.append(f"{tag} answer {a!r} 不在选项 {keys} 中")
        else:
            if q["options"] not in (None, []):
                errs.append(f"{tag} 非 choice 题不应有 options")
        if q["format"] == "judge" and ans is not None and ans not in ("√", "×"):
            errs.append(f"{tag} judge answer 应为 √/×: {ans!r}")
        if q["format"] == "fill" and isinstance(ans, list):
            blanks = q["stem"].count("___")
            if blanks and blanks < len(ans):
                errs.append(f"{tag} 空位数 {blanks} < 答案数 {len(ans)}")
        for o in q["options"] or []:
            if o.get("img") and not os.path.isfile(os.path.join(ROOT, o["img"])):
                errs.append(f"{tag} 选项图片不存在: {o['img']}")
        for img in q["images"] or []:
            if not os.path.isfile(os.path.join(ROOT, img)):
                errs.append(f"{tag} 图片不存在: {img}")
        if q["images"] and "image_required" not in q["flags"] and q["type"] == "glyph":
            pass
        if q["source_page"] is not None and not isinstance(q["source_page"], int):
            errs.append(f"{tag} source_page 应为整数或 null")
        if re.search(r"_{1,2}(?!_)", re.sub(r"_{3,}", "", q["stem"])):
            errs.append(f"{tag} stem 空位应统一为 ___")
    return errs


def main():
    args = sys.argv[1:]
    part = "--part" in args
    files = [a for a in args if a != "--part"]
    if not files:
        print(__doc__)
        sys.exit(2)
    bad = 0
    for p in files:
        errs = check(p, part)
        if errs:
            bad += 1
            print(f"✗ {p}: {len(errs)} 个问题")
            for e in errs[:50]:
                print("   -", e)
            if len(errs) > 50:
                print(f"   ... 另有 {len(errs) - 50} 个")
        else:
            with open(p, encoding="utf-8") as f:
                n = len(json.load(f)["questions"])
            print(f"✓ {p}: {n} 题")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

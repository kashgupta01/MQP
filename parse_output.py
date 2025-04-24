import json
import re
import csv
from typing import List, Dict, Pattern


COLS: List[str] = [
    "Technique",
    "Complex Name",
    "Organism",
    "Other Organisms",
    "Complex Function",
    "Proteins",
    "Genes",
    "Confidence Score",
]


VARIANTS: Dict[str, List[str]] = {
    "Complex Name": [r"Complex\s*Name", r"Name\s*of\s*Complex"],
    "Organism": [r"Organism\b", r"Species\b"],
    "Other Organisms": [r"Other\s*Organisms?", r"Additional\s*Organisms?", r"Presence\s*in\s*Other\s*Organisms"],
    "Complex Function": [r"Complex\s*Function", r"Function\s*of\s*Complex", r"Function\b"],
    "Proteins": [
        r"Proteins?",
        r"Protein\s*Components?",
        r"Protein\s*Composition",
        r"List\s*of\s*Proteins",
        r"Proteins\s*in\s*the\s*Complex",
        r"Protein\s*Comprising\s*the\s*Complex",
        r"Composition\s*\(List\s*of\s*Proteins\)",
    ],
    "Genes": [r"Genes", r"Gene\s*List", r"Corresponding\s*Genes?"],
    "Confidence Score": [
        r"Confidence\s*Score",
        r"Self\s*Confidence\s*Score",
        r"Confidence\s*Score\s*Calculation",
        r"Confidence\s*Score\s*Equation",
        r"Assigned\s*Score",
        r"Self\s*Confidence\s*Score\s*Calculation",
        r"Total\s*Self\s*Confidence\s*Score",
    ],
}

# Pre‑compiled helpers
LIST_MARKER_RE: Pattern[str] = re.compile(r"^[\s>*-]*\d*\.?\s*")
SEGMENTS_RE: Pattern[str] = re.compile(r"[\-–]\s*(?=['\"])")
CONF_EQ_RE: Pattern[str] = re.compile(r"^\([^=]*=.+\d+\.\d+")

# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------

def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

UNICODE_QUOTES = dict.fromkeys(map(ord, "\u2018\u2019\u201c\u201d"), None)

def _strip_decorations(line: str) -> str:
    line = line.translate(UNICODE_QUOTES)
    line = re.sub(r"^#+\s*", "", line)   # markdown headings
    line = line.replace("**", "")
    line = line.strip("'\"")
    line = line.replace("`", "")
    return line

# Build header regex maps
HEADER_PATTERNS: Dict[Pattern[str], str] = {}
INLINE_PATTERNS: Dict[Pattern[str], str] = {}
for canon, variants in VARIANTS.items():
    for v in variants:
        HEADER_PATTERNS[re.compile(rf"^[\s>*-]*\**\s*({v})\s*\**\s*:?$", re.I)] = canon
        INLINE_PATTERNS[re.compile(rf"^[\s>*-]*\**\s*({v})[^:]*:\s*(.+)$", re.I)] = canon

# -----------------------------------------------------------------------------
# Technique normaliser
# -----------------------------------------------------------------------------

def _normalize_technique(tag: str) -> str:
    tag = tag.lower()
    if "few" in tag:
        return "few-shot"
    if "zero" in tag:
        return "zero-shot"
    if "con" in tag:
        return "contextual"
    return tag or "unknown"

# -----------------------------------------------------------------------------
# Core extractor
# -----------------------------------------------------------------------------

def extract_to_csv(jsonl_path: str, csv_path: str, item_sep_regex: str = r"''|;|,") -> None:
    rows: List[Dict[str, str]] = []

    with open(jsonl_path, "r", encoding="utf-8") as jf:
        for line in jf:
            obj = json.loads(line)
            cid = obj.get("custom_id", "")
            if "|" in cid:
                tech_raw = cid.split("|")[-1]
                content = obj.get("response", {}).get("body", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                tech_raw = cid.split("__")[-1]
                content = obj.get("result", {}).get("message", {}).get("content", [{}])[0].get("text", "")

            technique = _normalize_technique(tech_raw)
            values: Dict[str, List[str]] = {c: [] for c in COLS}
            values["Technique"].append(technique)

            current_field: str | None = None
            for raw in content.splitlines():
                # explode jammed few‑shot lines into parts first
                for segment in SEGMENTS_RE.split(raw):
                    seg_raw = segment
                    if not seg_raw.strip():
                        # blank line
                        if current_field != "Confidence Score":
                            current_field = None
                        continue

                    seg_raw = LIST_MARKER_RE.sub("", seg_raw)
                    seg_raw = _strip_decorations(seg_raw)
                    line = _collapse_ws(seg_raw)
                    if not line:
                        continue

                    # If equation‑style score line, force field
                    if CONF_EQ_RE.match(line):
                        current_field = "Confidence Score"

                    # Inline header?
                    matched = False
                    for pat, canon in INLINE_PATTERNS.items():
                        m = pat.match(line)
                        if m:
                            val = m.group(2)
                            parts = [
                                _collapse_ws(p)
                                for p in re.split(item_sep_regex, val)
                                if _collapse_ws(p)
                            ]
                            values[canon].extend(parts)
                            current_field = None
                            matched = True
                            break
                    if matched:
                        continue

                    # Stand‑alone header?
                    for pat, canon in HEADER_PATTERNS.items():
                        if pat.match(line):
                            current_field = canon
                            matched = True
                            break
                    if matched:
                        continue

                    # Continuation
                    if current_field:
                        parts = [
                            _collapse_ws(p)
                            for p in re.split(item_sep_regex, line)
                            if _collapse_ws(p)
                        ]
                        values[current_field].extend(parts)

            # post‑process & dedupe
            row: Dict[str, str] = {}
            for col in COLS:
                uniq: List[str] = []
                seen: set[str] = set()
                for val in values[col]:
                    if val not in seen:
                        uniq.append(val)
                        seen.add(val)
                if col == "Confidence Score" and uniq:
                    m = re.findall(r"\d+\.\d+", " ".join(uniq))
                    row[col] = m[-1] if m else "; ".join(uniq)
                else:
                    row[col] = "; ".join(uniq)
            rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    extract_to_csv(
        jsonl_path="anthropic_outputs\claude-3-5-haiku_output_v2.jsonl",
        csv_path="parsed_output.csv",
    )

import json
import re
import csv
from typing import List, Dict, Pattern

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

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

# Mapping of header variants ➜ canonical names
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
        r"Protein\\s*Comprising\\s*the\\s*Complex",
        r"Composition\\s*\\(List\\s*of\\s*Proteins\\)",
    ],
    "Genes": [r"Genes", r"Genes?", r"Gene\s*List", r"Corresponding\s*Genes?"],
    "Confidence Score": [
        r"Confidence\s*Score",
        r"Self\s*Confidence\s*Score",
        r"Confidence\s*Score\s*Calculation",
        r"Confidence\s*Score\s*Equation",
        r"Assigned\s*Score",
        r"Self\\s*Confidence\\s*Score\\s*Calculation",
        r"Confidence\\s*Score\\s*Calculation",
        r"Total\s*Self\s*Confidence\s*Score",
        r"Total\s*Confidence\s*Score",
    ],
}

LIST_MARKER_RE: Pattern[str] = re.compile(r"^[\s>*-]*\d*\.?\s*")
SEGMENTS_RE: Pattern[str] = re.compile(r"[\-–]\s*(?=['\"])")
UNICODE_QUOTES = dict.fromkeys(map(ord, "\u2018\u2019\u201C\u201D"), None)


# cleaning & structuring helper functions

def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def _strip_decorations(line: str) -> str:
    line = line.translate(UNICODE_QUOTES)  # drop curly quotes
    line = re.sub(r"^#+\s*", "", line)  # markdown headings
    line = line.replace("**", "")
    line = line.strip("'\"")
    line = line.replace("`", "")
    return line

def _build_patterns() -> tuple[Dict[Pattern[str], str], Dict[Pattern[str], str]]:
    header_pat: Dict[Pattern[str], str] = {}
    inline_pat: Dict[Pattern[str], str] = {}
    for canon, variants in VARIANTS.items():
        for v in variants:
            header_pat[re.compile(rf"^[\s>*-]*\**\s*({v})\s*\**\s*:?$", re.I)] = canon
            inline_pat[re.compile(rf"^[\s>*-]*\**\s*({v})[^:]*:\s*(.+)$", re.I)] = canon
    return header_pat, inline_pat

HEADER_PATTERNS, INLINE_PATTERNS = _build_patterns()


# normalize technique name 

def _normalize_technique(tag: str) -> str:
    """Return canonical label: few-shot, zero-shot, contextual."""
    tag = tag.lower()
    if "few" in tag:
        return "few-shot"
    if "zero" in tag:
        return "zero-shot"
    if "con" in tag:
        return "contextual"
    return tag or "unknown"


# content extraction 

def extract_to_csv(jsonl_path: str, csv_path: str, item_sep_regex: str = r"''|;|,") -> None:
    rows: List[Dict[str, str]] = []

    with open(jsonl_path, "r", encoding="utf-8") as jf:
        for line in jf:
            obj = json.loads(line)
            raw_tag = obj.get("custom_id", "")
            if "|" in raw_tag:
                tech_raw = raw_tag.split("|")[-1]
            elif "__" in raw_tag:
                tech_raw = raw_tag.split("__")[-1]
            else:
                tech_raw = raw_tag
            technique = _normalize_technique(tech_raw)

            # OpenAI content shape
            if "response" in obj: 
                content = (
                    obj["response"].get("body", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
            else:  # Anthropic content shape
                content = (
                    obj.get("result", {})
                    .get("message", {})
                    .get("content", [{}])[0]
                    .get("text", "")
                )

            values: Dict[str, List[str]] = {c: [] for c in COLS}
            values["Technique"].append(technique)
            current_field: str | None = None

            for raw in content.splitlines():
                # break packed few‑shot line into pieces first
                for seg in SEGMENTS_RE.split(raw):
                    seg = LIST_MARKER_RE.sub("", seg)
                    seg = _strip_decorations(seg)
                    seg = _collapse_ws(seg)
                    if not seg:
                        continue

                    # stay inside Confidence Score block
                    if current_field == "Confidence Score":
                        parts = [p for p in re.split(item_sep_regex, seg) if _collapse_ws(p)]
                        values[current_field].extend(parts)
                        continue

                    # inline header
                    matched = False
                    for pat, canon in INLINE_PATTERNS.items():
                        m = pat.match(seg)
                        if m:
                            parts = [p for p in re.split(item_sep_regex, m.group(2)) if _collapse_ws(p)]
                            values[canon].extend(parts)
                            current_field = None
                            matched = True
                            break
                    if matched:
                        continue

                    # stand‑alone header
                    for pat, canon in HEADER_PATTERNS.items():
                        if pat.match(seg):
                            current_field = canon
                            matched = True
                            break
                    if matched:
                        continue

                    # continuation line
                    if current_field:
                        parts = [p for p in re.split(item_sep_regex, seg) if _collapse_ws(p)]
                        values[current_field].extend(parts)

            # collate & dedupe
            row: Dict[str, str] = {}
            for col in COLS:
                seen: set[str] = set()
                unique = []
                for item in values[col]:
                    if item not in seen:
                        unique.append(item)
                        seen.add(item)
                if col == "Confidence Score" and unique:
                    nums = re.findall(r"\d+\.\d+", unique[-1])
                    row[col] = nums[-1] if nums else unique[-1]
                else:
                    row[col] = "; ".join(unique)
            rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)



if __name__ == "__main__":
    extract_to_csv(
        jsonl_path="openai_outputs\o4-mini_output_v2.jsonl",
        csv_path="o4-mini_v2_parsed.csv",
    )
    print("Done → parsed_output.csv")

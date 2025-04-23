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

# --- Header variants ---------------------------------------------------------
VARIANTS: Dict[str, List[str]] = {
    "Complex Name": [
        r"Complex\s*Name",
        r"Name\s*of\s*Complex",
    ],
    "Organism": [
        r"Organism\b",
        r"Species\b",
    ],
    "Other Organisms": [
        r"Other\s*Organisms?",
        r"Additional\s*Organisms?",
        r"Presence\s*in\s*Other\s*Organisms",
    ],
    "Complex Function": [
        r"Complex\s*Function",
        r"Function\s*of\s*Complex",
        r"Function\b",
    ],
    "Proteins": [
        r"Proteins?",
        r"Protein\s*Components?",
        r"Protein\s*Composition",
        r"List\s*of\s*Proteins",
        r"Proteins\s*in\s*the\s*Complex",
        r"Protein\s*Comprising\s*the\s*Complex",
        r"Composition\s*\(List\s*of\s*Proteins\)",
    ],
    "Genes": [
        r"Genes\b",
        r"Gene\s*List",
        r"Corresponding\s*Genes?",
    ],
    "Confidence Score": [
        r"Confidence\s*Score",
        r"Self\s*Confidence\s*Score",
        r"Confidence\s*Score\s*Calculation",
        r"Self\s*Confidence\s*Score\s*Calculation",
        r"Total\s*Self\s*Confidence\s*Score",
        r"Total\s*Confidence\s*Score",
        r"Confidence\s*Score\s*Equation",
        r"Assigned\s*Score",
    ],
}

# Regex for stripping leading list markers ("1.", "-", "*", etc.)
LIST_MARKER_RE: Pattern[str] = re.compile(r"^[\s>*-]*\d*\.?\s*")

# Map of fancy Unicode quotes → nothing
UNICODE_QUOTES = dict.fromkeys(map(ord, "\u2018\u2019\u201c\u201d"), None)

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def _collapse_ws(s: str) -> str:
    """Trim and collapse internal whitespace."""
    return re.sub(r"\s+", " ", s.strip())


def _strip_decorations(line: str) -> str:
    """Remove markdown / typographic artefacts so header regexes match."""
    line = line.translate(UNICODE_QUOTES)      # drop curly quotes
    line = re.sub(r"^#+\s*", "", line)      # markdown headings
    line = line.replace("**", "")              # bold markers
    line = line.strip("'\"")                  # straight quotes
    line = line.replace("`", "")               # backticks
    return line


def _build_patterns() -> tuple[Dict[Pattern[str], str], Dict[Pattern[str], str]]:
    """Compile regex objects for header styles."""
    header_pat: Dict[Pattern[str], str] = {}
    inline_pat: Dict[Pattern[str], str] = {}

    for canon, variants in VARIANTS.items():
        for v in variants:
            header_pat[re.compile(rf"^[\s>*-]*\**\s*({v})\s*$", re.I)] = canon
            inline_pat[re.compile(rf"^[\s>*-]*\**\s*({v})\s*:\s*(.*)$", re.I)] = canon
    return header_pat, inline_pat

HEADER_PATTERNS, INLINE_PATTERNS = _build_patterns()

# -----------------------------------------------------------------------------
# Core extraction logic
# -----------------------------------------------------------------------------

def extract_to_csv(
    jsonl_path: str,
    csv_path: str,
    item_sep_regex: str = r"''|;|,",  # split on two single quotes, semicolon, comma
) -> None:
    """Parse a JSONL log and write a clean CSV."""

    rows: List[Dict[str, str]] = []

    with open(jsonl_path, "r", encoding="utf-8") as jf:
        for raw_line in jf:
            obj = json.loads(raw_line)

            # ---- technique & content ---------------------------------------
            custom_id = obj.get("custom_id", "")
            if "|" in custom_id:
                technique = custom_id.split("|")[-1]
                content = (
                    obj.get("response", {})
                    .get("body", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
            else:
                technique = custom_id.split("__")[-1]
                content = (
                    obj.get("result", {})
                    .get("message", {})
                    .get("content", [{}])[0]
                    .get("text", "")
                )

            # ---- initialise per‑row accumulator ----------------------------
            values: Dict[str, List[str]] = {c: [] for c in COLS}
            values["Technique"].append(technique)
            current_field: str | None = None

            # ---- iterate through content -----------------------------------
            for raw in content.splitlines():
                # Some models pack every header/value in ONE long line using
                # "-'Header: value'‑" concatenations (e.g. few‑shot style).
                # We split those on a hyphen *followed by* a quote so each
                # pair is parsed separately.
                for segment in re.split(r"-\s*(?=['\"])", raw):
                    if not segment.strip():
                        continue

                    segment = LIST_MARKER_RE.sub("", segment)
                    segment = _strip_decorations(segment)
                    line = _collapse_ws(segment)

                    if not line:
                        current_field = None
                        continue

                    # -- inside Confidence Score block ----------------------
                    if current_field == "Confidence Score":
                        # keep collecting until explicit *different* header
                        header_switched = False
                        for pat, canon in HEADER_PATTERNS.items():
                            if pat.match(line) and canon != "Confidence Score":
                                header_switched = True
                                break
                        if not header_switched:
                            values[current_field].append(line)
                            continue

                    # -- inline Header: value -------------------------------
                    matched_inline = False
                    for pat, canon in INLINE_PATTERNS.items():
                        m = pat.match(line)
                        if m:
                            val_part = m.group(2).strip()
                            if val_part:
                                items = [
                                    _collapse_ws(p)
                                    for p in re.split(item_sep_regex, val_part)
                                    if _collapse_ws(p)
                                ]
                                values[canon].extend(items)
                                current_field = None
                            else:
                                current_field = canon  # header only
                            matched_inline = True
                            break
                    if matched_inline:
                        continue

                    # -- stand‑alone header ---------------------------------
                    matched_header = False
                    for pat, canon in HEADER_PATTERNS.items():
                        if pat.match(line):
                            current_field = canon
                            matched_header = True
                            break
                    if matched_header:
                        continue

                    # -- continuation of current field ----------------------
                    if current_field:
                        items = [
                            _collapse_ws(p)
                            for p in re.split(item_sep_regex, line)
                            if _collapse_ws(p)
                        ]
                        values[current_field].extend(items)

            # ---- final tidy‑up per row -------------------------------------
            cleaned_row: Dict[str, str] = {}
            for col in COLS:
                seen, uniq = set(), []
                for item in values[col]:
                    if item not in seen:
                        uniq.append(item)
                        seen.add(item)
                if col == "Confidence Score" and uniq:
                    nums = re.findall(r"\d+\.\d+", " ".join(uniq))
                    cleaned_row[col] = nums[-1] if nums else "; ".join(uniq)
                else:
                    cleaned_row[col] = "; ".join(uniq)
            rows.append(cleaned_row)

    # ---- write CSV ----------------------------------------------------------
    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
        writer = csv.DictWriter(cf, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)

# -----------------------------------------------------------------------------
# Example CLI entry‑point ------------------------------------------------------
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    extract_to_csv(
        jsonl_path="gpt-4o_output_v2.jsonl",
        csv_path="clean.csv",
    )
    print("CSV written – open it to inspect results.")

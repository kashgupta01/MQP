import json
import re
import csv
from typing import List, Dict


def extract_to_csv_with_quotes(
    jsonl_path: str,
    csv_path: str,
    separator_regex: str = r"''",
) -> None:
    """
    Parse each `message.content` in an OpenAI JSONL response log and write the
    desired fields to a CSV file.

    • Adds a “technique” column taken from the part of `custom_id` that appears
      after the first “|”.
    • Normalises field names so that variants like “Complex Name”, "**complex
      name**", or "'Complex Name:'" are all recognised.
    • Splits multi‑item values on two single quotes (``' '``) – e.g.
      "ProteinA''ProteinB" → "ProteinA; ProteinB".

    Parameters
    ----------
    jsonl_path : str
        Path to the input .jsonl file.
    csv_path : str
        Destination for the output CSV.
    separator_regex : str, optional
        Regex used to split within a value (default ``r"''"``).
    """

    # Order of columns in the output
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

    # Common “spellings” for each field we have to recognise.
    VARIANTS: Dict[str, List[str]] = {
        "Complex Name": ["Complex\\s*Name", "Name\\s*of\\s*Complex"],
        "Organism": ["Organism?", "Species?", "Organism"],
        "Other Organisms": [
                            "Other\\s*Organisms?", 
                            "Additional\\s*Organisms?",
                            "Presence\\s*in\\s*Other\\s*Organisms"
                            ],
        "Complex Function": [
            "Complex\\s*Function", 
            "Function",
            "Function\\s*of\\s*Complex"
            ],
        "Proteins": [
            "Proteins?",
            "Protein\\s*Components?",
            "Protein\\s*Composition",
            "List\\s*of\\s*Proteins"
        ],
        "Genes": ["Genes?", "Gene\\s*List", "Corresponding\\s*Genes?"],
        "Confidence Score": [
            "Confidence\\s*Score",
            "Self\\s*Confidence\\s*Score",
        ],
    }

    # ------------------------------------------------------------------ helpers
    def _collapse_ws(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip())

    def _build_patterns() -> tuple[
        Dict[re.Pattern, str], Dict[re.Pattern, str]
    ]:
        """Compile stand‑alone‑header and inline “Header: value” patterns."""
        header_pat: Dict[re.Pattern, str] = {}
        inline_pat: Dict[re.Pattern, str] = {}

        for canon, variants in VARIANTS.items():
            for v in variants:
                #  Header on its own line (optional quotes / asterisks / colon)
                header_pat[
                    re.compile(
                        rf"""^[\'"]?      # optional opening quote
                             \s*(?:\*{{0,5}}\s*)?  # up to 3 asterisks
                             ({v})                # the field name
                             \s*(?:\*{{0,5}})?    # trailing asterisks
                             [\'"]?               # optional closing quote
                             \s*:?\s*$            # optional colon
                        """,
                        re.I | re.X,
                    )
                ] = canon

                #  “Header: value” on the same line
                inline_pat[
                    re.compile(
                        rf"""^[\'"]?      # optional opening quote
                             \s*(?:\*{{0,3}}\s*)?({v})[^:]*:\s*(.+)$
                        """,
                        re.I | re.X, 
                    )
                ] = canon
        return header_pat, inline_pat

    HEADER_PATTERNS, INLINE_PATTERNS = _build_patterns()

    # ------------------------------------------------------------------ parsing
    rows: List[Dict[str, str]] = []

    with open(jsonl_path, "r", encoding="utf‑8") as jf:
        for line in jf:
            rec = json.loads(line)

            custom_id = rec.get("custom_id", "")

            # OPEN AI -----------------------------
            technique = custom_id.split("|", 1)[1]

            # ANTHROPIC ---------------------------
            # technique = custom_id.split("__", 1)[1] 

            # OPEN AI ---------------------------------
            content = (
                rec.get("response", {})
                .get("body", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            # ANTHROPIC -------------------------------
            # content = (
            #     rec.get("result", {})
            #     .get("message", {})
            #     .get("content", [{}])[0]
            #     .get("text", "")
            # )


            # Accumulator for field values
            values: Dict[str, List[str]] = {c: [] for c in COLS}
            values["Technique"].append(technique)

            current_field: str | None = None

            for raw in content.splitlines():
                line = raw.strip()
                if not line:
                    continue

                # -------- First, try “Header: value” in the same line
                matched = False
                for pat, canon in INLINE_PATTERNS.items():
                    m = pat.match(line)
                    if m:
                        val_part = m.group(2)
                        parts = [
                            _collapse_ws(p)
                            for p in re.split(separator_regex, val_part)
                            if _collapse_ws(p)
                        ]
                        values[canon].extend(parts)
                        current_field = None
                        matched = True
                        break
                if matched:
                    continue

                # -------- Stand‑alone header line?
                for pat, canon in HEADER_PATTERNS.items():
                    if pat.match(line):
                        current_field = canon
                        matched = True
                        break
                if matched:
                    continue

                # -------- Continuation line for the current field
                if current_field:
                    parts = [
                        _collapse_ws(p)
                        for p in re.split(separator_regex, line)
                        if _collapse_ws(p)
                    ]
                    values[current_field].extend(parts)

            # Collate lists → single string per column
            rows.append({c: "; ".join(values[c]) for c in COLS})

    # ------------------------------------------------------------------ output
    with open(csv_path, "w", newline="", encoding="utf‑8") as cf:
        writer = csv.DictWriter(cf, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------- usage
if __name__ == "__main__":
    extract_to_csv_with_quotes(
        jsonl_path="openai_outputs\gpt-4o\gpt-4o_full_output.jsonl",
        csv_path="gpt-4o_parsed_v2.csv",
    )
    print(
        "Wrote CSV to gpt-4-1_parsed.csv "
        "— open it to inspect the results."
    )



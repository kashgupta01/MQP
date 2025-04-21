import json
import csv
import re
import os
from collections import defaultdict

def extract_to_csv(jsonl_path: str, csv_path: str):
    """
    Extracts specified fields from each message.content entry in an OpenAI
    JSONL response log and writes them to a CSV file.

    The parser is field‑name agnostic: it matches a variety of common
    capitalisation and phrasing variants (e.g. "Complex Name", "complex name:",
    "**Complex Name**", "Self confidence score", "Our self‑confidence score")
    and collects multi‑line values until the next recognised field header.

    Parameters
    ----------
    jsonl_path : str
        Path to the input .jsonl file returned by the OpenAI API.
    csv_path : str
        Path where the resulting CSV will be written.
    """

    # Canonical field names we want in the CSV
    canonical_fields = [
        "complex name",
        "organism",
        "complex function",
        "proteins",
        "genes",
        "other organisms",
        "confidence score",
    ]

    # Build a map of regex patterns (lower‑case) to canonical field
    variants = {
        "complex name": ["complex\\s*name", "name\\s*of\\s*complex"],
        "organism": ["organism", "species"],
        "complex function": ["complex\\s*function", "function"],
        "proteins": ["proteins?", "protein\\s*components?", "protein\\s*composition"],
        "genes": ["genes?", "gene\\s*list"],
        "other organisms": ["other\\s*organisms?", "additional\\s*organisms?"],
        "confidence score": ["confidence\\s*score", "self\\s*confidence\\s*score"],
    }

    pattern_to_field = {
        re.compile(rf"^(?:\*{{0,3}})?\s*({p})\s*(?:\*{{0,3}})?\s*:?$", re.I): canonical
        for canonical, pats in variants.items()
        for p in pats
    }
    # Separate pattern for "Header: value" on the same line
    pattern_inline = {
        re.compile(rf"^(?:\*{{0,3}})?\s*({p})[^:]*:\s*(.+)$", re.I): canonical
        for canonical, pats in variants.items()
        for p in pats
    }

    def normalise_text(text: str):
        # Collapse internal whitespace
        return re.sub(r"\s+", " ", text.strip())

    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            content = (
                obj.get("response", {})
                .get("body", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            values = defaultdict(list)
            current_field = None

            for raw_line in content.splitlines():
                line_str = raw_line.strip()
                if not line_str:
                    continue

                # Check "Field: value" format first
                matched = False
                for pat, canon in pattern_inline.items():
                    m = pat.match(line_str)
                    if m:
                        val = m.group(2)
                        values[canon].append(normalise_text(val))
                        current_field = None
                        matched = True
                        break
                if matched:
                    continue

                # Check if line is a field header without value
                for pat, canon in pattern_to_field.items():
                    if pat.match(line_str):
                        current_field = canon
                        matched = True
                        break
                if matched:
                    continue

                # Otherwise, treat as continuation of current field
                if current_field:
                    values[current_field].append(normalise_text(line_str))

            # Ensure all canonical fields exist (missing -> empty string)
            row = {
                field: "; ".join(values[field]) if values[field] else ""
                for field in canonical_fields
            }
            rows.append(row)

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=canonical_fields)
        writer.writeheader()
        writer.writerows(rows)


# --- Run the extraction on the uploaded file ---
input_file = "test_output.jsonl"
output_file = "complexes.csv"

extract_to_csv(input_file, output_file)

# Display where the file is and preview first 3 lines
print(f"CSV written to: {output_file}\n")

with open(output_file, "r", encoding="utf-8") as f:
    for i, l in zip(range(8), f):
        print(l.rstrip())


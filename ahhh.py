import json
import csv
import re
import os
from collections import defaultdict

# Define new extraction function including "technique"
def extract_to_csv_with_technique(jsonl_path: str, csv_path: str):
    canonical_fields = [
        "technique",
        "complex name",
        "organism",
        "complex function",
        "proteins",
        "genes",
        "other organisms",
        "confidence score",
    ]

    variants = {
        "complex name": ["complex\\s*name", "name\\s*of\\s*complex"],
        "organism": ["organism", "species"],
        "complex function": ["complex\\s*function", "function"],
        "proteins": ["proteins?", "protein\\s*components?", "protein\\s*composition"],
        "genes": ["genes?", "gene\\s*list"],
        "other organisms": ["other\\s*organisms?", "additional\\s*organisms?"],
        "confidence score": ["confidence\\s*score", "self\\s*confidence\\s*score"],
    }

    # Build regex maps
    pattern_to_field = {
        re.compile(rf"^(?:\*{{0,3}})?\s*({p})\s*(?:\*{{0,3}})?\s*:?$", re.I): canon
        for canon, pats in variants.items()
        for p in pats
    }
    pattern_inline = {
        re.compile(rf"^(?:\*{{0,3}})?\s*({p})[^:]*:\s*(.+)$", re.I): canon
        for canon, pats in variants.items()
        for p in pats
    }

    def tidy(text: str):
        return re.sub(r"\s+", " ", text.strip())

    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            custom_id = obj.get("custom_id", "")
            technique = custom_id.split("|")[1] if "|" in custom_id else ""

            content = (
                obj.get("response", {})
                .get("body", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            values = {field: [] for field in canonical_fields}
            values["technique"].append(technique)

            current_field = None
            for raw in content.splitlines():
                line = raw.strip()
                if not line:
                    continue

                # Inline "Field: value"
                matched = False
                for pat, canon in pattern_inline.items():
                    m = pat.match(line)
                    if m:
                        values[canon].append(tidy(m.group(2)))
                        current_field = None
                        matched = True
                        break
                if matched:
                    continue

                # Stand‑alone header
                for pat, canon in pattern_to_field.items():
                    if pat.match(line):
                        current_field = canon
                        matched = True
                        break
                if matched:
                    continue

                # Continuation
                if current_field:
                    values[current_field].append(tidy(line))

            row = {f: "; ".join(values[f]) if values[f] else "" for f in canonical_fields}
            rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=canonical_fields)
        writer.writeheader()
        writer.writerows(rows)

input_file = "test_output.jsonl"
output_file = "test.csv"
extract_to_csv_with_technique(input_file, output_file)

print("Created:", output_file)
with open(output_file, "r", encoding="utf-8") as f:
    for i, line in zip(range(8), f):
        print(line.rstrip())


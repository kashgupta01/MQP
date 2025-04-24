import json   

jsonl_path = "anthropic_outputs\claude-3-5-haiku_output_v2.jsonl"

with open(jsonl_path, "r", encoding="utf-8") as jf:
        for line in jf:
            obj = json.loads(line)
print(obj)
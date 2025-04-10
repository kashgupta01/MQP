import openai
import json

openai.api_key = ""

complexes = [
    "Kinetochore Mis12 complex",
    "Nuclear mitotic cohesin complex",
    "GPI-anchor transamidase complex"
]

prompt_techniques = {
    "zero-shot": "For each of the following protein {complex}, provide the role of the protein complex by labelling it as 'Complex Function', but avoid overgeneralization and long answers. Give the organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster) by labelling it as 'Organism'. Additionally, include a list of proteins the {complex} consists of and label the list 'Proteins'.",
    
    "few-shot": """For each of the following protein {complex}, provide the role of the protein complex (avoid generalization and long answers) and the organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster). Additionally, include a list of proteins the {complex} consists of. Here are an example of the output:
    'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible for gastric acid secretion in the stomach.' 
    'Organism: Mouse
    'Proteins: ATP4A, ATP4B """, 
            
    "contextual": """You are an expert in the field of biology and molecular machines. For each of the following protein {complex}, provide the role of the protein complex (avoid generalization and long answers) and the organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster). Additionally, include a list of proteins the {complex} consists of. Here is an example of the output: 
    'Complex Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible for gastric acid secretion in the stomach.' 
    'Organism: Mouse
    'Proteins: ATP4A, ATP4B"""
}

# 1. Create JSONL file
with open("batch_input.jsonl", "w") as f:
    for complex_name in complexes:
        for technique, template in prompt_techniques.items():
            prompt = template.format(complex=complex_name)
            json_line = {
                "custom_id": f"{complex_name}|{technique}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}]
                }
            }
            f.write(json.dumps(json_line) + "\n")

# 2. Upload input file
upload = openai.files.create(file=open("batch_input.jsonl", "rb"), purpose="batch")

# 3. Create batch job
batch = openai.batches.create(
    input_file_id=upload.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# 4. Save batch ID
with open("batch_job_id.txt", "w") as f:
    f.write(batch.id)

print("✅ Batch submitted. ID:", batch.id)
print("⏳ Status:", batch.status)

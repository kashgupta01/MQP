import openai

openai.api_key = ""

batch_id = open("batch_job_id.txt").read().strip()
batch = openai.batches.retrieve(batch_id)

if batch.status == "completed":
    file_id = batch.output_file_id
    content = openai.files.retrieve_content(file_id)

    with open("batch_output.jsonl", "wb") as f:
        f.write(content)
    print("✅ Output saved to batch_output.jsonl")
else:
    print("⏳ Batch not ready yet. Status:", batch.status)

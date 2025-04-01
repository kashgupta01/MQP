import openai
import requests
import pandas as pd

# Initialize API keys 
# OPENAI_API_KEY = ""
PERPLEXITY_API_KEY = ""
# ANTHROPIC_API_KEY = ""

# Define LLM APIs
LLM_APIS = {
    # "ChatGPT": ("https://api.openai.com/v1/chat/completions", OPENAI_API_KEY),
    "Perplexity": ("https://api.perplexity.ai/chat/completions", PERPLEXITY_API_KEY),
    # "Anthropic": ("https://api.anthropic.com/v1/messages", ANTHROPIC_API_KEY)
}

# Define list of protein complexes (do in batches?)
complexes = ["ATP4A-ATP4B complex", "Transmembrane channel-like (TMC) 2 complex"]

# Define prompting techniques
prompt_techniques = {
    "zero-shot": "For each of the following protein {complex}, provide the function of the protein complex by labelling it as 'Function'. Give the organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster) by labelling it as 'Organism'. Additionally, include a list of proteins the {complex} consists of and label the list 'Proteins'.",
    
    "few-shot": "For each of the following protein {complex}, provide the function of the protein complex and Gthe organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster). Additionally, include a list of proteins the {complex} consists of. Here are some examples of the output:
    'Function: This is a part of the larger ATP4 or H+/K+ ATPase complex, a proton pump responsible for gastric acid secretion in the stomach.' 
    'Organism: Mouse'
    'Proteins: ATP4A, ATP4B'"
    , 
            
    "contextual": "You are an expert in the field of biology and molecular machines. For each of the following protein {complex}, give the organism it belongs to (human, mouse/rat, C.elegans, or Drosophila melanogaster). Additionally, include a list of proteins the {complex} consists of."
}

# Initialize results list
results = []

#Method to call each API  
def call_api(llm_name, prompt):
    url, api_key = LLM_APIS[llm_name]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    if llm_name == "ChatGPT":
        data = {"model": "gpt-4", "messages": [{"role": "user", "content": prompt}]}
    elif llm_name == "Perplexity":
        data = {"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]}
    # elif llm_name == "Anthropic":
    #     data = {"model": "claude-2", "messages": [{"role": "user", "content": prompt}]}
    
    response = requests.post(url, json=data, headers=headers)
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

# Loop through each complex and each prompt technique
#Right now it just records responses in 1 row, but find a way to do it in separated columns 
for complex_name in complexes:
    for technique, template in prompt_techniques.items():
        prompt = template.format(complex=complex_name)
        
        for llm_name in LLM_APIS.keys():
            response_text = call_api(llm_name, prompt)
            results.append({
                "Complex": complex_name,
                "Technique": technique,
                "LLM": llm_name,
                "Response": response_text
            })

# Convert results to DataFrame
results_df = pd.DataFrame(results)
results_df.to_csv("protein_complexes_results.csv", index=False)

print("Data collection complete. Results saved to protein_complexes_results.csv.")

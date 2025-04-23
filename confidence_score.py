import pandas as pd
import numpy as np

combined_csv = ("all_62_complexes\combined_llm_results.csv")

df = pd.read_csv(combined_csv)

claude_dfs = {
    'haiku_zero_df' : [],
    'haiku_few_df' : [],
    'haiku_cont_df' : [],

    'sonnet_zero_df' : [],
    'sonnet_few_df' : [],
    'sonnet_cont_df' : [],

    'opus_zero_df' : [],
    'opus_few_df' : [],
    'opus_cont_df' : [],
}

chat_dfs = {
    'gpt-4-1_zero_df' : [],
    'gpt-4-1_few_df' : [],
    'gpt-4-1_cont_df' : [],

    'gpt-4o_zero_df' : [],
    'gpt-4o_few_df' : [],
    'gpt-4o_cont_df' : [],

    'o4-mini_zero_df' : [],
    'o4-mini_few_df' : [],
    'o4-mini_cont_df' : [],
}


for index, col in df.loc[:, ['Model', 'Technique', 'Confidence Score']].iterrows():
    model = col['Model']
    technique = col['Technique']

    match model:
        case "claude-3-5-haiku":
            if technique == "zero-shot":
                claude_dfs['haiku_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                claude_dfs['haiku_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                claude_dfs['haiku_cont_df'].append(col['Confidence Score'])
            else: 
                print("haiku technique not found")

    match model:
        case "claude-3-7-sonnet":
            if technique == "zero-shot":
                claude_dfs['sonnet_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                claude_dfs['sonnet_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                claude_dfs['sonnet_cont_df'].append(col['Confidence Score'])
            else: 
                print("sonnet technique not found")

    match model:
        case "claude-3-opus":
            if technique == "zero-shot":
                claude_dfs['opus_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                claude_dfs['opus_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                claude_dfs['opus_cont_df'].append(col['Confidence Score'])
            else: 
                print("opus technique not found")

    match model:
        case "gpt-4-1":
            if technique == "zero-shot":
                chat_dfs['gpt-4-1_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                chat_dfs['gpt-4-1_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                chat_dfs['gpt-4-1_cont_df'].append(col['Confidence Score'])
            else: 
                print("gpt-4-1 technique not found")

    match model:
        case "gpt-4o":
            if technique == "zero-shot":
                chat_dfs['gpt-4o_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                chat_dfs['gpt-4o_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                chat_dfs['gpt-4o_cont_df'].append(col['Confidence Score'])
            else: 
                print("gpt-4o technique not found")

    match model:
        case "o4-mini":
            if technique == "zero-shot":
                chat_dfs['o4-mini_zero_df'].append(col['Confidence Score'])
            elif technique == "few-shot":
                chat_dfs['o4-mini_few_df'].append(col['Confidence Score'])
            elif technique == "contextual":
                chat_dfs['o4-mini_cont_df'].append(col['Confidence Score'])
            else: 
                print("o4-mini technique not found")


for key, series in claude_dfs.items():
    convert_to_num = pd.to_numeric(series, errors="coerce")
    mean = np.nanmean(convert_to_num)
    non_num_count = pd.isna(convert_to_num).sum()
    print(f"\n{key}: \nScore Mean: {mean}\nUndefined Values: {non_num_count}")



import pandas as pd

csv_paths = {
    "claude-3-5-haiku" : "all_62_complexes\claude-3-5-haiku_v2_parsed.csv",
    "claude-3-7-sonnet" : "all_62_complexes\claude-3-7-sonnet_v2_parsed.csv",
    "claude-3-opus" : "all_62_complexes\claude-3-opus_v2_parsed.csv",
    "gpt-4-1"       : "all_62_complexes\gpt-4-1_v2_parsed.csv",    
    "gpt-4o"         : "all_62_complexes\gpt-4o_v2_parsed.csv",
    "o4-mini"    : "all_62_complexes\o4-mini_v2_parsed.csv",
}

# read csv and collect/label each model into a dataframe
dataframes = []
for model, path in csv_paths.items():
    df = (
    pd.read_csv(path, dtype=str, keep_default_na=False)
      .assign(Model=model)
    )
    dataframes.append(df)

df_all = pd.concat(dataframes, ignore_index=True)

# reorder so that model colum is first
cols = ["Model"] + [c for c in df_all.columns if c != "Model"]
df_all = df_all[cols]

out_path = "combined_llm_results.csv"
df_all.to_csv(out_path, index=False)
print(f"Combined file written to: {out_path}")

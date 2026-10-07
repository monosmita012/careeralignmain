import pandas as pd
pd.set_option("display.max_columns", None)   
pd.set_option("display.max_colwidth", 60)

for name in ["all_job_post", "dma_dataset", "candidate_role"]:
    df = pd.read_csv(f"data/raw/{name}.csv")
    print("=" * 50, name)
    print(df.shape)
    print(df.dtypes)
    print(df.head(3))
    print(df.isnull().sum())
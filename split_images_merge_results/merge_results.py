import pandas as pd

result_paths = ['../results.csv', '../results_for_paper.csv']
output_path = 'merged_results.csv'

dfs = pd.DataFrame()
for rst in result_paths:
    dfs = dfs.append(pd.read_csv(rst))
print(dfs)
dfs.to_csv(output_path)

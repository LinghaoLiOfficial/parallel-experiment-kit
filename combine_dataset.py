if __name__ == '__main__':
    import pandas as pd

    dataset_path = 'result/0429_10000_papers/phase_three_output_data_part_{}.csv'
    dataset_num = 10
    output_path = 'result/0429_10000_papers/output_data_all.csv'

    paper_df_list = []

    for i in range(1, dataset_num + 1):
        paper_df = pd.read_csv(
            dataset_path.format(str(i)),
            encoding='utf-8',
            index_col=False
        )
        paper_df_list.append(paper_df)

    # 按读取顺序纵向拼接
    full_paper_df = pd.concat(paper_df_list, axis=0, ignore_index=True)

    # 保存为新的完整 csv 文件
    full_paper_df.to_csv(output_path, encoding='utf-8-sig', index=False)

    print(f'拼接完成，共 {len(full_paper_df)} 条数据，已保存至：{output_path}')
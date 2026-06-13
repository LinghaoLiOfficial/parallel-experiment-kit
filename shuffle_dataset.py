if __name__ == '__main__':
    import csv
    import random

    random_state = 42
    old_data_path = 'data/ai_exposure/result01.csv'
    new_data_path = 'data/ai_exposure/shuffled_result01.csv'

    # 按 CSV 记录打乱，避免 pandas 解析异常，也避免按物理行打乱破坏带换行的字段。
    with open(old_data_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    if not all_rows:
        raise ValueError(f'输入文件为空: {old_data_path}')

    header = all_rows[0]
    rows = all_rows[1:]

    # 去除列数超过 7 的记录（仅保留列数 <= 7 的行）
    filtered_rows = [row for row in rows if len(row) <= 7]
    indexed_rows = list(enumerate(filtered_rows))

    rng = random.Random(random_state)
    rng.shuffle(indexed_rows)

    with open(new_data_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([*header, 'original_index'])
        for original_index, row in indexed_rows:
            writer.writerow([*row, original_index])

    print(f'数据集已成功打乱并保存为 {new_data_path}！')
    print(f'原始记录数(不含表头): {len(rows)}')
    print(f'过滤后记录数(不含表头): {len(filtered_rows)}')
    print(f'新数据集记录数(不含表头): {len(indexed_rows)}')

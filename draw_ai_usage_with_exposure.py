if __name__ == '__main__':
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    dataset_path = 'result/0429_10000_papers/output_data_all.csv'
    img_path = './draw_ai_usage_with_exposure.png'

    df = pd.read_csv(
        dataset_path,
        encoding='utf-8',
        index_col=False
    )

    mask = (
            pd.to_numeric(df['ai_usage_rate'], errors='coerce').notna() &
            pd.to_numeric(df['ai_exposure_rate'], errors='coerce').notna()
    )
    df_clean = df[mask].copy()

    df_clean['ai_usage_rate'] = df_clean['ai_usage_rate'].astype(float)
    df_clean['ai_exposure_rate'] = df_clean['ai_exposure_rate'].astype(float)

    # 画布大小
    fig, ax = plt.subplots(figsize=(8, 6))

    # 绘制散点图：修改散点大小和颜色
    sns.scatterplot(
        data=df_clean,
        x='ai_exposure_rate',
        y='ai_usage_rate',
        s=40,  # 散点大小
        color='blue',  # 散点颜色
        alpha=0.2,  # 透明度，可选
        ax=ax
    )

    # 将横纵坐标轴移动到图像正中央，形成十字形
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('center')

    # 隐藏上边框和右边框
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    # 让刻度只显示在中间的横纵轴上
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    # 添加横轴箭头
    ax.annotate(
        '',
        xy=(1.03, 0.5),
        xytext=(-0.03, 0.5),
        xycoords='axes fraction',
        arrowprops=dict(arrowstyle='->', linewidth=1.5, color='black')
    )
    # 添加纵轴箭头
    ax.annotate(
        '',
        xy=(0.5, 1.03),
        xytext=(0.5, -0.03),
        xycoords='axes fraction',
        arrowprops=dict(arrowstyle='->', linewidth=1.5, color='black')
    )

    plt.xlabel('AI Exposure Rate')
    plt.ylabel('AI Usage Rate')

    # 把 x 轴 label 移到右侧箭头附近
    ax.xaxis.set_label_coords(0.90, 0.55)
    # 把 y 轴 label 移到上方箭头附近
    ax.yaxis.set_label_coords(0.54, 0.90)

    plt.savefig(img_path, dpi=300, bbox_inches='tight')







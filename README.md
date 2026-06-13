# ai-exposure-calculation

AI 暴露度计算实验仓库。

这个仓库已经不再依赖 `wd_basekit`。原先从 `wd_basekit` 使用的能力已经内聚到本仓库自己的 `infrastructure/` 目录中，包括：
- 日志
- `Result` 返回结构
- CSV / JSON 文件处理
- FAISS 向量索引
- Neo4j Cypher 访问
- LLM API client 与 prompt parser
- 路径、时间、JSON schema 校验等基础工具

## 目录说明

- `app.py`: 默认运行入口
- `experiments/ai_exposure/`: AI 暴露度实验主体
- `framework/`: 多阶段并行执行框架
- `infrastructure/`: 本仓库内置基础设施实现
- `fix_ai_exposure_csv_schema.py`: 对历史 CSV 结果按固定 schema 重排列顺序

## 环境准备

建议使用 Python 3.11 或 3.12。

安装依赖：

```bash
pip install -r requirements.txt
```

`app.py` 入口现在也已经不再依赖 `aiwebcore`。

## 环境变量

项目使用根目录下的 `.env`。至少需要根据你的本地环境配置这些变量：

```env
ENV=dev
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs
LOG_MAX_SIZE_MB=10
LOG_BACKUP_COUNT=5

NEO4J_CONNECTOR_URI=bolt://localhost:7687
NEO4J_CONNECTOR_AUTH_USER=neo4j
NEO4J_CONNECTOR_AUTH_PASSWORD=your-password

QWEN_TEXT_API_KEY=your-text-key
QWEN_TEXT_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_EMBEDDING_API_KEY=your-embedding-key
QWEN_EMBEDDING_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 可选兜底：如果你不区分 text / embedding，也可以只配这一组
QWEN_API_KEY=your-shared-key
QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

OPENAI_API_URL=https://your-openai-compatible-endpoint/v1
OPENAI_API_KEY=your-key

ZHIPU_API_KEY=your-key
ZHIPU_API_URL=https://open.bigmodel.cn/api/paas/v4/
```

建议把仓库中的示例 `.env` 视为占位模板，替换为你自己的本地密钥和密码。

## 运行

默认入口：

```bash
python3 run/run_ai_exposure.py
```

`run/run_ai_exposure.py` 中当前内置了一组实验配置，包括输入数据路径、结果目录、并发数和是否断点续跑等参数。若要改任务配置，直接调整 [run/run_ai_exposure.py](/Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_exposure.py) 中的 `experiment_config`。

摘要级 AI 研究分析任务入口：

```bash
python3 run/run_ai_research_analysis.py
```

`run/run_ai_research_analysis.py` 中当前已内置：
- 固定 `task_id`
- 默认数据集路径 `data/ai_research_analysis/AI4S_llms_parse_with_openalex_title_abstract.csv`
- 默认模型配置
- 默认输出目录 `result/{task_id}/`

若要改任务配置，直接调整 [run/run_ai_research_analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_research_analysis.py) 中的变量与 `experiment_config`。

输入 CSV 至少需要包含摘要列，支持这些常见列名：
- `abstract`
- `full_abstract`
- `paper_abstract`
- `Abstract`
- `openalex_abstract`

如果有编号列，优先读取：
- `abstract_ID`
- `abstract_id`
- `id`
- `ID`
- `work_id`

如果有标题列，优先读取：
- `title`
- `paper_title`
- `Title`
- `openalex_title`

运行后会在结果目录生成：
- `analysis_output_data_part_*.csv`：完整明细结果
- `task1_phase_ai_usage.txt` / `.md` / `.csv`
- `task2_ai_function.txt` / `.md` / `.csv`
- `task3_ai_role.csv`
- `task4_essentiality.csv`

## CSV 修复脚本

如果历史 `phase_one` / `phase_two` / `phase_three` CSV 存在列顺序问题，可以用下面的脚本按固定 schema 重排列顺序：

```bash
python3 /Users/llh/PycharmProjects/parallel-experiment-kit/fix_ai_exposure_csv_schema.py \
  --stage phase_two \
  /path/to/input.csv \
  /path/to/output.fixed.csv
```

可选的 `--stage`：
- `phase_one`
- `phase_two`
- `phase_three`

## 当前状态

- `wd_basekit/` 目录和 `wd_basekit-0.1.40*.whl` 已从仓库中清理
- `aiwebcore` 的本仓库使用面也已内置，不再需要 `aiwebcore` 提供 `get_settings()` / `lifespan()`
- 业务代码已改为只引用本仓库内的 `infrastructure/` 实现
- CSV 追加写入已修复“列集合相同但顺序不同导致串列”的问题

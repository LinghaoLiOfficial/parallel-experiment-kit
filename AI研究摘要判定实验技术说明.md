# AI研究摘要判定实验技术说明

## 1. 文档目的

本文档用于完整说明当前仓库中新建实验 `ai_research_analysis` 的业务目标、输入输出约定、程序结构、处理流程、字段定义、提示词设计、运行方式、结果文件格式、边界条件与扩展建议。

该实验面向“论文摘要级别”的 AI 使用识别任务，目标是对一批已初步筛选为“可能使用了 AI”的论文摘要进行结构化分析，并输出以下四类结果：

1. AI 在研究流程不同环节中的使用类型；
2. AI 在研究中实现的功能；
3. AI 在研究中的“定位”；
4. AI 在研究中的必要性强弱及 0-5 分量化评分。

本实验复用了仓库既有的并行流水线框架、LLM 结构化解析机制、CSV 结果持久化机制，因此整体风格与 `ai_exposure` 实验保持一致，但在业务逻辑上是一个独立实验，不依赖 AI 暴露度的三阶段推断链路。

---

## 2. 业务目标

### 2.1 任务背景

用户给定若干论文摘要，这些摘要已经被人为或上游规则初步判定为“涉及 AI”。本实验不负责做“是否使用 AI”的初筛，而是在此基础上继续完成更细颗粒度的结构化识别。

### 2.2 四项输出任务

#### 任务一：研究环节中的 AI 使用类型

针对每篇摘要，识别 AI 是否用于以下四个研究环节：

1. 假设生成
2. 实验分析
3. 数据处理
4. 结果分析

其中，“假设生成”在当前实验中采用放宽口径。除“AI 明确用于提出科学假设”外，以下情形也允许判入该环节：

- AI 用于发现潜在模式、异常结构或候选规律；
- AI 用于识别候选关系、候选变量或候选机制；
- AI 用于筛选后续检验对象、研究方向或解释思路；
- AI 在正式实验分析前承担“知识形成”或“研究问题形成辅助”的角色。

相反，如果摘要只描述 AI 用于分类、预测、识别、测量、训练模型或结果解释，而未体现上述前置认知作用，则“假设生成”仍判为 `none`。

并为每个环节输出一个 AI 技术类别，类别集合固定为：

- `专家系统` = 0
- `知识表示` = 1
- `计算机视觉` = 2
- `机器学习` = 3
- `深度学习` = 4
- `进化计算` = 5
- `自然语言处理` = 6
- `大语言模型` = 7
- `强化学习` = 8
- `具身智能/机器人` = 9
- `none`

如果摘要中无法支持某一环节使用 AI，则该环节输出 `none`。

#### 任务二：AI 实现的功能

针对每篇摘要，识别 AI 实现了哪些功能。允许多选，功能集合固定为：

- `信息检索与提取` = 0
- `现象检测/监测` = 1
- `聚类与分类` = 2
- `推理/推断` = 3
- `估计、模拟与预测` = 4
- `决策与优化` = 5
- `流程加速` = 6
- `内容生成` = 7
- `none`

若摘要中不能合理识别上述功能，则输出 `none`。

#### 任务三：AI 在研究中的定位

针对每篇摘要，判断 AI 在研究中的角色定位。允许多选，定位集合固定为：

- `domain facilitator` = 1
- `method upgrader` = 2
- `episteme expander` = 3
- `none` = 0

同时要求输出支撑该判断的原句证据。

#### 任务四：AI 使用必要性评分

针对每篇摘要，依据摘要描述判断 AI 在研究中的必要性强弱，输出 `0-5` 的整数评分，并输出支撑该评分的原句证据。

评分定义如下：

- `0`：无法判断
- `1`：仅作为常规工具，明显可替代
- `2`：用于辅助处理或效率提升，但非核心
- `3`：用于核心分析任务，但传统方法可能完成
- `4`：AI 显著改变研究能力，传统方法难以达到相同效果
- `5`：没有 AI 基本无法开展该研究或无法得到核心发现

---

## 3. 实验在仓库中的位置

### 3.1 主要文件

本实验新增的核心文件如下：

- [run/run_ai_research_analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_research_analysis.py)
- [experiments/ai_research_analysis/experiment.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/experiment.py)
- [experiments/ai_research_analysis/schema.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/schema.py)
- [experiments/ai_research_analysis/stages/base.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/stages/base.py)
- [experiments/ai_research_analysis/stages/analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/stages/analysis.py)
- [experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisTemplate.json](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisTemplate.json)
- [experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisSchemas.json](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisSchemas.json)

并在以下文件完成注册接入：

- [experiments/registry.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/registry.py)
- [README.md](/Users/llh/PycharmProjects/parallel-experiment-kit/README.md)

### 3.2 与 `ai_exposure` 的关系

`ai_research_analysis` 与 `ai_exposure` 的关系是“同框架下的独立实验”：

- 共用 `framework/` 下的并行执行框架；
- 共用 `infrastructure/llm/` 的 LLM 结构化输出机制；
- 共用 `infrastructure/storage/` 的 CSV 持久化能力；
- 不复用 `ai_exposure` 的研究主题筛选、向量检索、技术成熟度或 AI 暴露度计算逻辑；
- 不依赖 Neo4j、FAISS、历史方法库等重型能力。

换句话说，当前实验是一个“摘要结构化判定器”，而不是“AI 暴露度测算器”。

---

## 4. 技术架构

## 4.1 总体结构

实验采用“单阶段并行分析 + 结果导出”的设计。整体链路为：

1. 读取输入 CSV；
2. 标准化摘要 ID、标题、摘要列；
3. 针对每篇摘要调用一次 LLM 结构化判定；
4. 对 LLM 返回值做字段归一化、别名映射、编号映射；
5. 将完整结果写入明细 CSV；
6. 在实验结束时自动导出面向四项任务的文本、Markdown、CSV 文件。

需要说明的是，当前版本对“假设生成”采用扩展判定规则，因此该阶段并不局限于严格意义上的显式科学假设提出，而是包含“模式发现到候选解释形成”的上游认知活动。

### 4.2 为什么是单阶段

本实验没有拆成多阶段，原因是：

1. 四项业务任务都围绕同一份摘要文本展开；
2. 各任务共享相同的输入上下文；
3. 结果之间不存在强顺序依赖；
4. 多阶段拆分会增加中间文件复杂度，但不会显著提高质量。

因此当前版本采用单次 LLM 调用，统一返回完整 JSON 结构，再进行后处理。

### 4.3 运行入口

运行入口文件为 [run/run_ai_research_analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_research_analysis.py)。

该入口负责：

1. 初始化运行环境；
2. 在脚本内定义固定 `task_id`、数据路径和结果路径；
3. 在脚本内构造实验配置；
4. 调用 `run_experiment("ai_research_analysis", experiment_config)` 执行实验。

### 4.4 实验类

[experiments/ai_research_analysis/experiment.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/experiment.py) 中定义了：

- `AIResearchAnalysisExperimentConfig`
- `AIResearchAnalysisExperiment`
- `run_ai_research_analysis_experiment`

其中：

- `AIResearchAnalysisExperimentConfig` 用于承载实验配置；
- `AIResearchAnalysisExperiment` 负责构造 `ExperimentContext`、初始化 `LLMService`、注册 stage；
- 当前只注册一个 stage，即 `AIResearchAnalysisStage`。

### 4.5 Stage 设计

[experiments/ai_research_analysis/stages/analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/stages/analysis.py) 是核心业务实现。

该 stage 负责：

1. 加载和标准化输入数据；
2. 并行处理每篇摘要；
3. 调用 LLM 获得结构化判定结果；
4. 将英文标准标签映射到要求的输出表示，并兼容中文旧值；
5. 写入总表；
6. 实验结束后导出任务级结果文件。

---

## 5. 输入数据规范

### 5.1 输入文件格式

输入为一个 CSV 文件，每一行代表一篇论文摘要。

### 5.2 支持的列名

程序会自动兼容多种常见列名。

#### 摘要 ID 列

优先顺序如下：

- `abstract_ID`
- `abstract_id`
- `id`
- `ID`
- `work_id`

若都不存在，程序会自动用行号生成字符串型 `abstract_ID`。

#### 标题列

优先顺序如下：

- `title`
- `paper_title`
- `Title`
- `openalex_title`

若不存在，标题将被置为空字符串。

#### 摘要列

优先顺序如下：

- `abstract`
- `full_abstract`
- `paper_abstract`
- `Abstract`
- `openalex_abstract`

如果上述列都不存在，程序会直接报错。

### 5.3 标准化后的内部字段

程序加载后，会统一形成以下内部三列：

- `abstract_ID`
- `title`
- `abstract`

这三列会缓存在 `context.state["paper_df"]` 中供后续 stage 使用。

---

## 6. 输出数据规范

### 6.1 明细总表

主结果文件为：

- `analysis_output_data_part_*.csv`

其字段定义在 [experiments/ai_research_analysis/schema.py](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/schema.py) 中：

- `abstract_ID`
- `paper_title`
- `paper_abstract`
- `hypothesis_AI_use`
- `experiment_AI_use`
- `data_AI_use`
- `result_AI_use`
- `AI_function`
- `ai_role`
- `ai_role_sentence`
- `essentiality`
- `essentiality_sentence`

### 6.2 任务一输出

自动导出以下文件：

- `task1_phase_ai_usage.txt`
- `task1_phase_ai_usage.md`
- `task1_phase_ai_usage.csv`

字段为：

- `abstract_ID`
- `hypothesis_AI_use`
- `experiment_AI_use`
- `data_AI_use`
- `result_AI_use`

#### 文本格式

每篇摘要渲染为：

```text
-摘要ID
[假设生成]：...
[实验分析]：...
[数据处理]：...
[结果分析]：...
```

#### Markdown 格式

使用 `pandas.DataFrame.to_markdown()` 生成表格。

#### CSV 格式

列名固定为：

- `abstract_ID`
- `hypothesis_AI_use`
- `experiment_AI_use`
- `data_AI_use`
- `result_AI_use`

### 6.3 任务二输出

自动导出以下文件：

- `task2_ai_function.txt`
- `task2_ai_function.md`
- `task2_ai_function.csv`

字段为：

- `abstract_ID`
- `AI_function`

#### 文本格式

每篇摘要渲染为：

```text
-摘要ID：功能编号
```

若多值，则用 `|` 拼接，例如：

```text
-A001：2|4|6
```

### 6.4 任务三输出

自动导出：

- `task3_ai_role.csv`

字段为：

- `abstract_ID`
- `ai_role`
- `sentence`

其中：

- `ai_role` 为编码后的定位结果；
- `sentence` 为支撑判断的摘要原句，多个句子之间使用 ` || ` 拼接。

### 6.5 任务四输出

自动导出：

- `task4_essentiality.csv`

字段为：

- `abstract_ID`
- `essentiality`
- `sentence`

其中：

- `essentiality` 为 0-5 整数分；
- `sentence` 为支撑评分的摘要原句，多个句子之间使用 ` || ` 拼接。

---

## 7. LLM 判定逻辑

### 7.1 单次判定策略

程序对每篇摘要只调用一次 LLM，请其一次性返回完整 JSON，包含：

1. 四个研究环节的 AI 使用类型；
2. AI 功能列表；
3. AI 定位列表；
4. AI 定位的证据句；
5. 必要性评分；
6. 必要性证据句。

这样做的优点是：

1. 降低单篇摘要的 API 调用次数；
2. 避免多轮调用产生标签不一致；
3. 使四项判断建立在同一理解上下文上。

### 7.2 提示词模板

模板文件位于：

- [AbstractAIResearchAnalysisTemplate.json](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisTemplate.json)

模板特点如下：

1. 明确说明任务目标；
2. 明确列出合法标签集合；
3. 明确指出“不能臆测，信息不足返回 none 或 0”；
4. 明确要求只返回 JSON；
5. 给出一个结构示例，帮助模型对齐字段格式。

### 7.3 Schema 约束

Schema 文件位于：

- [AbstractAIResearchAnalysisSchemas.json](/Users/llh/PycharmProjects/parallel-experiment-kit/experiments/ai_research_analysis/llm/AbstractAIResearchAnalysis/AbstractAIResearchAnalysisSchemas.json)

Schema 约束了以下结构：

- `phase_ai_usage` 必须是对象；
- 必须包含四个固定阶段键；
- `ai_functions` 必须是数组；
- `ai_role` 必须是数组；
- `ai_role_sentence` 必须是数组；
- `essentiality` 必须是整数；
- `essentiality_sentence` 必须是数组。

这层约束不会校验“值是否一定在枚举集合内”，但能保证整体 JSON 结构稳定。

---

## 8. 后处理与编码映射

### 8.1 为什么要做后处理

LLM 即使在结构化输出场景下，也可能返回以下变体：

1. 返回英文标准标签；
2. 返回中文旧标签；
3. 返回数字编号；
4. 返回中英混合；
5. 返回近义别名；
6. 返回空列表、空字符串或本应为数组的单字符串。

为了提高鲁棒性，程序在写出结果前做了一层“标签归一化 + 编码映射”。

### 8.2 研究环节 AI 类型映射

代码中定义：

- `AI_USE_ALIASES`
- `AI_USE_LABEL_TO_CODE`

处理策略是：

1. 先把模型输出规范化为标准英文标签；
2. 同时兼容中文旧标签和数字编号；
3. 再根据需求输出到阶段字段中。

当前阶段字段最终写的是标准英文标签，例如：

- `machine learning`
- `deep learning`
- `none`

这部分和任务描述略有差异：任务描述给出了类别与编号的对应关系，但任务一文本模板要求填“AI技术名称”。因此当前实现保留英文名称而不是编码数字，更利于文本和 Markdown 阅读，也更有利于与英文摘要保持一致。

### 8.3 AI 功能映射

功能映射分两层：

1. `AI_FUNCTION_ALIASES` 负责把英文标签、中文旧标签或编号规范化为标准英文标签；
2. `AI_FUNCTION_LABEL_TO_CODE` 负责把标准英文标签转换为编号。

最终输出到 `AI_function` 字段的是编号表示：

- 单值示例：`2`
- 多值示例：`2|4|6`
- 无法判断：`none`

### 8.4 AI 定位映射

定位映射同样分两层：

1. `AI_ROLE_ALIASES`
2. `AI_ROLE_LABEL_TO_CODE`

支持这些别名输入：

- `赋能应用` -> `domain facilitator` -> `1`
- `工具方法` -> `method upgrader` -> `2`
- `认识知识` -> `episteme expander` -> `3`
- `none` -> `0`

最终输出到 `ai_role` 的是编号表示：

- 单值示例：`2`
- 多值示例：`1|2`
- 无匹配：`0`

### 8.5 结果结构容错

为提高结构化抽取的稳定性，当前实现还增加了额外容错：

1. 若模型把应为数组的字段输出成单个字符串，则自动包装成单元素列表；
2. 若模型返回 `none`、空字符串或 `NaN` 风格缺失值，则统一回填为默认结果；
3. 若 `ai_role=0` 或 `essentiality=0`，则自动清空对应证据句，保证结果一致性；
4. 若存在“正向分数但无证据句”的样本，则自动导出审查表供人工复核。

### 8.6 必要性分数归一化

`essentiality` 会被强制归一化到 `[0, 5]` 区间：

1. 若无法转成整数，则记为 `0`；
2. 小于 `0` 的值截断为 `0`；
3. 大于 `5` 的值截断为 `5`。

这保证了最终 CSV 一定满足业务要求。

---

## 9. 关键流程详解

## 9.1 `prepare`

`AIResearchAnalysisStage.prepare()` 负责：

1. 读取并标准化输入 CSV；
2. 初始化 `CSVFileHandler`，准备写入 `analysis_output_data.csv`。

这里使用 `write_mode="a"`，意味着输出将按追加、分片、断点续跑的方式写入。

## 9.2 `get_indices`

`get_indices()` 根据：

- 已处理条数；
- 输入总条数；
- `max_paper_num`

构建本轮实际需要执行的索引范围。

因此实验天然支持：

1. 截断测试；
2. 中断后续跑；
3. 多批次处理。

## 9.3 `process_row`

这是最核心的方法。每一行执行流程如下：

1. 读取 `abstract_ID`、标题、摘要；
2. 调用 `LLMService.parse_text()`；
3. 使用模板和 JSON schema 约束模型输出；
4. 解析 `phase_ai_usage`；
5. 映射四个阶段的 AI 类型；
6. 解析 `ai_functions` 并转编号；
7. 解析 `ai_role` 并转编号；
8. 提取 `ai_role_sentence`；
9. 解析 `essentiality` 并归一化；
10. 提取 `essentiality_sentence`。

若某条摘要处理失败，程序不会中断整体任务，而是返回已知基本字段，剩余字段留空。这种设计适合批处理任务。

## 9.4 `flush_result`

`flush_result()` 负责：

1. 按 schema 补全缺失列；
2. 将当前摘要结果写入 CSV 分片文件；
3. 输出日志。

## 9.5 `finalize`

在所有摘要处理完成后，`finalize()` 会：

1. 刷新缓存到磁盘；
2. 读取完整总表；
3. 生成四项任务的对外文件。

这一步把“模型原始结构化结果”转成“用户可直接使用的交付件”。

---

## 10. 并行与断点续跑机制

### 10.1 并行执行

实验依赖 [framework/core/runner.py](/Users/llh/PycharmProjects/parallel-experiment-kit/framework/core/runner.py) 中的 `PipelineRunner`。

每个 stage 会通过 `ThreadPoolExecutor` 并行处理多条摘要。

并发数来源于：

- 优先读取配置中的 `max_workers`；
- 若未指定，则由框架默认按 CPU 数量取上限。

### 10.2 有序写出

虽然处理是并行的，但框架内部会按输入顺序依次 flush 结果，因此最终输出文件行顺序与输入顺序一致。

### 10.3 断点续跑

`CSVFileHandler` 会维护一个同名 `.json` 元数据文件，记录：

- 当前写入分片；
- 已处理条数；
- 已记录条数；
- 执行时长。

当 `resume=True` 时，可以基于该元文件继续执行。

---

## 11. 运行方式

### 11.1 基本命令

```bash
python3 /Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_research_analysis.py
```

### 11.2 当前内置配置

- 固定 `task_id`
- 默认输入数据集 `data/ai_research_analysis/AI4S_llms_parse_with_openalex_title_abstract.csv`
- 默认结果目录 `result/{task_id}/`
- 默认模型 `qwen / qwen3.6-flash`
- `resume=True`
- `to_shuffle=False`
- `max_workers=10`

### 11.3 调整方式

若需要替换数据集、任务 ID、模型或输出规模，直接修改 [run/run_ai_research_analysis.py](/Users/llh/PycharmProjects/parallel-experiment-kit/run/run_ai_research_analysis.py) 中的以下变量或配置项：

- `task_id`
- `paper_csv_path`
- `result_path`
- `llm_name`
- `llm_version`
- `checkpoint_rows`
- `max_rows_per_file`
- `resume`
- `max_paper_num`
- `to_shuffle`
- `max_workers`

---

## 12. 依赖与环境要求

### 12.1 Python 版本

仓库当前代码使用了 `str | None`、`dict[str, Any]` 等类型标注语法，因此需要 `Python 3.10+`。

仓库 README 中建议使用：

- `Python 3.11`
- `Python 3.12`

当前若使用 `Python 3.9`，则导入阶段就可能失败，这属于仓库整体兼容性要求，而不只是本实验的问题。

### 12.2 模型配置

本实验依赖 `infrastructure/llm/` 下的统一 LLM API 客户端，因此需要在 `.env` 中正确配置模型服务地址和密钥。

至少需要具备：

1. 文本生成模型访问能力；
2. 与所选 `llm_name` / `llm_version` 对应的可用 API 配置。

---

## 13. 当前实现的设计取舍

### 13.1 优点

1. 架构轻量，接入成本低；
2. 完整复用现有实验框架；
3. 单次调用即可返回四项任务结果，成本较低；
4. 输入列名兼容性较好；
5. 自动导出文本、Markdown、CSV 三类结果；
6. 对模型输出的别名和编号具备一定容错能力。

### 13.2 已知限制

1. 所有判断都基于摘要，无法利用全文补充上下文；
2. 当前 schema 只约束结构，不强约束枚举值；
3. 任务一输出保留的是中文 AI 类型名称，而不是编码数字；
4. 任务三和任务四当前只输出 CSV，没有同步导出 Markdown 或文本版；
5. 多值字段当前使用 `|` 拼接，方便 CSV 存储，但不适合作为严格数组格式的下游接口；
6. 必要性与定位的证据句完全依赖模型抽取，未做二次句子对齐验证。

---

## 14. 后续可扩展方向

### 14.1 提升输出一致性

可以在 JSON schema 外再增加业务级枚举校验，例如：

1. 强制 `phase_ai_usage` 的值只能来自预定义枚举；
2. 强制 `ai_functions` 和 `ai_role` 的数组元素只能来自合法集合；
3. 对 `essentiality` 增加最小值和最大值约束。

### 14.2 增加解释字段

当前任务一和任务二没有保留“依据句”。如果后续需要人工复核，可以新增：

- `phase_ai_usage_sentence`
- `ai_function_sentence`

用于解释模型为什么给出该标签。

### 14.3 增加全文级分析

如果后续不仅输入摘要，而是输入全文或方法段落，可以考虑：

1. 扩展输入字段；
2. 增加分段分析；
3. 让“必要性”与“定位”判断更稳定。

### 14.4 增加后校验模块

可以在 LLM 输出后增加规则校验器，例如：

1. 若 `ai_role=0`，但 `ai_role_sentence` 非空，则记录 warning；
2. 若 `essentiality=0`，但提供了强判断语句，则记录 review 标记；
3. 若四个阶段都是 `none`，但功能不为 `none`，则提示人工复核。

### 14.5 增加统一结果汇总页

当前四项任务分别导出文件。后续可以加一个“交付总览 Markdown”，集中展示：

1. 输入规模；
2. 各标签分布；
3. 失败样本数；
4. 示例判定结果；
5. 输出文件路径。

---

## 15. 一个最小工作示例

假设输入 CSV 内容如下：

```csv
abstract_ID,title,abstract
A001,Example Paper,"We develop a deep learning model to classify satellite images and predict crop yield."
```

程序可能生成类似结果：

### 15.1 任务一

```text
-A001
[假设生成]：none
[实验分析]：深度学习
[数据处理]：计算机视觉
[结果分析]：机器学习
```

### 15.2 任务二

```text
-A001：1|2|4
```

### 15.3 任务三

```csv
abstract_ID,ai_role,sentence
A001,2,"We develop a deep learning model to classify satellite images and predict crop yield."
```

### 15.4 任务四

```csv
abstract_ID,essentiality,sentence
A001,3,"We develop a deep learning model to classify satellite images and predict crop yield."
```

以上只是示意，并不代表固定判定结果；真实结果仍取决于模型对摘要语义的理解。

---

## 16. 结论

`ai_research_analysis` 实验已经在现有仓库框架中完成集成，实现了面向论文摘要的四项 AI 研究判定任务。它的核心特点是：

1. 单阶段并行处理；
2. 单次 LLM 结构化输出；
3. 对业务标签做规范化和编号映射；
4. 自动导出适合人工阅读和机器消费的多种结果文件。

如果后续需要把这个实验进一步产品化，最值得优先加强的方向是：

1. 枚举值强校验；
2. 证据句一致性检查；
3. 任务三与任务四的 Markdown / 文本导出；
4. 基于全文而不是仅摘要的升级版判定流程。

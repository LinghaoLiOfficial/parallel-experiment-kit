# AI暴露度计算理论部分

## 1. 问题定义与符号

设论文集合为 $\mathcal{P}=\{p_i\}_{i=1}^{N}$。对任意论文 $p$，定义其科研流程阶段集合为
$$
\mathcal{S}(p)=\{s_1,s_2,\dots,s_K\},
$$
其中每个阶段 $s_k$ 由大模型抽取，并给出阶段重要性权重（代码字段 `ranking`）$r_k>0$。

归一化阶段权重定义为
$$
w_k=\frac{r_k}{\sum_{j=1}^{K}r_j},\quad \sum_{k=1}^{K}w_k=1.
$$

对每个阶段定义AI使用指示变量
$$
u_k=\mathbb{I}(\text{phase }s_k\text{ uses AI methods}),\quad \nu_k\in\{0,1\}.
$$

## 2. 三阶段计算框架

### 2.1 Phase 1：样本筛选与结构化表征

Phase 1 完成以下任务：
1. 综述论文识别与剔除；
2. 研究问题抽取与主题相关性判别（能源转型/气候变化）；
3. 原始研究流程阶段映射 $\mathcal{S}(p)$ 及每阶段AI使用判断；
4. 对“未使用AI”的论文，将传统方法写入历史方法库（向量化后入库）。

经过筛选后得到有效论文子集 $\mathcal{P}_{\text{valid}}\subseteq\mathcal{P}$。

### 2.2 Phase 2：AI使用度（Usage）与不可替代性

若论文所有阶段均未使用AI（即 $\sum_k \nu_k=0$），则
$$
U(p)=0,\quad I(p)=0,
$$
其中 $U(p)$ 为AI使用度（`ai_usage_rate`），$I(p)$ 为AI不可替代得分（`ai_irreplaceable_score`）。

若模型判定论文AI为“不可或缺”（`ai_necessity = indispensable`），则
$$
U(p)=1,\quad I(p)=1.
$$

若论文“完全基于AI框架”（`ai_usage_level = fully\_based`），则
$$
U(p)=1,\quad I(p)=0.
$$

否则（部分基于AI），使用阶段权重加权得到
$$
U(p)=\sum_{k=1}^{K} w_k\nu_k=\sum_{k=1}^{K}\frac{r_k}{\sum_j r_j}\nu_k,
$$
并记 $I(p)=0$。

### 2.3 Phase 3：AI暴露度（Exposure）

若 $I(p)=1$，代码直接赋值
$$
E(p)=1,
$$
其中 $E(p)$ 对应 `ai_exposure_rate`。

当 $I(p)=0$ 时，系统先生成“AI原生替代方案”阶段映射 $\tilde{\mathcal{S}}(p)$，再进行两类检索匹配：
1. AI技术库匹配（含技术成熟度）；
2. 传统方法库匹配（用于替代可行性上下文）。

对任一阶段 $s_k$，若匹配到AI技术集合 $\mathcal{A}_k=\{a_{k,m}\}$，其中每个候选技术具有：
- 相对贡献分数 $q_{k,m}$（来自 `original_score`）；
- 成熟度 $\mu_{k,m}\in[0,1]$（按论文发表年份读取）。

代码中先进行归一化再取最大值：
$$
\hat{q}_{k,m}=\frac{q_{k,m}}{\sum_{a_{k,t}\in\mathcal{A}_k} q_{k,t}},
$$
$$
\phi_k=\max_{a_{k,m}\in\mathcal{A}_k}(\mu_{k,m}\hat{q}_{k,m}).
$$
若阶段无可用AI技术匹配，则 $\phi_k=0$。

最终暴露度为阶段加权和：
$$
E(p)=\sum_{k=1}^{K} w_k\phi_k=\sum_{k=1}^{K}\frac{r_k}{\sum_j r_j}\phi_k.
$$

## 3. 阈值与检索约束

设向量检索相似度阈值分别为
$$
\tau_{ai}=\texttt{ai\_tech\_distance\_threshold},\quad
\tau_{hist}=\texttt{history\_methods\_distance\_threshold}.
$$

仅保留满足相似度约束的候选：
$$
\text{sim}(x,a)\ge\tau_{ai},\qquad \text{sim}(x,h)\ge\tau_{hist}.
$$

阈值越高，匹配更严格，通常导致暴露度估计更保守。

## 4. 指标解释

1. $U(p)$（AI使用度）：描述“当前论文方法体系中AI介入范围”。
2. $I(p)$（AI不可替代性）：描述“论文是否已达到AI不可缺失状态”的离散判别。
3. $E(p)$（AI暴露度）：描述“在AI原生重构情境下，研究流程可被成熟AI技术覆盖的程度”，是面向替代/重构潜力的连续量化指标。

## 5. 与代码实现的一致性说明

本文公式与实现严格对应于 `aec/AIExposureCalculator.py`：
1. `ai_usage_rate` 由阶段 `ranking` 的归一化加权求和得到；
2. `ai_irreplaceable_score` 由 `ai_necessity` 规则判定（取 $0/1$）；
3. `ai_exposure_rate` 在 `ai_irreplaceable_score=1` 时直接置为 $1$，否则按“阶段权重 $\times$ AI技术成熟度贡献上界”累加。

因此，整套理论可视为“LLM语义判别 + 向量检索匹配 + 成熟度约束加权”的分阶段融合测度模型。

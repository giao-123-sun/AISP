# aisp/protocols/request.py

from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field, DirectoryPath, FilePath

# --- 通用子模块 ---

class Baseline(BaseModel):
    """
    定义一个用于 'improvement' 或 'findings' 任务的基线方法。
    这个基线是研究的起点。
    """
    baseline_name: str = Field(
        ...,
        description="基线方法的名称，例如 'GPT-4-Turbo_CoT_prompting'."
    )
    # AISB 会提供一个标准的 SOTA Baseline 库，可以直接引用
    aisb_sota_id: Optional[str] = Field(
        None,
        description="如果基线是 AISB 上的一个标准 SOTA 方法，请提供其唯一 ID。"
    )
    # 如果提供自定义基线，则需要以下字段
    custom_code_dir: Optional[DirectoryPath] = Field(
        None,
        description="包含基线方法完整可执行代码的目录路径。"
    )
    run_script: FilePath = Field(
        ...,
        description="指向可一键执行基线方法并输出结果的脚本路径，例如 './run.sh'。"
    )
    non_modifiable_files: List[FilePath] = Field(
        default_factory=list,
        description="一组在研究过程中不允许被 AI 修改的文件列表，通常包括评测逻辑和结果打印部分。"
    )

# --- L1 元类型：抽象的研究负载基类 ---

class ResearchPayloadBase(BaseModel):
    """
    【L1 元类型】所有具体研究请求负载的抽象基类。
    它定义了所有研究任务共有的字段。
    """
    # 这个 'type' 字段是实现“可辨识联合类型”的关键。
    # 每个子类都必须用一个字面量来覆盖它。
    type: str = Field(..., description="定义研究类型的唯一标识符。")
    topic: str = Field(..., description="对研究主题或核心目标的高度概括性描述。")

# --- 五种研究类型的具体输入定义 ---

class ImprovementRequestPayload(ResearchPayloadBase):
    """'Improvement' 类型的研究任务详情。"""
    type: Literal["improvement"] = "improvement"
    topic: str = "改进现有基线在特定任务上的表现"
    task_id: str = Field(
        ..., 
        description="要挑战的 AISB 任务的唯一 ID，例如 'agent-swe-bench-v1'。"
    )
    goal_description: str = Field(
        ...,
        description="明确的优化目标，例如 '在保持准确率不低于95%的情况下，将平均推理时间减少20%' 或 '将 SWE-bench 的 a@k 分数提高至少2个百分点'。"
    )
    baseline_to_improve: Baseline = Field(
        ...,
        description="需要被改进的基线方法。"
    )

class FindingsRequestPayload(ResearchPayloadBase):
    """'Findings' 类型的研究任务详情。"""
    type: Literal["findings"] = "findings"
    topic: str = Field(..., description="研究现象或主题的清晰描述，例如 '分析大型语言模型在数学推理中的“抄捷径”现象'。")
    hypotheses: List[str] = Field(
        default_factory=list,
        description="需要通过实验验证的一系列初步假设。"
    )
    related_aisb_tasks: Optional[List[str]] = Field(
        None,
        description="与该现象相关的 AISB 任务 ID 列表，实验将围绕这些任务展开。"
    )
    data_dir: Optional[DirectoryPath] = Field(
        None,
        description="研究所需的私有数据集目录。"
    )

class SurveyRequestPayload(ResearchPayloadBase):
    """'Survey' 类型的研究任务详情。"""
    type: Literal["survey"] = "survey"
    topic: str = Field(..., description="综述的核心主题，例如 '自主语言 Agent 的记忆机制研究综述'。")
    scope: str = Field(..., description="综述的范围和边界，例如 '主要关注 2023 年至今的长短期记忆模块设计'。")
    key_questions: List[str] = Field(
        ...,
        description="这篇综述需要回答的关键问题列表。"
    )

class BenchmarkRequestPayload(ResearchPayloadBase):
    """'Benchmark' 类型的研究任务详情。"""
    type: Literal["benchmark"] = "benchmark"
    domain: str = Field(..., description="新基准所属的领域，例如 '多模态 Agent 的工具使用能力'。")
    task_description: str = Field(..., description="对新基准要评测的核心能力的详细描述。")
    data_source_description: str = Field(..., description="构建该基准所需的数据来源和初步处理方案。")
    draft_eval_metrics: List[str] = Field(..., description="草拟的评测指标列表，例如 ['任务成功率', '步骤效率', 'API 调用合规性']。")

class TechniqueReportPayload(ResearchPayloadBase):
    """'Technique Report' 类型的研究任务详情。"""
    type: Literal["technique_report"] = "technique_report"
    technique_name: str = Field(..., description="新模型、系统或协议的名称。")
    abstract: str = Field(..., description="对该技术的简短摘要，说明其核心思想和目标。")
    target_tasks: List[str] = Field(
        ...,
        description="该技术主要设计用来解决的 AISB 任务 ID 列表。"
    )
    
# --- 统一的科研委托书模型 ---

class ResearchRequest(BaseModel):
    """
    AISP L1 核心输入对象：科研委托书。
    它封装了所有类型的科研任务，并指定了相应的评估流程。
    """
    request_id: str = Field(..., description="本次研究请求的唯一标识符。")
    

    # 根据 research_type 动态选择对应的 payload
    payload: Union[
        ImprovementRequestPayload,
        FindingsRequestPayload,
        SurveyRequestPayload,
        BenchmarkRequestPayload,
        TechniqueReportPayload
    ] = Field(..., description='type')

    # 评估流程定义，直接关联到最终的 '出口'
    # evaluation_flow: List[Literal["DeepReviewer", "CodeAgent", "AISB_Evaluator"]] = Field(
    #     ...,
    #     description="根据研究类型预设的评估流程。例如, 'improvement' 类型应为 ['DeepReviewer', 'CodeAgent', 'AISB_Evaluator']。"
    # )
# aisp/protocols/output.py

from typing import List, Optional, Dict, Any, Union,Literal
from pydantic import BaseModel, Field, DirectoryPath, FilePath

# --- 通用子模块 ---

class PerformanceMetrics(BaseModel):
    """
    用于记录在 AISB 任务上的性能指标。
    """
    task_id: str = Field(..., description="被评测的 AISB 任务的唯一 ID。")
    scores: Dict[str, Any] = Field(
        ..., 
        description="一个包含多个指标和对应分数的字典，例如 {'accuracy': 0.98, 'latency_ms': 150}。"
    )
    raw_eval_log: FilePath = Field(
        ...,
        description="指向由本地 AISB 评测工具生成的、不可篡改的原始日志文件的路径。"
    )

class PaperContent(BaseModel):
    """
    用于承载研究论文或报告的内容。
    """
    title: str
    authors: List[str] = ["AI Scientist"]
    abstract: str
    # 内容可以是 Markdown 或指向编译好的 PDF
    content_markdown: str = Field(..., description="使用 Markdown 格式撰写的完整报告内容。")
    figures: List[Dict[str, FilePath]] = Field(default_factory=list, description="报告中包含的图表，格式为 [{'caption': '图1标题', 'path': './fig1.png'}]。")

# --- L1 元类型：抽象的成果负载基类 ---

class ResearchOutputPayloadBase(BaseModel):
    """
    【L1 元类型】所有具体研究成果负载的抽象基类。
    """
    type: str = Field(..., description="定义研究成果类型的唯一标识符。")
    report: PaperContent = Field(..., description="所有研究成果都必须包含一份核心报告。")


# --- 五种研究类型的具体输出定义 ---

class ImprovementOutputPayload(BaseModel):
    """'Improvement' 类型的研究成果。"""
    type: Literal["improvement"] = "improvement"
    performance_gain: List[PerformanceMetrics]
    modified_code_dir: DirectoryPath
    report: PaperContent = Field(..., description="一份简短的报告，阐述改进的方法、实验设置和结果分析。")

class FindingsOutputPayload(BaseModel):
    """'Findings' 类型的研究成果。"""
    type: Literal["findings"] = "findings"
    report: PaperContent = Field(..., description="详细的研究报告，包含现象分析、实验设计、结果和讨论。")
    experimental_data: DirectoryPath = Field(..., description="所有用于支撑结论的原始实验数据、脚本和结果。")
    # 如果 findings 提出了新的 benchmark，这里会有初步实现
    proposed_benchmark_package: Optional[DirectoryPath] = Field(None, description="如果适用，包含新提出的 Benchmark 的原型代码和数据。")

class SurveyOutputPayload(BaseModel):
    """'Survey' 类型的研究成果。"""
    type: Literal["survey"] = "survey"
    report: PaperContent

class BenchmarkOutputPayload(BaseModel):
    """'Benchmark' 类型的研究成果。"""
    type: Literal["benchmark"] = "benchmark"
    benchmark_package: DirectoryPath = Field(..., description="完整的、可执行的新 Benchmark 包，包含数据、评测脚本和文档。")
    report: PaperContent = Field(..., description="一份描述该 Benchmark 设计理念、构建过程和统计特性的技术论文。")

class TechniqueReportOutputPayload(BaseModel):
    """'Technique Report' 类型的研究成果。"""
    type: Literal["technique_report"] = "technique_report"
    performance_on_target_tasks: List[PerformanceMetrics]
    source_code_dir: DirectoryPath

# --- 统一的科研成果报告模型 ---

class ResearchOutput(BaseModel):
    """
    AISP L1 核心输出对象：科研成果报告。
    """
    request_id: str = Field(..., description="与此成果对应的原始研究请求的 ID。")
    
    payload: Union[
        ImprovementOutputPayload,
        FindingsOutputPayload,
        SurveyOutputPayload,
        BenchmarkOutputPayload,
        TechniqueReportOutputPayload
    ] = Field(..., description='type')
    
    # 认知计算图的日志入口，实现了可回溯性
    logbook_path: FilePath = Field(
        ..., 
        description="指向本次研究全过程的 Logbook 文件路径，用于实现认知过程的可追溯审查。"
    )
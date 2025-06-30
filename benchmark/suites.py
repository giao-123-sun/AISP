# aisp/benchmark/suites.py

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- 1. 将我们设计的 AISB Task JSON 标准转化为 Python 对象 ---
# 这使得我们可以用类型安全的方式在代码中操作任务定义。

class SourceInfo(BaseModel):
    paper_title: str
    paper_url: str
    leaderboard_url: str

class MetricInfo(BaseModel):
    name: str
    description: str
    higher_is_better: bool

class SotaBaselineInfo(BaseModel):
    method_name: str
    method_id: str
    score: Dict[str, Any]
    method_summary: str
    execution: Dict[str, str]

class LocalEvaluatorInfo(BaseModel):
    evaluator_name: str
    version: str
    code_path: str # 相对 aisp/benchmark/ 的路径
    verification_hash: str

class AispTask(BaseModel):
    """
    一个 AISB 任务的 Pydantic 模型，完全对应其 JSON 结构。
    """
    task_id: str = Field(..., description="任务的唯一 ID")
    task_name: str
    version: str
    domain: str
    sub_domain: str
    task_description: str
    source: SourceInfo
    metrics: List[MetricInfo]
    sota_baseline: SotaBaselineInfo
    local_evaluator: LocalEvaluatorInfo
    
# --- 2. 定义 BenchmarkSuite，作为所有任务的集合与管理器 ---

class BenchmarkSuite:
    """
    一个评测套件，是 AISB 任务的集合。
    它负责从磁盘加载、索引和提供对所有标准任务的访问。
    """
    def __init__(self, tasks_dir: Path):
        self._tasks: Dict[str, AispTask] = {}
        self.load_from_directory(tasks_dir)

    def load_from_directory(self, tasks_dir: Path):
        """从指定目录加载所有 .json 格式的任务定义文件。"""
        if not tasks_dir.is_dir():
            # 在实际应用中可能会抛出更详细的错误
            print(f"Warning: Tasks directory '{tasks_dir}' not found.")
            return
            
        for file_path in tasks_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)
                task = AispTask(**task_data)
                if task.task_id in self._tasks:
                    # 保证 task_id 的唯一性
                    raise ValueError(f"Duplicate task_id '{task.task_id}' found in '{file_path}'")
                self._tasks[task.task_id] = task
        print(f"Loaded {len(self._tasks)} tasks into the benchmark suite.")

    def get_task(self, task_id: str) -> Optional[AispTask]:
        """通过 ID 获取一个具体的任务定义。"""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[AispTask]:
        """列出所有已加载的任务。"""
        return list(self._tasks.values())

    def list_tasks_by_domain(self, domain: str) -> List[AispTask]:
        """根据领域筛选任务。"""
        return [task for task in self._tasks.values() if task.domain.lower() == domain.lower()]


# --- 3. 实例化一个全局可用的标准评测套件 ---
# AISP 启动时，会自动加载 aisb_tasks/ 目录下的所有官方基准。
# 这里我们假设 aisb_tasks 目录在项目的顶层。
_project_root = Path(__file__).resolve().parents[2] 
_standard_tasks_dir = _project_root / "aisb_tasks"

StandardBenchmarks = BenchmarkSuite(tasks_dir=_standard_tasks_dir)

# 现在，系统的任何部分都可以通过 `from aisp.benchmark.suites import StandardBenchmarks`
# 来访问所有任务，例如 `task = StandardBenchmarks.get_task('agent-swe-bench-v1')`
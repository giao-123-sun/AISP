# aisp/benchmark/evaluator.py

import hashlib
import importlib
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

# 从其他协议模块导入所需的数据结构
from aisp.protocols.output import ResearchOutput, PerformanceMetrics
from aisp.benchmark.suites import StandardBenchmarks, AispTask

class BenchmarkEvaluator(ABC):
    """
    所有具体任务评测器的抽象基类。
    每个新评测任务的评测脚本都必须继承这个类并实现 evaluate 方法。
    """
    def __init__(self, task: AispTask):
        self.task = task

    @abstractmethod
    def evaluate(self, research_output: ResearchOutput) -> PerformanceMetrics:
        """
        执行评测的核心方法。
        
        Args:
            research_output: AI Scientist 提交的标准格式研究成果。

        Returns:
            一个包含分数和原始日志路径的 PerformanceMetrics 对象。
        """
        pass

class LocalEvaluatorRunner:
    """
    本地评测流程的调度器和执行者。
    它确保评测是在一个可信、不可篡改的环境下进行的。
    """
    def __init__(self, benchmarks_root: Path = Path(__file__).parent):
        self.benchmarks_root = benchmarks_root

    def _verify_integrity(self, code_path: Path, expected_hash: str) -> bool:
        """
        验证评测脚本的完整性，防止篡改。
        """
        if not code_path.exists():
            raise FileNotFoundError(f"Evaluator script not found at '{code_path}'")
        
        hasher = hashlib.sha256()
        with open(code_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        
        actual_hash = f"sha256:{hasher.hexdigest()}"
        
        if actual_hash != expected_hash:
            raise SecurityError(
                f"Evaluator script '{code_path}' has been tampered with! "
                f"Expected hash: {expected_hash}, but got: {actual_hash}"
            )
        
        print(f"Integrity check passed for '{code_path}'.")
        return True

    def run(self, research_output: ResearchOutput) -> PerformanceMetrics:
        """
        主执行函数：加载任务、验证评测器、运行评测、返回结果。
        """
        # 1. 根据输出，找到对应的任务定义
        # Improvement 和 Technique Report 直接包含任务ID
        if research_output.research_type in ["improvement", "technique_report"]:
            # 在一个更完整的系统中，会处理列表中的多个任务
            task_id = research_output.payload.performance_gain[0].task_id
        else:
            raise ValueError(f"Evaluation is not applicable for research type '{research_output.research_type}'")

        task = StandardBenchmarks.get_task(task_id)
        if not task:
            raise ValueError(f"Task with ID '{task_id}' not found in StandardBenchmarks.")

        # 2. 定位并验证评测器代码
        evaluator_info = task.local_evaluator
        evaluator_code_path = (self.benchmarks_root / evaluator_info.code_path).resolve()
        
        self._verify_integrity(evaluator_code_path, evaluator_info.verification_hash)

        # 3. 动态加载并实例化评测器
        # 例如，将 'evaluators/swe_bench_v1.py' 转化为 'aisp.benchmark.evaluators.swe_bench_v1'
        module_path = ".".join(evaluator_code_path.relative_to(self.benchmarks_root.parent).parts).replace('.py', '')
        
        try:
            evaluator_module = importlib.import_module(module_path)
            # 约定：每个评测模块中都有一个名为 'SpecificEvaluator' 的类
            EvaluatorClass = getattr(evaluator_module, "SpecificEvaluator")
            
            # 实例化
            evaluator_instance = EvaluatorClass(task=task)

        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to load evaluator from '{module_path}'. Error: {e}")
        
        # 4. 执行评测并返回结果
        print(f"Running evaluator '{evaluator_info.evaluator_name}' for task '{task.task_id}'...")
        metrics = evaluator_instance.evaluate(research_output)
        print(f"Evaluation finished. Score: {metrics.scores}")
        
        return metrics
from typing import List
import importlib
import importlib.util
from pathlib import Path

import yaml

from .ports import IGovernanceProvider, IStorageProvider
from .domain import PitchSchema, BetSchema, TaskSchema


def _import_omo_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        workspace_projects = Path(__file__).resolve().parents[3]
        leaf = module_name.rsplit(".", 1)[-1]
        module_path = workspace_projects / "omo" / "src" / "omo" / f"{leaf}.py"
        if not module_path.exists():
            raise
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

class EcosGovernanceProvider(IGovernanceProvider):
    def __init__(self, omo_dir_path: str | None = None):
        self.omo_dir = Path(omo_dir_path) if omo_dir_path else None
        try:
            self.omo_task_schema = _import_omo_module("omo.omo_task_schema")
        except ImportError:
            raise ImportError("The 'omo' package is required to use EcosGovernanceProvider. Install c2g[ecos].")

    def validate_pitch(self, pitch: PitchSchema) -> bool:
        if not pitch.upstream_ref:
            print("  ❌ [CR-STRATEGY-01 孤儿拦截] Pitch缺乏Upstream锚点，拒绝转化为Bet。")
            return False
        return True

    def validate_task(self, task: TaskSchema) -> bool:
        errors = self.omo_task_schema.validate_task_data(task.model_dump(), group="planned")
        if errors:
            print("  ❌ M2 防腐层拦截 (Schema Validation Failed)")
            for err in errors:
                print(f"     - {err}")
            return False
        return True

    def get_current_phase(self) -> str:
        if not self.omo_dir:
            return "unknown"
        system_file = self.omo_dir / "state" / "system.yaml"
        if not system_file.exists():
            return "unknown"
        data = yaml.safe_load(system_file.read_text(encoding="utf-8")) or {}
        phase = data.get("current_phase") or data.get("phase") or data.get("phase_id")
        return str(phase) if phase is not None else "unknown"

class EcosStorageProvider(IStorageProvider):
    def __init__(self, omo_dir_path):
        from pathlib import Path
        self.omo_dir = Path(omo_dir_path)
        try:
            self.omo_goal = _import_omo_module("omo.omo_goal")
            self.omo_io = _import_omo_module("omo.omo_io")
            self.omo_ingress = _import_omo_module("omo.omo_ingress")
        except ImportError:
            raise ImportError("The 'omo' package is required to use EcosStorageProvider. Install c2g[ecos].")

    def save_bet(self, bet: BetSchema) -> str:
        self.omo_ingress.create_goal(
            self.omo_dir,
            goal_id=bet.goal_id,
            title=bet.title,
            description=f"Bet: {bet.title} (Appetite: {bet.appetite})",
            ingress_plane="projects/c2g",
            source_ref=f"c2g:bet:{bet.goal_id}",
            extra_fields={
                "appetite": bet.appetite,
                "vector": bet.vector,
                "created_at": bet.created_at,
                "bet_status": bet.status,
            },
        )
        return bet.goal_id

    def save_task(self, task: TaskSchema) -> str:
        metadata = dict(task.metadata or {})
        task_data = {
            "id": task.task_id,
            "title": task.title,
            "status": "candidate",
            "task_type": metadata.get("task_type", "feature"),
            "risk_level": metadata.get("risk_level", "L0"),
            "depends_on": metadata.get("depends_on", []),
            "source_docs": metadata.get("source_docs", ["c2g:task-without-source-doc"]),
            "deliverables": metadata.get("deliverables", ["执行记录与源码修改"]),
            "imported_via": metadata.get("imported_via", "projects/c2g"),
            "context_uri": metadata.get("context_uri", f"bos://memory/tasks/{task.task_id}"),
            "assigned_to": None,
            "dispatch_id": None,
            "run_ref": None,
            "approval_ref": None,
            "review_ref": None,
            "knowledge_refs": [],
            "handoff_refs": [],
            "governance_refs": metadata.get("governance_refs", []),
            "entry_gate": metadata.get("entry_gate", []),
            "evidence_required": metadata.get("evidence_required", []),
            "test_plan": metadata.get("test_plan", ["c2g adapter default test plan"]),
            "allowed_operation_level": metadata.get("allowed_operation_level", "L0"),
            "human_approval_required": metadata.get("human_approval_required", False),
            "metadata": metadata,
        }
        self.omo_ingress.create_planned_task(
            self.omo_dir,
            task_data=task_data,
            ingress_plane="projects/c2g",
            source_ref=f"c2g:task:{task.task_id}",
        )
        return task.task_id

    def get_pitches(self) -> List[PitchSchema]:
        sandbox_dir = self.omo_dir.parent / "runtime" / "sandbox" / "pitches"
        if not sandbox_dir.exists():
            return []
        
        pitches = []
        for pf in sandbox_dir.glob("*.md"):
            content = pf.read_text(encoding="utf-8")
            upstream = None
            appetite = "Unknown"
            for line in content.split("\n"):
                if "> **Upstream**" in line:
                    upstream = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                if "**Appetite:**" in line:
                    appetite = line.replace("**Appetite:**", "").strip()
            
            p = PitchSchema(
                pitch_id=pf.name,
                title=pf.stem,
                content=content,
                upstream_ref=upstream,
                appetite=appetite,
                created_at="Unknown"
            )
            pitches.append(p)
        return pitches

    def delete_pitch(self, pitch_id: str) -> bool:
        pf = self.omo_dir.parent / "runtime" / "sandbox" / "pitches" / pitch_id
        if pf.exists():
            pf.unlink()
            return True
        return False

    def get_active_bets(self) -> List[BetSchema]:
        # Minimal mock for radar
        return [
            BetSchema(goal_id="BET-1", title="Indie Efficiency", description="", vector="V1", created_at=""),
            BetSchema(goal_id="BET-2", title="Agent Autonomy", description="", vector="V2", created_at="")
        ]

def get_providers(base_dir_path: str = None, adapter_type: str = "ecos"):
    """
    Dependency Injection point.
    adapter_type can be 'ecos' (default for eCOS workspace) or 'local' (standalone usage).
    """
    if adapter_type == "ecos":
        try:
            return EcosGovernanceProvider(base_dir_path), EcosStorageProvider(base_dir_path)
        except ImportError as e:
            print(f"⚠️ eCOS Adapter not available ({e}). Falling back to 'local' adapter.")
            adapter_type = "local"
    
    if adapter_type == "local":
        from .adapters_local import LocalGovernanceProvider, LocalStorageProvider
        return LocalGovernanceProvider(), LocalStorageProvider(base_dir_path or ".c2g_data")
    
    raise ValueError(f"Unknown adapter type: {adapter_type}")

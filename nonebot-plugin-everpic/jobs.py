"""全局画图任务队列管理"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JobInfo:
    internal_id: str  # 内部唯一标识
    job_id: str       # API 返回的 job_id，初始为空
    user_id: int
    group_id: int
    char_name: str
    variant_name: str
    status: str = "提交中"
    created_at: datetime = field(default_factory=datetime.now)


# 用 internal_id 作为 key，避免冲突
_active_jobs: dict[str, JobInfo] = {}


def create_job(user_id: int, group_id: int, char_name: str, variant_name: str) -> JobInfo:
    """创建并注册一个新任务，返回 JobInfo"""
    info = JobInfo(
        internal_id=uuid.uuid4().hex[:12],
        job_id="",
        user_id=user_id,
        group_id=group_id,
        char_name=char_name,
        variant_name=variant_name,
    )
    _active_jobs[info.internal_id] = info
    return info


def remove_job(info: JobInfo):
    _active_jobs.pop(info.internal_id, None)


def get_active_jobs() -> list[JobInfo]:
    return list(_active_jobs.values())


def active_count() -> int:
    return len(_active_jobs)

from datetime import datetime
from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
from nonebot.rule import Rule

from ..config import MAX_CONCURRENT_JOBS
from ..jobs import get_active_jobs, active_count


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic队列"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


@matcher.handle()
async def handle(event: GroupMessageEvent):
    jobs = get_active_jobs()
    count = active_count()

    if count == 0:
        await matcher.finish(f"📭 当前没有画图任务（上限{MAX_CONCURRENT_JOBS}个）")

    lines = [f"📋 当前画图队列（{count}/{MAX_CONCURRENT_JOBS}）\n"]
    for i, job in enumerate(jobs):
        elapsed = (datetime.now() - job.created_at).seconds
        lines.append(
            f"  {i+1}. {job.char_name} - {job.variant_name}\n"
            f"     状态: {job.status} | 用户: {job.user_id} | {elapsed}秒前"
        )

    await matcher.finish("\n".join(lines))

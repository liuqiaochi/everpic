import json
from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot, MessageSegment, Message
from nonebot.rule import Rule

from ..store import is_super_admin, get_recent_logs


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic日志")


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


@matcher.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await matcher.finish("❌ 仅超级管理员可以查看日志")

    text = event.get_plaintext().strip()
    rest = text[len("everpic日志"):].strip()

    try:
        count = int(rest) if rest else 5
        count = max(1, min(count, 50))
    except ValueError:
        count = 5

    logs = get_recent_logs(count)
    if not logs:
        await matcher.finish("📭 暂无请求日志")

    # 用合并转发发送，避免刷屏
    nodes = []
    for log in reversed(logs):  # 最新的在前
        body_str = json.dumps(log.get("request_body") or {}, ensure_ascii=False, indent=2)
        text_content = (
            f"⏰ {log.get('time', '?')}\n"
            f"👤 {log.get('user_name', '?')} ({log.get('user_id', '?')})\n"
            f"🏠 群: {log.get('group_id', '?')}\n"
            f"📦 请求:\n{body_str}"
        )
        nodes.append({
            "type": "node",
            "data": {
                "name": "EverPic Log",
                "uin": str(event.self_id),
                "content": Message(MessageSegment.text(text_content)),
            },
        })

    await bot.send_group_forward_msg(group_id=event.group_id, messages=nodes)

from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot, MessageSegment, Message
from nonebot.rule import Rule

from ..data import LORA_DATA

GROUP_SIZE = 20


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic角色"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


def _build_group_text(chars: list[dict], offset: int) -> str:
    """构建一组角色的文本"""
    lines = []
    for i, c in enumerate(chars):
        idx = offset + i + 1
        aliases = c.get("aliases", [])
        alias_str = "  别称: " + ", ".join(aliases) if aliases else ""
        lines.append(f"{idx}. {c['name_cn']}{alias_str}")
    return "\n".join(lines)


@matcher.handle()
async def handle(bot: Bot, event: GroupMessageEvent):
    total = len(LORA_DATA)
    # 分成每组 GROUP_SIZE 个
    chunks = [LORA_DATA[i:i + GROUP_SIZE] for i in range(0, total, GROUP_SIZE)]

    # 构建合并转发的节点
    nodes = []
    for g_idx, chunk in enumerate(chunks):
        offset = g_idx * GROUP_SIZE
        title = f"📋 角色列表 ({g_idx+1}/{len(chunks)})"
        text = title + "\n\n" + _build_group_text(chunk, offset)
        nodes.append({
            "type": "node",
            "data": {
                "name": "EverPic",
                "uin": str(event.self_id),
                "content": Message(MessageSegment.text(text)),
            },
        })

    # 发送合并转发
    await bot.send_group_forward_msg(group_id=event.group_id, messages=nodes)

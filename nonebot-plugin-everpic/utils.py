"""通用工具函数"""
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot


def extract_at_target(event: MessageEvent) -> int | None:
    """从消息中提取被@的用户ID"""
    for seg in event.message:
        if seg.type == "at":
            qq = seg.data.get("qq", "")
            if qq and qq != "all":
                return int(qq)
    return None


async def is_group_admin(bot: Bot, event: GroupMessageEvent) -> bool:
    """判断是否为群管理员/群主"""
    info = await bot.get_group_member_info(
        group_id=event.group_id, user_id=event.user_id
    )
    return info.get("role") in ("owner", "admin")


def is_group_msg(event: MessageEvent) -> bool:
    """判断是否为群消息"""
    return isinstance(event, GroupMessageEvent)

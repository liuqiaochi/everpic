from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
from nonebot.rule import Rule

from ..data import find_character


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic查变体")


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


@matcher.handle()
async def handle(event: GroupMessageEvent):
    text = event.get_plaintext().strip()
    char_kw = text[len("everpic查变体"):].strip()

    if not char_kw:
        await matcher.finish("用法: everpic查变体 角色名\n角色名支持中文名/韩文名/别称")

    char = find_character(char_kw)
    if not char:
        await matcher.finish(f"找不到角色「{char_kw}」，请发送 everpic角色 查看角色列表")

    lines = [f"📋 {char['name_cn']}（{char['name']}）的变体列表：\n"]
    for i, v in enumerate(char["variants"]):
        cn = v.get("name_cn", v["name"])
        lines.append(f"  {i+1}. {cn}")
    await matcher.finish("\n".join(lines))

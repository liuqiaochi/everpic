import base64
from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.rule import Rule

from ..render import render_help_image


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic帮助"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


@matcher.handle()
async def handle(event: GroupMessageEvent):
    img_bytes = render_help_image()
    b64 = base64.b64encode(img_bytes).decode()
    await matcher.finish(MessageSegment.image(f"base64://{b64}"))

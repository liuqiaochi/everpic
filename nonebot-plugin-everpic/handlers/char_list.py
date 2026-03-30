import base64
from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.rule import Rule

from ..render import render_char_list_images


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic角色"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


@matcher.handle()
async def handle(event: GroupMessageEvent):
    images = render_char_list_images()
    for img_bytes in images:
        b64 = base64.b64encode(img_bytes).decode()
        await matcher.send(MessageSegment.image(f"base64://{b64}"))

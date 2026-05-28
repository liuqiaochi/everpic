from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
from nonebot.rule import Rule


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic查尺寸"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)

SIZE_INFO = """📐 画图可用尺寸：

  3:4   → 竖版（默认）
  9:16  → 窄竖版
  4:3   → 横版
  16:9  → 宽横版
  1:1   → 正方形

用法: 画图 [尺寸] 角色名 [变体] [Prompt]
举例: 画图 9:16 红兰
举例: 画图 1:1 妮亚 缘分

也可以用中文: 竖/窄竖/横/宽横/方"""


@matcher.handle()
async def handle(event: GroupMessageEvent):
    await matcher.finish(SIZE_INFO)

from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
from nonebot.rule import Rule

from ..config import DRAW_COST, GIFT_MIN, GIFT_MAX
from ..store import is_super_admin, sign_in, get_user_points, gift_points
from ..utils import extract_at_target


# ---- everpic签到 ----
async def _sign_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic签到"


sign_matcher = on_message(rule=Rule(_sign_rule), priority=10, block=True)


@sign_matcher.handle()
async def handle_sign(event: GroupMessageEvent):
    if is_super_admin(event.user_id):
        await sign_matcher.finish("你是超级管理员，无需签到~")

    ok, gained, total = sign_in(event.user_id)
    if ok:
        await sign_matcher.finish(f"✅ 签到成功！获得 {gained} 积分，当前积分: {total}")
    else:
        await sign_matcher.finish(f"今天已经签到过了，当前积分: {total}")


# ---- everpic积分 ----
async def _points_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic积分"


points_matcher = on_message(rule=Rule(_points_rule), priority=10, block=True)


@points_matcher.handle()
async def handle_points(event: GroupMessageEvent):
    if is_super_admin(event.user_id):
        await points_matcher.finish("你是超级管理员，无需积分即可画图~")

    pts = get_user_points(event.user_id)
    await points_matcher.finish(f"💰 你的当前积分: {pts}（每次画图消耗{DRAW_COST}积分）")


# ---- everpic发积分 @某人 数量 ----
async def _gift_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic发积分")


gift_matcher = on_message(rule=Rule(_gift_rule), priority=10, block=True)


@gift_matcher.handle()
async def handle_gift(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await gift_matcher.finish("❌ 仅超级管理员可以发放积分")

    target = extract_at_target(event)
    if not target:
        await gift_matcher.finish("用法: everpic发积分 @某人 数量\n数量范围: 1~50")

    # 从纯文本中提取数量（去掉指令前缀后剩余的数字）
    text = event.get_plaintext().strip()
    rest = text[len("everpic发积分"):].strip()
    # rest 可能是 "30" 或者空（@不在纯文本里）
    amount = 0
    for part in rest.split():
        try:
            amount = int(part)
            break
        except ValueError:
            continue

    if amount < GIFT_MIN or amount > GIFT_MAX:
        await gift_matcher.finish(f"❌ 发放数量需在 {GIFT_MIN}~{GIFT_MAX} 之间")

    ok, reason, total = gift_points(target, amount)
    if not ok:
        await gift_matcher.finish(f"❌ {reason}")

    await gift_matcher.finish(f"✅ 已向用户 {target} 发放 {amount} 积分，对方当前积分: {total}")

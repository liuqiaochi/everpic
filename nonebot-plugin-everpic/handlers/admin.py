from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot
from nonebot.rule import Rule

from ..store import (
    load_blacklist, save_blacklist,
    is_super_admin, set_group_enabled, set_nsfw_filter,
)
from ..utils import extract_at_target, is_group_admin


# ---- everpic拉黑 ----
async def _ban_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic拉黑")


ban_matcher = on_message(rule=Rule(_ban_rule), priority=10, block=True)


@ban_matcher.handle()
async def handle_ban(bot: Bot, event: GroupMessageEvent):
    if not await is_group_admin(bot, event):
        await ban_matcher.finish("❌ 仅管理员可以操作拉黑")

    target = extract_at_target(event)
    if not target:
        await ban_matcher.finish("用法: everpic拉黑 @某人")

    bl = load_blacklist()
    uid = str(target)
    if uid in bl:
        await ban_matcher.finish(f"用户 {target} 已在黑名单中")

    bl.append(uid)
    save_blacklist(bl)
    await ban_matcher.finish(f"🚫 已将用户 {target} 加入黑名单")


# ---- everpic解除拉黑 ----
async def _unban_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic解除拉黑")


unban_matcher = on_message(rule=Rule(_unban_rule), priority=10, block=True)


@unban_matcher.handle()
async def handle_unban(bot: Bot, event: GroupMessageEvent):
    if not await is_group_admin(bot, event):
        await unban_matcher.finish("❌ 仅管理员可以操作解除拉黑")

    target = extract_at_target(event)
    if not target:
        await unban_matcher.finish("用法: everpic解除拉黑 @某人")

    bl = load_blacklist()
    uid = str(target)
    if uid not in bl:
        await unban_matcher.finish(f"用户 {target} 不在黑名单中")

    bl.remove(uid)
    save_blacklist(bl)
    await unban_matcher.finish(f"✅ 已将用户 {target} 移出黑名单")


# ---- everpic开启 / everpic关闭 ----
async def _enable_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic开启"


async def _disable_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic关闭"


enable_matcher = on_message(rule=Rule(_enable_rule), priority=5, block=True)
disable_matcher = on_message(rule=Rule(_disable_rule), priority=5, block=True)


@enable_matcher.handle()
async def handle_enable(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await enable_matcher.finish("❌ 仅超级管理员可以开启/关闭本群画图功能")
    set_group_enabled(event.group_id, True)
    await enable_matcher.finish("✅ 本群 EverPic 画图功能已开启")


@disable_matcher.handle()
async def handle_disable(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await disable_matcher.finish("❌ 仅超级管理员可以开启/关闭本群画图功能")
    set_group_enabled(event.group_id, False)
    await disable_matcher.finish("✅ 本群 EverPic 画图功能已关闭")


# ---- everpic安全开启 / everpic安全关闭 ----
async def _nsfw_on_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic安全开启"


async def _nsfw_off_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic安全关闭"


nsfw_on_matcher = on_message(rule=Rule(_nsfw_on_rule), priority=5, block=True)
nsfw_off_matcher = on_message(rule=Rule(_nsfw_off_rule), priority=5, block=True)


@nsfw_on_matcher.handle()
async def handle_nsfw_on(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await nsfw_on_matcher.finish("❌ 仅超级管理员可以操作")
    set_nsfw_filter(event.group_id, True)
    await nsfw_on_matcher.finish("🔞 本群 NSFW 过滤已开启（违禁词将被拦截）")


@nsfw_off_matcher.handle()
async def handle_nsfw_off(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await nsfw_off_matcher.finish("❌ 仅超级管理员可以操作")
    set_nsfw_filter(event.group_id, False)
    await nsfw_off_matcher.finish("🔓 本群 NSFW 过滤已关闭")

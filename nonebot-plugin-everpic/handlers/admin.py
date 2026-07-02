from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot
from nonebot.rule import Rule

from ..store import (
    load_blacklist, save_blacklist,
    is_super_admin, set_group_enabled, set_nsfw_filter,
    load_banned_words, add_banned_word, remove_banned_word,
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


# ---- everpic加违禁词 ----
async def _add_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic加违禁词")


add_banned_word_matcher = on_message(rule=Rule(_add_banned_word_rule), priority=10, block=True)


@add_banned_word_matcher.handle()
async def handle_add_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await add_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    text = event.get_plaintext().strip()
    word = text[len("everpic加违禁词"):].strip()
    if not word:
        await add_banned_word_matcher.finish("用法: everpic加违禁词 词\n多个词用空格分隔可一次添加多个")

    # 支持空格分隔添加多个
    words = word.split()
    success_count = 0
    fail_msgs = []
    for w in words:
        ok, info = add_banned_word(w)
        if ok:
            success_count += 1
        else:
            fail_msgs.append(info)

    msg = f"✅ 已添加 {success_count} 个违禁词"
    if fail_msgs:
        msg += "\n" + "\n".join(fail_msgs)
    await add_banned_word_matcher.finish(msg)


# ---- everpic删违禁词 ----
async def _del_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic删违禁词")


del_banned_word_matcher = on_message(rule=Rule(_del_banned_word_rule), priority=10, block=True)


@del_banned_word_matcher.handle()
async def handle_del_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await del_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    text = event.get_plaintext().strip()
    word = text[len("everpic删违禁词"):].strip()
    if not word:
        await del_banned_word_matcher.finish("用法: everpic删违禁词 词\n多个词用空格分隔可一次删除多个")

    words = word.split()
    success_count = 0
    fail_msgs = []
    for w in words:
        ok, info = remove_banned_word(w)
        if ok:
            success_count += 1
        else:
            fail_msgs.append(info)

    msg = f"✅ 已删除 {success_count} 个违禁词"
    if fail_msgs:
        msg += "\n" + "\n".join(fail_msgs)
    await del_banned_word_matcher.finish(msg)


# ---- everpic查违禁词 ----
async def _list_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic查违禁词"


list_banned_word_matcher = on_message(rule=Rule(_list_banned_word_rule), priority=10, block=True)


@list_banned_word_matcher.handle()
async def handle_list_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await list_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    words = load_banned_words()
    if not words:
        await list_banned_word_matcher.finish("📭 当前没有自定义违禁词（仅使用内置违禁词库）")

    # 每行显示多个，避免列表过长
    lines = [f"📋 自定义违禁词（共 {len(words)} 条）:"]
    for i in range(0, len(words), 5):
        batch = words[i:i + 5]
        lines.append("  " + " | ".join(batch))
    await list_banned_word_matcher.finish("\n".join(lines))

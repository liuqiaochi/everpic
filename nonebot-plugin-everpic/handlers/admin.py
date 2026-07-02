import logging

from nonebot import on_message, get_bot
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot, MessageSegment, Message
from nonebot.rule import Rule

logger = logging.getLogger("nonebot-plugin-everpic")

from ..store import (
    load_blacklist, save_blacklist,
    is_super_admin, set_group_enabled, set_nsfw_filter,
)
from ..nsfw import (
    add_banned_word, remove_banned_word,
    list_banned_words, search_banned_words,
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
    await nsfw_on_matcher.finish("🔞 本群 NSFW 过滤已开启（禁词将被拦截）")


@nsfw_off_matcher.handle()
async def handle_nsfw_off(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await nsfw_off_matcher.finish("❌ 仅超级管理员可以操作")
    set_nsfw_filter(event.group_id, False)
    await nsfw_off_matcher.finish("🔓 本群 NSFW 过滤已关闭")


# ---- everpic加禁词 ----
async def _add_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic加禁词")


add_banned_word_matcher = on_message(rule=Rule(_add_banned_word_rule), priority=10, block=True)


@add_banned_word_matcher.handle()
async def handle_add_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await add_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    text = event.get_plaintext().strip()
    word = text[len("everpic加禁词"):].strip()
    if not word:
        await add_banned_word_matcher.finish(
            "用法: everpic加禁词 词\n"
            "  含中文 → 中文词库（子串匹配）\n"
            "  含空格 → 英文短语库（子串匹配）\n"
            "  其他   → 英文单词库（词边界匹配）"
        )

    ok, info = add_banned_word(word)
    await add_banned_word_matcher.finish(("✅ " if ok else "❌ ") + info)


# ---- everpic删禁词 ----
async def _del_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip().startswith("everpic删禁词")


del_banned_word_matcher = on_message(rule=Rule(_del_banned_word_rule), priority=10, block=True)


@del_banned_word_matcher.handle()
async def handle_del_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await del_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    text = event.get_plaintext().strip()
    word = text[len("everpic删禁词"):].strip()
    if not word:
        await del_banned_word_matcher.finish("用法: everpic删禁词 词")

    ok, info = remove_banned_word(word)
    await del_banned_word_matcher.finish(("✅ " if ok else "❌ ") + info)


# ---- everpic查禁词 ----
async def _list_banned_word_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text == "everpic查禁词" or text.startswith("everpic查禁词 ")


list_banned_word_matcher = on_message(rule=Rule(_list_banned_word_rule), priority=10, block=True)


@list_banned_word_matcher.handle()
async def handle_list_banned_word(event: GroupMessageEvent):
    if not is_super_admin(event.user_id):
        await list_banned_word_matcher.finish("❌ 仅超级管理员可以操作")

    text = event.get_plaintext().strip()
    keyword = text[len("everpic查禁词"):].strip()

    # 不带关键词 → 显示统计 + 合并转发全部
    data = list_banned_words()
    counts = {k: len(v) for k, v in data.items()}
    total = sum(counts.values())

    if not keyword:
        # 构建合并转发：第一个节点放统计，后续每 50 个词一个节点
        nodes = []

        # 第一个节点：汇总统计
        summary = (
            f"📊 禁词库统计（共 {total} 条）\n"
            f"  英文单词: {counts['en_words']} 条\n"
            f"  英文短语: {counts['en_phrases']} 条\n"
            f"  中文关键词: {counts['cn_keywords']} 条"
        )
        nodes.append({
            "type": "node",
            "data": {
                "name": "EverPic 禁词库",
                "uin": str(event.self_id),
                "content": Message(MessageSegment.text(summary)),
            },
        })

        # 后续节点：每类按 50 个词分批
        for type_key, type_label in [
            ("en_words", "英文单词"),
            ("en_phrases", "英文短语"),
            ("cn_keywords", "中文关键词"),
        ]:
            words = data[type_key]
            if not words:
                continue
            for i in range(0, len(words), 50):
                batch = words[i:i + 50]
                content = f"【{type_label}】{i + 1}-{i + len(batch)}\n" + " | ".join(batch)
                nodes.append({
                    "type": "node",
                    "data": {
                        "name": "EverPic 禁词库",
                        "uin": str(event.self_id),
                        "content": Message(MessageSegment.text(content)),
                    },
                })

        bot = get_bot(str(event.self_id))
        try:
            await bot.send_group_forward_msg(group_id=event.group_id, messages=nodes)
            return
        except Exception as e:
            logger.warning(f"[EverPic] 查禁词合并转发失败: {e}，降级纯文本")
            # 降级：直接发统计
            await list_banned_word_matcher.finish(summary + "\n\n⚠️ 合并转发发送失败，请稍后重试")
        return

    # 带关键词 → 搜索
    result = search_banned_words(keyword)
    hit_total = sum(len(v) for v in result.values())
    if hit_total == 0:
        await list_banned_word_matcher.finish(f"🔍 未找到包含「{keyword}」的禁词")

    lines = [f"🔍 搜索「{keyword}」命中 {hit_total} 条:"]
    for type_key, type_label in [
        ("en_words", "英文单词"),
        ("en_phrases", "英文短语"),
        ("cn_keywords", "中文关键词"),
    ]:
        if result[type_key]:
            lines.append(f"\n【{type_label}】({len(result[type_key])} 条)")
            lines.append("  " + " | ".join(result[type_key]))
    await list_banned_word_matcher.finish("\n".join(lines))

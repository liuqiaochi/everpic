"""存词功能：存词 / 查词 / 删词"""
from nonebot import on_message, get_bot, logger
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.rule import Rule

from ..store import save_word, get_words, delete_word
from ..store import is_blacklisted
from ..config import MAX_WORDS


# ---- everpic存词 ----
async def _save_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text.startswith("everpic存词") or text == "存词"


save_matcher = on_message(rule=Rule(_save_rule), priority=10, block=True)


@save_matcher.handle()
async def handle_save(event: GroupMessageEvent):
    # 黑名单
    if is_blacklisted(event.user_id):
        await save_matcher.finish("❌ 你已被拉黑")

    # 提取引用消息 — reply 信息在 event.reply 中，不在 segments 里
    msg = event.get_message()
    logger.info(f"[EverPic] 存词收到消息, 共{len(msg)}个segment, event.reply={event.reply}")
    reply_id = None

    # 主路径: OneBot v11 的 event.reply 属性
    if event.reply:
        reply_id = event.reply.message_id
        logger.info(f"[EverPic] 存词 从event.reply获取reply_id={reply_id}")

    if not reply_id:
        logger.warning(
            f"[EverPic] 存词 未找到reply_id, "
            f"event.reply={event.reply}, segments=[{'; '.join(f'{s.type}:{dict(s.data)}' for s in msg)}]"
        )
        await save_matcher.finish(
            "❌ 请引用（回复）一条画图消息来存词\n用法: 回复画图消息 + everpic存词 备注"
        )

    # 获取被引用的消息内容
    try:
        bot = get_bot(str(event.self_id))
        reply_msg = await bot.get_msg(message_id=int(reply_id))
        raw_message = reply_msg.get("message", "")
        # get_msg 的 message 可能是字符串（纯文本）或 segments 数组
        if isinstance(raw_message, list):
            reply_text = "".join(
                seg.get("data", {}).get("text", "")
                for seg in raw_message
                if seg.get("type") == "text"
            ).strip()
        else:
            reply_text = str(raw_message).strip()
    except Exception:
        await save_matcher.finish("❌ 无法获取引用消息内容，可能已过期")

    # 检查是否"画图"开头
    if not reply_text.startswith("画图"):
        await save_matcher.finish("❌ 非画图提示词，只能存以「画图」开头的指令")

    # 提取备注
    full_text = event.get_plaintext().strip()
    # 去掉命令前缀 "everpic存词" 或 "存词"
    if full_text.startswith("everpic存词"):
        note = full_text[len("everpic存词"):].strip()
    else:
        note = full_text[len("存词"):].strip()

    success, idx, info = save_word(event.user_id, reply_text, note)
    if not success:
        await save_matcher.finish(f"❌ {info}")

    result = f"✅ {info}\n📝 {reply_text[:80]}{'...' if len(reply_text) > 80 else ''}"
    if note:
        result += f"\n📌 备注: {note}"
    await save_matcher.finish(result)


# ---- everpic查词 ----
async def _query_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text.startswith("everpic查词") or text == "查词"


query_matcher = on_message(rule=Rule(_query_rule), priority=10, block=True)


def _extract_query_and_target(event: GroupMessageEvent) -> tuple[str, int | None]:
    """从查词消息中提取关键词和目标用户ID。
    返回 (keyword, target_user_id | None)，None 表示查自己。
    """
    full_text = event.get_plaintext().strip()
    # 去掉命令前缀
    if full_text.startswith("everpic查词"):
        rest = full_text[len("everpic查词"):].strip()
    else:
        rest = full_text[len("查词"):].strip()

    # 检查 @ 提及
    target_id = None
    for seg in event.get_message():
        if seg.type == "at":
            target_id = int(seg.data.get("qq", 0))
            break

    # 从文本中去掉 @提及的占位符（@xxx 在 plaintext 中可能是 "@xxx" 或空白）
    if target_id:
        # 尝试从 rest 中去掉 @ 相关内容
        import re
        rest = re.sub(r'@\S+', '', rest).strip()

    return rest, target_id


@query_matcher.handle()
async def handle_query(event: GroupMessageEvent):
    keyword, target_id = _extract_query_and_target(event)
    user_id = target_id if target_id else event.user_id
    is_self = user_id == event.user_id

    words = get_words(user_id)
    if not words:
        who = "你" if is_self else f"用户 {user_id}"
        await query_matcher.finish(f"📭 {who}还没有存过提示词")

    # 按关键词过滤
    if keyword:
        filtered = [
            (i, w) for i, w in enumerate(words, 1)
            if keyword.lower() in w["prompt"].lower()
            or (w["note"] and keyword.lower() in w["note"].lower())
        ]
    else:
        filtered = [(i, w) for i, w in enumerate(words, 1)]

    if not filtered:
        await query_matcher.finish(f"🔍 未找到包含「{keyword}」的存词")

    who = "你" if is_self else f"用户 {user_id}"
    bot = get_bot(str(event.self_id))

    # 构建合并转发节点 — 标题嵌入 content，避免 QQ 客户端不显示 nickname
    nodes = []
    for idx, word in filtered:
        title = f"#{idx}"
        if word.get("note"):
            title += f" {word['note']}"
        content_text = f"{title}\n{word['prompt']}"
        nodes.append(
            MessageSegment.node_custom(
                user_id=event.self_id,
                nickname=f"{who}的存词",
                content=content_text,
            )
        )

    try:
        await bot.call_api(
            "send_group_forward_msg",
            group_id=event.group_id,
            messages=nodes,
        )
        return  # 已通过转发发送，不再发送其他消息
    except Exception:
        # 如果转发接口不可用，降级为普通文本
        lines = [f"📋 {who}的存词（{len(filtered)}条）:"]
        for idx, word in filtered:
            line = f"  #{idx} {word['prompt'][:60]}{'...' if len(word['prompt']) > 60 else ''}"
            if word["note"]:
                line += f"\n       📌 {word['note']}"
            lines.append(line)
        await query_matcher.finish("\n".join(lines))


# ---- everpic删词 ----
async def _delete_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text.startswith("everpic删词") or text == "删词"


delete_matcher = on_message(rule=Rule(_delete_rule), priority=10, block=True)


@delete_matcher.handle()
async def handle_delete(event: GroupMessageEvent):
    if is_blacklisted(event.user_id):
        await delete_matcher.finish("❌ 你已被拉黑")

    text = event.get_plaintext().strip()
    if text.startswith("everpic删词"):
        rest = text[len("everpic删词"):].strip()
    else:
        rest = text[len("删词"):].strip()

    if not rest:
        await delete_matcher.finish("用法: everpic删词 序号\n可以先发送 everpic查词 查看序号")

    try:
        index = int(rest)
    except ValueError:
        await delete_matcher.finish(f"❌ 无效序号「{rest}」，请输入数字")

    success, info = delete_word(event.user_id, index)
    if not success:
        await delete_matcher.finish(f"❌ {info}")

    await delete_matcher.finish(f"✅ {info}")

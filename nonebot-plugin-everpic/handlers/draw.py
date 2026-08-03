import base64
import json
from datetime import datetime
import httpx
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment, Message
from nonebot.rule import Rule

from ..config import MAX_CONCURRENT_JOBS, DRAW_COST, IMAGE_SAVE_DIR, SIZE_MAP, DEFAULT_SIZE
from ..data import find_character, find_variant, is_variant_matched
from ..store import (
    is_blacklisted, is_super_admin, is_group_enabled,
    is_nsfw_filter_on, get_user_points, deduct_points,
    get_draw_settings, append_request_log, save_image_job,
)
from ..nsfw import check_nsfw
from ..api import call_generate, poll_until_done
from ..jobs import create_job, remove_job, active_count


async def _rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text.startswith("画图 ") or text == "画图"


matcher = on_message(rule=Rule(_rule), priority=10, block=True)


def _parse_args(text: str):
    rest = text[len("画图"):].strip()
    if not rest:
        return None, None, None, DEFAULT_SIZE
    parts = rest.split()

    # 第一个参数尝试匹配尺寸
    size = DEFAULT_SIZE
    if parts[0].lower() in SIZE_MAP:
        size = SIZE_MAP[parts[0].lower()]
        parts = parts[1:]  # 消费掉尺寸参数

    if not parts:
        return None, None, None, size

    char_kw = parts[0]
    variant_kw = parts[1] if len(parts) >= 2 else ""
    prompt = " ".join(parts[2:]) if len(parts) >= 3 else ""
    return char_kw, variant_kw, prompt, size


@matcher.handle()
async def handle(event: GroupMessageEvent):
    # 群开关
    if not is_group_enabled(event.group_id):
        await matcher.finish("❌ 本群未开启 EverPic 画图功能，请联系超级管理员发送 everpic开启")

    # 黑名单
    if is_blacklisted(event.user_id):
        await matcher.finish("❌ 你已被拉黑，无法使用画图功能")

    # 积分（超管跳过）
    is_sa = is_super_admin(event.user_id)
    if not is_sa:
        pts = get_user_points(event.user_id)
        if pts < DRAW_COST:
            await matcher.finish(
                f"❌ 积分不足！当前积分: {pts}，需要: {DRAW_COST}\n发送 everpic签到 获取积分"
            )

    # 并发
    if active_count() >= MAX_CONCURRENT_JOBS:
        await matcher.finish(
            f"当前已有 {active_count()} 个任务生成中（上限{MAX_CONCURRENT_JOBS}），请稍后再试！"
        )

    # 解析参数
    text = event.get_plaintext().strip()
    char_kw, variant_kw, prompt, size = _parse_args(text)

    if not char_kw:
        await matcher.finish(
            "用法: 画图 [尺寸] 角色名 [变体名] [Prompt]\n"
            "尺寸可选: 3:4(默认) 9:16 4:3 16:9 1:1\n"
            "角色名支持中文名/韩文名/别称\n"
            "变体可选，不填则使用默认\n"
            "Prompt关键词可选"
        )

    char = find_character(char_kw)
    if not char:
        await matcher.finish(f"找不到角色「{char_kw}」，请发送 everpic角色 查看角色列表")

    # 变体匹配
    actual_variant_kw = variant_kw or ""
    actual_prompt = prompt or ""

    if actual_variant_kw and is_variant_matched(char, actual_variant_kw):
        variant = find_variant(char, actual_variant_kw)
    elif actual_variant_kw:
        actual_prompt = (actual_variant_kw + " " + actual_prompt).strip()
        variant = char["variants"][0]
    else:
        variant = char["variants"][0]

    # NSFW 过滤
    if is_nsfw_filter_on(event.group_id) and actual_prompt:
        hit = check_nsfw(actual_prompt)
        if hit:
            await matcher.finish(f"🔞 Prompt 包含违禁内容「{hit}」，已拦截")

    # 第一条消息
    size_label = next((k for k, v in SIZE_MAP.items() if v == size and ':' in k), size)
    info = (
        f"🎨 开始创建画图\n"
        f"{char['name_cn']} : {variant.get('name_cn', variant['name'])} [{size_label}]"
    )
    await matcher.send(info)

    # 创建任务记录
    job_info = create_job(
        user_id=event.user_id,
        group_id=event.group_id,
        char_name=char["name_cn"],
        variant_name=variant.get("name_cn", variant["name"]),
    )

    request_body = None
    try:
        user_settings = get_draw_settings(event.user_id)
        job_id = await call_generate(char, variant, actual_prompt, user_settings,
                                     return_body=True, size=size)
        # call_generate 现在返回 (job_id, body) 当 return_body=True
        if isinstance(job_id, tuple):
            job_id, request_body = job_id

        job_info.job_id = job_id
        job_info.status = "排队中"

        async def on_progress():
            job_info.status = "生成中"
            await matcher.send("⏳ 开始生成图片")

        img_bytes = await poll_until_done(job_id, on_progress)

        # 保存
        save_path = IMAGE_SAVE_DIR / f"{job_id}.png"
        save_path.write_bytes(img_bytes)
        logger.info(f"[EverPic] 图片已保存: {save_path}")

        # 构建回复消息：引用原消息 + 图片 + 积分信息
        b64 = base64.b64encode(img_bytes).decode()
        reply_msg = Message()
        reply_msg += MessageSegment.reply(event.message_id)

        if not is_sa:
            remaining = deduct_points(event.user_id, DRAW_COST)
            reply_msg += MessageSegment.text(f"💰 消耗 {DRAW_COST} 积分，剩余: {remaining}\n")

        reply_msg += MessageSegment.image(f"base64://{b64}")
        # 发送并获取 bot 发出的 message_id，记录到 job 映射供 HQ 引用反查
        bot = event.get_bot()
        receipt = await bot.send(event, reply_msg)
        bot_msg_id = None
        if receipt is not None:
            if hasattr(receipt, "message_id"):
                bot_msg_id = receipt.message_id
            elif isinstance(receipt, dict):
                bot_msg_id = receipt.get("message_id")
        if bot_msg_id is not None:
            save_image_job(str(bot_msg_id), job_id)

    except RuntimeError as e:
        logger.error(f"[EverPic] 生成失败: {e}")
        await matcher.send(f"❌ 生成失败: {e}")
    except httpx.ConnectError:
        logger.error("[EverPic] 无法连接到 EverPic 服务器")
        await matcher.send("❌ 无法连接到 EverPic 服务器，请检查网络或稍后重试")
    except httpx.TimeoutException:
        logger.error("[EverPic] 连接 EverPic 服务器超时")
        await matcher.send("❌ 连接服务器超时，请稍后重试")
    except Exception as e:
        logger.exception(f"[EverPic] 未知错误: {e}")
        await matcher.send(f"❌ 生成失败: {e}")
    finally:
        remove_job(job_info)

        # 记录请求日志
        try:
            sender = event.sender
            log_entry = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_name": sender.nickname or sender.card or str(event.user_id),
                "user_id": event.user_id,
                "group_id": event.group_id,
                "request_body": request_body,
            }
            append_request_log(log_entry)
        except Exception:
            pass

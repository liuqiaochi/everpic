"""HQ 高清升级：引用本机器人生成的图片 + 文本「HQ」"""
import base64
import httpx
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, MessageSegment, Message
from nonebot.rule import Rule

from ..config import DRAW_COST, MAX_CONCURRENT_JOBS, IMAGE_SAVE_DIR
from ..store import (
    is_blacklisted, is_super_admin, is_group_enabled,
    get_user_points, deduct_points, get_job_by_msg_id, save_image_job,
)
from ..api import call_upscale, poll_until_done
from ..jobs import create_job, remove_job, active_count


async def _hq_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    if not (text == "HQ" or text.startswith("HQ ")):
        return False
    # 必须引用一条消息（且是本机器人发出的图片）
    return bool(event.reply)


hq_matcher = on_message(rule=Rule(_hq_rule), priority=10, block=True)


def _extract_bot_msg_id(receipt):
    """从 onebot 发送回执里提取 bot 发出的 message_id"""
    if receipt is None:
        return None
    if hasattr(receipt, "message_id"):
        return receipt.message_id
    if isinstance(receipt, dict):
        return receipt.get("message_id")
    return None


@hq_matcher.handle()
async def handle_hq(event: GroupMessageEvent):
    # 群开关
    if not is_group_enabled(event.group_id):
        await hq_matcher.finish("❌ 本群未开启 EverPic 画图功能，请联系超级管理员发送 everpic开启")

    # 黑名单
    if is_blacklisted(event.user_id):
        await hq_matcher.finish("❌ 你已被拉黑，无法使用 HQ 功能")

    # 积分（超管跳过）
    is_sa = is_super_admin(event.user_id)
    if not is_sa:
        pts = get_user_points(event.user_id)
        if pts < DRAW_COST:
            await hq_matcher.finish(
                f"❌ 积分不足！当前积分: {pts}，需要: {DRAW_COST}\n发送 everpic签到 获取积分"
            )

    # 并发
    if active_count() >= MAX_CONCURRENT_JOBS:
        await hq_matcher.finish(
            f"当前已有 {active_count()} 个任务进行中（上限{MAX_CONCURRENT_JOBS}），请稍后再试！"
        )

    # 从被引用消息反查 server job_id
    reply_id = event.reply.message_id
    job_id = get_job_by_msg_id(str(reply_id))
    if not job_id:
        await hq_matcher.finish(
            "❌ 请引用一张由本机器人「画图」生成的图片（即本机器人发出的图片），再发送 HQ"
        )

    await hq_matcher.send("✨ 开始 HQ 高清升级...")

    job_info = create_job(
        user_id=event.user_id,
        group_id=event.group_id,
        char_name="HQ升级",
        variant_name="",
    )
    try:
        new_job_id = await call_upscale(job_id)

        async def on_progress():
            await hq_matcher.send("⏳ 正在生成 HQ 图片...")

        img_bytes = await poll_until_done(new_job_id, on_progress)

        # 保存
        save_path = IMAGE_SAVE_DIR / f"hq_{new_job_id}.png"
        save_path.write_bytes(img_bytes)

        # 构建回复：引用用户消息 + 图片 + 积分信息
        b64 = base64.b64encode(img_bytes).decode()
        reply_msg = Message()
        reply_msg += MessageSegment.reply(event.message_id)
        if not is_sa:
            remaining = deduct_points(event.user_id, DRAW_COST)
            reply_msg += MessageSegment.text(f"💰 HQ 消耗 {DRAW_COST} 积分，剩余: {remaining}\n")
        reply_msg += MessageSegment.image(f"base64://{b64}")
        bot = event.get_bot()
        receipt = await bot.send(event, reply_msg)
        bot_msg_id = _extract_bot_msg_id(receipt)
        if bot_msg_id is not None:
            save_image_job(str(bot_msg_id), new_job_id)

    except RuntimeError as e:
        logger.error(f"[EverPic] HQ 失败: {e}")
        await hq_matcher.send(f"❌ HQ 失败: {e}")
    except httpx.ConnectError:
        logger.error("[EverPic] 无法连接到 EverPic 服务器")
        await hq_matcher.send("❌ 无法连接到 EverPic 服务器，请检查网络或稍后重试")
    except httpx.TimeoutException:
        logger.error("[EverPic] 连接 EverPic 服务器超时")
        await hq_matcher.send("❌ 连接服务器超时，请稍后重试")
    except Exception as e:
        logger.exception(f"[EverPic] HQ 未知错误: {e}")
        await hq_matcher.send(f"❌ HQ 失败: {e}")
    finally:
        remove_job(job_info)

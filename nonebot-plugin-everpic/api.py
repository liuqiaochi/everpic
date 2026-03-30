"""EverPic API 调用"""
import asyncio
import httpx
from nonebot import logger
from .config import EVERPIC_API


async def call_generate(char: dict, variant: dict, user_prompt: str,
                       draw_settings: dict | None = None) -> str:
    """提交生成请求，返回 job_id。draw_settings 为用户自定义画图参数。"""
    from .config import (
        DEFAULT_MODEL_STRENGTH, DEFAULT_CLIP_STRENGTH,
        DEFAULT_STEPS, DEFAULT_CFG_SCALE, DEFAULT_NEGATIVE,
    )
    s = draw_settings or {}
    model_str = s.get("model_strength", DEFAULT_MODEL_STRENGTH)
    clip_str = s.get("clip_strength", DEFAULT_CLIP_STRENGTH)
    steps = s.get("steps", DEFAULT_STEPS)
    cfg = s.get("cfg_scale", DEFAULT_CFG_SCALE)
    user_neg = s.get("negative", DEFAULT_NEGATIVE)

    primary = {
        "ckpt": variant["ckpt"],
        "keyword": variant["keyword"],
        "name": variant["name"],
        "parent": char["name"],
    }

    positive_parts = [primary["keyword"]]
    if user_prompt:
        positive_parts.append(user_prompt)
    positive_parts.append("masterpiece, best quality, amazing quality")

    negative = "bad quality,worst quality,worst detail,sketch,censor,"
    if user_neg:
        negative += user_neg

    body = {
        "primary": primary,
        "positive": ", ".join(positive_parts),
        "negative": negative,
        "primary_model": model_str, "primary_clip": clip_str,
        "extra_model": model_str, "extra_clip": clip_str,
        "three_model": model_str, "three_clip": clip_str,
        "steps": steps, "cfgScale": cfg, "size": "portrait",
        "image_strength": 1, "count": 1,
    }

    logger.info("[EverPic] 正在提交生成请求...")
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            EVERPIC_API + "generate",
            json=body,
            headers={"Content-Type": "application/json"},
        )
        logger.info(f"[EverPic] generate 响应: {resp.status_code} {resp.text[:200]}")

        if resp.status_code == 403:
            raise RuntimeError(f"服务器拒绝: {resp.json().get('message', '403')}")
        if resp.status_code == 429:
            raise RuntimeError("请求过于频繁，请稍后再试")
        if not (200 <= resp.status_code < 300):
            raise RuntimeError(f"服务器错误: HTTP {resp.status_code}")

        job_id = resp.json().get("id", str(resp.json()))

    logger.info(f"[EverPic] 获得 job_id: {job_id}")
    return job_id


async def poll_until_done(job_id: str, on_progress) -> bytes:
    """轮询直到完成，IN_PROGRESS 时回调 on_progress，返回图片 bytes"""
    progress_sent = False
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        for i in range(150):
            await asyncio.sleep(2)
            try:
                resp = await client.get(EVERPIC_API + f"status/{job_id}")
            except httpx.TimeoutException:
                logger.warning(f"[EverPic] 轮询超时，重试... ({i})")
                continue
            except Exception as e:
                logger.warning(f"[EverPic] 轮询异常: {e}，重试... ({i})")
                continue

            if resp.status_code == 404:
                raise RuntimeError("任务已过期或未找到")
            if not (200 <= resp.status_code < 300):
                logger.warning(f"[EverPic] status 响应异常: {resp.status_code}")
                continue

            status = resp.json().get("status", "")
            logger.debug(f"[EverPic] 轮询 [{i*2}s] 状态: {status}")

            if status == "IN_PROGRESS" and not progress_sent:
                await on_progress()
                progress_sent = True
            elif status == "COMPLETED":
                logger.info("[EverPic] 生成完成，正在下载图片...")
                try:
                    img_resp = await client.get(EVERPIC_API + f"fetch/{job_id}")
                except Exception as e:
                    raise RuntimeError(f"图片下载异常: {e}")
                if img_resp.status_code != 200:
                    raise RuntimeError(f"图片下载失败: HTTP {img_resp.status_code}")
                logger.info(f"[EverPic] 图片下载完成: {len(img_resp.content)} bytes")
                return img_resp.content
            elif status == "FAILED":
                raise RuntimeError("服务器生成失败")

        raise RuntimeError("生成超时（5分钟）")

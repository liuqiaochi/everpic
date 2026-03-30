"""角色数据加载与查找"""
import json
from nonebot import logger
from .config import DATA_FILE

with open(DATA_FILE, "r", encoding="utf-8") as f:
    LORA_DATA: list[dict] = json.load(f)["characters"]

logger.info(f"[EverPic] 已加载 {len(LORA_DATA)} 个角色")


def find_character(keyword: str) -> dict | None:
    """通过 name / name_cn / aliases 查找角色"""
    keyword = keyword.strip()
    if not keyword:
        return None
    for c in LORA_DATA:
        if keyword in (c["name"], c["name_cn"]):
            return c
        if keyword in c.get("aliases", []):
            return c
    return None


def find_variant(char: dict, keyword: str) -> dict:
    """通过 name / name_cn / 序号查找变体，找不到返回第一个"""
    keyword = keyword.strip()
    if not keyword:
        return char["variants"][0]

    try:
        idx = int(keyword)
        if 1 <= idx <= len(char["variants"]):
            return char["variants"][idx - 1]
    except ValueError:
        pass

    for v in char["variants"]:
        if keyword in (v["name"], v.get("name_cn", "")):
            return v

    return char["variants"][0]


def is_variant_matched(char: dict, keyword: str) -> bool:
    """判断 keyword 是否真的匹配到了某个变体（而非 fallback）"""
    try:
        idx = int(keyword)
        return 1 <= idx <= len(char["variants"])
    except ValueError:
        pass
    for v in char["variants"]:
        if keyword in (v["name"], v.get("name_cn", "")):
            return True
    return False

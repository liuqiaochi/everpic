"""NSFW 违禁词过滤"""

NSFW_KEYWORDS = [
    # English
    "nsfw", "nude", "naked", "topless", "bottomless",
    "nipple", "nipples", "pussy", "vagina", "penis", "dick", "cock",
    "sex", "sexual", "intercourse", "penetration", "cum", "cumshot",
    "blowjob", "handjob", "footjob", "fellatio", "cunnilingus",
    "masturbat", "orgasm", "erotic", "hentai", "ahegao",
    "bondage", "bdsm", "tentacle", "rape", "gangbang",
    "spread legs", "spread_legs", "ass", "anus", "butthole",
    "groping", "undress", "strip", "panties down", "panties_down",
    "no panties", "no_panties", "no bra", "no_bra",
    "exposed", "genitals", "pubic", "crotch",
    "breast grab", "breast_grab", "breast sucking",
    "thighhighs only", "underwear only",
    "loli", "shota", "child", "underage", "minor",
    # 中文
    "裸体", "裸露", "色情", "性交", "做爱", "口交", "手交",
    "自慰", "高潮", "射精", "潮吹", "乳头", "阴道", "阴茎",
    "肛门", "内射", "中出", "无码", "里番",
    "强奸", "轮奸", "捆绑", "调教", "触手",
    "脱衣", "露出", "不穿", "没穿",
]


def check_nsfw(text: str) -> str | None:
    """检查文本是否包含 NSFW 关键词，返回匹配到的词或 None"""
    lower = text.lower()
    for kw in NSFW_KEYWORDS:
        if kw in lower:
            return kw
    return None

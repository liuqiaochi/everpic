"""NSFW 违禁词过滤"""
import re

# 英文单词级关键词（用词边界 \b 匹配，避免 ass 匹配到 class/glass 等）
_EN_WORDS = [
    "nsfw", "nude", "naked", "topless", "bottomless",
    "nipple", "nipples", "pussy", "vagina", "penis", "dick", "cock",
    "clitoris", "clit", "vulva", "labia", "urethra", "foreskin", "scrotum",
    "sex", "sexual", "intercourse", "penetration", "cum", "cumshot",
    "creampie", "bukkake", "facial", "deepthroat",
    "blowjob", "handjob", "footjob", "titjob", "boobjob", "paizuri",
    "fellatio", "cunnilingus", "rimjob", "analingus",
    "masturbation", "masturbating", "orgasm", "erotic", "hentai", "ahegao",
    "bondage", "bdsm", "tentacle", "rape", "gangbang", "orgy", "threesome",
    "ass", "anus", "butthole", "asshole", "rectum",
    "groping", "undress", "strip", "fondle", "molest",
    "exposed", "genitals", "pubic", "crotch", "groin",
    "ejaculation", "squirt", "squirting", "arousal",
    "dominatrix", "submissive", "sadism", "masochism", "fetish",
    "incest", "bestiality", "zoophilia", "necrophilia",
    "loli", "shota", "underage", "pedophile",
    "dildo", "vibrator", "buttplug", "fleshlight",
    "shibari", "gagged", "blindfold", "collar", "leash",
    "enema", "fisting", "pegging", "prolapse",
    "cameltoe", "upskirt", "downblouse", "wardrobe malfunction",
    "pornography", "porn", "xxx", "r18",
]

# 英文多词短语（用子串匹配即可，本身已足够具体）
_EN_PHRASES = [
    "spread legs", "spread_legs",
    "panties down", "panties_down",
    "no panties", "no_panties", "no bra", "no_bra",
    "breast grab", "breast_grab", "breast sucking",
    "thighhighs only", "underwear only",
]

# 中文关键词（子串匹配，中文没有词边界问题）
_CN_KEYWORDS = [
    "裸体", "裸露", "色情", "性交", "做爱", "口交", "手交",
    "自慰", "高潮", "射精", "潮吹", "乳头", "阴道", "阴茎",
    "肛门", "内射", "中出", "无码", "里番",
    "强奸", "轮奸", "捆绑", "调教", "触手",
    "脱衣", "露出", "不穿", "没穿",
]

# 预编译英文单词的正则（词边界匹配）
_en_word_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in _EN_WORDS) + r')\b',
    re.IGNORECASE,
)


def check_nsfw(text: str) -> str | None:
    """检查文本是否包含 NSFW 关键词，返回匹配到的词或 None"""
    # 英文单词（词边界）
    m = _en_word_pattern.search(text)
    if m:
        return m.group(0)

    lower = text.lower()

    # 英文短语（子串）
    for phrase in _EN_PHRASES:
        if phrase in lower:
            return phrase

    # 中文（子串）
    for kw in _CN_KEYWORDS:
        if kw in text:
            return kw

    return None

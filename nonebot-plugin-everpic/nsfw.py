"""NSFW 违禁词过滤"""
import re

from .store import load_banned_words

# 英文单词级关键词（用词边界 \b 匹配，避免 ass 匹配到 class/glass 等）
_EN_WORDS = [
    # --- 原有 ---
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
    "cameltoe", "upskirt", "downblouse",
    "pornography", "porn", "xxx", "r18",
    # --- 从 swearList.csv 新增（已去重）---
    "anal", "arrse", "arse", "assfucker", "assfukka", "assholes", "asswhole",
    "ballbag", "balls", "ballsack", "bastard", "bellend",
    "biatch", "bitch", "bitcher", "bitchers", "bitches", "bitchin", "bitching",
    "bloody", "bollock", "bollok", "boner", "boob", "boobs",
    "breast", "breasts", "buceta", "bugger", "bum", "butt", "buttmuch",
    "chink", "clits", "cnut",
    "cockface", "cockhead", "cockmunch", "cockmuncher", "cocks",
    "cocksuck", "cocksucked", "cocksucker", "cocksucking", "cocksucks",
    "cok", "cokmuncher", "coksucka", "coon", "cox", "crap",
    "cummer", "cumming", "cums", "cunilingus", "cunillingus",
    "cunt", "cuntlick", "cuntlicker", "cuntlicking", "cunts",
    "damn", "dickhead", "dildos", "dink", "dinks", "dirsa",
    "dogging", "donkeyribber", "doosh", "duche", "dyke",
    "ejaculate", "ejaculated", "ejaculates", "ejaculating", "ejaculatings", "ejakulate",
    "fag", "fagging", "faggitt", "faggot", "faggs", "fagot", "fagots", "fags",
    "fanny", "fannyflaps", "fannyfucker", "fatass",
    "fcuk", "fcuker", "fcuking", "feck", "fecker",
    "felching", "fellate",
    "fingerfuck", "fingerfucked", "fingerfucker", "fingerfuckers", "fingerfucking", "fingerfucks",
    "fistfuck", "fistfucked", "fistfucker", "fistfuckers", "fistfucking", "fistfuckings", "fistfucks",
    "flange", "fook", "fooker",
    "fuck", "fucka", "fucked", "fucker", "fuckers", "fuckhead", "fuckheads",
    "fuckin", "fucking", "fuckings", "fucks", "fuckwhit", "fuckwit",
    "fuk", "fuker", "fukker", "fukkin", "fuks", "fukwhit", "fukwit", "fux",
    "gaylord", "gaysex", "goatse",
    "hell", "hoar", "hoare", "hoer", "homo", "hore", "horniest", "horny", "hotsex",
    "jackoff", "jap", "jism", "jiz", "jizm", "jizz",
    "kawk", "knob", "knobead", "knobed", "knobend", "knobhead", "knobjocky", "knobjokey",
    "kock", "kondum", "kondums", "kum", "kummer", "kumming", "kums", "kunilingus",
    "lmfao", "lust", "lusting",
    "masochist", "masterb8", "masterbate", "masterbation", "masterbations", "masturbate",
    "mofo", "mothafuck", "mothafucka", "mothafuckas", "mothafuckaz",
    "mothafucked", "mothafucker", "mothafuckers", "mothafuckin", "mothafucking", "mothafuckings", "mothafucks",
    "motherfuck", "motherfucked", "motherfucker", "motherfuckers",
    "motherfuckin", "motherfucking", "motherfuckings", "motherfuckka", "motherfucks",
    "muff", "mutha", "muthafecker", "muthafuckker", "muther", "mutherfucker",
    "nazi", "nigga", "niggah", "niggas", "niggaz", "nigger", "niggers",
    "nob", "nobhead", "nobjocky", "nobjokey", "numbnuts", "nutsack",
    "orgasim", "orgasims", "orgasms",
    "pawn", "pecker", "penisfucker", "phonesex",
    "phuck", "phuk", "phuked", "phuking", "phukked", "phukking", "phuks", "phuq",
    "pigfucker", "pimpis", "piss", "pissed", "pisser", "pissers", "pisses",
    "pissflaps", "pissin", "pissing", "pissoff", "poop",
    "porno", "pornos", "prick", "pricks", "pron", "pube",
    "pusse", "pussi", "pussies", "pussys",
    "retard", "rimjaw", "rimming",
    "sadist", "schlong", "screwing", "scroat", "scrote", "scrotum", "semen",
    "shag", "shagger", "shaggin", "shagging", "shemale",
    "shit", "shitdick", "shite", "shited", "shitey", "shitfuck", "shitfull",
    "shithead", "shiting", "shitings", "shits", "shitted", "shitter", "shitters",
    "shitting", "shittings", "shitty",
    "skank", "slut", "sluts", "smegma", "smut", "snatch",
    "spac", "spunk",
    "testical", "testicle", "tit", "titfuck", "tits", "titt",
    "tittiefucker", "titties", "tittyfuck", "tittywank", "titwank",
    "tosser", "turd", "twat", "twathead", "twatty", "twunt", "twunter",
    "vaginal", "viagra", "wang", "wank", "wanker", "wanky",
    "whoar", "whore", "willies", "willy", "xrated",
    # --- swearList.csv 中的特殊术语 ---
    "clitoral", "phallic", "perineum", "intravaginal",
    "tonguejob", "tentaclejob", "glansjob", "glans", "tailjob", "shoejob",
    "sexually", "underwear", "menstruation", "menstrual",
    "erotibot", "pervert", "cleavage", "futa", "furry",
    "panties", "lingerie", "condom", "strips", "insertion",
    "peeing", "pee", "peeping", "erection", "yaoi",
    "cumdrip", "precum", "defloration", "netorare", "irrumatio",
    "spitroast", "tribadism", "impregnation", "frottage", "fertilization",
    "voyeurism", "anilingus", "newhalf", "futasub", "afterglow",
    "cumdump", "aroused", "naizuri", "autofacial",
    "autoarousal", "lolidom", "koonago", "aphrodisiac", "scat",
    "autofellatio", "pecjob", "autopaizuri", "aneros", "codpiece",
    "reichsadler", "bootjob", "oral", "tentacles", "fingering",
    "gaping", "phimosis", "ryona", "hairjob",
    "drugs", "drugged", "wax", "nakadashi",
    "pregnancy", "areola", "areolae",
]

# 英文多词短语（用子串匹配即可，本身已足够具体）
_EN_PHRASES = [
    # --- 原有 ---
    "spread legs", "spread_legs", "open legs", "open_legs",
    "panties down", "panties_down", "panties aside", "panties_aside",
    "no panties", "no_panties", "no bra", "no_bra",
    "no clothes", "no_clothes", "no underwear", "no_underwear",
    "breast grab", "breast_grab", "breast sucking", "breast_sucking",
    "nipple sucking", "nipple_sucking", "nipple pinch", "nipple_pinch",
    "thighhighs only", "underwear only", "nude filter",
    "pussy juice", "pussy_juice", "love juice", "love_juice",
    "sex toy", "sex_toy", "ball gag", "ball_gag",
    "body writing", "body_writing", "slave collar",
    "after sex", "after_sex", "used condom",
    # --- 从 swearList.csv 新增 ---
    "blow job", "bunny fucker", "carpet muncher", "cock-sucker",
    "dog-fucker", "fudge packer", "f u c k", "f u c k e r",
    "jack-off", "jerk-off", "mother fucker", "nob jokey",
    "s.o.b.", "son-of-a-bitch", "wardrobe malfunction",
    "ass-fucker", "god-dam", "god-damned",
    "master-bate", "mo-fo", "reach-around", "strap-on",
    "after rape", "public use", "urine meter",
    "fat mons", "pov crotch", "leg lock",
    "nipple-to-nipple", "missionary position",
]

# 中文关键词（子串匹配，中文没有词边界问题）
_CN_KEYWORDS = [
    # --- 原有 ---
    "裸体", "裸露", "色情", "性交", "做爱", "口交", "手交",
    "自慰", "高潮", "射精", "潮吹", "乳头", "阴道", "阴茎",
    "阴蒂", "阴唇", "肛门", "内射", "中出", "无码", "里番",
    "强奸", "轮奸", "捆绑", "调教", "触手", "乱伦",
    "脱衣", "露出", "不穿", "没穿", "全裸", "半裸",
    "淫荡", "淫乱", "肉棒", "肉穴", "骑乘", "后入",
    "颜射", "口爆", "吞精", "足交", "乳交", "肛交",
    "绳缚", "奴隶", "凌辱", "痴汉", "猥亵",
    "情趣用品", "按摩棒", "跳蛋", "飞机杯",
    # --- 从 swearList.csv 对应中文翻译新增 ---
    "混蛋", "王八蛋", "婊子", "荡妇", "贱人", "妓女",
    "屁股", "屁眼", "睾丸", "阴囊", "包皮",
    "鸡巴", "屌", "龟头", "阳具",
    "勃起", "精液", "精子", "前列腺",
    "吹箫", "舔阴", "舔肛", "指交",
    "拳交", "假阳具", "假鸡巴",
    "肛塞", "跳蛋", "振动棒",
    "变态", "偷窥", "恋童", "恋尸",
    "兽交", "人兽", "纳粹",
    "脏话", "操", "草泥马", "他妈的", "妈逼", "傻逼", "牛逼",
    "鸡掰", "干你娘", "去死",
    "阴毛", "会阴", "乳晕",
    "颜骑", "口球", "项圈",
    "灌肠", "脱肛", "肛裂",
    "怀孕", "受精", "受孕", "着床",
    "尿", "排尿", "偷看", "偷拍",
    "药物", "迷药", "下药",
    "扶她", "伪娘", "女装",
    "寝取", "凌辱", "轮姦",
    "摩擦", "磨蹭", "贴身",
    "三人行", "群交", "乱交",
    "春药", "催情", "媚药",
    "食粪", "排泄", "黄金浴",
    "内衣", "胸罩", "丁字裤", "情趣内衣",
    "舌交", "触手交", "鞋交", "靴交", "发交",
    "驼峰", "骆驼趾",
    "色图", "工口", "十八禁", "成人",
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

    # 动态违禁词（超管通过指令添加，子串匹配，大小写不敏感）
    for kw in load_banned_words():
        if not kw:
            continue
        if len(kw) <= 2 and kw.isascii():
            # 短英文词用词边界匹配，避免误伤
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                return kw
        else:
            # 中文或长词用子串匹配
            if kw.lower() in lower or kw in text:
                return kw

    return None

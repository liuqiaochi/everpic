"""NSFW 禁词过滤 — 词库持久化到 banned_words.json，支持动态增删查"""
import json
import re

from .config import BANNED_WORDS_FILE

# 默认英文单词（首次运行写入 JSON 文件作为初始数据）
_DEFAULT_EN_WORDS = [
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

# 默认英文短语（用子串匹配）
_DEFAULT_EN_PHRASES = [
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

# 默认中文关键词
_DEFAULT_CN_KEYWORDS = [
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


# ---- 内存缓存 ----
_cache = {
    "loaded": False,
    "en_words": [],
    "en_phrases": [],
    "cn_keywords": [],
    "pattern": None,
}


def _detect_type(word: str) -> str:
    """自动判断词应归属的类型：
    - 含中文字符 → cn_keywords（子串匹配）
    - 含空格 → en_phrases（子串匹配）
    - 否则 → en_words（词边界 \b 匹配）
    """
    if any('\u4e00' <= ch <= '\u9fff' for ch in word):
        return "cn_keywords"
    if ' ' in word:
        return "en_phrases"
    return "en_words"


def _load_file() -> dict:
    """从 JSON 文件加载词库；文件不存在则用默认值初始化并写入。"""
    if BANNED_WORDS_FILE.exists():
        try:
            with open(BANNED_WORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 兼容旧格式（扁平 list）— 自动迁移到三分类
            if isinstance(data, list):
                new_data = {
                    "en_words": list(_DEFAULT_EN_WORDS),
                    "en_phrases": list(_DEFAULT_EN_PHRASES),
                    "cn_keywords": list(_DEFAULT_CN_KEYWORDS),
                }
                for w in data:
                    w = w.strip()
                    if not w:
                        continue
                    t = _detect_type(w)
                    if w not in new_data[t]:
                        new_data[t].append(w)
                _save_file(new_data)
                return new_data
            if isinstance(data, dict):
                # 补全缺失的键
                return {
                    "en_words": data.get("en_words", list(_DEFAULT_EN_WORDS)),
                    "en_phrases": data.get("en_phrases", list(_DEFAULT_EN_PHRASES)),
                    "cn_keywords": data.get("cn_keywords", list(_DEFAULT_CN_KEYWORDS)),
                }
        except Exception:
            pass
    # 文件不存在或损坏，用默认值初始化
    data = {
        "en_words": list(_DEFAULT_EN_WORDS),
        "en_phrases": list(_DEFAULT_EN_PHRASES),
        "cn_keywords": list(_DEFAULT_CN_KEYWORDS),
    }
    _save_file(data)
    return data


def _save_file(data: dict):
    with open(BANNED_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ensure_loaded():
    """懒加载词库到缓存，并预编译英文单词正则。"""
    if not _cache["loaded"]:
        data = _load_file()
        _cache["en_words"] = data["en_words"]
        _cache["en_phrases"] = data["en_phrases"]
        _cache["cn_keywords"] = data["cn_keywords"]
        if _cache["en_words"]:
            _cache["pattern"] = re.compile(
                r'\b(' + '|'.join(re.escape(w) for w in _cache["en_words"]) + r')\b',
                re.IGNORECASE,
            )
        else:
            _cache["pattern"] = None
        _cache["loaded"] = True


def _invalidate():
    """使缓存失效，下次访问会重新加载。"""
    _cache["loaded"] = False


# ---- 检查接口 ----

def check_nsfw(text: str) -> str | None:
    """检查文本是否包含禁词，返回匹配到的词或 None"""
    _ensure_loaded()

    # 英文单词（词边界）
    if _cache["pattern"]:
        m = _cache["pattern"].search(text)
        if m:
            return m.group(0)

    lower = text.lower()

    # 英文短语（子串）
    for phrase in _cache["en_phrases"]:
        if phrase in lower:
            return phrase

    # 中文（子串）
    for kw in _cache["cn_keywords"]:
        if kw in text:
            return kw

    return None


# ---- 管理 API（供 admin 指令调用）----

def add_banned_word(word: str) -> tuple[bool, str]:
    """添加禁词。返回 (是否成功, 信息)"""
    word = word.strip()
    if not word:
        return False, "禁词不能为空"

    _ensure_loaded()
    word_type = _detect_type(word)
    target_list = _cache[word_type]

    if word in target_list:
        return False, f"「{word}」已在禁词列表中（{_type_label(word_type)}）"

    target_list.append(word)
    _save_file({
        "en_words": _cache["en_words"],
        "en_phrases": _cache["en_phrases"],
        "cn_keywords": _cache["cn_keywords"],
    })
    _invalidate()
    return True, f"已添加「{word}」（{_type_label(word_type)}）"


def remove_banned_word(word: str) -> tuple[bool, str]:
    """删除禁词。返回 (是否成功, 信息)"""
    word = word.strip()
    if not word:
        return False, "禁词不能为空"

    _ensure_loaded()

    # 先按自动检测的类型找，找不到再跨所有类型找
    word_type = _detect_type(word)
    if word in _cache[word_type]:
        _cache[word_type].remove(word)
        _save_file({
            "en_words": _cache["en_words"],
            "en_phrases": _cache["en_phrases"],
            "cn_keywords": _cache["cn_keywords"],
        })
        _invalidate()
        return True, f"已删除「{word}」（{_type_label(word_type)}）"

    # 跨类型查找
    for t in ("en_words", "en_phrases", "cn_keywords"):
        if word in _cache[t]:
            _cache[t].remove(word)
            _save_file({
                "en_words": _cache["en_words"],
                "en_phrases": _cache["en_phrases"],
                "cn_keywords": _cache["cn_keywords"],
            })
            _invalidate()
            return True, f"已删除「{word}」（{_type_label(t)}）"

    return False, f"「{word}」不在禁词列表中"


def list_banned_words() -> dict[str, list[str]]:
    """返回所有禁词，按类型分组"""
    _ensure_loaded()
    return {
        "en_words": list(_cache["en_words"]),
        "en_phrases": list(_cache["en_phrases"]),
        "cn_keywords": list(_cache["cn_keywords"]),
    }


def search_banned_words(keyword: str) -> dict[str, list[str]]:
    """按关键词搜索禁词（子串匹配，大小写不敏感）"""
    _ensure_loaded()
    kw_lower = keyword.lower()
    result = {"en_words": [], "en_phrases": [], "cn_keywords": []}
    for w in _cache["en_words"]:
        if kw_lower in w.lower():
            result["en_words"].append(w)
    for w in _cache["en_phrases"]:
        if kw_lower in w.lower():
            result["en_phrases"].append(w)
    for w in _cache["cn_keywords"]:
        if keyword in w or kw_lower in w.lower():
            result["cn_keywords"].append(w)
    return result


def _type_label(t: str) -> str:
    return {
        "en_words": "英文单词",
        "en_phrases": "英文短语",
        "cn_keywords": "中文",
    }.get(t, t)

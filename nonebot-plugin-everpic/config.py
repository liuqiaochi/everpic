from pathlib import Path

# 插件根目录
PLUGIN_DIR = Path(__file__).parent

# API
EVERPIC_API = "https://everpic.mephistopheles.moe/api/"

# 图片保存
IMAGE_SAVE_DIR = PLUGIN_DIR / "images"
IMAGE_SAVE_DIR.mkdir(exist_ok=True)

# 并发控制
MAX_CONCURRENT_JOBS = 3

# 积分
INITIAL_POINTS = 50
DRAW_COST = 10
SIGN_MIN = 10
SIGN_MAX = 30
GIFT_MIN = 1
GIFT_MAX = 50
DAILY_RECEIVE_LIMIT = 100

# 尺寸映射
SIZE_MAP = {
    "3:4": "portrait", "竖": "portrait", "竖版": "portrait", "portrait": "portrait",
    "9:16": "wportrait", "窄竖": "wportrait", "wportrait": "wportrait",
    "4:3": "landscape", "横": "landscape", "横版": "landscape", "landscape": "landscape",
    "16:9": "wlandscape", "宽横": "wlandscape", "wlandscape": "wlandscape",
    "1:1": "square", "方": "square", "正方": "square", "square": "square",
}
DEFAULT_SIZE = "portrait"

# 画图默认参数
DEFAULT_MODEL_STRENGTH = 0.9
DEFAULT_CLIP_STRENGTH = 1.0
DEFAULT_STEPS = 27
DEFAULT_CFG_SCALE = 6.0
DEFAULT_NEGATIVE = ""

# 用户设置文件
USER_SETTINGS_FILE = PLUGIN_DIR / "user_settings.json"

# 请求日志文件
REQUEST_LOG_FILE = PLUGIN_DIR / "request_log.json"

# 存词功能
MAX_WORDS = 20
WORD_STORE_FILE = PLUGIN_DIR / "word_store.json"

# 动态违禁词
BANNED_WORDS_FILE = PLUGIN_DIR / "banned_words.json"

# 数据文件路径
DATA_FILE = PLUGIN_DIR / "everpic_lora_list.json"
BLACKLIST_FILE = PLUGIN_DIR / "blacklist.json"
SUPER_ADMIN_FILE = PLUGIN_DIR / "super_admins.json"
GROUP_SETTINGS_FILE = PLUGIN_DIR / "group_settings.json"
POINTS_FILE = PLUGIN_DIR / "points.json"

# 字体搜索路径
FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]
LOCAL_FONT = PLUGIN_DIR / "font.ttf"

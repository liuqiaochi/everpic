from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="EverPic",
    description="EverPic 角色查询与图片生成",
    usage="发送 everpic帮助 查看指令列表",
)

# 导入 handlers 以注册所有 matcher
from .handlers import *  # noqa: F401, F403

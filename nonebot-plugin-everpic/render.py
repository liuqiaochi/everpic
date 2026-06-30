"""图片渲染"""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .config import FONT_PATHS, LOCAL_FONT
from .data import LORA_DATA


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    if LOCAL_FONT.exists():
        return ImageFont.truetype(str(LOCAL_FONT), size)
    return ImageFont.load_default()


def render_char_list_images() -> list[bytes]:
    """把角色列表渲染成 2 张 PNG 图片，每张约一半角色，3列布局，别称显示在名字下方"""
    title_font = _load_font(28)
    name_font = _load_font(20)
    alias_font = _load_font(16)

    pad_x, pad_y = 40, 30
    col_width = 260
    cols = 3
    title_height = 60

    # 布局：名字行 + 间距 + 别称行 + 底部间距
    name_line_h = 26
    gap = 4
    alias_line_h = 22
    item_bottom = 10
    item_height = name_line_h + gap + alias_line_h + item_bottom

    mid = len(LORA_DATA) // 2
    chunks = [LORA_DATA[:mid], LORA_DATA[mid:]]
    offsets = [0, mid]
    result = []

    for page, (chunk, offset) in enumerate(zip(chunks, offsets)):
        rows_per_col = (len(chunk) + cols - 1) // cols

        img_w = pad_x * 2 + col_width * cols
        img_h = pad_y * 2 + title_height + item_height * rows_per_col + 20

        img = Image.new("RGB", (img_w, img_h), "#1a1a2e")
        draw = ImageDraw.Draw(img)

        title = f"📋 EverPic 角色列表（{page+1}/2，共{len(LORA_DATA)}个）"
        draw.text((pad_x, pad_y), title, fill="#a78bfa", font=title_font)

        y_start = pad_y + title_height
        for i, c in enumerate(chunk):
            col = i // rows_per_col
            row = i % rows_per_col
            x = pad_x + col * col_width
            y = y_start + row * item_height

            # 角色名
            idx = offset + i + 1
            draw.text((x, y), f"{idx}. {c['name_cn']}", fill="#e0e0e0", font=name_font)

            # 别称（同色，稍小字号，有间距）
            aliases = c.get("aliases", [])
            if aliases:
                alias_text = "  " + ", ".join(aliases[:5])
                if len(aliases) > 5:
                    alias_text += "..."
                draw.text((x, y + name_line_h + gap), alias_text,
                          fill="#e0e0e0", font=alias_font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        result.append(buf.getvalue())

    return result


def render_help_image() -> bytes:
    """把帮助文本渲染成 PNG 图片"""
    title_font = _load_font(24)
    heading_font = _load_font(18)
    body_font = _load_font(15)

    lines = [
        ("title", "📖 EverPic 指令帮助"),
        ("blank", ""),
        ("heading", "【查看角色列表】"),
        ("body", "  everpic角色 → 返回所有可用角色的图片列表"),
        ("blank", ""),
        ("heading", "【画图】（消耗10积分，超级管理员免费）"),
        ("body", "  画图 [尺寸] 角色名 [变体] [Prompt]"),
        ("body", "  尺寸可选: 3:4(默认) 9:16 4:3 16:9 1:1"),
        ("body", "  角色名支持中文名/韩文名/别称"),
        ("body", "  变体可选，不填用默认；支持中文名/韩文名/序号"),
        ("body", "  Prompt可选，追加自定义关键词"),
        ("body", "  举例: 画图 妮亚"),
        ("body", "  举例: 画图 妮亚 缘分"),
        ("body", "  举例: 画图 9:16 红兰"),
        ("body", "  举例: 画图 梅菲 基础 1girl smile"),
        ("blank", ""),
        ("heading", "【积分系统】"),
        ("body", "  everpic签到 → 每天签到一次，获得10~30积分"),
        ("body", "  everpic积分 → 查看当前积分余额"),
        ("body", "  everpic发积分 @某人 数量（超级管理员）"),
        ("body", "  → 数量1~50，每人每天最多获赠100积分"),
        ("blank", ""),
        ("heading", "【查变体】"),
        ("body", "  everpic查变体 角色名"),
        ("body", "  举例: everpic查变体 妮亚"),
        ("blank", ""),
        ("heading", "【存词功能】（每人最多20条）"),
        ("body", "  everpic存词 [备注] → 回复画图消息存词"),
        ("body", "  everpic查词 [关键词] [@某人] → 查存词"),
        ("body", "  everpic删词 序号 → 删除指定存词"),
        ("body", "  举例: 回复画图消息 + everpic存词 测试"),
        ("body", "  举例: everpic查词 @某人"),
        ("body", "  举例: everpic查词 妮亚 查所有含妮亚的"),
        ("body", "  举例: everpic删词 3"),
        ("blank", ""),
        ("heading", "【队列查询】"),
        ("body", "  everpic队列 → 查看当前画图任务队列"),
        ("blank", ""),
        ("heading", "【画图设置】"),
        ("body", "  everpic设置 → 查看当前画图参数"),
        ("body", "  everpic设置 字段名 值 → 修改参数"),
        ("body", "  everpic重置设置 → 恢复默认"),
        ("body", "  字段: model/clip/steps/cfg/neg"),
        ("blank", ""),
        ("heading", "【管理指令】"),
        ("body", "  everpic拉黑 @某人（群管理员）"),
        ("body", "  everpic解除拉黑 @某人（群管理员）"),
        ("body", "  everpic开启 → 开启本群画图（超级管理员）"),
        ("body", "  everpic关闭 → 关闭本群画图（超级管理员）"),
        ("body", "  everpic安全开启 → 开启NSFW过滤（超级管理员）"),
        ("body", "  everpic安全关闭 → 关闭NSFW过滤（超级管理员）"),
        ("body", "  everpic日志 [数量] → 查看请求日志（超级管理员）"),
        ("blank", ""),
        ("heading", "【帮助】"),
        ("body", "  everpic帮助 → 显示本帮助信息"),
    ]

    pad_x, pad_y = 30, 25
    line_heights = {"title": 40, "heading": 32, "body": 24, "blank": 12}
    total_h = pad_y * 2 + sum(line_heights[t] for t, _ in lines)
    img_w = 580

    img = Image.new("RGB", (img_w, total_h), "#1a1a2e")
    draw = ImageDraw.Draw(img)

    y = pad_y
    for kind, text in lines:
        if kind == "title":
            draw.text((pad_x, y), text, fill="#a78bfa", font=title_font)
        elif kind == "heading":
            draw.text((pad_x, y), text, fill="#c084fc", font=heading_font)
        elif kind == "body":
            draw.text((pad_x, y), text, fill="#d4d4d4", font=body_font)
        y += line_heights[kind]

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

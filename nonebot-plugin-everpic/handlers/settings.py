from nonebot import on_message
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent
from nonebot.rule import Rule

from ..store import get_draw_settings, update_draw_setting, reset_draw_settings

# 可设置的字段及其验证规则
_FIELDS = {
    "model_strength": {"type": float, "min": 0.0, "max": 1.0, "label": "Model Strength"},
    "clip_strength":  {"type": float, "min": 0.0, "max": 1.0, "label": "Clip Strength"},
    "steps":          {"type": int,   "min": 1,   "max": 50,  "label": "Steps"},
    "cfg_scale":      {"type": float, "min": 1.0, "max": 20.0, "label": "CFG Scale"},
    "negative":       {"type": str,   "label": "Negative Prompt"},
}

# 中文别名映射
_ALIASES = {
    "模型强度": "model_strength", "model": "model_strength",
    "clip强度": "clip_strength", "clip": "clip_strength",
    "步数": "steps", "step": "steps",
    "cfg": "cfg_scale",
    "负面提示": "negative", "负面": "negative", "neg": "negative",
}


def _resolve_field(name: str) -> str | None:
    name = name.lower().strip()
    if name in _FIELDS:
        return name
    return _ALIASES.get(name)


# ---- everpic设置 查看 ----
async def _view_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text == "everpic设置"


view_matcher = on_message(rule=Rule(_view_rule), priority=10, block=True)


@view_matcher.handle()
async def handle_view(event: GroupMessageEvent):
    s = get_draw_settings(event.user_id)
    lines = [
        "⚙️ 你的画图设置：",
        f"  Model Strength: {s['model_strength']}",
        f"  Clip Strength: {s['clip_strength']}",
        f"  Steps: {s['steps']}",
        f"  CFG Scale: {s['cfg_scale']}",
        f"  Negative Prompt: {s['negative'] or '(空)'}",
        "",
        "修改: everpic设置 字段名 值",
        "重置: everpic重置设置",
        "字段名: model/clip/steps/cfg/neg",
    ]
    await view_matcher.finish("\n".join(lines))


# ---- everpic设置 字段 值 ----
async def _set_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    text = event.get_plaintext().strip()
    return text.startswith("everpic设置 ")


set_matcher = on_message(rule=Rule(_set_rule), priority=10, block=True)


@set_matcher.handle()
async def handle_set(event: GroupMessageEvent):
    text = event.get_plaintext().strip()
    parts = text.split(maxsplit=2)
    # parts: ["everpic设置", "字段名", "值"]

    if len(parts) < 3:
        await set_matcher.finish("用法: everpic设置 字段名 值\n字段名: model/clip/steps/cfg/neg")

    field_name = _resolve_field(parts[1])
    if not field_name:
        await set_matcher.finish(
            f"未知字段「{parts[1]}」\n可用字段: model, clip, steps, cfg, neg"
        )

    raw_value = parts[2]
    spec = _FIELDS[field_name]

    # negative 是字符串，特殊处理
    if spec["type"] == str:
        if raw_value in ("空", "无", "清空", "clear", "none"):
            raw_value = ""
        new_settings = update_draw_setting(event.user_id, field_name, raw_value)
        await set_matcher.finish(
            f"✅ {spec['label']} 已设置为: {raw_value or '(空)'}"
        )

    # 数值类型
    try:
        value = spec["type"](raw_value)
    except ValueError:
        await set_matcher.finish(f"❌ 值格式错误，{spec['label']} 需要 {spec['type'].__name__} 类型")

    if value < spec["min"] or value > spec["max"]:
        await set_matcher.finish(
            f"❌ {spec['label']} 范围: {spec['min']} ~ {spec['max']}"
        )

    new_settings = update_draw_setting(event.user_id, field_name, value)
    await set_matcher.finish(f"✅ {spec['label']} 已设置为: {value}")


# ---- everpic重置设置 ----
async def _reset_rule(event: MessageEvent) -> bool:
    if not isinstance(event, GroupMessageEvent):
        return False
    return event.get_plaintext().strip() == "everpic重置设置"


reset_matcher = on_message(rule=Rule(_reset_rule), priority=10, block=True)


@reset_matcher.handle()
async def handle_reset(event: GroupMessageEvent):
    reset_draw_settings(event.user_id)
    await reset_matcher.finish("✅ 画图设置已重置为默认值")

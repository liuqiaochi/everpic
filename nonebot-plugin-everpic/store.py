"""JSON 持久化存储：黑名单、超管、群设置、积分"""
import json
import random
from datetime import date

from .config import (
    BLACKLIST_FILE, SUPER_ADMIN_FILE, GROUP_SETTINGS_FILE, POINTS_FILE,
    INITIAL_POINTS, SIGN_MIN, SIGN_MAX, DAILY_RECEIVE_LIMIT,
)


def _load_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- 黑名单 ----

def load_blacklist() -> list[str]:
    return _load_json(BLACKLIST_FILE, [])


def save_blacklist(bl: list[str]):
    _save_json(BLACKLIST_FILE, bl)


def is_blacklisted(user_id: int) -> bool:
    return str(user_id) in load_blacklist()


# ---- 超级管理员 ----

def load_super_admins() -> list[str]:
    return _load_json(SUPER_ADMIN_FILE, [])


def is_super_admin(user_id: int) -> bool:
    return str(user_id) in load_super_admins()


# ---- 群设置 ----

def _load_group_settings() -> dict:
    return _load_json(GROUP_SETTINGS_FILE, {"enabled_groups": [], "nsfw_filter": {}})


def _save_group_settings(data: dict):
    _save_json(GROUP_SETTINGS_FILE, data)


def is_group_enabled(group_id: int) -> bool:
    return str(group_id) in _load_group_settings()["enabled_groups"]


def set_group_enabled(group_id: int, enabled: bool):
    data = _load_group_settings()
    gid = str(group_id)
    if enabled and gid not in data["enabled_groups"]:
        data["enabled_groups"].append(gid)
    elif not enabled and gid in data["enabled_groups"]:
        data["enabled_groups"].remove(gid)
    _save_group_settings(data)


def is_nsfw_filter_on(group_id: int) -> bool:
    return _load_group_settings().get("nsfw_filter", {}).get(str(group_id), True)


def set_nsfw_filter(group_id: int, on: bool):
    data = _load_group_settings()
    data.setdefault("nsfw_filter", {})[str(group_id)] = on
    _save_group_settings(data)


# ---- 积分 ----

def _load_points() -> dict:
    return _load_json(POINTS_FILE, {"users": {}})


def _save_points(data: dict):
    _save_json(POINTS_FILE, data)


def _ensure_user(data: dict, uid: str):
    if uid not in data["users"]:
        data["users"][uid] = {"points": INITIAL_POINTS, "last_sign": "", "received_today": 0, "received_date": ""}


def get_user_points(user_id: int) -> int:
    data = _load_points()
    uid = str(user_id)
    _ensure_user(data, uid)
    _save_points(data)
    return data["users"][uid]["points"]


def deduct_points(user_id: int, cost: int) -> int:
    data = _load_points()
    uid = str(user_id)
    _ensure_user(data, uid)
    data["users"][uid]["points"] -= cost
    _save_points(data)
    return data["users"][uid]["points"]


def sign_in(user_id: int) -> tuple[bool, int, int]:
    """返回 (是否成功, 获得积分, 当前总积分)"""
    data = _load_points()
    uid = str(user_id)
    today = date.today().isoformat()
    _ensure_user(data, uid)

    if data["users"][uid]["last_sign"] == today:
        return False, 0, data["users"][uid]["points"]

    gained = random.randint(SIGN_MIN, SIGN_MAX)
    data["users"][uid]["points"] += gained
    data["users"][uid]["last_sign"] = today
    _save_points(data)
    return True, gained, data["users"][uid]["points"]


def gift_points(target_id: int, amount: int) -> tuple[bool, str, int]:
    """管理员给用户发积分，返回 (是否成功, 原因, 当前总积分)"""
    data = _load_points()
    uid = str(target_id)
    today = date.today().isoformat()
    _ensure_user(data, uid)

    user = data["users"][uid]

    # 重置每日计数（如果日期变了）
    if user.get("received_date") != today:
        user["received_today"] = 0
        user["received_date"] = today

    already = user.get("received_today", 0)
    if already + amount > DAILY_RECEIVE_LIMIT:
        remaining = DAILY_RECEIVE_LIMIT - already
        return False, f"该用户今日已获赠 {already} 积分，还可获赠 {remaining} 积分", user["points"]

    user["points"] += amount
    user["received_today"] = already + amount
    _save_points(data)
    return True, "", user["points"]


# ---- 用户画图设置 ----
from .config import (
    USER_SETTINGS_FILE,
    DEFAULT_MODEL_STRENGTH, DEFAULT_CLIP_STRENGTH,
    DEFAULT_STEPS, DEFAULT_CFG_SCALE, DEFAULT_NEGATIVE,
)

_DEFAULT_DRAW_SETTINGS = {
    "model_strength": DEFAULT_MODEL_STRENGTH,
    "clip_strength": DEFAULT_CLIP_STRENGTH,
    "steps": DEFAULT_STEPS,
    "cfg_scale": DEFAULT_CFG_SCALE,
    "negative": DEFAULT_NEGATIVE,
}


def _load_user_settings() -> dict:
    return _load_json(USER_SETTINGS_FILE, {})


def _save_user_settings(data: dict):
    _save_json(USER_SETTINGS_FILE, data)


def get_draw_settings(user_id: int) -> dict:
    """获取用户画图设置，缺失字段用默认值补全"""
    data = _load_user_settings()
    uid = str(user_id)
    user_cfg = data.get(uid, {})
    return {**_DEFAULT_DRAW_SETTINGS, **user_cfg}


def update_draw_setting(user_id: int, key: str, value) -> dict:
    """更新单个设置项，返回更新后的完整设置"""
    data = _load_user_settings()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {}
    data[uid][key] = value
    _save_user_settings(data)
    return {**_DEFAULT_DRAW_SETTINGS, **data[uid]}


def reset_draw_settings(user_id: int):
    """重置用户设置为默认"""
    data = _load_user_settings()
    data.pop(str(user_id), None)
    _save_user_settings(data)

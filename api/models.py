"""
模型注册表 REST API

用户在"模型设置"中添加 / 切换符合 OpenAI 协议的模型（base_url + api_key + 模型名）。
API key 永不明文返回（GET 一律掩码）；PUT 时 api_key 留空 = 保留原 key。
切换 active 模型后：重读配置 → 重建模型单例 → 清空 Agent 缓存，
新会话 / 重连即使用新模型（已打开的对话主模型不变，刷新后生效）。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tool.config_handler import Model_Config, save_model_config
from tool.logger_handler import logger

router = APIRouter()


def _mask(k: str) -> str:
    """掩码 API key：短 key 显示 '****'，长 key 保留首 2 尾 4"""
    k = (k or "").strip()
    if not k:
        return ""
    if len(k) <= 8:
        return "****"
    return f"{k[:2]}****{k[-4:]}"


def _public(m: dict) -> dict:
    return {**m, "api_key": _mask(m.get("api_key", ""))}


def _find_model(name: str) -> dict | None:
    for m in Model_Config.get("models", []):
        if m.get("name") == name:
            return m
    return None


def _apply_change_or_400() -> dict:
    """调用 apply_model_change()；失败（如 base_url 不合法）返回 HTTP 400"""
    from factory.model_generator import apply_model_change
    try:
        return apply_model_change()
    except Exception as e:
        logger.exception(f"[models] 模型切换失败")
        raise HTTPException(status_code=400, detail=f"模型切换失败: {e}")


class ModelCreate(BaseModel):
    name: str
    label: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str


class ModelUpdate(BaseModel):
    label: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class SetActiveRequest(BaseModel):
    name: str


@router.get("/models")
async def api_list_models():
    """列出所有已配置模型，api_key 一律掩码返回"""
    return {
        "active_model": Model_Config.get("active_model"),
        "models": [_public(m) for m in Model_Config.get("models", [])],
    }


@router.post("/models")
async def api_add_model(req: ModelCreate):
    """添加模型。若当前无 active 模型，添加后自动设为 active 并生效"""
    name = (req.name or "").strip()
    model = (req.model or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="模型标识 (name) 不能为空")
    if not model:
        raise HTTPException(status_code=400, detail="模型名 (model) 不能为空")
    if _find_model(name):
        raise HTTPException(status_code=400, detail=f"模型 '{name}' 已存在")

    models = Model_Config.setdefault("models", [])
    models.append({
        "name": name,
        "label": (req.label or "").strip() or name,
        "base_url": (req.base_url or "").strip(),
        "api_key": (req.api_key or "").strip(),
        "model": model,
    })
    save_model_config()

    # 无 active 或首个模型 → 自动设为 active 并立即生效
    changed = not Model_Config.get("active_model") or len(models) == 1
    if changed:
        Model_Config["active_model"] = name
        save_model_config()
        _apply_change_or_400()

    logger.info(f"[models] 已添加模型: {name}")
    return {"created": name, "active": Model_Config.get("active_model")}


# 注意：/models/active 必须声明在 /models/{name} 之前，避免被 {name} 吞掉
@router.put("/models/active")
async def api_set_active(req: SetActiveRequest):
    """切换当前使用的模型，立即生效（清空 Agent 缓存）"""
    name = (req.name or "").strip()
    if not _find_model(name):
        raise HTTPException(status_code=404, detail=f"模型 '{name}' 不存在")
    Model_Config["active_model"] = name
    save_model_config()
    info = _apply_change_or_400()
    logger.info(f"[models] 已切换 active 模型: {name}")
    return {"active": name, "model_info": info}


@router.put("/models/{name}")
async def api_update_model(name: str, req: ModelUpdate):
    """更新模型配置。api_key 留空/缺省 → 保留原 key；更新的是 active 模型则立即生效"""
    target = _find_model(name)
    if not target:
        raise HTTPException(status_code=404, detail=f"模型 '{name}' 不存在")

    if req.label is not None:
        target["label"] = (req.label or "").strip() or name
    if req.base_url is not None:
        target["base_url"] = (req.base_url or "").strip()
    if req.model is not None:
        m = (req.model or "").strip()
        if not m:
            raise HTTPException(status_code=400, detail="模型名 (model) 不能为空")
        target["model"] = m
    if req.api_key:
        target["api_key"] = (req.api_key or "").strip()
    # api_key 为空串 → 保留原 key（不清空）

    save_model_config()
    if Model_Config.get("active_model") == name:
        _apply_change_or_400()
    logger.info(f"[models] 已更新模型: {name}")
    return {"updated": name}


@router.delete("/models/{name}")
async def api_delete_model(name: str):
    """删除模型。若删的是 active 模型，回退到列表中第一个模型"""
    models = Model_Config.get("models", [])
    if not _find_model(name):
        raise HTTPException(status_code=404, detail=f"模型 '{name}' 不存在")

    models[:] = [m for m in models if m.get("name") != name]
    was_active = Model_Config.get("active_model") == name
    if was_active:
        if models:
            Model_Config["active_model"] = models[0]["name"]
        else:
            Model_Config["active_model"] = ""
    save_model_config()

    if was_active:
        _apply_change_or_400()
    logger.info(f"[models] 已删除模型: {name}")
    return {"deleted": name, "active": Model_Config.get("active_model")}

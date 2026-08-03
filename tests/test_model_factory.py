"""
模型工厂测试
===========
验证 create_chatmodel / create_ragmodel 按 Model_Config 的 active 模型构建：
base_url 非空 → ChatOpenAI（任意 OpenAI 协议端点）；
base_url 为空 → ChatDeepSeek（内置 DeepSeek + 环境变量）。
"""
import pytest

from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

import factory.model_generator as mg
from api.models import _mask


@pytest.fixture
def custom_model_config(monkeypatch):
    """把 Model_Config 指向一个含自定义 OpenAI 协议模型的注册表"""
    cfg = {
        "active_model": "custom",
        "models": [
            {
                "name": "custom",
                "label": "Custom",
                "base_url": "http://127.0.0.1:9000/v1",
                "api_key": "sk-test-1234",
                "model": "gpt-4o-mini",
            },
            {
                "name": "default",
                "label": "DeepSeek",
                "base_url": "",
                "api_key": "",
                "model": "deepseek-v4-pro",
            },
        ],
    }
    monkeypatch.setattr(mg, "Model_Config", cfg)
    return cfg


def test_create_chatmodel_uses_custom_base_url(custom_model_config):
    cm = mg.create_chatmodel()
    assert isinstance(cm, ChatOpenAI)
    assert cm.model_name == "gpt-4o-mini"
    # base_url 是 openai_api_base 的 alias（必须用 base_url= 传参才会生效）
    assert cm.openai_api_base == "http://127.0.0.1:9000/v1"
    assert cm.openai_api_key.get_secret_value() == "sk-test-1234"


def test_create_chatmodel_uses_deepseek_when_no_base_url(monkeypatch):
    cfg = {
        "active_model": "default",
        "models": [
            {
                "name": "default",
                "label": "DeepSeek",
                "base_url": "",
                "api_key": "",
                "model": "deepseek-v4-pro",
            }
        ],
    }
    monkeypatch.setattr(mg, "Model_Config", cfg)
    cm = mg.create_chatmodel()
    assert isinstance(cm, ChatDeepSeek)
    assert cm.model_name == "deepseek-v4-pro"


def test_create_chatmodel_model_name_override(custom_model_config):
    cm = mg.create_chatmodel(model_name="deepseek-chat")
    assert cm.model_name == "deepseek-chat"


def test_create_ragmodel_uses_active_model(custom_model_config):
    rm = mg.create_ragmodel()
    assert isinstance(rm, ChatOpenAI)
    assert rm.model_name == "gpt-4o-mini"
    assert rm.openai_api_base == "http://127.0.0.1:9000/v1"


def test_active_missing_falls_back_to_first(custom_model_config):
    custom_model_config["active_model"] = "not-exist"
    cm = mg.create_chatmodel()
    assert cm.model_name == "gpt-4o-mini"


def test_mask():
    assert _mask("") == ""
    assert _mask("abc12345") == "****"           # 短 key
    assert _mask("sk-abcdefghijkl1234") == "sk****1234"   # 长 key 保留首2尾4

"""Dashboard utility functions."""


def get_config_value(config, key, default=None):
    """Get configuration value safely.

    Args:
        config: Settings object
        key: Dot-separated key (e.g., "llm.model")
        default: Default value if not found

    Returns:
        Configuration value or default
    """
    return config.get(key, default)


def get_milvus_config(config):
    """Get Milvus configuration as dict.

    Args:
        config: Settings object

    Returns:
        Milvus config dictionary
    """
    return {
        "uri": config.get("milvus.uri", "milvus.db"),
        "collection_name": config.get("milvus.collection_name", "rag_knowledge_hub"),
        "dense_dim": config.get("milvus.dense_dim", 2048)
    }


def get_llm_config(config):
    """Get LLM configuration as dict.

    Args:
        config: Settings object

    Returns:
        LLM config dictionary
    """
    api_key = config.get("llm.api_key", "")
    return {
        "provider": config.get("llm.provider", "dashscope"),
        "model": config.get("llm.model", "qwen-max"),
        "base_url": config.get("llm.base_url", ""),
        "api_key": "***" + api_key[-4:] if api_key else "未配置",
        "temperature": config.get("llm.temperature", 0.7),
        "max_tokens": config.get("llm.max_tokens", 2000)
    }


def get_embedding_config(config):
    """Get Embedding configuration as dict.

    Args:
        config: Settings object

    Returns:
        Embedding config dictionary
    """
    api_key = config.get("embedding.api_key", "")
    return {
        "provider": config.get("embedding.provider", "dashscope"),
        "model": config.get("embedding.model", "text-embedding-v4"),
        "base_url": config.get("embedding.base_url", ""),
        "api_key": "***" + api_key[-4:] if api_key else "未配置",
        "dimension": config.get("embedding.dimension", 2048)
    }

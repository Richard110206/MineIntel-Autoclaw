"""MineIntel 技能组共享基础设施层。

只放置跨 Skill 复用的底层能力：基础设施配置加载、AutoGLM 网页搜索与网页阅读客户端。
领域检索编排（论文、GitHub、导师、经验）保留在各 Skill 自己的 scripts 目录中，
通过 ``from mineintel_common import ...`` 复用本层。
"""

from .config import CONFIG_PATH, PACKAGE_DIR, display_path, load_infrastructure

__all__ = ["CONFIG_PATH", "PACKAGE_DIR", "display_path", "load_infrastructure"]

# Sandbox Testing Suite

沙箱环境测试套件 - 8个核心测试（Matplotlib, Mermaid, MCP工具, 数据科学, OpenCV, python-pptx, Ripgrep, 集成测试）

## 🚀 快速开始

测试使用**本机模式**（无需 host 容器），从 `mcp.json` 动态过滤 `desktop_commander` 配置。

```bash
# 1. 构建沙箱镜像（首次）
docker-compose build build-sandbox

# 2. 运行测试（从项目根目录）
./deeppresenter/test/run_script.sh

# 或直接使用 pytest
cd deeppresenter/test && pytest test_sandbox.py -v --output-dir=permanent && cd ../..
```

测试结果保存在 `deeppresenter/test/test_outputs/` 目录。

---

**生产模式**（Web 应用）：`docker-compose up -d deeppresenter-host` 启动完整服务（包含 deeppresenter + pptagent + sandbox，提供 Web UI）

**测试 vs 生产**：测试只加载 1 个服务（sandbox），生产加载 3 个服务；配置源统一为 `mcp.json`，测试时动态过滤

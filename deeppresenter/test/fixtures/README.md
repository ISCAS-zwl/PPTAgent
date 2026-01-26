# Sandbox Test Fixtures

这个目录包含用于测试沙箱环境的测试数据文件。

## 文件说明

### test_matplotlib.py
完整的matplotlib测试脚本，包含三种测试场景：
- **基础图表**：简单的折线图
- **中文支持**：包含中文标题、标签的柱状图
- **复杂图表**：多子图（折线图、柱状图、散点图、饼图）

可以直接在沙箱中运行：
```bash
python test_matplotlib.py
```

输出文件：
- `basic_plot.png` - 基础折线图
- `chinese_plot.png` - 中文柱状图
- `complex_plot.png` - 复杂多子图

### test_mermaid.mmd
Mermaid流程图测试文件，包含中文节点名称和样式定义。

使用mmdc命令生成图片：
```bash
mmdc -i test_mermaid.mmd -o output.png
```

## 使用方式

这些文件会被pytest测试用例使用，通过MCP/AgentEnv接口调用沙箱环境中的工具执行。

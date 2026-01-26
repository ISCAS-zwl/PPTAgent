"""
Matplotlib test script with Chinese support.
This script tests matplotlib's ability to render Chinese text and generate charts.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Configure Chinese fonts
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_basic_plot():
    """Create a basic line plot."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]

    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='blue', linewidth=2)
    plt.title('Basic Line Plot')
    plt.xlabel('X Axis')
    plt.ylabel('Y Axis')
    plt.grid(True, alpha=0.3)
    plt.savefig('basic_plot.png', dpi=100, bbox_inches='tight')
    plt.close()
    print('✓ basic_plot.png generated')


def create_chinese_plot():
    """Create a bar chart with Chinese labels."""
    categories = ['一月', '二月', '三月', '四月', '五月']
    values = [65, 78, 82, 90, 88]

    plt.figure(figsize=(10, 6))
    plt.bar(categories, values, color='steelblue', alpha=0.8)
    plt.title('销售数据统计 - 中文测试', fontsize=16, fontweight='bold')
    plt.xlabel('月份', fontsize=12)
    plt.ylabel('销售额（万元）', fontsize=12)
    plt.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, v in enumerate(values):
        plt.text(i, v + 1, str(v), ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('chinese_plot.png', dpi=100, bbox_inches='tight')
    plt.close()
    print('✓ chinese_plot.png generated')


def create_complex_plot():
    """Create complex plot with multiple subplots."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Subplot 1: Line plot
    x = np.linspace(0, 10, 100)
    ax1.plot(x, np.sin(x), label='sin(x)', color='blue')
    ax1.plot(x, np.cos(x), label='cos(x)', color='red')
    ax1.set_title('三角函数图像', fontsize=12, fontweight='bold')
    ax1.set_xlabel('x轴')
    ax1.set_ylabel('y轴')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Subplot 2: Bar chart
    categories = ['产品A', '产品B', '产品C', '产品D']
    values = [23, 45, 56, 78]
    ax2.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
    ax2.set_title('产品销量对比', fontsize=12, fontweight='bold')
    ax2.set_ylabel('销量')

    # Subplot 3: Scatter plot
    x_scatter = np.random.randn(50)
    y_scatter = np.random.randn(50)
    colors = np.random.rand(50)
    ax3.scatter(x_scatter, y_scatter, c=colors, s=100, alpha=0.6, cmap='viridis')
    ax3.set_title('散点图示例', fontsize=12, fontweight='bold')
    ax3.set_xlabel('特征1')
    ax3.set_ylabel('特征2')

    # Subplot 4: Pie chart
    sizes = [30, 25, 20, 25]
    labels = ['类别一', '类别二', '类别三', '类别四']
    colors_pie = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']
    ax4.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
    ax4.set_title('数据分布饼图', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('complex_plot.png', dpi=100, bbox_inches='tight')
    plt.close()
    print('✓ complex_plot.png generated')


if __name__ == '__main__':
    print('Starting matplotlib tests...')
    create_basic_plot()
    create_chinese_plot()
    create_complex_plot()
    print('All matplotlib tests completed successfully!')

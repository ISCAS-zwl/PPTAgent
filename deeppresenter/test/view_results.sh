#!/bin/bash
# 测试结果查看辅助脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/test_outputs"
TMP_DIR="/tmp/pytest-of-$USER"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 显示帮助
show_help() {
    cat << EOF
测试结果查看工具

用法: $0 [选项]

选项:
    -h, --help          显示帮助信息
    -l, --list          列出所有测试结果
    -p, --permanent     查看永久保存的测试结果
    -t, --temp          查看临时目录的测试结果
    -c, --clean         清理永久保存的测试结果
    -o, --open [TEST]   打开指定测试的输出目录

示例:
    $0 -l                          # 列出所有结果
    $0 -p                          # 查看永久保存的结果
    $0 -t                          # 查看临时结果
    $0 -o test_matplotlib_chinese  # 打开特定测试目录
    $0 -c                          # 清理永久结果

EOF
}

# 列出所有测试结果
list_results() {
    print_header "测试结果概览"

    # 永久保存的结果
    echo ""
    print_info "永久保存的测试结果 ($OUTPUT_DIR):"
    if [ -d "$OUTPUT_DIR" ] && [ "$(ls -A $OUTPUT_DIR 2>/dev/null)" ]; then
        for dir in "$OUTPUT_DIR"/*; do
            if [ -d "$dir" ]; then
                test_name=$(basename "$dir")
                file_count=$(find "$dir" -type f | wc -l)
                size=$(du -sh "$dir" | cut -f1)
                print_success "$test_name - $file_count 个文件 ($size)"

                # 列出图片文件
                images=$(find "$dir" -name "*.png" -o -name "*.jpg" -o -name "*.svg" 2>/dev/null)
                if [ -n "$images" ]; then
                    echo "$images" | while read img; do
                        echo "    📊 $(basename "$img")"
                    done
                fi
            fi
        done
    else
        print_info "  (空)"
    fi

    # 临时结果
    echo ""
    print_info "临时测试结果 ($TMP_DIR):"
    if [ -d "$TMP_DIR" ]; then
        latest=$(ls -td "$TMP_DIR"/pytest-* 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            age=$(stat -c %y "$latest" | cut -d' ' -f1,2 | cut -d'.' -f1)
            size=$(du -sh "$latest" | cut -f1)
            print_success "最新测试: $(basename "$latest")"
            echo "    时间: $age"
            echo "    大小: $size"
            echo "    路径: $latest"
        else
            print_info "  (无最近测试)"
        fi
    else
        print_info "  (目录不存在)"
    fi
}

# 查看永久结果
view_permanent() {
    print_header "永久保存的测试结果"

    if [ ! -d "$OUTPUT_DIR" ] || [ ! "$(ls -A $OUTPUT_DIR 2>/dev/null)" ]; then
        print_info "没有永久保存的测试结果"
        print_info "运行测试时使用: pytest --output-dir=permanent"
        return
    fi

    echo ""
    for dir in "$OUTPUT_DIR"/*; do
        if [ -d "$dir" ]; then
            test_name=$(basename "$dir")
            echo -e "${GREEN}━━━ $test_name ━━━${NC}"
            tree -L 2 "$dir" 2>/dev/null || ls -lh "$dir"
            echo ""
        fi
    done
}

# 查看临时结果
view_temp() {
    print_header "临时测试结果"

    if [ ! -d "$TMP_DIR" ]; then
        print_error "临时目录不存在: $TMP_DIR"
        return
    fi

    latest=$(ls -td "$TMP_DIR"/pytest-* 2>/dev/null | head -1)
    if [ -z "$latest" ]; then
        print_info "没有找到临时测试结果"
        return
    fi

    echo ""
    print_success "最新测试目录: $latest"
    echo ""
    tree -L 3 "$latest" 2>/dev/null || find "$latest" -type f -exec ls -lh {} \;
}

# 清理永久结果
clean_permanent() {
    print_header "清理永久测试结果"

    if [ ! -d "$OUTPUT_DIR" ] || [ ! "$(ls -A $OUTPUT_DIR 2>/dev/null)" ]; then
        print_info "没有需要清理的测试结果"
        return
    fi

    echo ""
    print_info "将删除以下目录:"
    ls -ld "$OUTPUT_DIR"/*/ 2>/dev/null || true

    echo ""
    read -p "确认删除? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$OUTPUT_DIR"/*
        print_success "清理完成"
    else
        print_info "取消清理"
    fi
}

# 打开测试目录
open_test() {
    local test_name=$1

    if [ -z "$test_name" ]; then
        print_error "请指定测试名称"
        echo "可用的测试:"
        ls -1 "$OUTPUT_DIR" 2>/dev/null || print_info "  (无)"
        return 1
    fi

    local test_dir="$OUTPUT_DIR/$test_name"
    if [ ! -d "$test_dir" ]; then
        print_error "测试目录不存在: $test_name"
        echo "可用的测试:"
        ls -1 "$OUTPUT_DIR" 2>/dev/null || print_info "  (无)"
        return 1
    fi

    print_success "打开目录: $test_dir"

    # 尝试在文件管理器中打开
    if command -v xdg-open &> /dev/null; then
        xdg-open "$test_dir"
    elif command -v nautilus &> /dev/null; then
        nautilus "$test_dir"
    elif command -v dolphin &> /dev/null; then
        dolphin "$test_dir"
    else
        echo "目录内容:"
        ls -lh "$test_dir"
    fi
}

# 主逻辑
if [ $# -eq 0 ]; then
    list_results
    exit 0
fi

case "$1" in
    -h|--help)
        show_help
        ;;
    -l|--list)
        list_results
        ;;
    -p|--permanent)
        view_permanent
        ;;
    -t|--temp)
        view_temp
        ;;
    -c|--clean)
        clean_permanent
        ;;
    -o|--open)
        open_test "$2"
        ;;
    *)
        print_error "未知选项: $1"
        echo "使用 -h 查看帮助"
        exit 1
        ;;
esac

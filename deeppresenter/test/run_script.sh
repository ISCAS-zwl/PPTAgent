#!/bin/bash
# Run merged sandbox tests - only the most challenging test for each tool

echo "========================================="
echo "🧪 Running Merged Sandbox Tests"
echo "   (Most challenging test per tool)"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure we're in the project root directory
if [ ! -f "pytest.ini" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Run merged tests
echo -e "${BLUE}📋 Running merged test suite...${NC}"
echo ""

# Change to test directory to ensure conftest.py is loaded
cd deeppresenter/test && pytest test_sandbox.py \
       -v --output-dir=permanent \
       -s \
       --tb=short

TEST_EXIT_CODE=$?

# Return to project root
cd ../..

echo ""
echo "========================================="
echo "📊 Test Results Summary"
echo "========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

echo ""
echo "Test Coverage:"
echo "  ✓ Matplotlib: Complex multi-subplot with Chinese"
echo "  ✓ Mermaid: Sequence diagram with Chinese"
echo "  ✓ MCP Tools: Complete workflow (7 tools)"
echo "  ✓ Data Science: Full pipeline (numpy+pandas+matplotlib+seaborn)"
echo "  ✓ Image Processing: OpenCV advanced (filters+shapes)"
echo "  ✓ Document Generation: python-pptx comprehensive"
echo "  ✓ System Tools: Ripgrep complex search"
echo "  ✓ Integration: Environment capabilities check"
echo ""

# Count test outputs
OUTPUT_DIR="deeppresenter/test/test_outputs"
if [ -d "$OUTPUT_DIR" ]; then
    echo "📂 Test outputs saved in: $OUTPUT_DIR"
    NUM_FILES=$(find "$OUTPUT_DIR" -type f | wc -l)
    echo "   - Generated files: $NUM_FILES"
    echo ""

    echo "📸 Sample generated files:"
    find "$OUTPUT_DIR" -name "*.png" -o -name "*.csv" -o -name "*.pptx" -o -name "*.txt" | head -15 | while read file; do
        echo "   - $file"
    done
fi

echo ""
echo "========================================="
echo ""
echo "💡 To view detailed results:"
echo "   ls $OUTPUT_DIR"
echo "   # Or: find $OUTPUT_DIR -name '*.png'"
echo ""

exit $TEST_EXIT_CODE

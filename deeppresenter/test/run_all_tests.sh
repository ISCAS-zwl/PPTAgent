#!/bin/bash
# Run all sandbox tools tests and save results

echo "========================================="
echo "🧪 Running All Sandbox Tools Tests"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Run tests
echo -e "${BLUE}📋 Running test suite...${NC}"
echo ""

pytest deeppresenter/test/test_sandbox.py \
       deeppresenter/test/test_sandbox_tools_complete.py \
       deeppresenter/test/test_sandbox_advanced_tools.py \
       -v --output-dir=permanent

TEST_EXIT_CODE=$?

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
echo "📂 Test outputs saved in:"
echo "   deeppresenter/test/test_outputs/"
echo ""

# Count test outputs
OUTPUT_DIR="deeppresenter/test/test_outputs"
if [ -d "$OUTPUT_DIR" ]; then
    NUM_DIRS=$(find "$OUTPUT_DIR" -maxdepth 1 -type d | wc -l)
    NUM_FILES=$(find "$OUTPUT_DIR" -type f | wc -l)
    echo "   - Test directories: $((NUM_DIRS - 1))"
    echo "   - Generated files: $NUM_FILES"
    echo ""

    echo "🔍 To view results:"
    echo "   ls -lh $OUTPUT_DIR"
    echo ""

    echo "📸 Sample generated files:"
    find "$OUTPUT_DIR" -name "*.png" -o -name "*.csv" -o -name "*.pptx" -o -name "*.html" | head -10 | while read file; do
        echo "   - $file"
    done
fi

echo ""
echo "========================================="

exit $TEST_EXIT_CODE

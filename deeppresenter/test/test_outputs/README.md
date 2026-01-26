# Test Outputs Directory

This directory stores **permanent** test results when running tests with `--output-dir=permanent` option.

## Structure

When tests run in permanent mode, each test creates its own subdirectory:

```
test_outputs/
├── test_matplotlib_basic/
│   ├── test_basic.py
│   └── basic_plot.png
├── test_matplotlib_chinese/
│   ├── test_chinese.py
│   └── chinese_plot.png
├── test_mermaid_chinese/
│   ├── chinese.mmd
│   └── chinese_diagram.png
└── ...
```

## Usage

### Temporary outputs (default, auto-cleanup)
```bash
pytest deeppresenter/test/test_sandbox.py
```
Results saved to: `/tmp/pytest-of-<user>/pytest-<N>/`

### Permanent outputs (keep all results)
```bash
pytest deeppresenter/test/test_sandbox.py --output-dir=permanent
```
Results saved to: `deeppresenter/test/test_outputs/`

## Cleanup

To clean all test outputs:
```bash
rm -rf deeppresenter/test/test_outputs/*
```

## Note

This directory is git-ignored by default. Test outputs are considered temporary artifacts.

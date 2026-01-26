"""
Sandbox Environment Testing

This test suite validates the sandbox environment's functionality, specifically:
1. Matplotlib chart generation (basic, Chinese text support, complex plots)
2. Mermaid diagram generation using mmdc (basic, Chinese text support)
3. Integration with MCP/AgentEnv interface

All tests use the desktop_commander MCP server running in Docker sandbox.
"""

import json
from pathlib import Path

import pytest
from PIL import Image


class TestMatplotlib:
    """Test matplotlib functionality in sandbox environment."""

    @pytest.mark.asyncio
    async def test_matplotlib_basic(
        self, agent_env, workspace, matplotlib_basic_script, tool_call_helper
    ):
        """Test basic matplotlib plot generation."""
        # Write the test script to workspace
        script_path = workspace / "test_basic.py"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(script_path), "content": matplotlib_basic_script},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write script: {write_result.text}"

        # Execute the script
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {script_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"Script execution failed: {exec_result.text}"
        assert "SUCCESS" in exec_result.text, f"Script did not report success: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "basic_plot.png" in list_result.text, "Output file not found in workspace"

        # Read and validate the image
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "basic_plot.png")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert not read_result.is_error, "Failed to read generated image"

        # Verify image dimensions by checking file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert not list_result.is_error, "Failed to list directory"
        assert "basic_plot.png" in list_result.text, "Output file not found"

    @pytest.mark.asyncio
    async def test_matplotlib_chinese(
        self, agent_env, workspace, matplotlib_chinese_script, tool_call_helper
    ):
        """Test matplotlib with Chinese text rendering."""
        # Write the test script
        script_path = workspace / "test_chinese.py"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(script_path), "content": matplotlib_chinese_script},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write script: {write_result.text}"

        # Execute the script
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {script_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"Script execution failed: {exec_result.text}"
        assert "SUCCESS" in exec_result.text, f"Script did not report success: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "chinese_plot.png" in list_result.text, "Chinese plot not found"

    @pytest.mark.asyncio
    async def test_matplotlib_complex(
        self, agent_env, workspace, matplotlib_complex_script, tool_call_helper
    ):
        """Test complex matplotlib plot with multiple subplots and Chinese text."""
        # Write the test script
        script_path = workspace / "test_complex.py"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(script_path), "content": matplotlib_complex_script},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write script: {write_result.text}"

        # Execute the script
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {script_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"Script execution failed: {exec_result.text}"
        assert "SUCCESS" in exec_result.text, f"Script did not report success: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "complex_plot.png" in list_result.text, "Complex plot not found"

    @pytest.mark.asyncio
    async def test_matplotlib_from_fixture_file(
        self, agent_env, workspace, fixtures_dir, tool_call_helper
    ):
        """Test matplotlib using the fixture script file."""
        fixture_script = fixtures_dir / "test_matplotlib.py"
        assert fixture_script.exists(), f"Fixture script not found: {fixture_script}"

        # Read the fixture script
        with open(fixture_script, encoding="utf-8") as f:
            script_content = f.read()

        # Write to workspace
        script_path = workspace / "test_matplotlib.py"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(script_path), "content": script_content},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write script: {write_result.text}"

        # Execute the script
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {script_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"Script execution failed: {exec_result.text}"

        # Check all three outputs were generated
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "basic_plot.png" in list_result.text
        assert "chinese_plot.png" in list_result.text
        assert "complex_plot.png" in list_result.text


class TestMermaid:
    """Test mermaid (mmdc) functionality in sandbox environment."""

    @pytest.mark.asyncio
    async def test_mermaid_basic(
        self, agent_env, workspace, mermaid_basic_diagram, tool_call_helper
    ):
        """Test basic mermaid flowchart generation."""
        # Write the mermaid diagram
        diagram_path = workspace / "basic.mmd"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(diagram_path), "content": mermaid_basic_diagram},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write diagram: {write_result.text}"

        # Create Puppeteer config to allow running Chromium as root
        puppeteer_config_path = workspace / ".puppeteerrc.json"
        puppeteer_config = '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
        config_call = tool_call_helper(
            "write_file",
            {"path": str(puppeteer_config_path), "content": puppeteer_config},
        )
        config_result = await agent_env.tool_execute(config_call)
        assert not config_result.is_error, f"Failed to write Puppeteer config: {config_result.text}"

        # Generate PNG using mmdc with Puppeteer config
        output_path = workspace / "basic_diagram.png"
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"mmdc -i {diagram_path} -o {output_path} -p {puppeteer_config_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"mmdc execution failed: {exec_result.text}"
        assert "Error:" not in exec_result.text, f"mmdc reported error: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "basic_diagram.png" in list_result.text, "Diagram PNG not found"

    @pytest.mark.asyncio
    async def test_mermaid_chinese(
        self, agent_env, workspace, mermaid_chinese_diagram, tool_call_helper
    ):
        """Test mermaid diagram with Chinese text."""
        # Write the Chinese diagram
        diagram_path = workspace / "chinese.mmd"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(diagram_path), "content": mermaid_chinese_diagram},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write diagram: {write_result.text}"

        # Create Puppeteer config to allow running Chromium as root
        puppeteer_config_path = workspace / ".puppeteerrc.json"
        puppeteer_config = '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
        config_call = tool_call_helper(
            "write_file",
            {"path": str(puppeteer_config_path), "content": puppeteer_config},
        )
        config_result = await agent_env.tool_execute(config_call)
        assert not config_result.is_error, f"Failed to write Puppeteer config: {config_result.text}"

        # Generate PNG using mmdc with Puppeteer config
        output_path = workspace / "chinese_diagram.png"
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"mmdc -i {diagram_path} -o {output_path} -p {puppeteer_config_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"mmdc execution failed: {exec_result.text}"
        assert "Error:" not in exec_result.text, f"mmdc reported error: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "chinese_diagram.png" in list_result.text, "Chinese diagram not found"

    @pytest.mark.asyncio
    async def test_mermaid_sequence(
        self, agent_env, workspace, mermaid_sequence_diagram, tool_call_helper
    ):
        """Test mermaid sequence diagram with Chinese text."""
        # Write the sequence diagram
        diagram_path = workspace / "sequence.mmd"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(diagram_path), "content": mermaid_sequence_diagram},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write diagram: {write_result.text}"

        # Create Puppeteer config to allow running Chromium as root
        puppeteer_config_path = workspace / ".puppeteerrc.json"
        puppeteer_config = '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
        config_call = tool_call_helper(
            "write_file",
            {"path": str(puppeteer_config_path), "content": puppeteer_config},
        )
        config_result = await agent_env.tool_execute(config_call)
        assert not config_result.is_error, f"Failed to write Puppeteer config: {config_result.text}"

        # Generate PNG using mmdc with Puppeteer config
        output_path = workspace / "sequence_diagram.png"
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"mmdc -i {diagram_path} -o {output_path} -p {puppeteer_config_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"mmdc execution failed: {exec_result.text}"
        assert "Error:" not in exec_result.text, f"mmdc reported error: {exec_result.text}"

        # Verify the output file exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "sequence_diagram.png" in list_result.text, "Sequence diagram not found"

    @pytest.mark.asyncio
    async def test_mermaid_from_fixture_file(
        self, agent_env, workspace, fixtures_dir, tool_call_helper
    ):
        """Test mermaid using the fixture diagram file."""
        fixture_diagram = fixtures_dir / "test_mermaid.mmd"
        assert fixture_diagram.exists(), f"Fixture diagram not found: {fixture_diagram}"

        # Read the fixture diagram
        with open(fixture_diagram, encoding="utf-8") as f:
            diagram_content = f.read()

        # Write to workspace
        diagram_path = workspace / "test_mermaid.mmd"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(diagram_path), "content": diagram_content},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write diagram: {write_result.text}"

        # Create Puppeteer config to allow running Chromium as root
        puppeteer_config_path = workspace / ".puppeteerrc.json"
        puppeteer_config = '{"args":["--no-sandbox","--disable-setuid-sandbox"]}'
        config_call = tool_call_helper(
            "write_file",
            {"path": str(puppeteer_config_path), "content": puppeteer_config},
        )
        config_result = await agent_env.tool_execute(config_call)
        assert not config_result.is_error, f"Failed to write Puppeteer config: {config_result.text}"

        # Generate PNG using mmdc with Puppeteer config
        output_path = workspace / "test_mermaid.png"
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"mmdc -i {diagram_path} -o {output_path} -p {puppeteer_config_path}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error, f"mmdc execution failed: {exec_result.text}"
        assert "Error:" not in exec_result.text, f"mmdc reported error: {exec_result.text}"

        # Verify output
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "test_mermaid.png" in list_result.text


class TestSandboxIntegration:
    """Integration tests for sandbox environment."""

    @pytest.mark.asyncio
    async def test_sandbox_tools_available(self, agent_env):
        """Verify that all required sandbox tools are available."""
        required_tools = [
            "execute_command",
            "write_file",
            "read_file",
            "list_directory",
            "create_directory",
            "move_file",
            "edit_file",
        ]

        available_tools = list(agent_env._tools_dict.keys())

        for tool in required_tools:
            assert tool in available_tools, f"Required tool '{tool}' not available"

    @pytest.mark.asyncio
    async def test_python_availability(self, agent_env, workspace, tool_call_helper):
        """Test that Python is available in the sandbox."""
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "python --version"},
        )
        result = await agent_env.tool_execute(exec_call)
        assert not result.is_error, "Python not available"
        assert "Python 3" in result.text, "Python version check failed"

    @pytest.mark.asyncio
    async def test_matplotlib_import(self, agent_env, workspace, tool_call_helper):
        """Test that matplotlib can be imported in the sandbox."""
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "python -c 'import matplotlib; print(matplotlib.__version__)'"},
        )
        result = await agent_env.tool_execute(exec_call)
        assert not result.is_error, "matplotlib import failed"
        assert len(result.text.strip()) > 0, "matplotlib version not returned"

    @pytest.mark.asyncio
    async def test_mmdc_availability(self, agent_env, workspace, tool_call_helper):
        """Test that mmdc (mermaid-cli) is available in the sandbox."""
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "mmdc --version"},
        )
        result = await agent_env.tool_execute(exec_call)
        assert not result.is_error, "mmdc not available"

    @pytest.mark.asyncio
    async def test_chinese_fonts_available(self, agent_env, workspace, tool_call_helper):
        """Test that Chinese fonts are installed in the sandbox."""
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "fc-list :lang=zh | head -5"},
        )
        result = await agent_env.tool_execute(exec_call)
        assert not result.is_error, "Font check failed"
        # Should find at least some Chinese fonts
        chinese_fonts = ["Noto", "WenQuanYi", "AR PL"]
        has_chinese_font = any(font in result.text for font in chinese_fonts)
        assert has_chinese_font, "No Chinese fonts found"

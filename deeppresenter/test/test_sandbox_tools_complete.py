"""
Complete Sandbox Tools Testing

This test suite validates ALL sandbox tools functionality:
1. File operations (write, read, edit, move)
2. Directory operations (create, list)
3. Command execution
4. File information retrieval

Tests all 7 desktop_commander tools comprehensively.
"""

import pytest
from pathlib import Path


class TestFileOperations:
    """Test all file operation tools."""

    @pytest.mark.asyncio
    async def test_write_and_read_file(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test write_file and read_file tools."""
        # Write a text file
        content = "Hello, World!\nThis is a test file.\n测试中文内容"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "test.txt"), "content": content},
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error, f"Failed to write file: {write_result.text}"

        # Read the file back
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "test.txt")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert not read_result.is_error, f"Failed to read file: {read_result.text}"
        assert "Hello, World!" in read_result.text
        assert "测试中文内容" in read_result.text

    @pytest.mark.asyncio
    async def test_write_file_append_mode(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test write_file with append mode."""
        # Write initial content
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "append_test.txt"), "content": "Line 1\n"},
        )
        await agent_env.tool_execute(write_call)

        # Append more content
        append_call = tool_call_helper(
            "write_file",
            {
                "path": str(workspace / "append_test.txt"),
                "content": "Line 2\n",
                "mode": "append",
            },
        )
        append_result = await agent_env.tool_execute(append_call)
        assert not append_result.is_error

        # Read and verify
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "append_test.txt")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert "Line 1" in read_result.text
        assert "Line 2" in read_result.text

    @pytest.mark.asyncio
    async def test_edit_file_single_replacement(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test edit_file tool with single replacement."""
        # Create a file with content to edit
        original_content = "version=1.0\nstatus=active\nmode=production"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "config.txt"), "content": original_content},
        )
        await agent_env.tool_execute(write_call)

        # Edit the file
        edit_call = tool_call_helper(
            "edit_file",
            {
                "file_path": str(workspace / "config.txt"),
                "old_string": "version=1.0",
                "new_string": "version=2.0",
            },
        )
        edit_result = await agent_env.tool_execute(edit_call)
        assert not edit_result.is_error, f"Edit failed: {edit_result.text}"

        # Verify the change
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "config.txt")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert "version=2.0" in read_result.text
        assert "version=1.0" not in read_result.text
        assert "status=active" in read_result.text

    @pytest.mark.asyncio
    async def test_edit_file_multiple_replacements(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test edit_file tool with multiple replacements."""
        # Create a file with repeated content
        content = "foo\nfoo\nfoo\nbar"
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "multi.txt"), "content": content},
        )
        await agent_env.tool_execute(write_call)

        # Replace all occurrences
        edit_call = tool_call_helper(
            "edit_file",
            {
                "file_path": str(workspace / "multi.txt"),
                "old_string": "foo",
                "new_string": "baz",
                "expected_replacements": 3,
            },
        )
        edit_result = await agent_env.tool_execute(edit_call)
        assert not edit_result.is_error

        # Verify all replacements
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "multi.txt")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert "baz" in read_result.text
        assert "foo" not in read_result.text
        assert read_result.text.count("baz") == 3

    @pytest.mark.asyncio
    async def test_move_file_rename(self, agent_env, workspace, tool_call_helper):
        """Test move_file tool for renaming."""
        # Create a file
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "old_name.txt"), "content": "test content"},
        )
        await agent_env.tool_execute(write_call)

        # Rename the file
        move_call = tool_call_helper(
            "move_file",
            {
                "source": str(workspace / "old_name.txt"),
                "destination": str(workspace / "new_name.txt"),
            },
        )
        move_result = await agent_env.tool_execute(move_call)
        assert not move_result.is_error, f"Move failed: {move_result.text}"

        # Verify old file is gone
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "new_name.txt" in list_result.text
        assert "old_name.txt" not in list_result.text

        # Verify content is preserved
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "new_name.txt")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert "test content" in read_result.text


class TestDirectoryOperations:
    """Test directory operation tools."""

    @pytest.mark.asyncio
    async def test_create_directory_single_level(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test create_directory with single level."""
        # Create a directory
        create_call = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "test_dir")},
        )
        create_result = await agent_env.tool_execute(create_call)
        assert not create_result.is_error, f"Failed to create directory: {create_result.text}"

        # Verify directory exists
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "[DIR] test_dir" in list_result.text or "test_dir" in list_result.text

    @pytest.mark.asyncio
    async def test_create_directory_nested(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test create_directory with nested directories."""
        # Create nested directories
        nested_path = workspace / "level1" / "level2" / "level3"
        create_call = tool_call_helper(
            "create_directory",
            {"path": str(nested_path)},
        )
        create_result = await agent_env.tool_execute(create_call)
        assert not create_result.is_error

        # Verify nested structure
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace), "depth": 3},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert "level1" in list_result.text
        assert "level2" in list_result.text
        assert "level3" in list_result.text

    @pytest.mark.asyncio
    async def test_create_directory_idempotent(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test that create_directory is idempotent."""
        dir_path = str(workspace / "idempotent_test")

        # Create directory first time
        create_call1 = tool_call_helper(
            "create_directory",
            {"path": dir_path},
        )
        result1 = await agent_env.tool_execute(create_call1)
        assert not result1.is_error

        # Create same directory again (should not error)
        create_call2 = tool_call_helper(
            "create_directory",
            {"path": dir_path},
        )
        result2 = await agent_env.tool_execute(create_call2)
        assert not result2.is_error

    @pytest.mark.asyncio
    async def test_list_directory_with_files_and_dirs(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test list_directory with mixed content."""
        # Create directories
        create_dir1 = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "subdir1")},
        )
        await agent_env.tool_execute(create_dir1)

        create_dir2 = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "subdir2")},
        )
        await agent_env.tool_execute(create_dir2)

        # Create files
        write_file1 = tool_call_helper(
            "write_file",
            {"path": str(workspace / "file1.txt"), "content": "content1"},
        )
        await agent_env.tool_execute(write_file1)

        write_file2 = tool_call_helper(
            "write_file",
            {"path": str(workspace / "file2.txt"), "content": "content2"},
        )
        await agent_env.tool_execute(write_file2)

        # List directory
        list_call = tool_call_helper(
            "list_directory",
            {"path": str(workspace)},
        )
        list_result = await agent_env.tool_execute(list_call)
        assert not list_result.is_error

        # Verify all items are listed
        result_text = list_result.text
        assert "subdir1" in result_text
        assert "subdir2" in result_text
        assert "file1.txt" in result_text
        assert "file2.txt" in result_text


class TestCommandExecution:
    """Test execute_command tool with various scenarios."""

    @pytest.mark.asyncio
    async def test_execute_simple_command(self, agent_env, workspace, tool_call_helper):
        """Test execute_command with simple commands."""
        # Test echo
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "echo 'Hello from sandbox'"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error
        assert "Hello from sandbox" in exec_result.text

    @pytest.mark.asyncio
    async def test_execute_python_script(self, agent_env, workspace, tool_call_helper):
        """Test execute_command with Python script."""
        # Write a Python script
        script_content = """
import sys
print(f"Python version: {sys.version}")
print("Script executed successfully")
"""
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "test_script.py"), "content": script_content},
        )
        await agent_env.tool_execute(write_call)

        # Execute the script
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {workspace / 'test_script.py'}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error
        assert "Script executed successfully" in exec_result.text

    @pytest.mark.asyncio
    async def test_execute_command_with_pipes(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test execute_command with piped commands."""
        # Create a file with content
        write_call = tool_call_helper(
            "write_file",
            {
                "path": str(workspace / "numbers.txt"),
                "content": "1\n2\n3\n4\n5\n",
            },
        )
        await agent_env.tool_execute(write_call)

        # Use pipes to process the file
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"cat {workspace / 'numbers.txt'} | wc -l"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error
        assert "5" in exec_result.text

    @pytest.mark.asyncio
    async def test_execute_command_with_chinese(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test execute_command with Chinese characters."""
        exec_call = tool_call_helper(
            "execute_command",
            {"command": "echo '中文测试：你好世界'"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error
        assert "中文测试" in exec_result.text or "你好世界" in exec_result.text


class TestFileInfo:
    """Test file information retrieval using alternative methods.

    Note: get_file_info tool is not available in desktop_commander.
    We use alternative methods (ls, stat) to verify file information.
    """

    @pytest.mark.asyncio
    async def test_get_file_info_text_file(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test file info retrieval using ls command."""
        # Create a text file
        content = "Test content" * 100
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "info_test.txt"), "content": content},
        )
        await agent_env.tool_execute(write_call)

        # Get file info using ls command
        info_call = tool_call_helper(
            "execute_command",
            {"command": f"ls -lh {workspace / 'info_test.txt'}"},
        )
        info_result = await agent_env.tool_execute(info_call)
        assert not info_result.is_error
        # Should contain file name and size information
        assert "info_test.txt" in info_result.text

    @pytest.mark.asyncio
    async def test_get_file_info_binary_file(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test file info retrieval for binary files using ls command."""
        # Generate an image using matplotlib
        script_content = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.figure(figsize=(4, 3))
plt.plot([1, 2, 3], [1, 4, 9])
plt.savefig('test_image.png')
print('Image created')
"""
        write_call = tool_call_helper(
            "write_file",
            {"path": str(workspace / "gen_image.py"), "content": script_content},
        )
        await agent_env.tool_execute(write_call)

        # Execute to generate image
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {workspace / 'gen_image.py'}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert "Image created" in exec_result.text

        # Get file info using ls command
        info_call = tool_call_helper(
            "execute_command",
            {"command": f"ls -lh {workspace / 'test_image.png'}"},
        )
        info_result = await agent_env.tool_execute(info_call)
        assert not info_result.is_error
        assert "test_image.png" in info_result.text


class TestComplexWorkflow:
    """Test complex workflows combining multiple tools."""

    @pytest.mark.asyncio
    async def test_full_workflow_create_edit_move(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test a complete workflow: create directory, write file, edit, move."""
        # Step 1: Create directory structure
        create_dir = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "project" / "src")},
        )
        await agent_env.tool_execute(create_dir)

        create_backup = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "project" / "backup")},
        )
        await agent_env.tool_execute(create_backup)

        # Step 2: Write initial file
        write_call = tool_call_helper(
            "write_file",
            {
                "path": str(workspace / "project" / "src" / "app.py"),
                "content": "# Version 1.0\nprint('Hello')\n",
            },
        )
        write_result = await agent_env.tool_execute(write_call)
        assert not write_result.is_error

        # Step 3: Edit the file
        edit_call = tool_call_helper(
            "edit_file",
            {
                "file_path": str(workspace / "project" / "src" / "app.py"),
                "old_string": "# Version 1.0",
                "new_string": "# Version 2.0",
            },
        )
        edit_result = await agent_env.tool_execute(edit_call)
        assert not edit_result.is_error

        # Step 4: Move to backup
        move_call = tool_call_helper(
            "move_file",
            {
                "source": str(workspace / "project" / "src" / "app.py"),
                "destination": str(workspace / "project" / "backup" / "app_v2.py"),
            },
        )
        move_result = await agent_env.tool_execute(move_call)
        assert not move_result.is_error

        # Step 5: Verify final state
        list_backup = tool_call_helper(
            "list_directory",
            {"path": str(workspace / "project" / "backup")},
        )
        list_result = await agent_env.tool_execute(list_backup)
        assert "app_v2.py" in list_result.text

        # Verify content
        read_call = tool_call_helper(
            "read_file",
            {"path": str(workspace / "project" / "backup" / "app_v2.py")},
        )
        read_result = await agent_env.tool_execute(read_call)
        assert "# Version 2.0" in read_result.text

    @pytest.mark.asyncio
    async def test_workflow_data_processing(
        self, agent_env, workspace, tool_call_helper
    ):
        """Test workflow: create data, process with Python, organize results."""
        # Create data directory
        create_dir = tool_call_helper(
            "create_directory",
            {"path": str(workspace / "data")},
        )
        await agent_env.tool_execute(create_dir)

        # Write input data
        write_data = tool_call_helper(
            "write_file",
            {
                "path": str(workspace / "data" / "input.txt"),
                "content": "apple\nbanana\napple\norange\nbanana\napple\n",
            },
        )
        await agent_env.tool_execute(write_data)

        # Write processing script
        script = """
from collections import Counter

with open('data/input.txt', 'r') as f:
    items = [line.strip() for line in f]

counts = Counter(items)
with open('data/output.txt', 'w') as f:
    for item, count in counts.items():
        f.write(f'{item}: {count}\\n')

print('Processing complete')
"""
        write_script = tool_call_helper(
            "write_file",
            {"path": str(workspace / "process.py"), "content": script},
        )
        await agent_env.tool_execute(write_script)

        # Execute processing
        exec_call = tool_call_helper(
            "execute_command",
            {"command": f"python {workspace / 'process.py'}"},
        )
        exec_result = await agent_env.tool_execute(exec_call)
        assert not exec_result.is_error
        assert "Processing complete" in exec_result.text

        # Verify output
        read_output = tool_call_helper(
            "read_file",
            {"path": str(workspace / "data" / "output.txt")},
        )
        output_result = await agent_env.tool_execute(read_output)
        assert "apple: 3" in output_result.text
        assert "banana: 2" in output_result.text
        assert "orange: 1" in output_result.text


class TestToolsAvailability:
    """Test that all required tools are available."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(self, agent_env):
        """Verify all 7 desktop_commander tools are available.

        Note: get_file_info is NOT available in desktop_commander (commit 252a00d).
        Only 7 tools are provided by the MCP server.
        """
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

        missing_tools = [tool for tool in required_tools if tool not in available_tools]

        assert len(missing_tools) == 0, f"Missing tools: {missing_tools}"
        print(f"\n✓ All {len(required_tools)} tools are available: {required_tools}")

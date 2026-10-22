import pytest

from agentgrade.mcp_agent_demo import select_tools
from agentgrade.servers import FILESYSTEM_READ_ONLY_TOOLS


def test_default_is_the_full_read_only_allowlist():
    assert select_tools(None) == FILESYSTEM_READ_ONLY_TOOLS


def test_can_narrow_the_allowlist():
    assert select_tools("list_directory, read_text_file") == ["list_directory", "read_text_file"]


def test_can_never_widen_the_allowlist():
    with pytest.raises(ValueError, match="write_file"):
        select_tools("read_text_file,write_file")

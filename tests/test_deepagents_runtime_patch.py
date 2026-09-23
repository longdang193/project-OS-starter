from pathlib import Path
import importlib.util
import sys

_PATCH_MODULE_SPEC = importlib.util.spec_from_file_location(
    "project_patch_deepagents_runtime",
    Path(__file__).resolve().parents[1] / "scripts" / "patch_deepagents_runtime.py",
)
assert _PATCH_MODULE_SPEC is not None and _PATCH_MODULE_SPEC.loader is not None
_PATCH_MODULE = importlib.util.module_from_spec(_PATCH_MODULE_SPEC)
sys.modules[_PATCH_MODULE_SPEC.name] = _PATCH_MODULE
_PATCH_MODULE_SPEC.loader.exec_module(_PATCH_MODULE)
patch_headless_mcp_guard = _PATCH_MODULE.patch_headless_mcp_guard
patch_mcp_tools = _PATCH_MODULE.patch_mcp_tools
patch_model_retry_budget = _PATCH_MODULE.patch_model_retry_budget
patch_stdio_lookup = _PATCH_MODULE.patch_stdio_lookup
patch_windows_lookup = _PATCH_MODULE.patch_windows_lookup
patcher_main = _PATCH_MODULE.main


def test_patch_mcp_tools_avoids_async_path_resolution(tmp_path: Path) -> None:
    target = tmp_path / "mcp_tools.py"
    target.write_text(
        "    if explicit_config_path:\n"
        "        config_path = (\n"
        "            str(project_context.resolve_user_path(explicit_config_path))\n"
        "            if project_context is not None\n"
        "            else explicit_config_path\n"
        "        )\n"
        "        configs.append(load_mcp_config(config_path))\n",
        encoding="utf-8",
    )

    assert patch_mcp_tools(target) is True
    patched = target.read_text(encoding="utf-8")
    assert "resolve_user_path(explicit_config_path)" not in patched
    assert "Path(explicit_config_path).expanduser()" in patched
    assert patch_mcp_tools(target) is False


def test_patch_stdio_lookup_offloads_windows_command_resolution(tmp_path: Path) -> None:
    target = tmp_path / "mcp_tools.py"
    target.write_text(
        '    params = StdioServerParameters(\n'
        '        command=stdio["command"],\n'
        '        args=stdio["args"],\n'
        '        # Already expanded: `_build_connection` runs `resolve_mcp_server_env`\n'
        '        # over `env` before the connection is built, with a richer grammar\n'
        '        # (`${VAR:-default}`) that raises on an unset reference. A second pass\n'
        '        # here could only re-scan resolved secrets and warn about a value that\n'
        '        # legitimately contains `${`.\n'
        '        env=stdio.get("env"),\n'
        '        cwd=stdio.get("cwd"),\n'
        '        encoding=encoding,\n'
        '        encoding_error_handler=errors,\n'
        '    )\n',
        encoding="utf-8",
    )

    assert patch_stdio_lookup(target) is True
    patched = target.read_text(encoding="utf-8")
    assert "await asyncio.to_thread(shutil.which, params.command)" in patched
    assert patch_stdio_lookup(target) is False


def test_patch_mcp_tools_accepts_upstream_config_path(tmp_path: Path) -> None:
    target = tmp_path / "mcp_tools.py"
    target.write_text(
        "        config_path = Path(explicit_config_path).expanduser()\n",
        encoding="utf-8",
    )

    assert patch_mcp_tools(target) is False


def test_patch_stdio_lookup_skips_fastmcp_runtime(tmp_path: Path) -> None:
    target = tmp_path / "mcp_tools.py"
    target.write_text(
        "from fastmcp import FastMCP\n"
        "from langchain.mcp import as_langchain_tool\n",
        encoding="utf-8",
    )

    assert patch_stdio_lookup(target) is False


def test_patch_headless_mcp_guard_allows_only_browser_list_probe(
    tmp_path: Path,
) -> None:
    target = tmp_path / "auto_mode.py"
    target.write_text(
        "    def _rejection(self, request: ToolCallRequest) -> ToolMessage | None:\n"
        "        if request.tool_call[\"name\"] not in self._tool_names:\n"
        "            return None\n"
        "        return ToolMessage(\n"
        "            content=(\n"
        "                \"This MCP action requires approval, but the current headless runtime \"\n"
        "                \"has no approval UI. Run it in the interactive TUI or choose a \"\n"
        "                \"read-only MCP action.\"\n"
        "            ),\n"
        "            name=request.tool_call[\"name\"],\n"
        "            tool_call_id=_tool_call_id(request.tool_call),\n"
        "            status=\"error\",\n"
        "        )\n",
        encoding="utf-8",
    )

    assert patch_headless_mcp_guard(target) is True
    patched = target.read_text(encoding="utf-8")
    assert 'args.get("action") == "list"' in patched
    assert "name == \"playwright_browser_tabs\"" in patched
    assert patch_headless_mcp_guard(target) is False


def test_patch_windows_lookup_accepts_current_mcp_source_shape(tmp_path: Path) -> None:
    target = tmp_path / "utilities.py"
    target.write_text(
        "    try:\n"
        "        # First check if command exists in PATH as-is\n"
        "        if command_path := shutil.which(command):\n",
        encoding="utf-8",
    )

    assert patch_windows_lookup(target) is True
    assert "Path(command).is_absolute()" in target.read_text(encoding="utf-8")
    assert patch_windows_lookup(target) is False


def test_patch_windows_lookup_accepts_legacy_mcp_source_shape(tmp_path: Path) -> None:
    target = tmp_path / "utilities.py"
    target.write_text(
        "    try:\n"
        "        # First check if command exists on PATH as-is\n"
        "        if command_path := shutil.which(command):\n",
        encoding="utf-8",
    )

    assert patch_windows_lookup(target) is True
    assert patch_windows_lookup(target) is False


def test_patch_model_retry_budget_caps_auxiliary_defaults(tmp_path: Path) -> None:
    target = tmp_path / "model_retry.py"
    target.write_text(
        "# Total sleep the interactive model node may spend across one call's retries.\n"
        "# Per-delay caps bound nothing (see `_delay_budget_guard`): five honoured\n"
        "# `Retry-After` hints of `_MAX_RETRY_AFTER_SECONDS` each would stall a turn for\n"
        "# five minutes behind a spinner. One full honoured hint still fits.\n"
        "_MAX_INTERACTIVE_TOTAL_DELAY_SECONDS = 60.0\n"
        "def retry_model_call(*, max_total_delay: float | None = None): pass\n"
        "def aretry_model_call(*, max_total_delay: float | None = None): pass\n",
        encoding="utf-8",
    )

    assert patch_model_retry_budget(target) is True
    patched = target.read_text(encoding="utf-8")
    assert "_MAX_INTERACTIVE_TOTAL_DELAY_SECONDS = 10.0" in patched
    assert patched.count(
        "max_total_delay: float | None = _MAX_INTERACTIVE_TOTAL_DELAY_SECONDS"
    ) == 2
    assert patch_model_retry_budget(target) is False


def test_patcher_skips_deleted_windows_runtime_for_fastmcp(tmp_path: Path) -> None:
    package_root = tmp_path / "site-packages"
    deepagents_root = package_root / "deepagents_code"
    deepagents_root.mkdir(parents=True)
    utility = package_root / "mcp" / "os" / "win32" / "utilities.py"
    utility.parent.mkdir(parents=True)
    utility.write_text("def resolve_command(command): pass\n", encoding="utf-8")
    mcp_tools = deepagents_root / "mcp_tools.py"
    mcp_tools.write_text(
        "from fastmcp import FastMCP\n"
        "from langchain.mcp import as_langchain_tool\n"
        "        config_path = Path(explicit_config_path).expanduser()\n",
        encoding="utf-8",
    )
    (deepagents_root / "auto_mode.py").write_text(
        "    def _rejection(self, request: ToolCallRequest) -> ToolMessage | None:\n"
        "        if request.tool_call[\"name\"] not in self._tool_names:\n"
        "            return None\n"
        "        return ToolMessage(\n"
        "            content=(\n"
        "                \"This MCP action requires approval, but the current headless runtime \"\n"
        "                \"has no approval UI. Run it in the interactive TUI or choose a \"\n"
        "                \"read-only MCP action.\"\n"
        "            ),\n"
        "            name=request.tool_call[\"name\"],\n"
        "            tool_call_id=_tool_call_id(request.tool_call),\n"
        "            status=\"error\",\n"
        "        )\n",
        encoding="utf-8",
    )
    (deepagents_root / "model_retry.py").write_text(
        "# Total sleep the interactive model node may spend across one call's retries.\n"
        "# Per-delay caps bound nothing (see `_delay_budget_guard`): five honoured\n"
        "# `Retry-After` hints of `_MAX_RETRY_AFTER_SECONDS` each would stall a turn for\n"
        "# five minutes behind a spinner. One full honoured hint still fits.\n"
        "_MAX_INTERACTIVE_TOTAL_DELAY_SECONDS = 60.0\n"
        "def retry_model_call(*, max_total_delay: float | None = None): pass\n"
        "def aretry_model_call(*, max_total_delay: float | None = None): pass\n",
        encoding="utf-8",
    )

    assert patcher_main([str(mcp_tools)]) == 0
    assert patcher_main([str(mcp_tools)]) == 0


def test_patcher_rejects_unknown_windows_runtime(tmp_path: Path) -> None:
    package_root = tmp_path / "site-packages"
    deepagents_root = package_root / "deepagents_code"
    deepagents_root.mkdir(parents=True)
    mcp_tools = deepagents_root / "mcp_tools.py"
    mcp_tools.write_text(
        _PATCH_MODULE._VULNERABLE + _PATCH_MODULE._STDIO_LOOKUP,
        encoding="utf-8",
    )
    (deepagents_root / "auto_mode.py").write_text(
        _PATCH_MODULE._HEADLESS_MCP_REJECTION,
        encoding="utf-8",
    )
    (deepagents_root / "model_retry.py").write_text(
        _PATCH_MODULE._MODEL_RETRY_BUDGET
        + "def retry_model_call(*, max_total_delay: float | None = None): pass\n"
        + "def aretry_model_call(*, max_total_delay: float | None = None): pass\n",
        encoding="utf-8",
    )

    try:
        patcher_main([str(mcp_tools)])
    except RuntimeError as exc:
        assert "Unsupported DeepAgents Windows MCP runtime" in str(exc)
    else:
        raise AssertionError("unknown Windows runtime was accepted")

from ismain import is_main

from pyship.launcher_stub import CS_LAUNCHER_TEMPLATE, CLI_ERROR_HANDLER, GUI_ERROR_HANDLER


def _format_template(is_gui: bool) -> str:
    """Format the C# template for a test app name."""
    app_name = "testapp"
    error_handler = GUI_ERROR_HANDLER if is_gui else CLI_ERROR_HANDLER
    hide_window = "psi.CreateNoWindow = true;" if is_gui else ""
    return CS_LAUNCHER_TEMPLATE.format(
        app_name=app_name,
        error_handler=error_handler,
        hide_window=hide_window,
    )


def test_launcher_stub_log_format():
    """Verify the formatted C# launcher template contains correct logging infrastructure and log calls."""

    cli_source = _format_template(is_gui=False)
    gui_source = _format_template(is_gui=True)

    for source in [cli_source, gui_source]:
        # Logging infrastructure
        assert "static string logFilePath" in source
        assert "static void InitLogging(string appName)" in source
        assert "static void Log(string level, string message)" in source
        assert "InitLogging(appName)" in source
        assert 'Path.Combine(localAppData, appName, "log")' in source
        assert 'appName + "_launcher.log"' in source
        assert "File.AppendAllText(logFilePath, line)" in source
        assert 'DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss,fff")' in source
        assert 'appName + "_stub' in source

        # Log calls at key steps
        assert '"stub starting' in source
        assert '"arguments:' in source
        assert '"appName=' in source
        assert '"searching for CLIP directories' in source
        assert '"candidate directories found' in source
        assert '"valid CLIPs' in source
        assert '"selected latest CLIP' in source
        assert '"pythonExe=' in source
        assert '"command:' in source
        assert '"starting process"' in source
        assert '"process started - PID=' in source
        assert '"process exited - exitCode=' in source

        # Error logging before error handlers
        assert 'Log("ERROR"' in source

        # Error resilience - catch blocks around logging
        assert "catch (Exception)" in source

    # CLI-specific: console error output, no CreateNoWindow
    assert "Console.Error.WriteLine(msg)" in cli_source
    assert "CreateNoWindow" not in cli_source

    # GUI-specific: MessageBox and CreateNoWindow
    assert "MessageBox.Show" in gui_source
    assert "CreateNoWindow = true" in gui_source


if is_main():
    test_launcher_stub_log_format()

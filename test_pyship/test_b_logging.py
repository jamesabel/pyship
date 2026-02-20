from pyship.logging import log_process_output


def test_log_process_output_basic():
    collected = []
    lines = log_process_output("stdout", b"hello\nworld\n", log_function=collected.append)
    assert lines == ["hello", "world"]
    assert any("hello" in s for s in collected)
    assert any("world" in s for s in collected)


def test_log_process_output_empty_bytes():
    collected = []
    lines = log_process_output("stdout", b"", log_function=collected.append)
    assert lines == []
    assert collected == []


def test_log_process_output_filters_blank_lines():
    collected = []
    lines = log_process_output("stdout", b"line1\n\n   \nline2", log_function=collected.append)
    assert lines == ["line1", "line2"]


def test_log_process_output_strips_whitespace():
    lines = log_process_output("stdout", b"  trimmed  \n")
    assert lines == ["trimmed"]


def test_log_process_output_includes_output_type_in_log():
    collected = []
    log_process_output("mytype", b"someline", log_function=collected.append)
    assert any("mytype" in s for s in collected)


def test_log_process_output_includes_line_content_in_log():
    collected = []
    log_process_output("stdout", b"important_string", log_function=collected.append)
    assert any("important_string" in s for s in collected)


def test_log_process_output_multiple_lines_each_logged():
    collected = []
    log_process_output("stdout", b"a\nb\nc", log_function=collected.append)
    assert len(collected) == 3


def test_log_process_output_returns_list():
    result = log_process_output("stdout", b"line1\nline2")
    assert isinstance(result, list)


def test_log_process_output_default_log_function_does_not_raise():
    # Uses the default log function - just verify no exception
    lines = log_process_output("stdout", b"test line")
    assert lines == ["test line"]


def test_log_process_output_single_line_no_newline():
    lines = log_process_output("stderr", b"single line without newline")
    assert lines == ["single line without newline"]

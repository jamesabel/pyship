from pyship.ci import is_ci


def test_is_ci_false_by_default(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert is_ci() is False


def test_is_ci_with_ci_env_var(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CI", "true")
    assert is_ci() is True


def test_is_ci_with_github_actions_env_var(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert is_ci() is True


def test_is_ci_ci_case_insensitive_upper(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CI", "TRUE")
    assert is_ci() is True


def test_is_ci_github_actions_case_insensitive_upper(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "True")
    assert is_ci() is True


def test_is_ci_false_when_ci_is_false(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CI", "false")
    assert is_ci() is False


def test_is_ci_false_when_ci_is_empty(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CI", "")
    assert is_ci() is False


def test_is_ci_false_when_ci_is_1(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("CI", "1")
    assert is_ci() is False


def test_is_ci_true_when_both_set(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert is_ci() is True

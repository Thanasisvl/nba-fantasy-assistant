import ast
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[1] / "src" / "nfa" / "domain"


def nfa_imports_outside_domain(source: str) -> list[str]:
    bad: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        else:
            continue
        for name in names:
            if name == "nfa" or (name.startswith("nfa.") and not name.startswith("nfa.domain")):
                bad.append(name)
    return bad


def test_detector_flags_adapter_import() -> None:
    assert nfa_imports_outside_domain("from nfa.adapters import http") == ["nfa.adapters"]


def test_detector_flags_package_root_import() -> None:
    assert nfa_imports_outside_domain("from nfa import clock") == ["nfa"]


def test_detector_allows_domain_and_stdlib() -> None:
    assert nfa_imports_outside_domain("import json\nfrom nfa.domain.raw import RawResponse") == []


def test_domain_imports_only_domain() -> None:
    for path in DOMAIN.rglob("*.py"):
        assert nfa_imports_outside_domain(path.read_text()) == [], path

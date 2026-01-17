venv:
	python -m venv .venv
	.venv/Scripts/pip.exe install -e .[dev]

test:
	.venv/Scripts/pytest.exe tests -v

format_and_lint:
	.venv/Scripts/ruff.exe format .
	.venv/Scripts/ruff.exe check . --fix
	.venv/Scripts/flake8.exe .
	.venv/Scripts/mypy.exe .

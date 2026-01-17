venv:
	python3 -m venv .venv
	.venv/bin/pip install -e .[dev]

test:
	.venv/bin/pytest tests -v

format_and_lint:
	.venv/bin/ruff format .
	.venv/bin/ruff check . --fix
	.venv/bin/flake8 .
	.venv/bin/mypy .

.PHONY: install run test clean

install:
	uv sync

run:
	uv run outerloop

test:
	uv run pytest

clean:
	rm -rf .pytest_cache **/__pycache__ dist *.egg-info

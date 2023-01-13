PYTHONPATH=./shell_operator

.PHONY: build test clean publish
build:
	poetry build

test:
	poetry run pytest

clean:
	rm -rf build dist *.egg-info

publish: clean build
	poetry publish

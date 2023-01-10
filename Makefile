.PHONY: build test clean
build:
	poetry build

test:
	poetry run pytest

clean:
	rm -rf build dist *.egg-info

upload: clean build
	poetry publish

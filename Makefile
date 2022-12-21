.PHONY: build test clean
build:
	python -m build

test:
	python -m pytest

clean:
	rm -rf build dist *.egg-info

upload: clean build
	python -m twine upload dist/*

.PHONY: all clean install test_all uninstall

all: install

clean:
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

install:
	python setup.py install

test_all: install
	pytest -v -s test

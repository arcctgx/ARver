.PHONY: release image wheels ext test sdist clean gitclean

CWD = $(shell pwd -P)
USER = $(shell id -u)
GROUP = $(shell id -g)
VERSION = $(shell cat utils/IMAGE_VERSION)

release: sdist wheels

image:
	docker build --tag arcctgx/arver-builder:$(VERSION) .

wheels:
	docker run --rm -u "$(USER):$(GROUP)" -v "$(CWD):/package" arcctgx/arver-builder:$(VERSION)

ext:
	python3 setup.py build_ext --verbose --inplace

test:
	python3 -m unittest discover -v -s tests/ -p "*_test.py"

sdist:
	python3 setup.py sdist

clean:
	$(RM) -vrf build dist wheelhouse

gitclean:
	git clean -e .vscode -fdx

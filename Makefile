.PHONY: release image test clean gitclean

CWD = $(shell pwd -P)
USER = $(shell id -u)
GROUP = $(shell id -g)
VERSION = $(shell cat utils/IMAGE_VERSION)

image:
	docker build --tag arcctgx/arver-builder:$(VERSION) .

release:
	docker run --rm -u "$(USER):$(GROUP)" -v "$(CWD):/package" arcctgx/arver-builder:$(VERSION)

test:
	python3 -m unittest discover -v -s tests/ -p "*_test.py"

clean:
	$(RM) -vrf build dist wheelhouse

gitclean:
	git clean -e .vscode -fdx

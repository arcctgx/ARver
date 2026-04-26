.PHONY: release test clean gitclean

CWD = $(shell pwd -P)

release:
	docker run --rm -e PLAT=manylinux2014_x86_64 -v $(CWD):/pkg quay.io/pypa/manylinux2014_x86_64 /pkg/utils/build-wheels.sh

test:
	python3 -m unittest discover -v -s tests/ -p "*_test.py"

clean:
	$(RM) -vrf build dist wheelhouse

gitclean:
	git clean -e .vscode -fdx

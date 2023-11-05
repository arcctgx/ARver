.PHONY: release image wheels test sdist clean

CWD = $(shell pwd -P)
USER = $(shell id -u)
GROUP = $(shell id -g)

release: sdist wheels

image:
	docker build --tag arcctgx/arver-builder .

wheels:
	docker run --rm -u "$(USER):$(GROUP)" -v "$(CWD):/package" arcctgx/arver-builder

test:
	python3 -m unittest discover -v -s tests/ -p "*_test.py"

sdist:
	python3 setup.py sdist

clean:
	$(RM) -vrf build dist wheelhouse

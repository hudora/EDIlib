check: dependencies
	-pep8 -r --ignore=E501 edilib/
	pyflakes edilib/
	pylint -iy --max-line-length=110 -d E1101 edilib/

test: dependencies
	PYTHONPATH=. ./pythonenv/bin/python test/test_recordbased.py

dependencies:
	virtualenv --python=python2.5 --no-site-packages --unzip-setuptools pythonenv
	pip install --environment=pythonenv huSoftM

clean:
	rm -Rf pythonenv/
	find . -name '*.pyc' -or -name '*.pyo' -delete

.PHONY: deploy pylint clean check dependencies

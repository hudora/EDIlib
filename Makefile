check: dependencies
	pep8 -r --ignore=E501 edilib/
	pyflakes edilib/
	-pylint -iy --max-line-length=110 -d E1101 edilib/

test: dependencies testdata
	PYTHONPATH=. ./pythonenv/bin/python test/test_recordbased.py
	PYTHONPATH=. ./pythonenv/bin/python edilib/softm/content.py

dependencies:
	virtualenv --python=python2.5 --no-site-packages --unzip-setuptools pythonenv
	pythonenv/bin/pip install -r requirements.txt

testdata:
	rm -rf testdata
	git clone git@github.com:hudora/Testdaten.git testdata  # HUDORA only!

clean:
	rm -Rf pythonenv/
	find . -name '*.pyc' -or -name '*.pyo' -delete

.PHONY: deploy pylint clean check dependencies

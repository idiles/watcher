test:
	nosetests --with-doctest --doctest-tests

clean:
	for f in `find . -name '*.pyc'`; do rm $$f; done
	for f in `find . -name '*.pyo'`; do rm $$f; done
	for f in `find . -name '*~'`; do rm $$f; done

install:
	mkdir /opt/watcher
	cp -r * /opt/watcher

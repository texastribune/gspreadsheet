
help:
	@echo "make commands:"
	@echo "  make help  - this help"
	@echo "  make test  - run tests"

test:
	nosetests --nocapture

.PHONY: help test


help:
	@echo "make commands:"
	@echo "  make help  - this help"
	@echo "  make test  - run tests"
	@echo "  make todo  - list notes in the code"

test:
	nosetests --nocapture

todo:
	grep -rI "TODO" gspreadsheet/

.PHONY: help test todo

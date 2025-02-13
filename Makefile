.PHONY: check
check:
	python -c "from browser_ops import run; print('ok')"
	python -m pytest -q

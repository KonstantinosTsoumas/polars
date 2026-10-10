SHELL := /bin/bash
VENV  := .venv
PY    := $(VENV)/bin/python

.PHONY: help install install-release test test-rust test-python lint clean

help:
	@echo "install          build the plugin in debug mode and install it"
	@echo "install-release  build optimised (use this for any benchmarking)"
	@echo "test             run the Rust and Python test suites"
	@echo "clean            remove build artefacts and the virtualenv"

$(VENV):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install maturin pytest polars

install: $(VENV)
	unset CONDA_PREFIX && source $(VENV)/bin/activate && maturin develop

install-release: $(VENV)
	unset CONDA_PREFIX && source $(VENV)/bin/activate && maturin develop --release

# The pure logic lives in a dependency-free crate, so it tests without pyo3,
# Polars, or a Python interpreter in the picture.
test-rust:
	cargo test -p leetspeak-core

test-python: install
	$(PY) -m pytest tests/ -q

test: test-rust test-python

clean:
	cargo clean
	rm -rf $(VENV) leetspeak/*.so .pytest_cache

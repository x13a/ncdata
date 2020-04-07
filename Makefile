.PHONY: env

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
VENV_PREFIX := ./venv
VENV_BINDIR := $(VENV_PREFIX)/bin
NAME := ncprivacy
TARGET := $(BINDIR)/$(NAME)

all: env

env:
	python3 -m venv --prompt $(NAME) $(VENV_PREFIX)
	( \
		source $(VENV_BINDIR)/activate; \
		pip install -U "."; \
		deactivate; \
	)

install:
	install -d $(BINDIR)/
	ln $(VENV_BINDIR)/$(NAME) $(TARGET)

uninstall:
	rm -f $(TARGET)
	rm -rf $(VENV_PREFIX)/

test:
	python3 -m unittest

.PHONY: env

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
LIBDIR ?= $(PREFIX)/lib
NAME := ncprivacy
VENV_DIR := ./venv
DEST_LIB := $(LIBDIR)/$(NAME)
DEST := $(BINDIR)/$(NAME)

all: env

define make_env
	python3 -m venv --prompt $(NAME) $(1)
	( \
		source $(1)/bin/activate; \
		pip install -U "."; \
		deactivate; \
	)
endef

env:
	$(call make_env,$(VENV_DIR))

install:
	install -d $(LIBDIR)/ $(BINDIR)/
	$(call make_env,$(DEST_LIB))
	ln -s $(DEST_LIB)/bin/$(NAME) $(DEST)

uninstall:
	rm -f $(DEST)
	rm -rf $(DEST_LIB)/

clean:
	rm -rf $(VENV_DIR)/

test:
	python3 -m unittest

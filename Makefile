.PHONY: env

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
LIBDIR ?= $(PREFIX)/lib
VENV_PREFIX := ./venv
VENV_BINDIR := $(VENV_PREFIX)/bin
NAME := ncprivacy
LIB_PREFIX := $(LIBDIR)/$(NAME)
LIB_BINDIR := $(LIB_PREFIX)/bin
TARGET := $(BINDIR)/$(NAME)

all: env

define make_env
	python3 -m venv --prompt $(NAME) $(1)
	( \
		source $(2)/activate; \
		pip install -U "."; \
		deactivate; \
	)
endef

env:
	$(call make_env,$(VENV_PREFIX),$(VENV_BINDIR))

install:
	install -d $(LIBDIR)/ $(BINDIR)/
	$(call make_env,$(LIB_PREFIX),$(LIB_BINDIR))
	ln -s $(LIB_BINDIR)/$(NAME) $(TARGET)

uninstall:
	rm -f $(TARGET)
	rm -rf $(LIB_PREFIX)/

clean:
	rm -rf $(VENV_PREFIX)/

test:
	python3 -m unittest

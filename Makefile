.PHONY: env

NAME        := ncdata

prefix      ?= /usr/local
exec_prefix ?= $(prefix)
bindir      ?= $(exec_prefix)/bin
libdir      ?= $(exec_prefix)/lib

venvdir     := ./venv
bindestdir  := $(DESTDIR)$(bindir)
libdestdir  := $(DESTDIR)$(libdir)
bindest     := $(bindestdir)/$(NAME)
libdest     := $(libdestdir)/$(NAME)

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
	$(call make_env,$(venvdir))

installdirs:
	install -d $(libdestdir)/ $(bindestdir)/

install: installdirs
	$(call make_env,$(libdest))
	ln -s $(libdest)/bin/$(NAME) $(bindest)

uninstall:
	rm -f $(bindest)
	rm -rf $(libdest)/

clean:
	rm -rf $(venvdir)/

test:
	python3 -m unittest

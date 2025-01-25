include ../mk/common-dirs.mk
include ../mk/common-tools.mk

MODEL_DIRS := $(dir $(shell $(FIND) . -type f -name "config.toml"))

.PHONY:	all clean install uninstall $(MODEL_DIRS)

all clean install: $(MODEL_DIRS)

$(MODEL_DIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

uninstall: $(MODEL_DIRS)
	-$(RMDIR_P) $(DEST_MODELS_DIR)/
	-$(RMDIR_P) $(DEST_STATIC_MODELS_DIR)/

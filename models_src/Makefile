MODEL_DIRS := test test_rows twinkle

include ../mk/common-dirs.mk
include ../mk/common-tools.mk

.PHONY:	all clean install uninstall $(MODEL_DIRS)

all clean install: $(MODEL_DIRS)

$(MODEL_DIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

uninstall: $(MODEL_DIRS)
	-$(RMDIR) $(DEST_MODELS_DIR)/
	-$(RMDIR) $(DEST_STATIC_MODELS_DIR)/

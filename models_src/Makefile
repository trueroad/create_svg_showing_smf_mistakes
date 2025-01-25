include ../mk/common-dirs.mk
include ../mk/common-tools.mk

# モデルディレクトリ（config.tomlが存在するディレクトリを検索して使用）
MODEL_DIRS := $(dir $(shell $(FIND) . -type f -name "config.toml"))

# モデルディレクトリのMakefile
MODEL_MAKEFILES = $(addsuffix /Makefile, $(MODEL_DIRS))

.PHONY:	all clean install uninstall $(MODEL_DIRS)

all clean install: $(MODEL_DIRS)

$(MODEL_MAKEFILES): template.mk
	$(BUILD_MODEL_MAKEFILE) $< $(MAKE_DIR) $(dir $@)

$(MODEL_DIRS): $(MODEL_MAKEFILES)
	$(MAKE) -C $@ $(MAKECMDGOALS)

uninstall: $(MODEL_DIRS)
	-$(RMDIR_P) $(DEST_MODELS_DIR)/
	-$(RMDIR_P) $(DEST_STATIC_MODELS_DIR)/

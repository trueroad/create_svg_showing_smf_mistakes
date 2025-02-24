include ../mk/common-dirs.mk
include ../mk/common-tools.mk

# モデルディレクトリ（config.tomlが存在するディレクトリを検索して使用）
MODEL_DIRS := $(dir $(shell $(FIND) . -type f -name "config.toml"))

# モデルディレクトリに生成するMakefile
MODEL_MAKEFILES = $(addsuffix /Makefile, $(MODEL_DIRS))

# モデルディレクトリに生成する.gitignore
MODEL_GITIGNORES = $(addsuffix /.gitignore, $(MODEL_DIRS))

# モデル一覧
MODELS_JSON = models.json

.PHONY:	all clean install uninstall $(MODEL_DIRS)

all: $(MODEL_DIRS) $(MODEL_GITIGNORES) $(MODELS_JSON)

$(MODEL_MAKEFILES): template.mk
	$(BUILD_MODEL_MAKEFILE) $< $(dir $@) > $@

$(MODEL_GITIGNORES):
	echo "Makefile" > $@
	echo ".gitignore" >> $@

$(MODEL_DIRS): $(MODEL_MAKEFILES)
	$(MAKE) -C $@ $(MAKECMDGOALS)

$(MODELS_JSON):
	$(BUILD_MODELS_JSON) $(MODELS_SRC_DIR) $(MODEL_DIRS) > $@

clean: $(MODEL_DIRS)
	-$(RM) $(MODEL_MAKEFILES) $(MODEL_GITIGNORES) $(MODELS_JSON)

install: $(MODEL_DIRS)
	$(INSTALL_DATA) $(MODELS_JSON) $(DEST_STATIC_MODELS_DIR)

uninstall: $(MODEL_DIRS)
	-$(RMDIR) $(DEST_MODELS_DIR)/
	$(RM) $(DEST_STATIC_MODELS_DIR)/$(MODELS_JSON)
	-$(RMDIR) $(DEST_STATIC_MODELS_DIR)/

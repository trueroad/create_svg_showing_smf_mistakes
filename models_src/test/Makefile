# モデルディレクトリ（このディレクトリ）
MODEL_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

# テスト用評価対象の拡張子を除いたファイル名
FOREVALS = foreval empty no_match1 no_match2 magic_command_clear

include ../../mk/common-dirs.mk
include $(MAKE_DIR)/models.mk

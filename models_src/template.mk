# モデルディレクトリ（このディレクトリ）
MODEL_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

include @MAKE_DIR@/models.mk

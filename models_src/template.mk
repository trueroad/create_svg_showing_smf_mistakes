# モデルディレクトリ（このディレクトリ）
MODEL_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

# モデル名（モデルソースディレクトリ中のディレクトリ名）
MODEL_NAME := @MODEL_NAME@

include @MODELS_SRC_DIR_FROM_MODEL_DIR@/../mk/models.mk

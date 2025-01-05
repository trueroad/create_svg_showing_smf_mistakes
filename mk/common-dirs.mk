# makeディレクトリ（このファイルがあるディレクトリ）
MAKE_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

# ベースディレクトリ
BASE_DIR := $(realpath $(MAKE_DIR)/..)

# インストール先ディレクトリ
DESTDIR ?= $(BASE_DIR)
DEST_MODELS_DIR ?= $(DESTDIR)/models
DEST_STATIC_DIR ?= $(DESTDIR)/static
DEST_STATIC_MODELS_DIR ?= $(DEST_STATIC_DIR)/models

# 共通ディレクトリ
LY_DIR = $(BASE_DIR)/ly
SCRIPT_DIR = $(BASE_DIR)/script
MODELS_SRC_DIR = $(BASE_DIR)/models_src

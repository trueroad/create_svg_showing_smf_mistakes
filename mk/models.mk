# makeディレクトリ（このファイルがあるディレクトリ）
MAKE_DIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))

# 各種ディレクトリ・ツール
include $(MAKE_DIR)/common-dirs.mk
include $(MAKE_DIR)/common-tools.mk

# モデル名（モデルソースディレクトリ中のディレクトリ名）
MODEL_NAME = $(shell $(REALPATH_RELATIVE_TO) $(MODELS_SRC_DIR) $(MODEL_DIR))

# モデル設定ファイル名
MODEL_CONFIG = config.toml

# モデルの拡張子を除いたファイル名
MODEL_STEM = model

# モデルの PDF/SVG 用ファイル名
LAYOUT_STEM = $(MODEL_STEM).layout
# モデルの SMF (.mid) 用ファイル名
MIDI_STEM = $(MODEL_STEM).midi
# モデルの音楽イベント用ファイル名
EVENT_STEM = $(MODEL_STEM).event

# モデル PDF
CROPPED_PDF = $(LAYOUT_STEM).cropped.pdf
# モデル SVG
CROPPED_SVG = $(MODEL_STEM).svg
# モデル SMF
MODEL_MID = $(MODEL_STEM).mid

# モデル PDF から得る CropBox とリンク情報のテキストファイル
LINK_TEXT = $(LAYOUT_STEM).cropped.link.txt
# モデルの音楽イベント一覧のテキストファイル
NOTES_TEXT = $(EVENT_STEM)-unnamed-staff.notes

# モデルの tick 音符座標リスト
LIST_TEXT = $(MODEL_STEM).list.txt

# テスト用評価対象 SMF
FOREVALS_MID = $(addsuffix .mid, $(FOREVALS))

# テスト用評価対象 PDF
FOREVALS_PDF = $(addsuffix .pdf, $(FOREVALS))


# .ly 中間ファイル
INTERMEDIATE_LY = $(LAYOUT_STEM).ly $(MIDI_STEM).ly $(EVENT_STEM).ly

# テスト用評価対象 .ly
FOREVALS_LY = $(filter-out $(INTERMEDIATE_LY) $(MODEL_STEM).ly, \
	$(wildcard *.ly))

# テスト用評価対象 SMF
FOREVALS_MID = $(FOREVALS_LY:.ly=.mid)

# テスト用評価対象 PDF
FOREVALS_PDF = $(FOREVALS_LY:.ly=.pdf)


# 後で不要となる中間ファイル
TARGET_INTERMEDIATE = $(INTERMEDIATE_LY) \
	$(CROPPED_PDF) \
	$(LINK_TEXT) $(NOTES_TEXT)

# ターゲットのうちユーザに見せる（static ディレクトリに入れる）もの
TARGET_STATIC_MODEL = $(CROPPED_SVG)

# ターゲットのうちシステムだけが使うもの
TARGET_MODEL = $(MODEL_MID) $(LIST_TEXT)

# 間違い表示 SVG の生成に必要なターゲット
TARGET = $(TARGET_STATIC_MODEL) $(TARGET_MODEL)

# テスト用評価対象ターゲット
TARGET_TEST = $(FOREVALS_MID) $(FOREVALS_PDF)

# インストールファイルのうちユーザに見せる（static ディレクトリに入れる）もの
INSTALL_STATIC_MODEL = $(TARGET_STATIC_MODEL)

# インストールファイルのうちシステムだけが使うもの
INSTALL_MODEL = $(TARGET_MODEL) $(MODEL_CONFIG)


all: $(TARGET_INTERMEDIATE) $(TARGET) $(TARGET_TEST)

.PHONY: all clean install uninstall

clean:
	$(RM) *~ $(TARGET_INTERMEDIATE) $(TARGET) $(TARGET_TEST)

install: $(TARGET)
	$(INSTALL) -d $(DEST_STATIC_MODELS_DIR)/$(MODEL_NAME)
	$(INSTALL_DATA) $(INSTALL_STATIC_MODEL) \
		$(DEST_STATIC_MODELS_DIR)/$(MODEL_NAME)
	$(INSTALL) -d $(DEST_MODELS_DIR)/$(MODEL_NAME)
	$(INSTALL_DATA) $(INSTALL_MODEL) \
		$(DEST_MODELS_DIR)/$(MODEL_NAME)

uninstall:
	$(RM) $(addprefix $(DEST_MODELS_DIR)/$(MODEL_NAME)/, $(INSTALL_MODEL))
	-$(RMDIR_P) $(DEST_MODELS_DIR)/$(MODEL_NAME)/
	$(RM) $(addprefix $(DEST_STATIC_MODELS_DIR)/$(MODEL_NAME)/, \
		$(INSTALL_STATIC_MODEL))
	-$(RMDIR_P) $(DEST_STATIC_MODELS_DIR)/$(MODEL_NAME)/


# モデルの include 元となる .ly
$(LAYOUT_STEM).ly: $(LY_DIR)/$(LAYOUT_STEM).ly
	$(LN_S) $< $@
$(MIDI_STEM).ly: $(LY_DIR)/$(MIDI_STEM).ly
	$(LN_S) $< $@
$(EVENT_STEM).ly: $(LY_DIR)/$(EVENT_STEM).ly
	$(LN_S) $< $@

# LilyPond でクロップされた PDF を出力する
#
# PNG と非クロップ版 PDF も出力されてしまうので削除する。
%.cropped.pdf: %.ly
	$(LILYPOND) -dcrop --pdf $<
	$(RM) $*.cropped.png $*.pdf

# PDF から SVG を生成する
#
# Poppler 付属の pdftocairo を使用する。
# 文字はすべてアウトライン化される。
# 寸法や位置関係など PDF と完全一致した SVG が出力される。
# リンク等は消滅する（バージョンによって消滅しないかもしれないので要確認）。
%.svg: %.layout.cropped.pdf
	$(PDFTOCAIRO) -svg $< $@

# LilyPond で SMF (.mid) を出力する
#
# Linux や Cygwin ではデフォルト拡張子が .midi なので .mid を指定する。
%.mid: %.midi.ly
	$(LILYPOND) -dmidi-extension=mid $<
	$(MV) $*.midi.mid $@

# PDF の CropBox とリンク情報を出力する
%.link.txt: %.pdf
	$(SHOW_PDF_LINK) $< > $@

# LilyPond で音楽イベントを出力する
#
# 譜の名前を付けていないのでファイル名に `unnamed` が付く。
# 出力が上書きではなく追記になってしまうので一旦出力ファイルを消す。
# PDF が出力されるので削除する。
%-unnamed-staff.notes: %.ly
	$(RM) $@
	$(LILYPOND) $<
	$(RM) $*.pdf

# モデルの tick 音符座標リストを出力する
%.list.txt: %.mid %.layout.cropped.link.txt %.event-unnamed-staff.notes
	$(CREATE_TICK_NOTE_RECT_LIST) $^ $@

# LilyPond で評価対象 SMF と PDF を出力する
%.mid %.pdf: %.ly
	$(LILYPOND) -dmidi-extension=mid $<

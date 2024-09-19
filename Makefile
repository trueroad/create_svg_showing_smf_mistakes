# モデルの拡張子を除いたファイル名
MODEL_STEM = model
# 評価対象の拡張子を除いたファイル名
FOREVAL_STEM = foreval

# PDF 経由で生成するモデル SVG
CROPPED_PDF_SVG = $(MODEL_STEM).cropped.pdf.svg

# モデルの楽譜 PDF から得るCropBox とリンク情報のテキストファイル
LINK_TXT = $(MODEL_STEM).annot.cropped.link.txt

# モデル SMF (.mid)
MIDI_MID = $(MODEL_STEM).midi.mid

# モデルの音楽イベント一覧のテキストファイル
NOTES_TEXT = $(MODEL_STEM).event-unnamed-staff.notes


# モデルの tick 音符座標リスト
LIST_TEXT = $(MODEL_STEM).list.txt


# 評価対象 SMF (.mid)
FOREVAL_MID = $(FOREVAL_STEM).mid
# 評価対象の楽譜 PDF
FOREVAL_PDF = $(FOREVAL_STEM).pdf


# 間違い表示 SVG
MISTAKES_SVG = $(FOREVAL_STEM).mistakes.svg


PREPARE_TARGET = $(CROPPED_PDF_SVG) $(LINK_TXT) $(MIDI_MID) $(NOTES_TEXT) \
	$(LIST_TEXT) \
	$(FOREVAL_MID) $(FOREVAL_PDF)

TARGET = $(MISTAKES_SVG)

all: prepare $(TARGET)

prepare: $(PREPARE_TARGET)

.PHONY: all clean dist-clean prepare

SED = sed
LILYPOND = lilypond
PDFTOCAIRO = pdftocairo
SHOW_PDF_LINK = ./show_pdf_link.py
CREATE_TICK_NOTE_RECT_LIST = ./create_tick_note_rect_list.py
CREATE_SVG_SHOWING_SMF_MISTAKES = ./create_svg_showing_smf_mistakes.py

clean:
	$(RM) *~ $(TARGET)

dist-clean: clean
	$(RM) $(PREPARE_TARGET)

# PDF から SVG を生成する
#
# Poppler 付属の pdftocairo を使用する。
# 文字はすべてアウトライン化される。
# 寸法や位置関係など PDF と完全一致した SVG が出力される。
# リンク等は消滅する。
%.cropped.pdf.svg: %.cropped.pdf
	$(PDFTOCAIRO) -svg $< $@

# LilyPond でクロップされた PDF を出力する
#
# PNG と非クロップ版 PDF も出力されてしまうので削除する。
%.cropped.pdf: %.ly
	$(LILYPOND) -dcrop --pdf $<
	$(RM) $*.cropped.png $*.pdf

# LilyPond で SMF (.mid) を出力する
#
# Linux や Cygwin ではデフォルト拡張子が .midi なので .mid を指定する。
%.mid: %.ly
	$(LILYPOND) -dmidi-extension=mid $<

# LilyPond で音楽イベントを出力する
#
# 譜の名前を付けていないのでファイル名に `unnamed` が付く。
# 出力が上書きではなく追記になってしまうので一旦出力ファイルを消す。
# `\layout {}` が無くて補完されてしまい PDF が出力されるので削除する。
%-unnamed-staff.notes: %.ly
	$(RM) $@
	$(LILYPOND) $<
	$(RM) $*.pdf

# ポイント＆クリックを有効にした .ly を生成する
%.annot.ly: %.ly
	$(SED) -r \
		-e 's/\\pointAndClickOff/\\pointAndClickOn/' \
		$< > $@

# PDF を出力せずに SMF (.mid) を出力する .ly を生成する
%.midi.ly: %.ly
	$(SED) -r \
		-e 's/\\layout \{\}/% \\layout \{\}/' \
		-e 's/% \\midi \{\}/\\midi \{\}/' \
		$< > $@

# 音楽イベントを出力し（event-listener.ly をインクルードする）
# ポイント＆クリックを有効にし、
# PDF を出力しない .ly を生成する。
%.event.ly: %.ly
	$(SED) -r \
		-e 's/%%% INCLUDE %%%/\\include "event-listener.ly"/' \
		-e 's/\\pointAndClickOff/\\pointAndClickOn/' \
		-e 's/\\layout \{\}/% \\layout \{\}/' \
		$< > $@

# PDF の CropBox とリンク情報を出力する
%.link.txt: %.pdf
	$(SHOW_PDF_LINK) $< > $@

# モデルの tick 音符座標リストを出力する
%.list.txt: %.midi.mid %.annot.cropped.link.txt %.event-unnamed-staff.notes
	$(CREATE_TICK_NOTE_RECT_LIST) $^ $@

# LilyPond で評価対象 SMF と PDF を出力する
%.mid %.pdf: %.ly
	$(LILYPOND) -dmidi-extension=mid $<

# 間違い表示 SVG を出力する
$(MISTAKES_SVG): $(LIST_TEXT) $(MIDI_MID) $(FOREVAL_MID)
	$(CREATE_SVG_SHOWING_SMF_MISTAKES) $^ $@

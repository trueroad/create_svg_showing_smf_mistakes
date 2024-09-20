# モデルの拡張子を除いたファイル名
MODEL_STEM = model
# 評価対象の拡張子を除いたファイル名
FOREVAL_STEM = foreval

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

# 評価対象 SMF
FOREVAL_MID = $(FOREVAL_STEM).mid
# 評価対象 PDF
FOREVAL_PDF = $(FOREVAL_STEM).pdf

# 間違い表示 SVG
MISTAKES_SVG = $(FOREVAL_STEM).mistakes.svg


# prepare 後は不要となる中間ファイル
INTERMEDIATE_TARGET = $(CROPPED_PDF) \
	$(LINK_TEXT) $(NOTES_TEXT)

# 間違い表示 SVG の生成に必要なファイル
PREPARE_TARGET = $(CROPPED_SVG) $(MODEL_MID) \
	$(LIST_TEXT) \
	$(FOREVAL_MID) $(FOREVAL_PDF)

# 最終ターゲット：foreval.mid から間違い表示 SVG を生成する
TARGET = $(MISTAKES_SVG)

all: prepare $(TARGET)

#intermediate: $(INTERMEDIATE_TARGET)
prepare: $(PREPARE_TARGET)

.PHONY: all clean dist-clean prepare

SED = sed
MV = mv
LILYPOND = lilypond
PDFTOCAIRO = pdftocairo
SHOW_PDF_LINK = ./show_pdf_link.py
CREATE_TICK_NOTE_RECT_LIST = ./create_tick_note_rect_list.py
CREATE_SVG_SHOWING_SMF_MISTAKES = ./create_svg_showing_smf_mistakes.py

clean:
	$(RM) *~ $(TARGET)

dist-clean: clean
	$(RM) $(INTERMEDIATE_TARGET) $(PREPARE_TARGET)


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

# 間違い表示 SVG を出力する
$(MISTAKES_SVG): $(LIST_TEXT) $(MODEL_MID) $(FOREVAL_MID)
	$(CREATE_SVG_SHOWING_SMF_MISTAKES) $^ $@

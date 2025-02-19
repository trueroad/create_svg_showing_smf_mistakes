LILYPOND = lilypond
PDFTOCAIRO = pdftocairo

SHOW_PDF_LINK = $(SCRIPT_DIR)/show_pdf_link.py
CREATE_TICK_NOTE_RECT_LIST = $(SCRIPT_DIR)/create_tick_note_rect_list.py
BUILD_MODEL_MAKEFILE = $(SCRIPT_DIR)/build_model_makefile.py
BUILD_MODELS_JSON = $(SCRIPT_DIR)/build_models_json.py

MV = mv
LN_S = ln -s
RMDIR = rmdir
RMDIR_P = rmdir -p
INSTALL = install
INSTALL_DATA = $(INSTALL) -m 644
REALPATH_RELATIVE_TO = realpath --relative-to
FIND = find
TAR = tar
TAR_CVA_F = $(TAR) -cva -f
TIMIDITY_48K_MONO = timidity \
	--volume-compensation \
	-s 48000 -Ow --output-mono \
	--output-signed --output-16bit --output-linear
FFMPEG = ffmpeg
FFMPEG_OPTION_WEBM_OPUS = \
	-hide_banner \
	-y \
	-vn \
	-codec:a libopus \
	-b:a 96K \
	-application audio \
	-f webm

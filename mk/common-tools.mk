LILYPOND = lilypond
PDFTOCAIRO = pdftocairo

SHOW_PDF_LINK = $(SCRIPT_DIR)/show_pdf_link.py
CREATE_TICK_NOTE_RECT_LIST = $(SCRIPT_DIR)/create_tick_note_rect_list.py
BUILD_MODEL_MAKEFILE = $(SCRIPT_DIR)/build_model_makefile.py

MV = mv
LN_S = ln -s
RMDIR_P = rmdir -p
INSTALL = install
INSTALL_DATA = $(INSTALL) -m 644
REALPATH_RELATIVE_TO = realpath --relative-to
FIND = find

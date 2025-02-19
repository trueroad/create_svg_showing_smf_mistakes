include mk/common-dirs.mk
include mk/common-tools.mk

# モデル SMF
MODEL_MID = models/test/model.mid
# モデルの tick 音符座標リスト
LIST_TEXT = models/test/model.list.txt
# モデル設定ファイル
MODEL_CONFIG = models/test/config.toml

# 評価対象 SMF
FOREVAL_MID = models_src/test/foreval.mid

# 間違い表示 SVG
MISTAKES_SVG = foreval.mistakes.svg

# 最終ターゲット：foreval.mid から間違い表示 SVG を生成する
TARGET = $(MISTAKES_SVG)

all: prepare $(TARGET)

prepare: $(MODEL_MID) $(LIST_TEXT) $(MODEL_CONFIG) $(FOREVAL_MID)

.PHONY: all clean prepare \
	models-intermediate-tarball models-tarball \
	clean-post

CREATE_SVG_SHOWING_SMF_MISTAKES = ./create_svg_showing_smf_mistakes.py

$(FOREVAL_MID):
	$(MAKE) -C models_src

$(MODEL_MID) $(LIST_TEXT) $(MODEL_CONFIG) &: $(FOREVAL_MID)
	$(MAKE) -C models_src install


clean:
	$(RM) *~ $(TARGET)

# 間違い表示 SVG を出力する
$(MISTAKES_SVG): $(LIST_TEXT) $(MODEL_MID) $(MODEL_CONFIG) $(FOREVAL_MID)
	$(CREATE_SVG_SHOWING_SMF_MISTAKES) \
		$(MODEL_CONFIG) $(FOREVAL_MID) \
		$@


models-intermediate-tarball:
	$(TAR_CVA_F) models-intermediate.tar.zst models_src/

models-tarball:
	$(TAR_CVA_F) models.tar.zst static/models/ models/

clean-post:
	-$(RM) post.bin
	-$(RM) temp_*.mid
	-$(RM) temp_*.svg

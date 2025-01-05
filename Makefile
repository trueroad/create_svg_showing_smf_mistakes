# モデル SMF
MODEL_MID = models/test/model.mid
# モデルの tick 音符座標リスト
LIST_TEXT = models/test/model.list.txt

# 評価対象 SMF
FOREVAL_MID = models_src/test/foreval.mid

# 間違い表示 SVG
MISTAKES_SVG = foreval.mistakes.svg

# 最終ターゲット：foreval.mid から間違い表示 SVG を生成する
TARGET = $(MISTAKES_SVG)

all: prepare $(TARGET)

prepare: $(MODEL_MID) $(LIST_TEXT) $(FOREVAL_MID)

.PHONY: all clean prepare

CREATE_SVG_SHOWING_SMF_MISTAKES = ./create_svg_showing_smf_mistakes.py

$(MODEL_MID) $(LIST_TEXT) $(FOREVAL_MID):
	$(MAKE) -C models_src
	$(MAKE) -C models_src install


clean:
	$(RM) *~ $(TARGET)

# 間違い表示 SVG を出力する
$(MISTAKES_SVG): $(LIST_TEXT) $(MODEL_MID) $(FOREVAL_MID)
	$(CREATE_SVG_SHOWING_SMF_MISTAKES) $^ $@

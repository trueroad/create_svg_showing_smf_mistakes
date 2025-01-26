/**
 * Test common
 * @module test_common
 * @author Masamichi Hosoda <trueroad@trueroad.jp>
 * @copyright (C) Masamichi Hosoda 2025
 * @license BSD-2-Clause
 * @see {@link https://github.com/trueroad/create_svg_showing_smf_mistakes}
 */

//
// API URL
//

export const postUrl = "../midi/diffsvg";
const modelsJsonUrl = "models/models.json";

//
// Element ID
//

// Button
const loadButton = document.getElementById("loadButton");
const clearButton = document.getElementById("clearButton");

// Select
const modelSelect = document.getElementById("modelSelect");

// Div
const imagesDiv = document.getElementById("imagesDiv");

// Img
const modelImg = document.getElementById("modelImg");
export const mistakesImg = document.getElementById("mistakesImg");

// Input
export const modelName = document.getElementById("modelName");

// Textarea
export const postResult = document.getElementById("postResult");

//
// UI function
//

// load時にblobのURLをrevokeして解放する
export function revokeMistakeURL() {
  console.log("revokeMistakeURL");

  URL.revokeObjectURL(mistakesImg.src);
  // あわせてイベントリスナを外す
  // （外さないとblob由来でない解放不要URLのloadでも呼ばれてしまう）
  mistakesImg.removeEventListener("load", revokeMistakeURL);
}

// モデルをロードする
function clickLoadButton() {
  console.log("clickLoadButton");

  // 表示差分をクリアする
  clickClearButton();

  // モデル名を取得してモデルSVGを設定
  const name = modelName.value;
  modelImg.src = `models/${name}/model.svg`

  // イベントリスナでloadされたら高さ調整が走る

  console.log("clickLoadButton done");
}

// 差分表示をクリアする
function clickClearButton() {
  console.log("clickClearButton");

  // 何も描画しないSVGをblobに用意する
  const spacer_svg = `<svg xmlns="http://www.w3.org/2000/svg"
     width="1" height="1" viewBox="0 0 1 1" />`;
  const blob = new Blob([spacer_svg],
                        {type: "image/svg+xml"});
  // blobからURLを作る
  mistakesImg.src = URL.createObjectURL(blob);
  // loadされたらURLを解放する関数を登録
  mistakesImg.addEventListener("load", revokeMistakeURL);

  console.log("clickClearButton done");
}

// 楽譜表示部の子要素の高さを親要素にそのまま設定する
// position: relativeにしている親要素はそのままだと高さがゼロなので、
// その下にある要素が重なって見えてしまう。
// 高さを設定してやればよいのだが、
// CSSでは子要素の高さに応じた設定ができない。
// そこでJavaScriptで子要素の高さを取得して親要素に設定してやる。
function setImagesDivHeight() {
  console.log("setImagesDivHeight");

  const rect = modelImg.getBoundingClientRect();
  imagesDiv.style.height = rect.height + "px";
  imagesDiv.style.width = rect.width + "px";
}

// 楽譜選択のプルダウンボックスを設定する
function setupModelSelect() {
  console.log("setupModelSelect");

  fetch(modelsJsonUrl)
    .then((resp) => {
      console.log("resp.ok: ", resp.ok);
      console.log("resp.status: ", resp.status);
      console.log("resp.statusText: ", resp.statusText);
      if(!resp.ok) {
        // 通信は成功したがコードが不成功だったので後段のエラー処理へ投げる
        throw new Error(`${resp.status} ${resp.statusText}`);
      }
      // レスポンスをJSONとして取り出して次に渡す
      return resp.json();
    })
    .then((resp_json) => {
      console.log(resp_json);

      for (const phrase of resp_json["phrase_list"]) {
        console.log(phrase);

        let option = document.createElement("option");
        option.text = phrase["title"];
        option.value = phrase["name"];
        modelSelect &&
          modelSelect.appendChild(option);
      }
    })
    .catch((reason) => {
      // エラー発生
      console.error(reason);
    });
}

// 楽譜選択のプルダウンボックスが変更された
function changeModelSelect() {
  console.log("changeModelSelect");

  // 選択された値を読み込んでテキストボックスを上書き、自動でロードする
  const value = modelSelect.value;
  if (value != "") {
    modelName.value = value;
    clickLoadButton();
  }
}

//
// Add event listener
//

loadButton &&
  loadButton.addEventListener("click", clickLoadButton);
clearButton &&
  clearButton.addEventListener("click", clickClearButton);
modelImg &&
  modelImg.addEventListener("load", setImagesDivHeight);
modelSelect &&
  modelSelect.addEventListener("change", changeModelSelect);

setupModelSelect();

modelImg.style.transformOrigin = "0 0";
modelImg.style.transform = "scale(1.0) ";
mistakesImg.style.transformOrigin = "0 0";
mistakesImg.style.transform = "scale(1.0) ";

if (modelImg.complete) {
  // モデルSVGの読み込みが完了済なら高さ調整を呼ぶ
  // （未完了ならイベントリスナでload時に呼ばれる）
  console.log("modelImg.complete true")
  setImagesDivHeight();
}

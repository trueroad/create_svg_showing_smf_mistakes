/**
 * Test common
 * @module test_common
 * @author Masamichi Hosoda <trueroad@trueroad.jp>
 * @copyright (C) Masamichi Hosoda 2025
 * @license BSD-2-Clause
 * @see {@link https://github.com/trueroad/create_svg_showing_smf_mistakes}
 */

//
// Element ID
//

// Button
const loadButton = document.getElementById("loadButton");
const clearButton = document.getElementById("clearButton");

// Div
const imagesDiv = document.getElementById("imagesDiv");

// Img
const modelImg = document.getElementById("modelImg");
export const mistakesImg = document.getElementById("mistakesImg");

// Input
export const forevalName = document.getElementById("forevalName");

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

  // モデル名を取得してモデルSVGを設定
  const name = forevalName.value;
  modelImg.src = `models/${name}/model.svg`

  // イベントリスナでloadされたら高さ調整が走る

  console.log("clickLoadButton done");
}

// 差分表示をクリアする
function clickClearButton() {
  console.log("clickClearButton");

  // 何も描画しないSVGをblobに用意する
  const blob = new Blob([`<svg xmlns="http://www.w3.org/2000/svg"
     width="1" height="1" viewBox="0 0 1 1" />`
                        ],
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

  imagesDiv.style.height = modelImg.offsetHeight + "px";
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

if (modelImg.complete) {
  // モデルSVGの読み込みが完了済なら高さ調整を呼ぶ
  // （未完了ならイベントリスナでload時に呼ばれる）
  console.log("modelImg.complete true")
  setImagesDivHeight();
}

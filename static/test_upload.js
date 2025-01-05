/**
 * Test upload SMF
 * @module test_upload
 * @author Masamichi Hosoda <trueroad@trueroad.jp>
 * @copyright (C) Masamichi Hosoda 2025
 * @license BSD-2-Clause
 * @see {@link https://github.com/trueroad/create_svg_showing_smf_mistakes}
 */

import {
  mistakesImg, forevalName, postResult, revokeMistakeURL
} from "./test_common.js";

//
// Element ID
//

// Button
const diffButton = document.getElementById("diffButton");

// Input
const forevalFile = document.getElementById("forevalFile");

//
// UI function
//

// 選択された評価対象SMFをアップロードして差分SVGを取得し表示する
function clickDiffButton() {
  console.log("clickDiffButton");

  // 選択されたファイルを取得する
  const fileList = forevalFile.files;
  console.log(fileList);
  if(fileList.length == 0) {
    console.log("No file selected");
    postResult.textContent = "No file selected";
    return;
  }
  const file = fileList[0];
  console.log(file);

  // フォームを作成して選択されたファイルとモデル名を格納する
  const formData = new FormData();
  formData.append("foreval", file, "foreval.mid");
  formData.append("name", forevalName.value);

  // APIへ作成したフォームをPOSTする
  fetch("../midi/diffsvg", {method: "POST", body: formData})
    .then((resp) => {
      // POSTレスポンスのチェックと加工
      console.log("resp.ok: ", resp.ok);
      console.log("resp.status: ", resp.status);
      console.log("resp.statusText: ", resp.statusText);
      if(!resp.ok) {
        // 通信は成功したがコードが不成功だったので後段のエラー処理へ投げる
        throw new Error(`${resp.status} ${resp.statusText}`);
      }
      // レスポンスをフォームとして取り出して次に渡す
      return resp.formData();
    })
    .then((resp_form) => {
      // フォームからSVGとJSONを取り出して処理
      console.log(resp_form);
      const diffsvg = resp_form.get("diffsvg");
      const jsondata = resp_form.get("json");
      console.log(diffsvg);
      console.log(jsondata);

      // SVGのblobからURLを作る
      mistakesImg.src = URL.createObjectURL(diffsvg);
      // loadされたらURLを解放する関数を登録
      mistakesImg.addEventListener("load", revokeMistakeURL);

      // JSONのblobをパースして結果表示する
      jsondata.text()
        .then((text) => {
          const j = JSON.parse(text)
          console.log(j);
          postResult.textContent = JSON.stringify(j);
        })
    })
    .catch((reason) => {
      // エラー発生
      console.error(reason);
      // エラー内容を結果表示する
      postResult.textContent = reason;
    });

  console.log("clickDiffButton done");
}

//
// Add event listener
//

diffButton &&
  diffButton.addEventListener("click", clickDiffButton);

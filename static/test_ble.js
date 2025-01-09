/**
 * Test BLE-MIDI
 * @module test_ble
 * @author Masamichi Hosoda <trueroad@trueroad.jp>
 * @copyright (C) Masamichi Hosoda 2023, 2025
 * @license BSD-2-Clause
 * @see {@link https://github.com/trueroad/create_svg_showing_smf_mistakes}
 */

import {BleMidiDevice} from "./tr-MidiJS/BleMidiDevice.js";
import {MidiFilter} from "./tr-MidiJS/MidiFilter.js";
import {GapDetector} from "./tr-MidiJS/GapDetector.js";
import {SmfEncoder} from "./tr-MidiJS/SmfEncoder.js";
import {getISOStringTZ} from "./getISOStringTZ.js";

import {
  mistakesImg, forevalName, postResult, postUrl, revokeMistakeURL
} from "./test_common.js";

/**
 * BleMidiDevice class instance.
 * @type {module:BleMidiDevice.BleMidiDevice}
 */
export const bleMidiDevice = new BleMidiDevice();

/**
 * MidiFilter class instance.
 * @type {module:MidiFilter.MidiFilter}
 */
export const midiFilter = new MidiFilter();

/**
 * GapDetector class instance.
 * @type {module:GapDetector.GapDetector}
 */
export const gapDetector = new GapDetector();

/**
 * SmfEncoder class instance.
 * @type {module:SmfEncoder.SmfEncoder}
 */
export const smfEncoder = new SmfEncoder();

//
// Element ID
//

// Button
const selectStartButton = document.getElementById("selectStartButton");
const stopButton = document.getElementById("stopButton");

// Status span
const statusSpan = document.getElementById("statusSpan");

//
// Handler
//

/**
 * Handler function to be called when the value is changed.
 * @param {number} timeStamp - Timestamp in millisecond.
 * @param {ArrayBuffer} value - Changed value.
 */
function handlerValueChanged(timeStamp, value) {
  // Pass through to MIDI decoder
  bleMidiDevice.bleMidiPacket.decode(timeStamp, value);
}

// Set the sample handler function.
bleMidiDevice.handlerValueChanged = handlerValueChanged;

/**
 * Handler function to be called
 *     when a MIDI message (fragmented) is decoded.
 * @param {number} delta - Delta time in millisecond.
 * @param {Uint8Array} message - MIDI message (fragmented).
 */
function handlerMidiMessageDecoded(delta, message) {
  // Pass through to MIDI reassembler
  bleMidiDevice.bleMidiPacket.reassemble(delta, message);
}

// Set the sample handler function.
bleMidiDevice.bleMidiPacket.handlerMidiMessageDecoded =
  handlerMidiMessageDecoded;

/**
 * Handler function to be called
 *     when fragmented MIDI messages are reassembled.
 * @param {number} delta - Delta time in millisecond.
 * @param {Uint8Array} message - MIDI message (reassembled).
 */
function handlerMidiMessageReassembled(delta, message) {
  // Pass through to MIDI filter
  midiFilter.filter(delta, message);
}

// Set the handler function.
bleMidiDevice.bleMidiPacket.handlerMidiMessageReassembled =
  handlerMidiMessageReassembled;

/**
 * Handler function to be called
 *     when a MIDI message is filtered.
 * @param {number} delta - Delta time in millisecond.
 * @param {Uint8Array} message - MIDI message (filtered).
 */
function handlerMidiMessageFiltered(delta, message) {
  // Gap detection
  gapDetector.detect(delta, message);

  // Logging
  console.log(JSON.stringify({"delta": delta,
                              "message": Array.from(message)}));

  // Pass through to SMF encoder
  smfEncoder.encode(delta, message);
}

// Set the handler function.
midiFilter.handlerMidiMessageFiltered =
  handlerMidiMessageFiltered;

/**
 * Handler function to be called when a gap is detected.
 */
function HandlerGapDetected() {
  console.log("*** Gap detected ***");
  _post_smf();
}

// Set the handler function.
gapDetector.handlerGapDetected = HandlerGapDetected;

/**
 * POST divided SMF.
 * @private
 */
async function _post_smf() {
  // Builds an SMF from buffer containing arrived MIDI messages.
  const blob = smfEncoder.build();

  // Clear the buffer.
  // Subsequent incoming messages will be stored in the next SMF.
  smfEncoder.initialize();
  const text = JSON.stringify({"Module": "BleMidiDevice.js",
                               "Device": bleMidiDevice.getDeviceName(),
                               "User-Agent": navigator.userAgent,
                               "Language": navigator.language,
                               "Location": location.href,
                               "Date": getISOStringTZ(recordingDateTime)});
  smfEncoder.meta_text(0, 1, text);

  // Builds a form from the built SMF.
  const formData = new FormData();
  formData.append("foreval", blob, "foreval.mid");
  formData.append("name", forevalName.value);

  try {
    const resp = await fetch(postUrl, {method: 'POST', body: formData});
    if (resp.status !== 200) {
      postResult.value = resp.status + " " + resp.statusText;
    } else {
      const resp_form = await resp.formData();

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
    }
  } catch (err) {
    postResult.value = err;
  }
}

//
// UI function
//

/** Recording date time */
let recordingDateTime;

async function selectStart() {
  if (bleMidiDevice.isConnected()) {
    statusSpan.innerText = "disconnecting...";
    try {
      await bleMidiDevice.disconnect();
    } catch (err) {
      statusSpan.innerText = err;
      return;
    }
  }

  statusSpan.innerText = "initializing...";

  bleMidiDevice.bleMidiPacket.initializeDecoder();
  bleMidiDevice.bleMidiPacket.initializeReassembler();
  midiFilter.initialize();
  smfEncoder.initialize();

  statusSpan.innerText = "selecting...";

  try {
    await bleMidiDevice.select();
  } catch (err) {
    statusSpan.innerText = err;
    return;
  }

  statusSpan.innerText = "connecting...";

  try {
    await bleMidiDevice.connect();
  } catch (err) {
    statusSpan.innerText = err;
    return;
  }

  statusSpan.innerText = "starting...";

  bleMidiDevice.bleMidiPacket.initializeDecoder();
  bleMidiDevice.bleMidiPacket.initializeReassembler();
  midiFilter.initialize();
  smfEncoder.initialize();

  recordingDateTime = new Date();
  const text = JSON.stringify({"Module": "BleMidiDevice.js",
                               "Device": bleMidiDevice.getDeviceName(),
                               "User-Agent": navigator.userAgent,
                               "Language": navigator.language,
                               "Location": location.href,
                               "Date": getISOStringTZ(recordingDateTime)});
  smfEncoder.meta_text(0, 1, text);

  bleMidiDevice.bleMidiPacket.setWaitUntilStable(true);

  try {
    await bleMidiDevice.start();
  } catch (err) {
    statusSpan.innerText = err;
    return;
  }

  bleMidiDevice.bleMidiPacket.startWaitUntilStableTimeout();

  stopButton.removeAttribute("disabled");
  statusSpan.innerText = "Recording...";
}

async function stop() {
  statusSpan.innerText = "stopping...";

  try {
    await bleMidiDevice.stop();
  } catch (err) {
    statusSpan.innerText = err;
    return;
  }

  if (!gapDetector.isInGap()) {
    _post_smf();
  }

  stopButton.setAttribute("disabled", true);
  statusSpan.innerText = "Stopped.";
}

//
// Add event listener
//

selectStartButton &&
  selectStartButton.addEventListener("click", selectStart);
stopButton &&
  stopButton.addEventListener("click", stop);

window.addEventListener("beforeunload", stop);

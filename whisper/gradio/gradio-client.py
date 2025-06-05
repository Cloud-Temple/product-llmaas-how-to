"""
@misc{radford2022whisper,
  doi = {10.48550/ARXIV.2212.04356},
  url = {https://arxiv.org/abs/2212.04356},
  author = {Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya},
  title = {Robust Speech Recognition via Large-Scale Weak Supervision},
  publisher = {arXiv},
  year = {2022},
  copyright = {arXiv.org perpetual, non-exclusive license}
}
"""

# import logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger("gradio")
# logger.setLevel(logging.DEBUG)
# logger = logging.getLogger("websockets")
# logger.setLevel(logging.DEBUG)

import gradio as gr
import requests
import numpy as np
from pydub import AudioSegment
import io
import queue
import json, time


class AudioProcessor:
    # curl --request POST --url 'http://80.75.153.201:8000/asr/' -F "file=@test.wav"

    #  curl -X 'POST' 'https://api.ai.cloud-temple.com/v1/audio/transcriptions' -H 'Authorization: Bearer G3H4I5J6K7L8M9N0O1P2Q3R4S5T6U7V8W9X0Y1Z2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4' -F 'file=@test_audio.wav;type=audio/x-wav' \
    # -H 'accept: application/json' \
    # -H 'Content-Type: multipart/form-data' \
    # -F 'language=fr' \
    # -F 'response_format=json' \
    # -F 'temperature=0'

    def __init__(self, server_url="https://api.ai.cloud-temple.com/v1/audio/transcriptions"):
        self.server_url = server_url
        self.audio_queue = queue.Queue()
        self.is_processing = False
        self.current_text = ""

    def process_audio_chunk(self, audio_chunk, sample_rate):
        byte_io = io.BytesIO()
        audio_segment = AudioSegment(audio_chunk.tobytes(), frame_rate=sample_rate * 2, sample_width=2, channels=1)  # was 16000
        # # Export to file
        # filename = f"chunk_{time.time()}.wav"
        # audio_segment.export(filename, format="wav")

        # Export to server
        audio_segment.export(byte_io, format="wav")
        files = {"file": ("chunk.wav", byte_io.getvalue())}
        response = requests.post(self.server_url, files=files)
        if response.status_code == 200:
            j = response.json()
            if len(j["segments"]) > 0:
                return j["text"], j["segments"][0]["avg_logprob"], j["segments"][0]["no_speech_prob"]
            else:
                return "no segments", 0, 1
        return "status_code " + str(response.status_code), 0, 1


processor = AudioProcessor()

arrays = []
history = []


def process_audio(audio) -> str:
    global arrays
    global history

    if len(audio) == 0:
        return state

    sample_rate, one_chunk = audio
    arrays.append(np.array(one_chunk))

    t0 = time.time()
    all_chunks = np.concatenate(arrays)
    # print(type(arrays), type(all_chunks)) # <class 'list'> <class 'numpy.ndarray'>
    text, logprob, no_speech = processor.process_audio_chunk(all_chunks, sample_rate)
    # print("\tlen(all_chunks)", len(all_chunks), "\n\tlogprob:", logprob,"\n\tno_speech:", no_speech,"\n\ttext:", text, "\n\n")
    t1 = time.time()
    print("abs", t0 - t1, "ponderized", (t0 - t1) / len(all_chunks))

    if no_speech < 0.15:  # FIXME : Magic value.
        arrays = []
        history.append(text)
    if len(arrays) >= 10:
        arrays.pop(0)  # The oldest chunck is remove, to keep the inputs not so large.

    # Returning history avoiding too mush concatenation.
    if len(history) > 1:
        out = " ".join(history)
        history = [out]
        return out
    if len(history) == 0:
        return ""
    else:
        return history[0]


with gr.Blocks() as demo:
    audio_input = gr.Audio(sources=["microphone"], streaming=True)
    text_output = gr.Textbox()

    audio_input.stream(process_audio, inputs=audio_input, outputs=text_output)


print("Startup queue")
demo.queue()
demo.launch()
# demo.launch(debug=True)

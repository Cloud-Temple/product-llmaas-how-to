# 🤖 Qwen3-Omni Multimodal Demo

This project provides a complete example of using the **Qwen3-Omni** model via the LLMaaS API.
It highlights the model's multimodal capabilities, specifically handling direct audio and video streams via the Chat Completions API.

## 🌟 Features

- **Audio-to-Text**: Sending an audio file (URL) and receiving a text response (translation, transcription, reply).
- **Video-to-Text**: Sending a video file (URL) and receiving a description or analysis.
- **OpenAI Client**: Uses the standard Python `openai` library, demonstrating API compatibility.
- **Rich Output**: Uses `rich` for a modern console rendering.

## 📋 Prerequisites

- **Python 3.10** or higher.
- Network access to the LLMaaS API (`api.ai.cloud-temple.com` or internal endpoint).
- A valid API Key.

## 🚀 Installation

1. **Clone the repository** (or copy this folder).

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and modify variables:
   - `API_ENDPOINT`: API URL. Default is production (`https://api.ai.cloud-temple.com/v1`). For a direct internal test, use the server IP (`https://172.16.0.17:8000/v1`).
   - `API_KEY`: Your API Key.
   - `SSL_VERIFY`: `true` for production, `false` for self-signed dev/internal environments.

## 🎮 Usage

Simply run the main script:

```bash
python3 qwen-omni-demo.py
```

The script will sequentially execute:
1.  An audio test (Chinese -> English translation).
2.  A video test (Drawing scene description).

## 🧩 Project Structure

```text
exemples/qwen_omni_demo/
├── .env.example       # Configuration template
├── qwen-omni-demo.py  # Main script (API Client)
├── README.md          # Documentation (FR)
├── README_EN.md       # Documentation (EN)
└── requirements.txt   # Python dependencies
```

## ⚠️ Troubleshooting

- **502 Bad Gateway Error**:
  - Check that the LLM Proxy on the target server has been updated to support `audio_url` and `video_url` fields (See RFC-0047).
  - If you are using the public Load Balancer, ensure it does not filter these fields.

- **401 Unauthorized Error**:
  - Check your `API_KEY` in the `.env` file.

# PhotoAnalyzer - Multimodal Image Analysis

PhotoAnalyzer is a powerful CLI tool for image analysis using the LLMaaS API with state-of-the-art multimodal models like **Qwen3-VL** and **Qwen3-Omni**.

## 🚀 Features

- **Detailed Analysis**: Precise description of content, objects, people, and atmosphere.
- **Advanced Multimodal Support**: Compatible with the latest vision models (`qwen3-vl`, `qwen3-omni`).
- **Specialized Prompts**: Predefined analysis modes (technical, emotions, security, medical, etc.).
- **Flexible Formats**: Supports JPG, PNG, WEBP.
- **Structured Output**: Neat terminal display and text file export.

## 🛠️ Installation

1.  **Prerequisites**: Python 3.8+ installed.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configuration**:
    Copy the example `.env` file (if present) or configure your keys via `config.json` or environment variables.
    ```bash
    # .env example
    LLMAAS_API_URL=https://api.ai.cloud-temple.com/
    LLMAAS_API_KEY=your_api_key_here
    ```

## 📖 Usage

### Simple Analysis
```bash
python photoanalyzer.py images/bird.png
```

### Model Selection
Use **Qwen3** models for better performance:
```bash
# Lightweight default model
python photoanalyzer.py images/bird.png --model qwen3-vl:8b

# Very powerful model (recommended)
python photoanalyzer.py images/bird.png --model qwen3-omni:30b
```

### Analysis Types
Use the `-t` option to target the analysis:
```bash
# Technical analysis (composition, light)
python photoanalyzer.py images/journal.png -t technical

# Emotion analysis
python photoanalyzer.py images/woman.jpg -t emotions

# Text transcription (contextual OCR)
python photoanalyzer.py document.jpg -t text
```

### Advanced Options
- **Save**: `-o result.txt` to save the output.
- **Custom Prompt**: `-p "Find all errors in this electrical diagram"` (overrides analysis type).
- **Silent Mode**: `--silent` to display only the raw result (useful for pipes).
- **Debug**: `--debug` to see API request details.

## 🤖 Supported Models

- **`qwen3-vl:8b`**: Fast and efficient for most tasks.
- **`qwen3-omni:30b`**: Very high precision, excellent understanding of details and complex context.
- **`granite3.2-vision:2b`**: Ultra-lightweight for simple analyses.

## 📁 Project Structure

- `photoanalyzer.py`: Main CLI script.
- `api_utils.py`: API call management (OpenAI Vision compatible).
- `image_utils.py`: Image processing and validation.
- `cli_ui.py`: User interface management (Rich).

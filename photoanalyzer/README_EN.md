# PhotoAnalyzer - Multimodal Image Analyzer

PhotoAnalyzer is an advanced Python CLI tool for image analysis using the LLMaaS API with multimodal models. It offers a polished user interface with debug modes, multiple output formats, and support for various specialized analysis prompt types.

## 🚀 Key Features

### Advanced Multimodal Analysis
- **12 predefined analysis types**: general, technical, people, objects, scene, colors, composition, emotions, text, security, medical, count
- **Custom prompts**: Support for custom prompts for specific analyses
- **Automatic content detection**: Prompt optimization based on the detected image type

### Robust Image Management
- **Supported formats**: JPEG, PNG, GIF, BMP, TIFF, WebP
- **Full validation**: Format, size, dimensions verification
- **Automatic optimization**: Smart resizing and compression
- **Detailed information**: Metadata, EXIF, transparency, animation

### Advanced User Interface
- **Exhaustive debug mode**: Detailed processing information
- **Silent mode**: Clean output for redirection
- **Colored display**: Rich interface with formatted panels
- **Integrated help**: Complete documentation of options

### Flexible Configuration
- **JSON file**: Centralized configuration via `config.json`
- **Environment variables**: `.env` support for sensitive parameters
- **CLI arguments**: Full override via command line
- **Automatic saving**: Smart filename generation

## 📋 Prerequisites

- Python 3.8 or higher
- Access to the Cloud Temple LLMaaS API
- Available multimodal models (e.g., `qwen2.5-vl:7b`)

## 🛠️ Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure authentication**:
   ```bash
   # Option 1: Environment variables
   cp .env.example .env
   # Edit .env with your actual values
   
   # Option 2: Configuration file
   cp config.example.json config.json
   # Edit config.json with your parameters
   ```

3. **Verify installation**:
   ```bash
   python photoanalyzer.py --help
   ```

## 🎯 Usage

### Basic Examples

```bash
# General analysis of an image
python photoanalyzer.py image.jpg

# Analysis with a specific type
python photoanalyzer.py photo.png -t people

# Analysis with a custom prompt
python photoanalyzer.py screenshot.png -p "Describe the visible technical elements"

# Save to a file
python photoanalyzer.py image.jpg -o description.txt

# Debug mode for diagnostics
python photoanalyzer.py image.jpg --debug
```

### Available Analysis Types

| Type | Description |
|------|-------------|
| `general` | Detailed general description (default) |
| `technical` | Technical analysis (quality, composition, lighting) |
| `people` | Focus on people (number, ages, expressions) |
| `objects` | Identification and description of objects |
| `scene` | Description of the scene and context |
| `colors` | Analysis of colors and chromatic harmony |
| `composition` | Analysis of visual composition |
| `emotions` | Analysis of emotions and mood |
| `text` | Transcription of visible text |
| `security` | Security analysis (equipment, vulnerabilities) |
| `medical` | Medical analysis (with warning) |
| `count` | Precise counting of elements |

```bash
# List all available types
python photoanalyzer.py --list-types
```

### Advanced Configuration

#### Via JSON File (`config.json`)
```json
{
  "api_url": "https://api.ai.cloud-temple.com",
  "api_token": "your_api_key",
  "default_model": "qwen2.5-vl:7b",
  "default_max_tokens": 1000,
  "default_temperature": 0.3,
  "default_analysis_type": "general",
  "output_directory": "./photoanalyzer_outputs"
}
```

#### Via Environment Variables (`.env`)
```bash
LLMAAS_API_URL=https://api.ai.cloud-temple.com
LLMAAS_API_KEY=your_api_key
LLMAAS_DEFAULT_MODEL=qwen2.5-vl:7b
PHOTOANALYZER_OUTPUT_DIR=./outputs
```

## 📝 Command-Line Options

### Required Arguments
- `IMAGE_FILE_PATH`: Path to the image to be analyzed

### Main Options
- `-o, --output-file`: File to save the analysis
- `-t, --analysis-type`: Predefined analysis type
- `-p, --custom-prompt`: Custom prompt (has priority)
- `-m, --model`: Multimodal model to use

### API Configuration
- `--api-url`: LLMaaS API URL
- `--api-key`: API authentication key
- `--ollama-url`: URL of a direct Ollama backend (e.g., http://localhost:11434). Bypasses the LLMaaS API.
- `-c, --config-file`: JSON configuration file

### Model Parameters
- `--max-tokens`: Maximum tokens to generate (default: 1000)
- `--temperature`: Generation temperature (0.0-1.0, default: 0.3)

### Display Options
- `--debug`: Verbose debug mode
- `--silent`: Silent mode (clean output)
- `--list-types`: Display available analysis types

### Utilities
- `--output-dir`: Custom output directory
- `--help`: Display full help

## 🔧 Advanced Usage Examples

### Analysis of Photos of People
```bash
# Focused analysis on people
python photoanalyzer.py team.jpg -t people -o team_analysis.txt

# Precise counting of people
python photoanalyzer.py group.jpg -t count --debug
```

### Analysis of Screenshots
```bash
# Technical analysis of an interface
python photoanalyzer.py interface.png -t technical

# Text extraction
python photoanalyzer.py document.png -t text --silent > extracted_text.txt
```

### Security Analysis
```bash
# Security assessment of a site
python photoanalyzer.py industrial_site.jpg -t security -o security_report.txt
```

### Batch Workflows
```bash
# Processing multiple images
for img in *.jpg; do
    python photoanalyzer.py "$img" -t general -o "${img%.*}_analysis.txt" --silent
done
```

## 🔍 Debug Mode

The debug mode (`--debug`) displays detailed information:

- **Image validation**: Format, dimensions, size, metadata
- **Base64 encoding**: Compression statistics
- **API request**: Payload, model, parameters
- **API response**: Tokens, duration, stop reason
- **Configuration**: Resolved parameters and sources

```bash
python photoanalyzer.py image.jpg --debug
```

## 📊 Output Management

### Automatic Saving
```bash
# Automatic filename generation with timestamp
python photoanalyzer.py photo.jpg -o auto

# Result: photo_general_1672531200.txt
```

### Output Formats
- **Console**: Formatted display with Rich
- **Text file**: Raw result saving
- **Silent mode**: Clean output for redirection

## 🐛 Troubleshooting

### Common Errors

**Image not found**
```bash
ERROR: The specified image file 'image.jpg' does not exist.
```
→ Check the file path and existence

**Unsupported format**
```bash
File format '.bmp' not supported.
```
→ Convert to JPEG/PNG or check supported formats

**API Error**
```bash
API Error (HTTP 401): Unauthorized
```
→ Check your API key in the configuration

**Image too large**
```bash
# File size error before sending
The image file is too large (52.3 MB). Maximum size: 50 MB.
# Request size error after encoding (often on Nginx)
413 Request Entity Too Large
```
→ Reduce the image size manually or use the provided optimization script.

### Image Optimization Utility (`resize_image.py`)

If you encounter the `413 Request Entity Too Large` error, it means the image, even if its dimensions are acceptable, is too heavy once encoded in base64. The `resize_image.py` script is provided to help you reduce the file size.

**Usage:**
```bash
# Basic usage (resizes if > 2048px)
python3 examples/photoanalyzer/resize_image.py path/to/your/image.png

# Force more aggressive resizing
python3 examples/photoanalyzer/resize_image.py path/to/your/image.png --max-dim 800 --quality 75
```

- `--max-dim <pixels>`: Sets the maximum dimension (width or height).
- `--quality <1-100>`: Sets the compression quality for JPEG images.

The script will create a new image with the `_optimized` suffix. Then use this new image for analysis.

### In-depth Diagnostics
```bash
# Test API connectivity
python photoanalyzer.py image.jpg --debug | grep "API"

# Full image validation
python photoanalyzer.py image.jpg --debug | grep -A 10 "Image Validation"
```

## 🧪 Testing and Validation

### Configuration Test
```bash
# Check configuration
python photoanalyzer.py --list-types

# Test with a simple image
python photoanalyzer.py test_image.jpg -t general --debug
```

### Benchmarking
```bash
# Measure performance
time python photoanalyzer.py large_image.jpg -t general --silent
```

## 🔒 Security and Privacy

- **API keys**: Stored in `.env` (not versioned)
- **Sensitive images**: No local cache, processed in memory
- **Debug logs**: No exposure of sensitive data
- **HTTPS**: All API communications are encrypted

## 📚 Integration and Extensibility

### Usage as a Module
```python
from api_utils import analyze_image_api
from image_utils import encode_image_to_base64

# Direct usage
image_b64 = encode_image_to_base64("image.jpg")
result = analyze_image_api(api_url, api_key, model, image_b64, prompt)
```

### Extending Analysis Types
Modify `ANALYSIS_PROMPTS` in `photoanalyzer.py` to add new types:

```python
ANALYSIS_PROMPTS["custom"] = "Your custom prompt..."
```

## 🔄 Update and Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Cleaning Temporary Files
```bash
rm -rf ./photoanalyzer_outputs/*.tmp
```

## 📈 Performance and Optimization

- **Optimal images**: ≤ 2048px on the side, JPEG/PNG format
- **Recommended models**: `qwen2.5-vl:7b` for speed/quality balance
- **Recommended tokens**: 500-1500 depending on analysis complexity
- **Optimal temperature**: 0.1-0.3 for factual analyses, 0.5-0.7 for creative ones

## 🆘 Support and Documentation

- **API Documentation**: [Cloud Temple LLMaaS API](https://api.ai.cloud-temple.com/swagger/)
- **Technical issues**: See logs in `--debug` mode
- **Supported models**: Check `/v1/models` with `multimodal: true` capability

---

**Note**: PhotoAnalyzer requires multimodal models compatible with the OpenAI format for image analysis. Ensure your LLMaaS instance has models like `qwen2.5-vl`, `gemma3`, `granite3.2-vision`, or equivalents with vision support.

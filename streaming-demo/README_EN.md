# LLMaaS Streaming Demonstration - Cloud Temple

## 📋 Description

A simple and minimal example to demonstrate the **real-time streaming** capabilities of the **Cloud Temple LLMaaS API** using Server-Sent Events (SSE).

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

This demonstration shows how to:
- ✅ Activate streaming with `"stream": true`
- ✅ Process SSE events in real-time
- ✅ Display tokens as they are generated
- ✅ Calculate performance metrics (generation speed)

## 🚀 Quick Usage

### Initial Configuration
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure the config file
cp config.example.json config.json
# Edit config.json with your API token
```

### Basic Execution
```bash
python streaming_demo.py
```

### With Advanced Options
```bash
# Specific model
python streaming_demo.py --model gemma3:4b

# Debug mode (displays all payloads)
python streaming_demo.py --debug

# Custom prompt
python streaming_demo.py "Explain the concept of streaming in computer science"

# Full combination
python streaming_demo.py --model granite3.3:8b --debug "Tell me a story"
```

## 📊 Display Example

```
🔧 Configuration:
   - API: https://api.ai.cloud-temple.com/v1
   - Model: granite3.3:2b
   - Streaming: Enabled (SSE)

🚀 LLMaaS Streaming Demonstration
📊 Model: granite3.3:2b
💭 Question: Write a short story about a robot discovering art.

🎬 Streaming Response:
==================================================
Once upon a time, a small robot named ARIA...
[Text displayed token by token in real-time]
==================================================
✅ Streaming finished!
📊 Tokens received: 158
⏱️  Duration: 3.42s
🚀 Speed: 46.2 tokens/s
```

## 🔧 Technical Features

### **External Configuration**
- `config.json` file for API and default parameters
- `config.example.json` template for initialization
- Automatic loading with JSON validation
- Support for custom config path (`--config`)

### **Advanced Debug Mode**
- Detailed display of request/response payloads with `--debug`
- Visualization of raw SSE chunks
- JSON parsing and content extraction logs
- Comprehensive performance statistics
- Enhanced error handling

### **Server-Sent Events (SSE)**
- Optimized HTTP streaming protocol
- Real-time token reception
- Robust handling of malformed events

### **Modern CLI Interface**
- Argparse support with detailed help
- Positional arguments and named options
- Integrated usage examples
- Explicit error messages

### **Performance Metrics**
- Automatic token counting
- Throughput calculation (tokens/second)
- Total latency measurement
- Debug mode with JSON statistics

### **Error Handling**
- Configurable timeouts via config.json
- Connection error handling
- Clean interruption with Ctrl+C
- Robust configuration file validation

## 🎯 Recommended Models

| Model | Size | Speed | Use Case |
|---|---|---|---|
| `granite3.3:2b` | 2B | ~45 t/s | Quick demonstrations |
| `gemma3:4b` | 4B | ~58 t/s | Balanced quality |
| `qwen3:8b` | 8B | ~29 t/s | Sophisticated responses |
| `cogito:3b` | 3B | ~63 t/s | Logical reasoning |

## 💡 Key Code Points

### Streaming Activation
```python
payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "stream": True,  # 🔑 Crucial point
    "max_tokens": 300,
    "temperature": 0.8
}
```

### SSE Processing
```python
for line in response.iter_lines():
    if line.startswith("data: "):
        data_content = line[6:]  # Remove "data: "
        
        if data_content == "[DONE]":
            break
            
        chunk = json.loads(data_content)
        content = chunk["choices"][0]["delta"].get("content", "")
        
        if content:
            print(content, end="", flush=True)
```

## ⚡ Advantages of Streaming

1. **User Experience**: Immediate display, no waiting
2. **Perceived Performance**: Optimal responsiveness even for long texts
3. **Control**: Ability to interrupt generation at any time
4. **Efficiency**: Optimal bandwidth utilization

## 🔗 Useful Links

- [Full Cloud Temple documentation](https://docs.cloud-temple.com)
- [Cloud Temple Console](https://console.cloud-temple.com)
- [Other examples](../README.md)

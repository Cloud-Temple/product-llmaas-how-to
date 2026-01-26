# Example: Simple Tool Calling

This directory contains a simple example of "Tool Calling" with the LLMaaS API. It demonstrates how a language model can interact with external functions to accomplish specific tasks.

## Files

- `test_tool_calling.py`: The main Python script implementing the example's logic.
- `.env.example`: A configuration file example for environment variables.
- `requirements.txt`: Necessary Python dependencies to run the script.

## Features

The `test_tool_calling.py` script uses a simple `calculator` function to evaluate mathematical expressions. The process is as follows:
1.  The script sends a question to the LLMaaS API, providing the description of the `calculator` tool.
2.  The LLM model analyzes the question and, if it determines the tool is relevant, generates a call to the `calculator` function with the necessary arguments.
3.  The script intercepts this call and executes the `calculator` function locally.
4.  The tool's execution result is sent back to the LLM.
5.  The LLM uses this result to formulate a final response to the user.

## Command Line Options

The `test_tool_calling.py` script supports the following options:

-   `--stream`: Enables streaming mode for LLM responses. Text is displayed as it is generated.
-   `--model <MODEL_NAME>`: Specifies the LLM model to use for the test (e.g., `qwen3:30b-a3b`). If not specified, the default model from the `.env` file is used.
-   `--debug`: Enables debug mode. Displays complete payloads (requests and responses) sent to and received from the API, as well as streaming deltas in `--stream` mode.

## Prerequisites

-   Python 3.x
-   A valid LLMaaS API key.

## Installation

1.  **Clone this repository** (if not already done).
2.  **Navigate** to the example directory:
    ```bash
    cd exemples/simple_tool_calling/
    ```
3.  **Create a `.env` file** by copying `.env.example`:
    ```bash
    cp .env.example .env
    ```
4.  **Open the `.env` file** and replace `"votre_cle_api_ici"` with your LLMaaS API key.
5.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the `exemples/simple_tool_calling/` directory:

```bash
python3 test_tool_calling.py
```

### Usage Examples with Options:

-   Run in streaming mode:
    ```bash
    python3 test_tool_calling.py --stream
    ```
-   Specify a model and enable debugging:
    ```bash
    python3 test_tool_calling.py --model qwen3:30b-a3b --debug
    ```
-   Combine all options:
    ```bash
    python3 test_tool_calling.py --stream --model qwen3:30b-a3b --debug
    ```

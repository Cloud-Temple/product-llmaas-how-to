# Advanced Python Script for Testing LLMaaS Cloud Temple API

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Objective
This Python script (`test_api_models.py`) allows testing and comparing responses from various Language Models (LLMs) accessible via the **Cloud Temple LLMaaS API**. It offers advanced features for configuration, model selection, request customization, and result display. This is an adaptation of the original PowerShell script.

## Features
1.  **External Configuration**: Reads the API endpoint and authentication token from a `config.json` file. Also allows setting default values for passes, temperature, max tokens, and timeout.
2.  **Dynamic Model Discovery**: Automatically retrieves the list of available models from the API's `/models` endpoint.
3.  **Model Selection**: Allows specifying models to test via the `--models` argument (comma-separated list of IDs). If omitted, all available models are tested.
4.  **Prompt Customization**: The prompt sent to the models can be defined via the `--prompt` argument.
5.  **Multiple Tests**: Performs a configurable number of passes (requests) for each model (via `--passes` argument) to evaluate consistency and performance.
6.  **Generation Parameters**: Allows controlling temperature (`--temperature`) and maximum number of tokens (`--max-tokens`) for requests.
7.  **Debug Mode**: A `--debug` option enables detailed display of request, response, and error information, including the body of API error responses.
8.  **Improved Error Handling**: Catches API errors (e.g., 403 Forbidden) and attempts to extract and display the detailed message provided in the JSON response (e.g., "Prompt blocked for security reasons") without crashing the script.
9.  **Colored Output**: Uses colors (via the `rich` library) to distinguish information, successes, and failures in the console.
10. **Summary Table**: Displays a final summary (via `rich.table`) comparing the performance (successes, errors, average time, total time, tokens/second, etc.) of each tested model.
11. **Model Parallelism**: Allows testing multiple models simultaneously to speed up the process (`--parallel-models` argument).
12. **Request Parallelism**: Allows sending multiple requests in parallel to the same model to test its load handling capability (`--parallel-requests` argument).
13. **Detailed Statistics**: Displays information on tokens per second and backend details (if provided by the API) for each response.

## Prerequisites
-   Python 3.7+
-   Libraries listed in `requirements.txt` (mainly `requests` and `rich`). Install them with:
    ```bash
    pip install -r requirements.txt
    ```
-   A `config.json` file in the same directory as the script, containing at least:
    ```json
    {
        "api": {
            "endpoint": "YOUR_API_URL",
            "token": "YOUR_BEARER_TOKEN"
        }
    }
    ```
    Optionally, a `defaults` section can be added to override the script's default values:
    ```json
    {
        "api": { ... },
        "defaults": {
            "passes": 5,
            "temperature": 0.8,
            "max_tokens": 512,
            "timeout": 60
        }
    }
    ```

## Usage

**Basic syntax:**
```bash
python test_api_models.py [Arguments...]
```
**Main arguments:**
*   `--models "<id1>,<id2>..."`: List of model IDs to test. If omitted, tests all available models.
*   `--prompt "<your_prompt>"`: The prompt to send.
*   `--passes <number>`: Number of requests per model.
*   `--temperature <value>`: Temperature for generation (e.g., 0.7).
*   `--max-tokens <number>`: Maximum number of output tokens.
*   `-e`, `--endpoint <URL>`: Full URL of the API endpoint to use (e.g., `http://preprod.api.ai.cloud-temple.com/v1`). Overrides the configuration file value if specified.
*   `--debug`: Activates detailed display.
*   `--config-file <path>`: Uses a specific configuration file.
*   `--parallel-models <number>`: Number of models to test in parallel (default: 1).
*   `--parallel-requests <number>`: Number of requests to send in parallel for each model (default: 1).

**Examples:**

1.  **Test all models with default parameters:**
    ```bash
    python test_api_models.py
    ```

2.  **Test specific models (`cogito:3b` and `qwen3:4b`) with 5 passes:**
    ```bash
    python test_api_models.py --models "cogito:3b,qwen3:4b" --passes 5
    ```

3.  **Test all models with a custom prompt and in debug mode:**
    ```bash
    python test_api_models.py --prompt "Explain photosynthesis in one sentence." --debug
    ```

4.  **Test a model with specific temperature and token count:**
    ```bash
    python test_api_models.py --models "llama3.1" --temperature 0.5 --max-tokens 100
    ```

5.  **Use a specific configuration file:**
    ```bash
    python test_api_models.py --config-file "../other_config.json"
    ```
6.  **Use a specific endpoint via command line:**
    ```bash
    python test_api_models.py --endpoint "http://my-other-api.local/v1" --models "cogito:3b"
    ```

7.  **Test 3 models in parallel, each with 2 requests in parallel:**
    ```bash
    python test_api_models.py --models "cogito:3b,qwen3:4b,gemma3:1b" --passes 5 --parallel-models 3 --parallel-requests 2
    ```

8.  **Test all models, 2 models at a time in parallel, with 3 passes per model, each pass having 4 requests in parallel:**
    ```bash
    python test_api_models.py --passes 3 --parallel-models 2 --parallel-requests 4
    ```

## Notes
-   Error handling attempts to extract details from API error JSON responses, but the exact format may vary depending on the API implementation.
-   Using a large number of parallel requests (`--parallel-requests`) combined with a large number of parallel models (`--parallel-models`) can heavily strain your machine and the target API. Use with discretion.

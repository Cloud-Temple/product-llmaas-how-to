# Advanced PowerShell Script for Testing LLMaaS Cloud Temple API

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Objective
This PowerShell script (`test_api_models.ps1`) allows testing and comparing responses from various Language Models (LLMs) accessible via the **Cloud Temple LLMaaS API**. It offers advanced features for configuration, model selection, request customization, and result display.

## Features
1.  **External Configuration**: Reads the API endpoint and authentication token from a `config.json` file. Also allows setting default values for passes, temperature, max tokens, and timeout.
2.  **Dynamic Model Discovery**: Automatically retrieves the list of available models from the API's `/models` endpoint.
3.  **Model Selection**: Allows specifying models to test via the `-Models` parameter (comma-separated list of IDs). If omitted, all available models are tested.
4.  **Prompt Customization**: The prompt sent to the models can be defined via the `-Prompt` parameter.
5.  **Multiple Tests**: Performs a configurable number of passes (requests) for each model (via `-Passes` parameter) to evaluate consistency and performance.
6.  **Generation Parameters**: Allows controlling temperature (`-Temperature`) and maximum number of tokens (`-MaxTokens`) for requests.
7.  **Debug Mode**: A `-Debug` option enables detailed display of request, response, and error information, including the body of API error responses.
8.  **Improved Error Handling**: Catches API errors (e.g., 403 Forbidden) and attempts to extract and display the detailed message provided in the JSON response (e.g., "Prompt blocked for security reasons") without crashing the script.
9.  **Colored Output**: Uses colors to distinguish information, successes, and failures in the console.
10. **Summary Table**: Displays a final summary comparing the performance (successes, errors, average time, total time) of each tested model.

## Prerequisites
-   PowerShell 5.1 or higher.
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
```powershell
powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 [Parameters...]
```
*Note:* `-ExecutionPolicy Bypass` may be necessary if your system's execution policy prevents script execution.

**Examples:**

1.  **Test all models with default parameters:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1
    ```

2.  **Test specific models (`cogito:3b` and `qwen3:4b`) with 5 passes:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Models "cogito:3b,qwen3:4b" -Passes 5
    ```

3.  **Test all models with a custom prompt and in debug mode:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Prompt "Explain photosynthesis in one sentence." -Debug
    ```

4.  **Test a model with specific temperature and token count:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -Models "llama3.1" -Temperature 0.5 -MaxTokens 100
    ```

5.  **Use a specific configuration file:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File ./test_api_models.ps1 -ConfigFile "../other_config.json"
    ```

## Notes
-   The script attempts to force UTF-8 output encoding, but correct display of accented characters may still depend on your PowerShell console's configuration (font, code page).
-   Error handling attempts to extract details from API error JSON responses, but the exact format may vary depending on the API implementation.

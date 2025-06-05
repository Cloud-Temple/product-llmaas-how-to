# Example: Listing LLMaaS Models with Style

This Python script (`list_models.py`) is an elegant example for querying the `/v1/models` endpoint of the **Cloud Temple LLMaaS API** and displaying the list of available models in a well-formatted table using the `rich` library.

📖 **Full documentation**: [docs.cloud-temple.com](https://docs.cloud-temple.com)

## Features

- Loading configuration (API URL and token) from a `.env` file.
- Calling the LLMaaS API to retrieve the list of models.
- Handling connection errors and HTTP responses.
- Displaying models in a clear and colorful table, sorted by ID.
- Visual progress indication during API call.

## Prerequisites

- Python 3.7+
- Dependencies listed in `requirements.txt`

## Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <llmaas_repo_url>
    cd path/to/llmaas/examples/list_models_pretty
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your API credentials**:
    - Copy the `.env.example` file to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file with your LLMaaS API URL and access token:
      ```env
      LLMAAS_API_URL="https://your-llmaas-api.com"
      LLMAAS_API_TOKEN="your_personal_token"
      ```

## Usage

Once installation and configuration are complete, simply run the script:

```bash
python list_models.py
```

The script will display a table listing the available models, with their ID, owner, object type, creation date, and aliases.

## Directory Structure

```
list_models_pretty/
├── .env.example        # Example environment configuration file
├── list_models.py      # The main Python script
├── README.md           # This instruction file
└── requirements.txt    # List of Python dependencies
```

## Customization

- **API URL and Token**: Modify the `.env` file to point to your LLMaaS instance.
- **Table Display**: The script uses `rich.table.Table`. You can customize columns, styles, and sorting directly in the `display_models_table` function of the `list_models.py` script.

---

Carefully developed by Cline.

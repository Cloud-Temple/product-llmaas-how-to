# LLMaaS Status API Demonstrator

This directory contains an example of using the public status API of the Cloud Temple LLMaaS platform.

## Goal

The goal of this script is to provide developers with a concrete integration example for:
1.  **Monitoring the overall health** of the LLMaaS platform.
2.  **Retrieving real-time performance metrics** (TTFB, Throughput) for each model.
3.  **Estimating energy consumption** of requests, combining API usage data with model energy specifications (kWh/million tokens).

## Prerequisites

- Python 3.8+
- Internet access (to reach `https://llmaas.status.cloud-temple.app`)

## Installation

1.  Create a virtual environment (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Launch the dashboard script:

```bash
python3 status_dashboard.py
```

### Options

You can specify a limited list of models to check via the `--models` option:

```bash
python3 status_dashboard.py --models "llama3.3:70b,mistral-large-3:675b"
```

## Technical Operation

The script queries two endpoints of the public API:

1.  `GET /api/platform-status`: To get the global state (`operational`, `degraded`, etc.) and the list of failed models.
2.  `GET /api/platform-status?model=<model_id>`: To get detailed metrics for a specific model.

### Energy Data

The current status API provides usage metrics (tokens) and performance (speed), but does not directly provide the energy consumption coefficient per model.

This script therefore integrates a **local knowledge base** (`MODEL_ENERGY_MAP`) containing consumption values (in kWh per million tokens) from the platform's technical documentation. It uses these values to calculate an estimated energy consumption for the test request (probe) performed by the status API.

**Calculation Formula:**
```
Energy (Wh) = (Total Tokens / 1,000,000) * Model_Consumption (kWh/M) * 1000
```

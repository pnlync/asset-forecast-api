# Asset Price Forecast API (v1)

A simple REST API that accepts a single **asset ticker** and returns **daily price forecasts for the next N days** (default **7**). Each forecast point is aligned to **UTC 00:00:00**.

---

## Documentation

- Detailed API docs: [`docs/api.md`](https://chatgpt.com/g/g-p-69958d2e2bac819190193240369a54b8-scalable-project/c/docs/api.md)

---

## Base URL

Set this to your deployed endpoint:

- `https://<YOUR_BASE_URL>`

Example:

- `https://api.example.com`

---

## Quick Start

### Get a 7-day forecast (default)

```bash
curl -s "<https://api.example.com/v1/forecast/AAPL>" \\
  -H "Accept: application/json"
```

### Get a 7-day forecast (explicit)

```bash
curl -s "https://api.example.com/v1/forecast/BTC-USD?horizon_days=7" \
  -H "Accept: application/json"
```

---

## API Overview

### Endpoint

- `GET /v1/forecast/{ticker}`

### Input

- **Path parameter**: `ticker` (string)
- **Optional query parameter**: `horizon_days` (integer, default 7)

### Output (High Level)

- JSON response containing:
    - `ticker`, `currency`, `timezone=UTC`, `generated_at`
    - `horizon_days`, `anchor_time_utc="00:00:00"`
    - `forecasts[]`: an array of `{ date, timestamp, predicted_price }`

---


## Key Conventions

- **Timezone**: all dates/timestamps are **UTC**
- **Alignment**: each daily point is at **00:00:00Z**
- **Horizon definition**: forecasts start from **tomorrow (UTC)** and return **N consecutive days**
- **Equities on weekends**: forecasts are still returned to ensure a stable, fixed-length daily series

---

## Optional Health Check (if enabled)

- `GET /v1/health`

---

## License / Disclaimer

This project is for educational purposes. Forecasts are not investment advice.

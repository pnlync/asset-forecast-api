# Asset Price Forecast API (v1)

This document describes a REST API that accepts a single **asset ticker** and returns **daily price forecasts for the next N days** (default **7**). Each forecast represents the predicted price at **UTC 00:00:00** for that day.

---

## 1) Base URL

Replace this with the actual deployed address:

- **Base URL**: `https://<YOUR_BASE_URL>`

Example:

- `https://api.example.com`

---

## 2) Key Conventions (Read This First)

### 2.1 Timezone and Date Alignment
- All dates/timestamps are in **UTC**.
- Each forecast point is aligned to **00:00:00Z** (UTC midnight).
- Returned fields:
  - `date`: `YYYY-MM-DD` (UTC date)
  - `timestamp`: `YYYY-MM-DDT00:00:00Z`

### 2.2 “Next N Days” Definition
- Forecasts start from **tomorrow (UTC)** and include **N consecutive days**.
  - If a request is generated on `2026-02-18` UTC, the first forecast date is `2026-02-19`.

### 2.3 Price Definition
- `predicted_price` is a **reference forecast price** for that day at UTC 00:00:00.
- For equities (stocks), forecasts are still returned for weekends/holidays to ensure a stable, fixed-length output.

### 2.4 Supported Ticker Formats
The API accepts **one ticker string**. Typical examples:
- Equities: `AAPL`, `TSLA`, `MSFT`
- Crypto pairs: `BTC-USD`, `ETH-USD`

> If a ticker is valid syntactically but not supported by the service/model, the API returns an error (see §6).

---

## 3) Content Types

### Request
- `Accept: application/json`

### Response
- `Content-Type: application/json; charset=utf-8`

---

## 4) Endpoints

### 4.1 Get Forecast (Primary Endpoint)

**GET** `/v1/forecast/{ticker}`

#### Path Parameters
| Name   | Type   | Required | Description |
|--------|--------|----------|-------------|
| ticker | string | Yes      | Asset ticker (e.g., `AAPL`, `BTC-USD`) |

#### Query Parameters (Optional)
| Name         | Type    | Required | Default | Description |
|--------------|---------|----------|---------|-------------|
| horizon_days | integer | No       | 7       | Forecast horizon in days. The service is designed for a **7-day** horizon. If other values are not supported, the API returns `400 INVALID_PARAMETER`. |

---

## 5) Success Response

### 5.1 HTTP 200 OK

#### Response Body (JSON)
```json
{
  "ticker": "AAPL",
  "currency": "USD",
  "timezone": "UTC",
  "generated_at": "2026-02-18T12:34:56Z",
  "horizon_days": 7,
  "anchor_time_utc": "00:00:00",
  "forecasts": [
    { "date": "2026-02-19", "timestamp": "2026-02-19T00:00:00Z", "predicted_price": 192.34 },
    { "date": "2026-02-20", "timestamp": "2026-02-20T00:00:00Z", "predicted_price": 191.02 },
    { "date": "2026-02-21", "timestamp": "2026-02-21T00:00:00Z", "predicted_price": 190.77 },
    { "date": "2026-02-22", "timestamp": "2026-02-22T00:00:00Z", "predicted_price": 189.55 },
    { "date": "2026-02-23", "timestamp": "2026-02-23T00:00:00Z", "predicted_price": 190.11 },
    { "date": "2026-02-24", "timestamp": "2026-02-24T00:00:00Z", "predicted_price": 191.90 },
    { "date": "2026-02-25", "timestamp": "2026-02-25T00:00:00Z", "predicted_price": 193.08 }
  ]
}
```

---

### 5.2 Field Reference

| Field | Type | Description |
| --- | --- | --- |
| ticker | string | Normalized ticker returned by the service |
| currency | string | Quote currency (e.g., `USD`). For crypto pairs, typically inferred from the ticker (e.g., `BTC-USD` → `USD`). |
| timezone | string | Always `UTC` |
| generated_at | string | Forecast generation time in UTC (ISO 8601, ends with `Z`) |
| horizon_days | int | Number of forecast days returned (default 7) |
| anchor_time_utc | string | Always `00:00:00` (UTC midnight alignment) |
| forecasts | array | Array of forecast points; length equals `horizon_days` |
| forecasts.date | string | UTC date (`YYYY-MM-DD`) |
| forecasts.timestamp | string | UTC timestamp at midnight (`YYYY-MM-DDT00:00:00Z`) |
| forecasts.predicted_price | number | Predicted price for that UTC midnight point |

### 5.3 Output Guarantees

- `forecasts` is sorted in ascending order by `date`.
- `forecasts.length == horizon_days`.
- `timestamp` is always `date + "T00:00:00Z"`.

---

## 6) Error Handling

### 6.1 Error Response Format (All Errors)

All non-200 responses return a consistent JSON structure:

```json
{
  "error": {
    "code": "INVALID_TICKER",
    "message": "Ticker not recognized or unsupported.",
    "details": {
      "ticker": "AAA???"
    }
  }
}
```

### Error Fields

| Field | Type | Description |
| --- | --- | --- |
| error.code | string | Machine-readable error identifier |
| error.message | string | Human-readable explanation |
| error.details | object | Optional structured context to help debugging |

### 6.2 Common Status Codes

| HTTP | error.code | When It Happens | Caller Action |
| --- | --- | --- | --- |
| 400 | INVALID_PARAMETER | Invalid query parameter (e.g., unsupported `horizon_days`) | Fix the request and retry |
| 400 | INVALID_TICKER | Malformed ticker (empty/illegal characters) | Correct ticker and retry |
| 404 | NOT_SUPPORTED | Ticker format is valid but not supported / no data | Use a supported ticker |
| 429 | RATE_LIMITED | Too many requests | Retry with backoff |
| 500 | INTERNAL_ERROR | Unexpected server error | Retry later; contact provider if persistent |

---

## 7) Rate Limits and Retry Guidance (Recommended)

- If `429 RATE_LIMITED` occurs, retry with exponential backoff:
    - 1s → 2s → 4s → 8s (max 3–5 attempts)
- Always set a client timeout (e.g., 10 seconds).

---

## 8) Examples

### 8.1 cURL

### Default 7-day forecast

```bash
curl -s "https://api.example.com/v1/forecast/AAPL" \
  -H "Accept: application/json"
```

### Explicit horizon_days=7

```bash
curl -s "https://api.example.com/v1/forecast/BTC-USD?horizon_days=7" \
  -H "Accept: application/json"
```

### 8.2 JavaScript (fetch)

```jsx
const baseUrl = "https://api.example.com";
const ticker = "BTC-USD";

const url = `${baseUrl}/v1/forecast/${encodeURIComponent(ticker)}?horizon_days=7`;

const res = await fetch(url, { headers: { "Accept": "application/json" } });

if (!res.ok) {
  const err = await res.json().catch(() => null);
  throw new Error(`HTTP ${res.status}: ${JSON.stringify(err)}`);
}

const data = await res.json();
console.log(data.ticker, data.horizon_days);
console.log(data.forecasts);
```

### 8.3 Python (requests)

```python
import requests

base_url = "https://api.example.com"
ticker = "AAPL"

url = f"{base_url}/v1/forecast/{ticker}"
params = {"horizon_days": 7}

r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=10)

if r.status_code != 200:
    try:
        print("Error:", r.json())
    except Exception:
        print("Error:", r.text)
    r.raise_for_status()

data = r.json()
for item in data["forecasts"]:
    print(item["date"], item["predicted_price"])
```

---

## 9) Optional Endpoint (If Enabled): Health Check

**GET** `/v1/health`

### HTTP 200 OK

```json
{
  "status": "ok",
  "time_utc": "2026-02-18T12:34:56Z",
  "version": "v1"
}
```

---

## 10) FAQ

### Q1: Do I need to specify whether the ticker is a stock or crypto?

No. The API accepts a single ticker. The service interprets it internally.

### Q2: Why are timestamps always at midnight UTC?

This is a deliberate alignment rule to avoid timezone ambiguity and provide one consistent daily point.

### Q3: Why do equities still return values on weekends?

The API returns a stable N-day daily series for integration simplicity (fixed length, fixed alignment).

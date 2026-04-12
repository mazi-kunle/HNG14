# Gender Classification API

A lightweight REST API built with Flask that classifies names by gender using the [Genderize.io](https://genderize.io) API. It processes and enriches the raw Genderize response before returning it to the client.

---

## Features

- Classifies a name as male or female with a probability score
- Computes a confidence flag based on probability and sample size
- Input validation with appropriate HTTP error codes
- CORS enabled for cross-origin access
- Clean, consistent JSON error responses

---

## Requirements

- Python 3.8+
- pip

---

## Installation

```bash
git clone https://github.com/mazi-kunle/HNG14.git
cd day0
pip install -r requirements.txt
```

---

## Running the Server

**Development:**
```bash
flask run
```
## live website
https://hng-14-bza9us6y4-mazi-kunles-projects.vercel.app

## API Reference

### `GET /api/classify`

Classifies a name by gender.

**Query Parameters**

| Parameter | Type   | Required | Description        |
|-----------|--------|----------|--------------------|
| `name`    | string | Yes      | The name to classify |

**Success Response `200`**

```json
{
  "status": "success",
  "data": {
    "name": "James",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-01T12:00:00Z"
  }
}
```

**Fields**

| Field          | Description                                                       |
|----------------|-------------------------------------------------------------------|
| `gender`       | `male` or `female`                                                |
| `probability`  | Confidence score from Genderize (0 to 1)                          |
| `sample_size`  | Number of samples Genderize used for the prediction               |
| `is_confident` | `true` if probability >= 0.7 AND sample_size >= 100, else `false` |
| `processed_at` | UTC timestamp of when the request was processed (ISO 8601)        |

---

## Error Responses

All errors follow this structure:

```json
{
  "status": "error",
  "message": "<error message>"
}
```

| Status Code | Cause                                              |
|-------------|----------------------------------------------------|
| `400`       | `name` parameter is missing or empty               |
| `422`       | `name` parameter is not a valid string             |
| `500`       | No prediction available for the provided name      |
| `502`       | Genderize API is unreachable or returned an error  |

---

## Project Structure

```
.
├── app/
│   ├── __init__.py        # App factory
│   └── routes.py          # /api/classify endpoint       
├── run.py
└── README.md
```

---

## Dependencies

- [Flask](https://flask.palletsprojects.com/) — web framework
- [Flask-CORS](https://flask-cors.readthedocs.io/) — CORS header support
- [Requests](https://docs.python-requests.org/) — HTTP client for Genderize API

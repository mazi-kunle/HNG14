# Profile Intelligence Service

A Flask-based REST API that enriches name-based profiles by aggregating data from three external APIs — Genderize, Agify, and Nationalize — and storing the results for retrieval and management.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)

---

## Overview

This service accepts a name, calls three public APIs in parallel to infer gender, estimated age, and likely nationality, aggregates the results into a structured profile, and stores it with a UUID v7 identifier and a UTC timestamp.

**External APIs used (no API key required):**

| API | Endpoint |
|---|---|
| Genderize | `https://api.genderize.io?name={name}` |
| Agify | `https://api.agify.io?name={name}` |
| Nationalize | `https://api.nationalize.io?name={name}` |

**Data processing rules:**

- **Genderize** → extracts `gender`, `gender_probability`, and `count` (renamed to `sample_size`)
- **Agify** → extracts `age` and classifies it into an `age_group`:
  - `0–12` → `child`
  - `13–19` → `teenager`
  - `20–59` → `adult`
  - `60+` → `senior`
- **Nationalize** → extracts the country list and picks the entry with the highest probability as `country_id`

Profiles are **idempotent** — submitting the same name twice returns the existing record instead of creating a duplicate.

---

## Tech Stack

- **Runtime:** Python 3
- **Framework:** Flask
- **ID generation:** UUID v7
- **Timestamps:** UTC ISO 8601

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone (https://github.com/mazi-kunle/HNG14.git)
cd day1

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
python3 main.py
```

The server starts on `http://localhost:5000` by default.

---

## live website

https://hng14-production-81d0.up.railway.app

## API Reference

### 1. Create a Profile

**`POST /api/profiles`**

Accepts a name, enriches it via external APIs, and stores the result. If a profile for that name already exists, the existing record is returned.

**Request body:**
```json
{ "name": "ella" }
```

**Success — new profile (201):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DRC",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**Success — profile already exists (200):**
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### 2. Get a Profile by ID

**`GET /api/profiles/{id}`**

**Success (200):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 25,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### 3. List Profiles

**`GET /api/profiles`**

Returns all stored profiles. Supports optional case-insensitive query parameters for filtering.

**Query parameters:**

| Parameter | Description | Example |
|---|---|---|
| `gender` | Filter by gender | `male`, `female` |
| `country_id` | Filter by country code | `NG`, `US` |
| `age_group` | Filter by age group | `adult`, `child` |

**Example:** `GET /api/profiles?gender=male&country_id=NG`

**Success (200):**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "id-1",
      "name": "emmanuel",
      "gender": "male",
      "age": 25,
      "age_group": "adult",
      "country_id": "NG"
    },
    {
      "id": "id-2",
      "name": "sarah",
      "gender": "female",
      "age": 28,
      "age_group": "adult",
      "country_id": "US"
    }
  ]
}
```

---

### 4. Delete a Profile

**`DELETE /api/profiles/{id}`**

Deletes the profile with the given ID.

**Success:** `204 No Content`

---

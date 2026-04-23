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
cd day2

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

### 5. Advanced Search Query — Natural Language API

## Overview

The `/api/profiles/search` endpoint accepts plain English queries and converts them into structured filters automatically — no special syntax required.

**Endpoint:**
```
GET /api/profiles/search?q=<your query>
```

**Full example:**
```
GET /api/profiles/search?q=young males from nigeria&page=1&limit=20
```

---

## Query Parameters

| Parameter | Type    | Required | Default | Description                        |
|-----------|---------|----------|---------|------------------------------------|
| `q`       | string  | Yes      | —       | Plain English search query         |
| `page`    | integer | No       | `1`     | Page number for pagination         |
| `limit`   | integer | No       | `10`    | Number of results per page         |

---

## What You Can Search For

### Gender

Use natural gender words anywhere in the query.

| Query example             | Filter applied      |
|---------------------------|---------------------|
| `males`                   | `gender=male`       |
| `females`                 | `gender=female`     |
| `women`                   | `gender=female`     |
| `boys`                    | `gender=male`       |
| `male and female`         | *(no gender filter)*|

> **Note:** Combining both genders (e.g. `male and female`) cancels out the gender filter — all genders are returned.

Accepted words: `male`, `males`, `man`, `men`, `boy`, `boys`, `female`, `females`, `woman`, `women`, `girl`, `girls`

---

### Age Groups

Use age group keywords to filter by a defined life stage.

| Keyword                          | Filter applied                              |
|----------------------------------|---------------------------------------------|
| `teenager`, `teen`, `teens`      | `age_group=teenager` + `min_age=13, max_age=19` |
| `adult`, `adults`                | `age_group=adult` + `min_age=20, max_age=59`    |
| `senior`, `seniors`, `elderly`   | `age_group=senior` + `min_age=60`               |

---

### "Young" Keyword *(Parser-only)*

`young` and `youth` are special — they map to ages **16–24** for search purposes only. They are **not** stored age groups.

| Query example   | Filter applied                  |
|-----------------|---------------------------------|
| `young males`   | `gender=male, min_age=16, max_age=24` |
| `youth`         | `min_age=16, max_age=24`        |

> **Important:** `young` will never appear as an `age_group` value in the results — it only affects the age range.

---

### Age Modifiers

Combine directional keywords with a number to set a minimum or maximum age.

| Query example           | Filter applied   |
|-------------------------|------------------|
| `above 30`              | `min_age=30`     |
| `over 18`               | `min_age=18`     |
| `below 25`              | `max_age=25`     |
| `under 40`              | `max_age=40`     |
| `teenagers above 17`    | `age_group=teenager, min_age=17, max_age=19` |

Accepted `above` words: `above`, `over`, `older`, `atleast`, `minimum`, `min`, `plus`  
Accepted `below` words: `below`, `under`, `younger`, `atmost`, `maximum`, `max`

> **Tip:** When an age modifier conflicts with an age group's default bounds, the explicit modifier wins. For example, `teenagers above 17` overrides the group's default `min_age=13` with `min_age=17`.

---

### Country

Use country names or demonyms, with or without a preposition.

| Query example           | Filter applied     |
|-------------------------|--------------------|
| `from nigeria`          | `country_id=NG`    |
| `in kenya`              | `country_id=KE`    |
| `people of ghana`       | `country_id=GH`    |
| `angolans`              | `country_id=AO`    |

Accepted prepositions: `from`, `in`, `of`

---

## Combined Query Examples

| Query                                   | Interpreted As                                                   |
|-----------------------------------------|------------------------------------------------------------------|
| `young males`                           | `gender=male, min_age=16, max_age=24`                           |
| `females above 30`                      | `gender=female, min_age=30`                                     |
| `people from angola`                    | `country_id=AO`                                                 |
| `adult males from kenya`                | `gender=male, age_group=adult, min_age=20, max_age=59, country_id=KE` |
| `male and female teenagers above 17`    | `age_group=teenager, min_age=17, max_age=19`                    |
| `young males from nigeria`              | `gender=male, min_age=16, max_age=24, country_id=NG`            |
| `senior women in ghana`                 | `gender=female, age_group=senior, min_age=60, country_id=GH`    |

---

## Response Format

### Success `200`

```json
{
  "query": "young males from nigeria",
  "interpreted_as": {
    "gender": "male",
    "min_age": 16,
    "max_age": 24,
    "country_id": "NG"
  },
  "page": 1,
  "limit": 20,
  "results": []
}
```

The `interpreted_as` field shows exactly how your query was understood — useful for debugging.

### Uninterpretable Query `422`

Returned when no filters could be extracted from the query.

```json
{
  "status": "error",
  "message": "Unable to interpret query"
}
```

### Missing Query Parameter `400`

```json
{
  "status": "error",
  "message": "Missing or empty parameter"
}

```

---

## Rules & Limitations

- **Rule-based parsing only** — no AI or LLMs are used. The parser works by matching keywords and patterns.
- Queries must contain at least one recognizable keyword (gender, age group, age modifier, or country) to return results.
- Word order does not matter — `nigeria from males young` is parsed the same as `young males from nigeria`.
- Unrecognized words are safely ignored.
- Country support is limited to the countries defined in the system. Unsupported country names will be ignored.
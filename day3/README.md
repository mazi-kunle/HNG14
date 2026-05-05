# Insighta Labs — Backend

The core API powering the Insighta Labs+ platform. Built with Flask, it handles authentication, profile intelligence, and data management. The backend is a pure REST API — all responses are JSON except auth redirects.

---

## System Architecture

The system is made up of three separate components that all share the same backend. The CLI tool and web portal both communicate with the Flask backend which handles all business logic, authentication, and database operations. The backend talks to GitHub for OAuth authentication and to external APIs (Genderize, Agify, Nationalize) for profile intelligence data.

---

## Project Structure

The project follows the Application Factory + Blueprint pattern. Each feature lives in its own module with its own routes, keeping the codebase clean and maintainable.

The `app/auth/` module handles all authentication — GitHub OAuth, token generation, and token refresh. The `app/profiles/` module handles all profile operations — listing, creating, searching, and exporting. The `app/middleware/` module contains decorators that protect routes and enforce roles. The `app/utils/` module contains shared utilities used across the entire app — database helpers, NLP parser, response formatters, and request logger.

---

## Authentication Flow

### Web Portal Flow

The web portal login starts when the user clicks "Login with GitHub". The web portal redirects to the backend `/auth/github` endpoint. The backend generates a random state value, stores it in the session, then redirects the browser to GitHub's OAuth page. After the user approves access, GitHub redirects back to the backend `/auth/github/callback` with a temporary code and the state. The backend validates the state against what was stored in the session, then exchanges the code with GitHub to get a GitHub access token. The backend uses that token to fetch the user's profile from GitHub, creates or updates the user in the database, generates its own access and refresh tokens, and redirects the browser to the web portal with the tokens in the URL. The web portal receives the tokens and sets them as HTTP-only cookies.

### CLI Flow

The CLI login starts when the user runs `insighta login`. The CLI generates a `code_verifier` and derives a `code_challenge` from it using SHA256 (PKCE). The CLI starts a temporary local server on `localhost:8765` then opens the browser to the backend `/auth/github` endpoint with the `code_challenge` as a query parameter. After the user approves on GitHub, GitHub redirects to `localhost:8765/callback` with the temporary code. The CLI's local server catches the code, shuts down, then sends a POST request to the backend `/auth/github/callback` with the code and `code_verifier`. The backend verifies the PKCE challenge, exchanges the code with GitHub, generates tokens, and returns them as JSON. The CLI saves the tokens to `~/.insighta/credentials.json` and prints "Logged in as @username".

### Why PKCE for CLI

The CLI cannot safely store a `client_secret` because it runs on the user's machine and the code can be read. PKCE replaces the need for a `client_secret` by using a mathematical proof — the CLI generates a random `code_verifier`, derives a `code_challenge` from it, and sends the challenge to GitHub upfront. When exchanging the code later, only the party that generated the original `code_verifier` can complete the exchange. Even if someone intercepts the temporary code, they cannot use it without the `code_verifier` which only exists in the CLI's memory.

---

## Token Handling

The system uses two tokens — a short-lived access token and a longer-lived refresh token. The access token expires in 3 minutes and is used on every API request. The refresh token expires in 5 minutes and is only used to get a new access token when the current one expires.

When an access token expires the client automatically calls `POST /auth/refresh` with the refresh token, receives a new access and refresh token pair, updates its stored tokens, and retries the original request. The user never sees an interruption.

Token rotation is enforced — every time the refresh token is used it is immediately invalidated and a new pair is issued. The old refresh token is stored in the database so if someone tries to use a stolen refresh token after it has already been used, the backend detects it and rejects the request.

The CLI stores tokens in `~/.insighta/credentials.json`. The web portal stores tokens in HTTP-only cookies which JavaScript cannot read, protecting against XSS attacks.

---

## Role Enforcement

The system has two roles — `admin` and `analyst`. Admins have full access and can create, delete, read, and search profiles. Analysts are read-only and can only read and search profiles.

The first user to sign up automatically gets the admin role. All subsequent users get the analyst role. Roles can be manually updated in the database.

Roles are enforced using middleware decorators that run before every route handler. Every protected route has three decorators — `@require_auth` which validates the JWT token and loads the user, `@require_api_version` which checks the `X-API-Version: 1` header, and `@require_role` which checks the user's role against the required roles for that endpoint. If any check fails the request is rejected before the route handler runs.

---

## Natural Language Search

The `/api/profiles/search?q=` endpoint accepts natural language queries like "young males from nigeria" or "adults over 30 from the US". The `nlp_parser.py` module parses these queries by extracting gender keywords, age group keywords, country references, and age ranges, then converts them into database filter parameters that are passed to the standard profile query.

---

## Rate Limiting

Auth endpoints are limited to 10 requests per minute. All other endpoints are limited to 60 requests per minute per user. Requests that exceed the limit receive a `429 Too Many Requests` response.

---

## Request Logging

Every request is logged with the HTTP method, endpoint, status code, and response time. Logs are written to both the terminal and `insighta.log`.

---

## Setup

### Prerequisites

Python 3.8 or higher, MySQL or SQLite, and two GitHub OAuth Apps — one for the web portal and one for the CLI.

### Installation

```bash
git clone https://github.com/mazi-kunle/HNG14.git
cd day3
pip install -r requirements.txt
```

The following variables are required:

```bash
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///insighta.db

GITHUB_CLIENT_ID=your_web_client_id
GITHUB_CLIENT_SECRET=your_web_client_secret
GITHUB_REDIRECT_URI=http://localhost:5000/auth/github/callback

GITHUB_CLI_CLIENT_ID=your_cli_client_id
GITHUB_CLI_CLIENT_SECRET=your_cli_client_secret
GITHUB_CLI_REDIRECT_URI=http://localhost:8765/callback

WEB_PORTAL_URL=http://localhost:3000
```


```

### Seed Database

```bash
python -m seeds.seed
```

### Run

```bash
python3 run.py
```

The server runs on `http://localhost:5000`.

---

## API Reference

### Auth Endpoints

`GET /auth/github` redirects the user to GitHub OAuth. No authentication required.

`GET /auth/github/callback` handles the OAuth callback for the web portal. GitHub redirects here after the user approves access. No authentication required.

`POST /auth/github/callback` handles the OAuth callback for the CLI. The CLI sends the code and code_verifier here. No authentication required.

`POST /auth/refresh` accepts a refresh token and returns a new access and refresh token pair. The old refresh token is immediately invalidated.

`POST /auth/logout` accepts a refresh token and invalidates it server-side. The user is logged out on all clients.

### Profile Endpoints

All profile endpoints require the `X-API-Version: 1` header and a valid Bearer token.

`GET /api/profiles` returns a paginated list of profiles. Supports filtering by gender, country, age group, min age, max age, and sorting. Available to admin and analyst.

`POST /api/profiles` creates a new profile by fetching data from external APIs. Requires a `name` in the request body. Admin only.

`GET /api/profiles/<id>` returns a single profile by ID. Available to admin and analyst.

`DELETE /api/profiles/<id>` deletes a profile by ID. Admin only.

`GET /api/profiles/search?q=` accepts a natural language query and returns matching profiles. Available to admin and analyst.

`GET /api/profiles/export?format=csv` exports profiles as a CSV file. Supports the same filters as the list endpoint. Available to admin and analyst.

`GET /api/whoami` returns the currently authenticated user's profile. Available to admin and analyst.

---

---

## Deployment

The backend is deployed on Railway. Set all environment variables in the Railway dashboard under the Variables tab.

Live URL: `https://hng14-production-81d0.up.railway.app`
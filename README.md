# SQL Generator — AI-Powered SQL from Plain English

> Built by **[backendbrilliance](https://dynamicallyblunttech.com)** · EPAM

An interactive web application that converts natural language into SQL queries using your own database schema (ERD). Upload a YAML ERD, describe what you want in plain English, and get production-ready PostgreSQL instantly.

---

## Author

| |                                                              |
|---|--------------------------------------------------------------|
| **Handle** | aagrahari                                                    |
| **Organization** | EPAM                                                         |
| **Website** | [dynamicallyblunttech.com](https://dynamicallyblunttech.com) |


- [Quick Start (Docker Hub)](#quick-start-docker-hub)
- [Publishing to Docker Hub](#publishing-to-docker-hub)
- [Features](#features)
- [ERD Format](#erd-format)
- [Installation](#installation)
  - [Local (Python)](#local-python)
  - [Docker](#docker)
  - [Docker Compose](#docker-compose)
- [LLM Provider Setup](#llm-provider-setup)
- [Using the UI](#using-the-ui)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)

---

## Quick Start (Docker Hub)

> No Python. No code. Just Docker.

```bash
docker run -d -p 5000:5000 --name sql-gen aagrahari/sql-generator:latest
```

Then open **http://localhost:5000** in your browser.

**With your API key pre-configured:**
```bash
docker run -d -p 5000:5000 \
  -e OPENAI_API_KEY=sk-... \
  -e FLASK_SECRET_KEY=your-random-secret \
  --name sql-gen \
  aagrahari/sql-generator:latest
```

**Persist uploaded ERDs across restarts:**
```bash
docker run -d -p 5000:5000 \
  -e OPENAI_API_KEY=sk-... \
  -e FLASK_SECRET_KEY=your-random-secret \
  -v ./uploads:/app/uploads \
  --name sql-gen \
  aagrahari/sql-generator:latest
```

**Useful commands:**
```bash
docker stop sql-gen          # Stop the container
docker start sql-gen         # Restart it (data preserved)
docker logs sql-gen          # View logs
docker rm -f sql-gen         # Remove container
docker pull aagrahari/sql-generator:latest  # Get latest version
```

---

## Publishing to Docker Hub

Follow these steps to build and push an updated image.

**Prerequisites:** Docker Desktop + a [Docker Hub](https://hub.docker.com) account.

```bash
# 1. Log in
docker login

# 2. Build with your Docker Hub username as prefix
docker build -t aagrahari/sql-generator:latest .

# 3. (Optional) Tag a versioned release
docker tag aagrahari/sql-generator:latest aagrahari/sql-generator:1.0

# 4. Push to Docker Hub
docker push aagrahari/sql-generator:latest
docker push aagrahari/sql-generator:1.0
```

Image is then publicly available at:
`https://hub.docker.com/r/aagrahari/sql-generator`

**To publish an update:**
```bash
docker build -t aagrahari/sql-generator:latest .
docker push aagrahari/sql-generator:latest
```

---

## Features

- 📄 **Upload your own ERD** — drag-and-drop YAML schema upload
- 💬 **Natural language → SQL** — describe what you want, get PostgreSQL back
- 🔌 **Three LLM providers** — OpenAI, GitHub Models (free tier), or local Ollama
- 🗂️ **Schema Explorer** — browse tables and columns in the sidebar
- 📋 **Query History** — last 50 queries saved in the browser
- 📥 **Copy / Download** — one-click copy or `.sql` file download
- 🐳 **Docker-ready** — single command to run anywhere

---

## ERD Format

Upload a YAML file with the following structure:

```yaml
tables:
  users:
    columns:
      id:
        type: bigserial
        notNull: true
      email:
        type: varchar(255)
        notNull: true
      created_at:
        type: timestamptz
        notNull: true
        default: now()
    constraints:
      pk_users:
        type: PRIMARY KEY
        columnNames: [id]
      uq_users_email:
        type: UNIQUE
        columnNames: [email]

  orders:
    columns:
      id:
        type: bigserial
        notNull: true
      user_id:
        type: bigint
        notNull: true
      total:
        type: numeric(10,2)
    constraints:
      pk_orders:
        type: PRIMARY KEY
        columnNames: [id]
      fk_orders_user:
        type: FOREIGN KEY
        columnNames: [user_id]
        targetTableName: users
        targetColumnNames: [id]
```

**Supported constraint types:** `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `INDEX`

---

## Installation

### Local (Python)

**Requirements:** Python 3.10+

```bash
# 1. Clone / copy the project folder
cd SQLGenerator

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or GITHUB_TOKEN

# 5. Run
python app.py
```

Open **http://localhost:5000** in your browser.

---

### Docker

**Requirements:** Docker Desktop (or Docker Engine on Linux)

```bash
# Build the image
docker build -t sql-generator .

# Run (no API key pre-configured — enter in UI settings)
docker run -p 5001:5001 sql-generator

# Run with API keys pre-configured
docker run -p 5001:5001 \
  -e OPENAI_API_KEY=sk-... \
  -e FLASK_SECRET_KEY=my-random-secret \
  sql-generator

# Persist uploaded ERDs across container restarts
docker run -p 5001:5001 \
  -v $(pwd)/uploads:/app/uploads \
  -e OPENAI_API_KEY=sk-... \
  sql-generator
```

Open **http://localhost:5001** in your browser.

---

### Docker Compose

```bash
# Copy and edit environment variables (optional)
cp .env.example .env
# Add OPENAI_API_KEY, GITHUB_TOKEN, FLASK_SECRET_KEY to .env

# Start
docker-compose up --build

# Stop
docker-compose down
```

The `uploads/` folder is mounted as a volume, so uploaded ERDs survive restarts.

---

## LLM Provider Setup

Configure the provider by clicking **"LLM Provider"** in the top-right of the UI. Three providers are supported:

### OpenAI

| Field | Value |
|---|---|
| API Key | Your OpenAI key (`sk-...`) from [platform.openai.com](https://platform.openai.com/api-keys) |
| Model | `gpt-4o-mini` (default), `gpt-4o`, `gpt-4-turbo`, etc. |

### GitHub Models (Free Tier)

| Field | Value |
|---|---|
| Token | A GitHub Personal Access Token (PAT) with `models:read` scope — [create one here](https://github.com/settings/tokens) |
| Model | `gpt-4o-mini`, `gpt-4o`, `Phi-4`, `Meta-Llama-3.1-70B-Instruct`, etc. |

GitHub Models is free for personal use with generous rate limits. No credit card required.

### Ollama (Local)

| Field | Value |
|---|---|
| Base URL | `http://localhost:11434/v1` (default) |
| Model | Any model you have pulled, e.g. `llama3.2`, `mistral`, `codellama` |

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.2
ollama serve
```

---

## Using the UI

1. **Upload ERD** — Click **"Upload ERD"** in the sidebar (or drag-and-drop a `.yaml`/`.yml` file onto the upload modal). The sidebar will populate with your tables.

2. **Browse Schema** — Click any table in the sidebar to see its columns, types, primary keys, and foreign key relationships.

3. **Write a Prompt** — Type a plain-English description in the prompt box, for example:
   - *"Show all orders placed in the last 30 days with customer email"*
   - *"Count total revenue per product category, ordered by highest first"*
   - *"Find users who haven't placed any orders"*

4. **Generate SQL** — Click **"Generate SQL"** (or press `Ctrl+Enter`). The SQL appears in the editor with syntax highlighting.

5. **Use the Result** — Copy to clipboard or download as a `.sql` file using the buttons above the editor.

6. **History** — The last 50 generated queries are saved in your browser. Click the clock icon in the toolbar to browse and reload previous queries.

7. **Remove ERD** — Click the **×** next to the ERD name in the sidebar to remove the current schema and upload a different one.

---

## API Reference

All endpoints return JSON. Errors follow `{"error": "<message>"}` with an appropriate HTTP status code.

---

### `GET /`

Serves the web application UI.

---

### `GET /api/schema`

Returns the active ERD for the current session.

**Response (ERD loaded)**
```json
{
  "tables": [
    {
      "name": "users",
      "columnCount": 4,
      "columns": [
        {
          "name": "id",
          "type": "bigserial",
          "notNull": true,
          "isPrimaryKey": true,
          "isForeignKey": false,
          "foreignKey": null
        }
      ]
    }
  ],
  "total": 1,
  "erd_name": "my-schema.yaml",
  "is_custom": true
}
```

**Response (no ERD uploaded)**
```json
{
  "tables": [],
  "total": 0,
  "erd_name": null,
  "is_custom": false
}
```

---

### `POST /api/upload-erd`

Uploads a YAML ERD file and associates it with the current session.

**Request** — `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | `.yaml` or `.yml` ERD file (max 5 MB) |

**Response (success)**
```json
{
  "success": true,
  "erd_name": "my-schema.yaml",
  "tables": [ ... ],
  "total": 12,
  "is_custom": true
}
```

**Error responses**

| HTTP | Reason |
|---|---|
| `400` | No file provided |
| `400` | File is not `.yaml` / `.yml` |
| `400` | File exceeds 5 MB |
| `400` | Invalid YAML syntax |
| `400` | Missing top-level `tables` key |
| `400` | ERD contains no tables |

---

### `POST /api/reset-erd`

Removes the uploaded ERD from the current session.

**Response**
```json
{
  "tables": [],
  "total": 0,
  "erd_name": null,
  "is_custom": false
}
```

---

### `POST /api/generate`

Generates a SQL query from a natural language prompt using the configured LLM.

**Request body** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | ✅ | Natural language description of the query |
| `provider` | string | | `openai` (default), `github`, or `ollama` |
| `model` | string | | Model name (default: `gpt-4o-mini`) |
| `api_key` | string | | API key / PAT. Falls back to environment variable if omitted |
| `base_url` | string | | Custom base URL (useful for self-hosted or Ollama) |

**Example request**
```json
{
  "prompt": "Show all customers with more than 5 orders in the last 90 days",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

**Response (success)**
```json
{
  "sql": "SELECT c.id, c.email, COUNT(o.id) AS order_count\nFROM customers c\nJOIN orders o ON o.customer_id = c.id\nWHERE o.created_at >= NOW() - INTERVAL '90 days'\nGROUP BY c.id, c.email\nHAVING COUNT(o.id) > 5\nORDER BY order_count DESC;",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "prompt_tokens": 812,
  "completion_tokens": 74
}
```

**Error responses**

| HTTP | Reason |
|---|---|
| `400` | Prompt is empty |
| `400` | No ERD uploaded |
| `400` | API key / token missing |
| `500` | LLM API error (invalid key, quota exceeded, connection refused) |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | Pre-configure OpenAI key (can also be entered in UI) |
| `GITHUB_TOKEN` | _(empty)_ | Pre-configure GitHub PAT for GitHub Models |
| `FLASK_SECRET_KEY` | `dev-secret-change-in-production` | **Change this in production.** Used to sign session cookies |
| `FLASK_DEBUG` | `true` (local) / `false` (Docker) | Enable Flask debug mode |

> **Security note:** Always set a strong, random `FLASK_SECRET_KEY` in production. You can generate one with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

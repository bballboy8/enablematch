# EnableMatch Backend

FastAPI-based backend for the EnableMatch platform. Powers AI-driven candidate analysis, Salesforce integration, and Gong call data processing.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Runtime | Python 3.12 |
| ASGI Server | Uvicorn |
| Database | MongoDB |
| AI | OpenAI GPT |
| CRM | Salesforce |
| Call Intelligence | Gong |

---

## Getting Started

### Local Development

```bash
git clone https://github.com/bballboy8/enablematch
cd enablematch

# Create virtual environment
virtualenv venv --python=python3.12
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example app/.env        # then fill in values

# Run the application
python app/application.py
```

### Docker

```bash
# Build
docker build -t enablematch .

# Run
docker run -d -p 80:80 enablematch
```

Access the application at `http://localhost` and the auto-generated API docs at `http://localhost/docs`.

---

## Environment Variables

Place these in `app/.env`:

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB connection string |
| `OPENAI_API_KEY` | OpenAI API key |
| `SALESFORCE_USERNAME` | Salesforce login username |
| `SALESFORCE_PASSWORD` | Salesforce login password |
| `SALESFORCE_SECURITY_TOKEN` | Salesforce security token |
| `GONG_API_KEY` | Gong API key |
| `GONG_API_SECRET` | Gong API secret |
| `SECRET_KEY` | JWT signing secret |

---

## Project Structure

```
app/
├── application.py           # App entry point
├── main.py                  # FastAPI app, middleware, router registration
├── controllers/             # Route handlers (thin layer, delegates to services)
│   ├── auth_controller.py
│   ├── candidate_analysis_controller.py
│   ├── gong_controller.py
│   └── salesforce_controller.py
├── services/                # Business logic
├── models/                  # ORM / data models
├── blueprints/              # Pydantic request/response schemas
├── config/                  # DB connection, constants
├── utils/                   # Helpers, dependencies, pipeline config
│   └── thirdparty/          # OpenAI, Gong, Salesforce API wrappers
├── routers/                 # Router composition
└── migrations/              # DB seed scripts
```

---

## API Reference

Base path: `/api`

> **Legend:** ✅ = actively consumed by the EnableMatch Frontend dashboard

---

### Authentication — `/api/auth`

| Method | Endpoint | Auth | Description | Frontend |
|--------|----------|:----:|-------------|:--------:|
| POST | `/auth/signin` | No | Authenticate with email + password, returns JWT | ✅ |
| POST | `/auth/signup` | No | Register a new user account | |
| POST | `/auth/token` | No | OAuth2 password-flow token endpoint (form-based) | |
| GET | `/auth/get_user_details` | Yes | Return profile of the token's owner | |

**Sign-in request/response:**

```json
// Request
{ "email": "user@example.com", "password": "secret" }

// Response
{
  "message": "Login successful",
  "token": "<JWT>",
  "user": { "id": "...", "email": "...", "name": "..." }
}
```

---

### Candidate Analysis — `/api/candidate-analysis`

| Method | Endpoint | Auth | Description | Frontend |
|--------|----------|:----:|-------------|:--------:|
| POST | `/generate-metadata-for-candidates` | Yes | Kick off background AI metadata generation for all candidates matching the supplied job requirements | ✅ |
| GET | `/list-all-metadata-generation-process` | Yes | Paginated list of all metadata generation triggers with status + progress | ✅ |
| POST | `/stop-metadata-generation-process` | Yes | Cancel a running metadata generation trigger by `trigger_id` | ✅ |
| GET | `/get-current-salesfoce-candidates` | Yes | Paginated Salesforce candidate list with optional contractor filter | ✅ |
| GET | `/get-ai-matrix-by-trigger-id` | Yes | AI-scored candidates for a trigger, with sort and min-score filtering | ✅ |
| GET | `/active-prompt-configurations` | Yes | Fetch all active AI prompt configurations (DB + code fallbacks) | ✅ |
| PUT | `/active-prompt-configurations/{prompt_key}` | Yes | Update system and/or user prompt for a given prompt key | ✅ |
| POST | `/analyze-candidate` | No | Analyse a single candidate given a job description and optional Gong call IDs / LinkedIn URL | |
| POST | `/analyze-database-candidate` | Yes | Analyse a candidate already stored in the DB | |
| GET | `/get-content-of-pdf-from-salesforce-user` | Yes | Retrieve text content of the first PDF attached to a Salesforce user | |
| PUT | `/generate-conversation-summary` | Yes | Background task: generate conversation summaries for all candidates | |
| GET | `/get-target-candidates` | Yes | Background task: fetch and store target candidates | |
| POST | `/get-candidate-suggestions-from-db` | Yes | DB-based candidate scoring for a job description | |
| POST | `/select-candidates-for-matching` | Yes | Background task: select and store best-matched candidates for a JD | |
| GET | `/get-best-candidate` | Yes | Background task: determine and store the top candidate for a JD | |
| POST | `/test-gpt` | Yes | Smoke-test the OpenAI integration | |

**`POST /generate-metadata-for-candidates` body:**

```json
{
  "job_description": "string",
  "compensation_range": "string",
  "location": "string",
  "contractors_only": false
}
```

**`GET /list-all-metadata-generation-process` query params:**

| Param | Default | Description |
|-------|---------|-------------|
| `page` | 1 | Page number |
| `page_size` | 10 | Results per page |

**`GET /get-current-salesfoce-candidates` query params:**

| Param | Default | Description |
|-------|---------|-------------|
| `page` | 1 | Page number |
| `page_size` | 10 | Results per page |
| `contractors_only` | false | Filter to contractors only |

**`GET /get-ai-matrix-by-trigger-id` query params:**

| Param | Default | Description |
|-------|---------|-------------|
| `trigger_id` | — | Required. Trigger UUID |
| `page` | 1 | Page number |
| `page_size` | 10 | Results per page |
| `sort_by` | `final_score` | Field to sort by |
| `min_score` | 0 | Minimum score filter |

**`PUT /active-prompt-configurations/{prompt_key}` body:**

```json
{
  "system_prompt": "string",
  "user_prompt": "string"
}
```

---

### Gong — `/api/gong`

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|-------------|
| GET | `/get-gong-users` | Yes | List all Gong users |
| GET | `/get-calls-by-date-range` | Yes | Fetch calls within a date range (`start_date`, optional `end_date`) |
| POST | `/get-call-transcript-by-call-id` | Yes | Retrieve transcripts for one or more call IDs |
| GET | `/get-gong-extensive-call-data` | No | Bulk-load extensive Gong call data |
| GET | `/get-matching-calls` | No | Search calls by title keyword (`search_query`) |
| GET | `/collect-call-transcripts` | Yes | Background task: collect and store all call transcripts |

---

### Salesforce — `/api/salesforce`

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|-------------|
| GET | `/get-salesforce-data` | Yes | Run an arbitrary SOQL `query` |
| GET | `/get-salesforce-contacts` | Yes | List all Salesforce contacts |
| POST | `/create-salesforce-contact` | Yes | Create a contact (`full_name`, `email`) |
| POST | `/upload-resume` | Yes | Upload a resume file and link it to a Salesforce record |
| GET | `/get-linked-files` | Yes | Get files linked to a record by `linked_entity_id` |
| GET | `/download-file` | Yes | Download a file by `content_document_id` |
| GET | `/get-salesforce-user-first-document` | Yes | Get the first document attached to a user |
| POST | `/attach-note-to-user` | Yes | Attach a note (`note_title`, `note_body`) to a Salesforce user |
| GET | `/get-salesforce-user-notes` | Yes | Get all notes for a Salesforce user |
| GET | `/get-salesforce-users` | Yes | List all Salesforce users stored in the DB |
| PUT | `/assign-current-ote-user-to-salesforce-users` | Yes | Sync OTE values from Salesforce into the DB |
| GET | `/fetch-gong-conversation-ids-by-email` | Yes | Fetch Gong conversation IDs for a candidate by email |
| GET | `/get-each-table-count` | Yes | Return row count for each database table |
| PUT | `/assign-gong-conversation-id-to-all-user` | Yes | Background task: match and assign Gong IDs to all candidates |
| GET | `/run-raw-salesforce-query` | Yes | Background task: run a raw Salesforce test query |
| PUT | `/convert-tinyurl-to-linkedin` | Yes | Background task: expand TinyURL LinkedIn links |
| PUT | `/add-current-ote-to-candidates-blob` | Yes | Background task: write OTE values into candidate blob |
| POST | `/sync-salesforce-users` | Yes | Background task: full Salesforce ↔ DB user sync (also runs automatically every 10 minutes) |

---

## Frontend-Consumed Endpoints Summary

The following 8 endpoints are actively called by the [EnableMatch Frontend](https://github.com/bballboy8/enablematch-frontend) dashboard:

| Method | Endpoint | Used In |
|--------|----------|---------|
| POST | `/api/auth/signin` | Login page |
| POST | `/api/candidate-analysis/generate-metadata-for-candidates` | Dashboard — trigger metadata generation |
| GET | `/api/candidate-analysis/list-all-metadata-generation-process` | Dashboard — ProcessList widget |
| POST | `/api/candidate-analysis/stop-metadata-generation-process` | Dashboard — ProcessList widget |
| GET | `/api/candidate-analysis/get-current-salesfoce-candidates` | Candidates page |
| GET | `/api/candidate-analysis/get-ai-matrix-by-trigger-id` | AI Matrix page |
| GET | `/api/candidate-analysis/active-prompt-configurations` | AI Prompts page |
| PUT | `/api/candidate-analysis/active-prompt-configurations/{prompt_key}` | AI Prompts page |

---

## Background Tasks

Several endpoints enqueue work as FastAPI `BackgroundTasks` (fire-and-forget). In addition, one periodic task runs automatically:

| Task | Trigger | Frequency |
|------|---------|-----------|
| Salesforce user sync | Startup + periodic | Every 10 minutes |
| Metadata generation | `POST /generate-metadata-for-candidates` | On demand |
| Conversation summary generation | `PUT /generate-conversation-summary` | On demand |
| Target candidate fetch | `GET /get-target-candidates` | On demand |
| Vector store upload | `PUT /upload-cooked-records-to-pinecone` | On demand |
| Candidate matching selection | `POST /select-candidates-for-matching` | On demand |
| Gong transcript collection | `GET /collect-call-transcripts` | On demand |
| Gong ID assignment | `PUT /assign-gong-conversation-id-to-all-user` | On demand |

---

## Code Quality

```bash
ruff --output-format=github .
```

## Stopping Docker

```bash
docker stop $(docker ps -q --filter ancestor=enablematch)
```

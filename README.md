# FOSSEE Secure Login System

A secure authentication system built as part of the FOSSEE Autumn Fellowship screening task. This project implements the same login/auth functionality using **two different backend approaches** — a custom Flask+PostgreSQL backend and Appwrite BaaS — and compares them side-by-side using a single unified frontend.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Implementation 1: Custom REST Backend](#implementation-1-custom-rest-backend-flask--postgresql)
- [Implementation 2: Appwrite Backend](#implementation-2-appwrite-backend-as-a-service)
- [Frontend Integration Approach](#frontend-integration-approach)
- [How to Run](#how-to-run)
- [API Endpoints](#api-endpoints)
- [Security Features](#security-features)
- [JWT vs Session-Based Auth](#jwt-vs-session-based-auth)
- [Logout Mechanism](#logout-mechanism)
- [Comparison: Custom Backend vs Appwrite](#comparison-custom-backend-vs-appwrite)
- [Project Structure](#project-structure)

---

## Architecture Overview

The project uses a **single `index.html` frontend** with a mode-switching mechanism. The user selects one of three backend modes via radio buttons in the GUI:

```
                          ┌──────────────────────┐
                          │   index.html (GUI)   │
                          │   Mode Selector:      │
                          │   ○ Mock              │
                          │   ○ Custom REST       │
                          │   ○ Appwrite          │
                          └──────┬───────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
     ┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐
     │  mock-api.js  │  │  Flask Backend   │  │ appwrite-adapter │
     │  (in-browser) │  │  (Python/REST)   │  │  (Web SDK)       │
     │               │  │                  │  │                  │
     │ seed-data.json│  │  PostgreSQL DB   │  │  Appwrite Cloud  │
     └──────────────┘  └─────────────────┘  └──────────────────┘
```

Each function (`doRegister()`, `doLogin()`, `getMe()`, etc.) checks the selected mode and dispatches to the correct implementation:
- **Mock** → `mock-api.js` (in-browser simulation, no backend needed)
- **Custom REST** → Flask backend via `fetch()` HTTP requests
- **Appwrite** → Appwrite Cloud via Web SDK (`appwrite-adapter.js`)

---

## Implementation 1: Custom REST Backend (Flask + PostgreSQL)

**Tech Stack:** Python 3.10+, Flask, PostgreSQL, SQLAlchemy, JWT (PyJWT), bcrypt, Flask-Limiter

### How Authentication Works

1. **Registration** (`POST /register`):
   - User submits email + password
   - Password is hashed using **bcrypt** with automatic salting (never stored in plaintext)
   - New user record is created in PostgreSQL

2. **Login** (`POST /login`):
   - Server verifies email exists and password matches the bcrypt hash
   - On success, generates a **JWT token** containing `user_id`, `email`, and `exp` (expiration)
   - Token is signed with `SECRET_KEY` using HS256 algorithm
   - Token is valid for **24 hours**

3. **Protected Routes** (`GET /me`, `GET /files`, etc.):
   - The `@token_required` decorator extracts the JWT from the `Authorization: Bearer <token>` header
   - It checks the `blacklisted_tokens` table (for logged-out tokens)
   - It decodes and verifies the JWT signature and expiration
   - It fetches the user from the database and passes it to the route handler

4. **Logout** (`POST /logout`):
   - The current JWT is added to the `blacklisted_tokens` database table
   - The middleware rejects any future requests with that token
   - See [Logout Mechanism](#logout-mechanism) for detailed explanation

5. **File Access Control** (`GET /files/:id`):
   - Files are filtered by `user_id` — users only see their own files
   - Accessing another user's file returns **403 Forbidden** (not 404)
   - This distinction is important: 404 = "doesn't exist", 403 = "exists but not yours"

### Database Schema

```
┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│       users          │     │       files          │     │  blacklisted_tokens  │
├─────────────────────┤     ├─────────────────────┤     ├──────────────────────┤
│ id (PK)             │◄────│ user_id (FK)         │     │ id (PK)              │
│ email (unique)      │     │ id (PK)              │     │ token (unique, TEXT)  │
│ password (bcrypt)   │     │ filename             │     │ blacklisted_at       │
│ full_name           │     │ file_path            │     └──────────────────────┘
│ created_at          │     │ file_size            │
└─────────────────────┘     │ uploaded_at          │
                            └─────────────────────┘
```

---

## Implementation 2: Appwrite Backend-as-a-Service

**Tech Stack:** Appwrite Cloud, Appwrite Web SDK (frontend), Appwrite Python SDK (seeding)

### How Authentication Works

1. **Registration**: Appwrite's built-in `account.create()` handles user creation with automatic password hashing.
2. **Login**: `account.createEmailPasswordSession()` creates a secure session. Appwrite manages session tokens internally.
3. **Logout**: `account.deleteSession('current')` destroys the active session server-side.
4. **Protected Routes**: The Appwrite SDK automatically attaches session cookies. If no session exists, API calls fail with 401.
5. **File Access Control**: Uses **document-level permissions**. Each file document is created with `Permission.read(Role.user(userId))` — only the owner can see it. Other users get a 404 (the document is invisible to them). This is proper Row Level Security.

### Appwrite Console Setup

To reproduce the Appwrite setup, the evaluator should:

1. **Create Project** at [cloud.appwrite.io](https://cloud.appwrite.io)
2. **Add Web Platform**: Type = JavaScript, Hostname = `localhost`
3. **Create Database**: Name = `fossee_db`
4. **Create Table/Collection** inside the database: Name = `files`
5. **Add Columns/Attributes** to the `files` table:

   | Key        | Type    | Size | Required |
   |------------|---------|------|----------|
   | `user_id`  | String  | 255  | Yes      |
   | `filename` | String  | 255  | Yes      |
   | `file_path`| String  | 500  | Yes      |
   | `file_size`| Integer | —    | No       |

6. **Table Permissions**: Add role "Users" with "Create" permission only (document-level permissions handle read/update/delete)
7. **Create Storage Bucket**: Name = `user-files`, Permissions = Users (Create, Read)
8. **Create API Key** (for the Python seed script): Name = `fossee-backend`, Scopes = All
9. **Update `.env`** with your Project ID, Database ID, and API Key
10. **Run seed script**: `python appwrite_seed.py`

---

## Frontend Integration Approach

The FOSSEE-provided `index.html` GUI is used as-is (no visual changes). The JavaScript functions have been modified to support **conditional backend switching**:

```javascript
async function doLogin() {
  const mode = getMode();  // 'mock', 'custom', or 'appwrite'

  if (mode === 'mock')     result = mockLogin(email, password);
  if (mode === 'appwrite') result = await appwriteLogin(email, password);
  if (mode === 'custom')   result = await request('/login', { ... });
}
```

### Files Added/Modified

| File | Purpose |
|------|---------|
| `client/index.html` | Modified JS to dispatch based on selected backend mode |
| `client/mock-api.js` | In-browser mock API (no backend needed) |
| `client/seed-data.json` | Test data for mock mode |
| `client/appwrite-adapter.js` | Appwrite Web SDK bridge functions |

---

## How to Run

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running
- A modern web browser

### Step 1: Install Dependencies

```bash
cd fossee
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL password and Appwrite credentials
```

### Step 3: Run Custom Backend (Phase 1)

```bash
python create_db.py     # Create database tables
python seed.py          # Seed 3 test users with files
python run.py           # Start Flask server at http://127.0.0.1:5000
```

### Step 4: Seed Appwrite Backend (Phase 2)

```bash
# First set up Appwrite console (see Appwrite Console Setup above)
# Then update .env with your Appwrite credentials
python appwrite_seed.py   # Seed users and files into Appwrite
```

### Step 5: Test with Frontend

1. Open `client/index.html` in your browser
2. **Custom REST mode**: Select "Custom REST backend", set Base URL to `http://127.0.0.1:5000`
3. **Appwrite mode**: Select "Appwrite", enter your Project ID and Database ID
4. **Mock mode**: Select "Mock" (works without any backend)
5. Use the quick-fill buttons to test with seeded users (password: `Password123!`)

---

## API Endpoints

### Authentication

| Method | Endpoint    | Description              | Auth Required |
|--------|-------------|--------------------------|---------------|
| POST   | `/register` | Create a new user        | No            |
| POST   | `/login`    | Authenticate & get JWT   | No            |
| POST   | `/logout`   | Blacklist current token  | Yes (Bearer)  |

### Protected Routes

| Method | Endpoint       | Description                 | Auth Required |
|--------|----------------|-----------------------------|---------------|
| GET    | `/me`          | Get current user's profile  | Yes (Bearer)  |
| GET    | `/files`       | List current user's files   | Yes (Bearer)  |
| GET    | `/files/:id`   | Get a specific file by ID   | Yes (Bearer)  |

### Example: Login → Get Files → Access Control

```
1. LOGIN
   POST /login  { "email": "alice@example.com", "password": "Password123!" }
   → 200 { "message": "Login successful", "token": "eyJhbG..." }

2. GET MY FILES (as Alice)
   GET /files   Authorization: Bearer eyJhbG...
   → 200 { "files": [{ "id": 1, "filename": "report.pdf" }, ...], "count": 2 }

3. ACCESS ANOTHER USER'S FILE (as Alice, trying Bob's file)
   GET /files/3  Authorization: Bearer eyJhbG...
   → 403 { "error": "Access denied — this file does not belong to you" }
```

---

## Security Features

| Feature                  | Custom Backend                          | Appwrite                          |
|--------------------------|-----------------------------------------|-----------------------------------|
| Password Storage         | bcrypt hash + auto salt                 | Argon2 (built-in)                 |
| Authentication           | JWT (HS256, 24h expiry)                 | Session-based (built-in)          |
| Logout                   | Server-side token blacklist             | Server-side session deletion      |
| Rate Limiting            | 5 login attempts/min (Flask-Limiter)    | Built-in abuse protection         |
| Error Message Security   | Generic "Invalid email or password"     | Generic errors (built-in)         |
| File Access Control      | Manual user_id check (403 vs 404)       | Document-level permissions (RLS)  |
| CORS                     | Flask-CORS                              | Built-in CORS config              |

---

## JWT vs Session-Based Auth

| Aspect              | JWT (Custom Backend)                   | Session-Based (Appwrite)               |
|---------------------|----------------------------------------|----------------------------------------|
| Storage             | Token in client (localStorage/header)  | Session ID in HTTP-only cookie         |
| Server State        | Stateless — no server session store    | Stateful — session on server           |
| Scalability         | Horizontally scalable (no shared state)| Requires shared session store          |
| Expiration          | Built into token (`exp` claim)         | Server controls timeout                |
| Logout              | Requires blacklist table               | Simply delete session on server        |
| Mobile Friendly     | Yes (no cookie dependency)             | Harder (cookies unreliable on mobile)  |
| Security Risk       | Token theft = access until expiry      | Session fixation/hijacking possible    |

### Why JWT for the Custom Backend?
1. **Stateless**: No server-side session storage needed — the token itself contains all auth info
2. **Scalable**: Works across multiple servers without shared state
3. **Self-contained**: The `user_id` and `exp` are embedded in the token payload
4. **Trade-off accepted**: The need for a blacklist table on logout is a small price for statelessness

### Why Sessions for Appwrite?
Appwrite uses session-based auth internally because:
1. It manages everything server-side with HTTP-only secure cookies
2. Logout is instant — just delete the session (no blacklist needed)
3. It's more secure by default (tokens can't be stolen from JavaScript)

---

## Logout Mechanism

### The Challenge with JWT
JWT tokens are **self-contained and stateless**. Once a token is issued, it remains valid until its `exp` time. There is no built-in "revoke" mechanism in the JWT spec.

### Solution: Token Blacklisting

```
                     ┌─────────────┐
  POST /logout  ───► │ Add token   │
                     │ to blacklist│
                     │   table     │
                     └──────┬──────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  blacklisted_tokens     │
              │  ┌─────┬──────────────┐ │
              │  │ id  │ token (hash) │ │
              │  ├─────┼──────────────┤ │
              │  │ 1   │ eyJhbG...    │ │
              │  │ 2   │ eyJhbG...    │ │
              │  └─────┴──────────────┘ │
              └─────────────────────────┘
                            │
                  On every protected request:
                            │
                            ▼
              ┌─────────────────────────┐
              │  @token_required checks:│
              │  1. Token in header?    │
              │  2. Token blacklisted?  │──► YES → 401 Unauthorized
              │  3. Token valid/signed? │
              │  4. Token not expired?  │
              │  5. User exists in DB?  │
              └─────────────────────────┘
                            │
                        ALL PASS
                            │
                            ▼
                  Route handler executes
```

### Flow
1. User calls `POST /logout` with their JWT
2. The token is stored in the `blacklisted_tokens` table
3. On subsequent requests, the `@token_required` middleware queries this table
4. If the token is found → reject with 401 ("Token has been logged out")
5. Otherwise → proceed normally

### Trade-offs
| Pro | Con |
|-----|-----|
| Simple to implement | Extra DB query on every protected request |
| Works with existing database | Blacklist table grows over time |
| Effective invalidation | Could use Redis for better performance |

### Alternative: Appwrite's Approach
Appwrite avoids this problem entirely — it uses server-side sessions, so logout simply deletes the session record. No blacklist needed.

---

## Comparison: Custom Backend vs Appwrite

| Aspect                | Custom Backend (Flask)                  | Appwrite                              |
|-----------------------|-----------------------------------------|---------------------------------------|
| **Setup Time**        | Hours (DB schema, routes, middleware)   | Minutes (console clicks)              |
| **Auth Code**         | ~200 lines (bcrypt, JWT, blacklist)     | 0 lines (built-in)                    |
| **Database**          | PostgreSQL + SQLAlchemy ORM             | Appwrite Document DB                  |
| **File Security**     | Manual `user_id` check (403/404)        | Document-level permissions (RLS)      |
| **Rate Limiting**     | Flask-Limiter (manual config)           | Built-in abuse protection             |
| **Customization**     | Full control over every detail          | Limited to Appwrite's API surface     |
| **Learning Value**    | Very High — understand auth internals   | Lower — abstracted away               |
| **Production Ready**  | Needs hardening (HTTPS, Redis, etc.)    | Production-ready out of the box       |
| **Cost**              | Server hosting costs                    | Free tier available                   |
| **Vendor Lock-in**    | None — fully portable code              | Tied to Appwrite ecosystem            |

### Verdict
- **Custom Backend** excels at teaching how authentication actually works under the hood
- **Appwrite** excels at rapid development and enterprise-grade security out of the box
- For a production application with tight deadlines, Appwrite saves weeks of development
- For learning and full control, a custom backend is invaluable

---

## Project Structure

```
fossee/
├── app/                          # Custom Flask Backend (Phase 1)
│   ├── __init__.py               # App factory, extensions, blueprint registration
│   ├── config.py                 # Environment variable loading
│   ├── models.py                 # SQLAlchemy models (User, File, BlacklistedToken)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py               # POST /register, /login, /logout
│   │   ├── user.py               # GET /me
│   │   └── files.py              # GET /files, GET /files/:id
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py    # @token_required JWT verification decorator
│   └── utils/
│       ├── __init__.py
│       └── security.py           # bcrypt hash/verify utilities
│
├── client/                       # Frontend (all 3 modes)
│   ├── index.html                # GUI with mode-switching logic
│   ├── mock-api.js               # In-browser mock API
│   ├── seed-data.json            # Test data for mock mode
│   └── appwrite-adapter.js      # Appwrite Web SDK bridge
│
├── run.py                        # Flask dev server entry point
├── create_db.py                  # PostgreSQL table creation
├── seed.py                       # Seed script — Custom Backend
├── appwrite_seed.py              # Seed script — Appwrite
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Excludes .env, __pycache__, venv
└── README.md                     # This file
```

---

## Test Credentials

All seeded users share the same password for easy testing:

| User  | Email               | Password       |
|-------|---------------------|----------------|
| Alice | alice@example.com   | Password123!   |
| Bob   | bob@example.com     | Password123!   |
| Carol | carol@example.com   | Password123!   |

---

## Video Demo Checklist

For the submission video, demonstrate:

1. **Custom Backend Mode**
   - Start Flask server (`python run.py`)
   - Register a new user → show 201 response
   - Login → show JWT token auto-filled
   - GET /me → show user profile
   - GET /files → show user's files
   - GET /files/:id with another user's file → show 403
   - Logout → show token cleared
   - Try GET /me after logout → show 401

2. **Appwrite Mode**
   - Switch to Appwrite mode in GUI
   - Enter Project ID and Database ID
   - Login → show session created
   - GET /me → show profile from Appwrite
   - GET /files → show files from Appwrite database
   - Logout → show session destroyed

3. **Explain the Architecture**
   - How mode-switching works in `index.html`
   - JWT flow (custom backend) vs Session flow (Appwrite)
   - Token blacklisting for logout
   - Document-level permissions in Appwrite

---

## Author

Built as part of the **FOSSEE Autumn Fellowship 2026** screening task.

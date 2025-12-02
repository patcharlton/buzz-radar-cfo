# Buzz Radar CFO Dashboard

A web-based AI CFO advisor for Buzz Radar Limited that connects to Xero accounting software, pulls financial data, and displays key metrics on a dashboard.

## Phase 1 Features

- Xero OAuth2 integration
- Real-time cash position across all bank accounts
- Outstanding receivables and payables tracking
- Overdue invoice highlighting
- Profit & Loss summary for current month
- Manual data sync capability

## Prerequisites

- Python 3.9+
- Node.js 18+
- Xero Developer Account

## Setup

### 1. Xero App Registration

1. Go to [Xero Developer Portal](https://developer.xero.com/app/manage)
2. Create a new app with:
   - App name: "Buzz Radar CFO"
   - Company or application URL: `http://localhost:5173`
   - Redirect URI: `http://localhost:5000/callback`
3. Note your Client ID and Client Secret

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp ../.env.example .env
```

Edit `.env` with your Xero credentials:

```env
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
XERO_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=generate_a_random_secret_key_here
DATABASE_URL=sqlite:///cfo.db
ENCRYPTION_KEY=your_32_byte_base64_encoded_key
```

Generate an encryption key:
```python
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
```

Start the backend:
```bash
python app.py
```

The backend runs on http://localhost:5000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend runs on http://localhost:5173

## Usage

1. Open http://localhost:5173 in your browser
2. Click "Connect to Xero"
3. Authorize the app with your Xero account
4. View your financial dashboard

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Initiate Xero OAuth flow |
| GET | `/callback` | Handle OAuth callback |
| GET | `/auth/status` | Check connection status |
| POST | `/auth/disconnect` | Disconnect from Xero |
| GET | `/api/dashboard` | Get all dashboard data |
| GET | `/api/cash-position` | Get bank balances |
| GET | `/api/receivables` | Get outstanding invoices |
| GET | `/api/payables` | Get bills to pay |
| GET | `/api/pnl` | Get P&L summary |
| POST | `/api/sync` | Trigger data refresh |

### History & Metrics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history/snapshots` | Get historical monthly snapshots (last 60 months) |
| GET | `/api/history/cash` | Get cash position trend with dates |
| GET | `/api/history/revenue` | Get revenue with MoM% and YoY% |
| GET | `/api/history/trends` | Get combined trends for sparklines |
| GET | `/api/metrics/runway` | Get runway months and avg monthly burn |
| POST | `/api/history/backfill` | Trigger historical data backfill from Xero |
| POST | `/api/history/snapshot` | Manually trigger snapshot capture |

## Project Structure

```
buzz-radar-cfo/
├── backend/
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration (SQLite/PostgreSQL)
│   ├── wsgi.py                # WSGI entry point
│   ├── requirements.txt
│   ├── xero/
│   │   ├── auth.py            # OAuth2 handling
│   │   ├── client.py          # Xero API wrapper
│   │   └── models.py          # Data models
│   ├── database/
│   │   ├── db.py              # Database setup
│   │   └── models.py          # SQLAlchemy models
│   ├── routes/
│   │   ├── auth_routes.py     # OAuth routes
│   │   ├── data_routes.py     # Core API endpoints
│   │   ├── ai_routes.py       # AI analysis endpoints
│   │   ├── history_routes.py  # Historical data endpoints
│   │   └── projection_routes.py
│   ├── scripts/
│   │   └── backfill_history.py  # Historical data backfill
│   ├── jobs/
│   │   └── capture_snapshot.py  # Monthly snapshot capture
│   ├── ai/
│   │   ├── claude_client.py   # Claude API wrapper
│   │   ├── prompts.py         # AI prompt templates
│   │   └── cache.py           # AI response caching
│   └── context/               # Business context YAML files
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── dashboard/     # Dashboard cards
│       │   ├── charts/        # Chart components (Sparkline, etc.)
│       │   ├── ui/            # Shadcn/UI components
│       │   └── layout/        # Navigation
│       └── services/
│           └── api.js
├── .env.example
├── .gitignore
└── README.md
```

## Historical Data Management

### Backfilling Historical Data

To populate historical P&L data from Xero (up to 5 years):

```bash
cd backend

# Dry run to see what would be captured
python -m backend.scripts.backfill_history --dry-run

# Run actual backfill (60 months by default)
python -m backend.scripts.backfill_history

# Backfill only last 24 months
python -m backend.scripts.backfill_history --months 24
```

### Monthly Snapshot Capture

Capture current financial snapshot (designed to run monthly via cron):

```bash
cd backend

# Dry run
python -m backend.jobs.capture_snapshot --dry-run

# Capture actual snapshot
python -m backend.jobs.capture_snapshot
```

For Render, set up a scheduled job with:
- Command: `python -m backend.jobs.capture_snapshot`
- Schedule: First of each month

## Database

The application supports both SQLite (development) and PostgreSQL (production).

### PostgreSQL Setup (Render)

1. Create a PostgreSQL database on Render
2. Add the internal database URL as `DATABASE_URL` environment variable
3. The app automatically converts `postgres://` to `postgresql://` for SQLAlchemy compatibility
4. Tables are created automatically on first run via `db.create_all()`

### Database Models

- `monthly_snapshots`: Historical monthly financial data (P&L, cash, AR/AP)
- `account_balances_history`: Individual account balance trends
- `xero_tokens`: Encrypted OAuth tokens
- `ai_cache`: Cached AI responses with TTL

## Security Notes

- Tokens are encrypted at rest using Fernet symmetric encryption
- OAuth state parameter prevents CSRF attacks
- Access tokens auto-refresh before expiry
- Never commit `.env` file

## Features

- **AI CFO Analysis**: Claude-powered daily insights and Q&A
- **Cash Runway**: Calculated runway based on 6-month burn rate
- **Historical Trends**: Sparklines showing 12-month trends
- **YoY Comparisons**: Year-over-year growth indicators
- **Financial Projections**: 3-month forward projections
- **Anomaly Detection**: AI-powered financial anomaly alerts
- **Pipeline Integration**: Notion or YAML-based sales pipeline

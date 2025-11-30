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

## Project Structure

```
buzz-radar-cfo/
├── backend/
│   ├── app.py                 # Flask application
│   ├── config.py              # Configuration
│   ├── requirements.txt
│   ├── xero/
│   │   ├── auth.py            # OAuth2 handling
│   │   ├── client.py          # Xero API wrapper
│   │   └── models.py          # Data models
│   ├── database/
│   │   ├── db.py              # Database setup
│   │   └── models.py          # SQLAlchemy models
│   └── routes/
│       ├── auth_routes.py     # OAuth routes
│       └── data_routes.py     # API endpoints
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── Dashboard.jsx
│       │   ├── CashPosition.jsx
│       │   ├── Receivables.jsx
│       │   ├── Payables.jsx
│       │   ├── ProfitLoss.jsx
│       │   └── InvoiceList.jsx
│       └── services/
│           └── api.js
├── .env.example
├── .gitignore
└── README.md
```

## Security Notes

- Tokens are encrypted at rest using Fernet symmetric encryption
- OAuth state parameter prevents CSRF attacks
- Access tokens auto-refresh before expiry
- Never commit `.env` file

## Next Phase (Phase 2)

- Claude AI integration for financial analysis
- Daily recommendations based on data
- Chat interface for questions
- Business context integration

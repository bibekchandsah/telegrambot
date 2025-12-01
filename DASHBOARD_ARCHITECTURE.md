# Admin Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ADMIN DASHBOARD                          │
│                     (Web-Based Interface)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                         │
├─────────────────────────────────────────────────────────────────┤
│  templates/dashboard.html                                       │
│  ├── Statistics Cards (5 metrics)                               │
│  ├── Navigation Tabs (All Users, Online, Chat, Queue, Search)   │
│  ├── User Tables (with pagination)                              │
│  ├── Search Form (filters)                                      │
│  └── User Detail Modal                                          │
│                                                                  │
│  static/css/dashboard.css                                       │
│  └── Responsive styling, gradients, animations                  │
│                                                                  │
│  static/js/dashboard.js                                         │
│  ├── AJAX API calls                                             │
│  ├── Real-time updates (30s interval)                           │
│  ├── Tab navigation                                             │
│  ├── Pagination logic                                           │
│  └── Search functionality                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/AJAX
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND (Flask API)                           │
├─────────────────────────────────────────────────────────────────┤
│  admin_dashboard.py                                             │
│  ├── Route: GET /                        → Dashboard HTML       │
│  ├── Route: GET /api/stats               → Statistics          │
│  ├── Route: GET /api/users               → All users (paged)   │
│  ├── Route: GET /api/users/online        → Online users        │
│  ├── Route: GET /api/users/in-chat       → Users in chat       │
│  ├── Route: GET /api/users/in-queue      → Queue users         │
│  ├── Route: GET /api/users/search        → Search results      │
│  ├── Route: GET /api/users/<id>          → User details        │
│  ├── Route: GET /api/users/<id>/history  → Chat history        │
│  └── Route: GET /health                  → Health check        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  src/services/dashboard.py                                      │
│  ├── get_statistics()            → Aggregate stats              │
│  ├── get_all_users_paginated()   → User list with pagination    │
│  ├── get_online_users()          → Active users (queue + chat)  │
│  ├── get_users_in_chat()         → Chat sessions with partners  │
│  ├── get_users_in_queue()        → Waiting users                │
│  ├── search_users()              → Multi-criteria search        │
│  ├── get_user_details()          → Complete user profile        │
│  ├── get_user_chat_history()     → User chat logs               │
│  └── _get_user_info()            → Helper: fetch profile        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REDIS CLIENT                                  │
├─────────────────────────────────────────────────────────────────┤
│  src/db/redis_client.py                                         │
│  ├── get(key)                    → Get value                    │
│  ├── scan(cursor, match, count)  → Iterate keys                 │
│  ├── lrange(key, start, end)     → List range                   │
│  ├── llen(key)                   → List length                  │
│  ├── smembers(key)               → Set members                  │
│  └── Connection pooling (max 10 connections)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REDIS DATABASE                             │
├─────────────────────────────────────────────────────────────────┤
│  Data Structures:                                               │
│  ├── bot:all_users (SET)         → All user IDs                │
│  ├── profile:{user_id} (JSON)    → User profiles               │
│  ├── state:{user_id} (STRING)    → Current state               │
│  ├── pair:{user_id} (STRING)     → Chat partner ID             │
│  ├── queue:waiting (LIST)        → Waiting queue               │
│  ├── preferences:{user_id} (JSON)→ User preferences            │
│  └── history:{user_id}:* (JSON)  → Chat history (future)       │
└─────────────────────────────────────────────────────────────────┘


DATA FLOW EXAMPLES:
═══════════════════

1. View Statistics
   ────────────────
   Browser → GET /api/stats
   Flask → dashboard.get_statistics()
   Service → Redis queries (SMEMBERS, LLEN, SCAN)
   Redis → Return counts
   Service → Aggregate data
   Flask → JSON response
   Browser → Update UI cards


2. View All Users (Page 1)
   ────────────────────────
   Browser → GET /api/users?page=1&per_page=20
   Flask → dashboard.get_all_users_paginated(1, 20)
   Service → Redis: SMEMBERS bot:all_users
   Service → For each user: GET profile:{user_id}
   Service → Sort, paginate, return slice
   Flask → JSON response with pagination info
   Browser → Render table + pagination controls


3. Search User by Gender
   ──────────────────────
   Browser → GET /api/users/search?gender=Male
   Flask → dashboard.search_users(gender="Male")
   Service → Redis: SMEMBERS bot:all_users
   Service → For each: GET profile:{user_id}, filter by gender
   Service → Return matching users
   Flask → JSON response
   Browser → Display results table


4. View User Details
   ─────────────────
   Browser → GET /api/users/123456789
   Flask → dashboard.get_user_details(123456789)
   Service → Multiple Redis queries:
            - GET profile:123456789
            - GET state:123456789
            - GET pair:123456789
            - GET preferences:123456789
            - LRANGE queue:waiting (check if in queue)
   Service → Aggregate all data
   Flask → JSON response
   Browser → Display in modal popup


5. Monitor Users in Chat
   ──────────────────────
   Browser → GET /api/users/in-chat
   Flask → dashboard.get_users_in_chat()
   Service → Redis: SCAN pair:*
   Service → For each pair: GET user profile + partner ID
   Service → Return list with partner info
   Flask → JSON response
   Browser → Render table with partner column


SECURITY FLOW (Future):
════════════════════════

┌──────────┐  Login    ┌──────────┐  Auth Token  ┌──────────┐
│  Browser │ ────────> │  Flask   │ ───────────> │  Session │
└──────────┘           │  Auth    │              │  Store   │
     │                 └──────────┘              └──────────┘
     │ Include Token                                   │
     │ in Headers                                      │
     ▼                                                 ▼
┌──────────┐  Verify   ┌──────────┐  Check      ┌──────────┐
│  API     │ ────────> │  Flask   │ ───────────>│  Redis   │
│  Request │           │  Verify  │             │  Session │
└──────────┘           └──────────┘             └──────────┘


DEPLOYMENT ARCHITECTURE:
════════════════════════

Production Setup:

                    Internet
                       │
                       ▼
              ┌────────────────┐
              │   Firewall     │
              │   Port 443     │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   nginx/Apache │
              │   Reverse Proxy│
              │   SSL/TLS      │
              └────────────────┘
                       │
                       ▼
        ┌──────────────┴──────────────┐
        │                              │
        ▼                              ▼
┌───────────────┐            ┌─────────────────┐
│ Telegram Bot  │            │ Flask Dashboard │
│ (bot.py)      │            │ (port 5000)     │
│ Port: Webhook │            │ Internal only   │
└───────────────┘            └─────────────────┘
        │                              │
        │                              │
        └──────────────┬───────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Redis Server  │
              │  Port 6379     │
              │  Password Auth │
              └────────────────┘


FILE STRUCTURE:
═══════════════

admin_dashboard.py          # Entry point
├── Flask app initialization
├── Route definitions
├── Async wrapper functions
└── Server startup

src/services/dashboard.py  # Business logic
├── DashboardService class
├── Data fetching methods
├── Search algorithms
└── Data aggregation

templates/dashboard.html    # UI markup
├── Header & stats cards
├── Tab navigation
├── User tables
├── Search form
└── Modal dialogs

static/css/dashboard.css    # Styling
├── Layout (grid, flex)
├── Colors & gradients
├── Responsive breakpoints
└── Animations

static/js/dashboard.js      # Client logic
├── API communication
├── DOM manipulation
├── Event handlers
└── State management


CONFIGURATION:
══════════════

.env file:
├── BOT_TOKEN              # Telegram bot
├── REDIS_URL              # Database
├── DASHBOARD_PORT=5000    # Web port
├── DASHBOARD_HOST=0.0.0.0 # Bind address
└── ENVIRONMENT=development # Mode


MONITORING & LOGGING:
════════════════════

┌──────────────┐
│   Browser    │
│   Console    │ ← JavaScript logs
└──────────────┘

┌──────────────┐
│   Flask      │
│   Logs       │ ← Request logs, errors
└──────────────┘

┌──────────────┐
│   Redis      │
│   Monitor    │ ← Key operations, slow queries
└──────────────┘

┌──────────────┐
│   System     │
│   Logs       │ ← Resource usage, uptime
└──────────────┘

# Architecture - Energy Dashboard

## 🏗️ System Architecture

This document describes the architecture, design patterns, and component relationships in the Energy Dashboard system.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Data Flow](#data-flow)
5. [Integration Patterns](#integration-patterns)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Design Patterns](#design-patterns)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                                                                  │
│  Pages → Components → Store (Zustand) → API Client → Routes     │
└────────────────────────────────────────┬────────────────────────┘
                                         │ HTTP/REST
                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI/Python)                     │
│                                                                  │
│  Routes → Schemas → Services → Data Layer → External APIs       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Agents (Data Ingestion, Email Scheduling)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Integrations: SharePoint, Google Sheets, SMB, APIs    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
    [Database]         [Cache Layer]      [External Services]
    PostgreSQL          Redis (optional)   SharePoint, Google, etc
```

## Backend Architecture

### Layered Architecture

```
┌────────────────────────────────────┐
│    API Routes Layer                │
│  (routes/*.py - HTTP endpoints)    │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│    Schemas Layer                   │
│  (schemas/*.py - Data validation)  │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│    Services Layer                  │
│  (services/* - Business logic)     │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│    Data Layer                      │
│  (models/* - Database models)      │
└────────────────┬───────────────────┘
                 │
┌────────────────▼───────────────────┐
│    External Integrations           │
│  (SharePoint, Google, SMB, APIs)   │
└────────────────────────────────────┘
```

### Backend Directory Structure

```
backend/app/
├── core/                  # Core application logic
│   ├── config.py         # Configuration & settings
│   ├── logger.py         # Centralized logging
│   ├── exceptions.py     # Custom exceptions
│   └── constants.py      # Application constants
├── api/
│   ├── main.py           # FastAPI app instantiation
│   └── middleware.py     # CORS, Auth middleware
├── routes/               # API endpoint handlers
│   ├── energy.py
│   ├── kpis.py
│   ├── export.py
│   └── scheduler.py
├── schemas/              # Pydantic models for request/response
│   ├── energy.py
│   ├── kpi.py
│   └── responses.py
├── services/             # Business logic layer
│   ├── data/            # Data management services
│   ├── integrations/    # External integrations
│   └── export_service.py
├── agents/              # Data processing agents
│   ├── ingestion/       # Data ingestion pipeline
│   └── email/           # Email scheduling agent
├── models/              # Database models (ORM)
├── utils/               # Utility & helper functions
└── main.py              # Application entry point
```

### Request-Response Flow

```
HTTP Request
    │
    ▼
Route Handler (routes/*)
    │
    ├─ Validate Input (schemas/*)
    │
    ▼
Service Method (services/*)
    │
    ├─ Process Business Logic
    ├─ Call External APIs if needed
    ├─ Access Database
    │
    ▼
Response Schema (schemas/*)
    │
    ▼
HTTP Response (JSON)
```

## Frontend Architecture

### Component Hierarchy

```
App.jsx
├── Layout
│   ├── Header
│   ├── Sidebar
│   └── Main Content
│       ├── Pages
│       │   ├── Dashboard
│       │   ├── Energy
│       │   └── Reports
│       └── Components
│           ├── Charts
│           ├── Tables
│           ├── Filters
│           └── Common
└── Footer
```

### State Management Pattern (Zustand)

```
Store (Zustand)
├── dateStore       # Date range state
├── tabStore        # Active tab state
├── themeStore      # Theme settings
└── dataStore       # Cached data state
    │
    └─→ accessed by components via hooks
```

### API Client Pattern

```
Frontend Component
    │
    ├─→ useEnergyData() hook
    │   │
    │   ▼
    ├─→ API Client (api/client.js)
    │   │
    │   ├─ Axios instance
    │   ├─ Request interceptors (auth, error handling)
    │   └─ Response interceptors (data transformation)
    │
    ▼
    │
    ├─→ Store (Zustand) → Cache data
    │
    ▼
    Render Component
```

### Component Patterns

```
Presentational Components (ui/*.jsx)
├─ Stateless
├─ Props driven
└─ Reusable

Container Components (pages/*.jsx)
├─ Stateful
├─ Data fetching logic
└─ Page-level logic
```

## Data Flow

### Energy Data Ingestion

```
1. Data Sources
   ├─ APIs (Grid, Solar, Diesel systems)
   ├─ SMB Share (historical data)
   └─ Manual uploads

2. Ingestion Pipeline
   ├─ Extract (extract data from sources)
   ├─ Transform (validate & process)
   ├─ Load (save to database/cache)
   └─ Notify (trigger email, update UI)

3. Storage
   ├─ Primary: Database (PostgreSQL)
   ├─ Cache: Redis (optional)
   └─ Archive: Google Sheets, SharePoint

4. Retrieval
   └─ API endpoints serve to frontend
```

### Scheduler-Driven Tasks

```
Time Trigger (APScheduler)
    │
    ├─→ Daily Ingestion Job (9 AM)
    │   └─ Run ingestion_orchestrator.py
    │
    └─→ Daily Email Report Job (6 PM)
        └─ Run email scheduler
            ├─ Generate report
            ├─ Send via SMTP
            └─ Log execution
```

## Integration Patterns

### SharePoint Integration

```
Authentication
├─ MSAL → Azure AD
├─ Get access token
└─ Store credentials

Data Operations
├─ Read: Query SharePoint lists
├─ Write: Create/update list items
└─ Delete: Remove old records

Sync Strategy
├─ Pull-based: Scheduled jobs fetch data
└─ Push-based: Export endpoints push data
```

### Google Sheets Integration

```
Authentication
├─ OAuth 2.0 flow
├─ gspread library
└─ Service account credentials

Write Operations
├─ Append data to sheet
├─ Update specific cells/ranges
└─ Create new sheets

Read Operations
├─ Query data from sheet
└─ Cache in memory
```

### External API Integration

```
Pattern: Adapter Pattern

ExternalAPI
    │
    ├─→ APIClient (adapter)
    │   ├─ Normalize responses
    │   ├─ Handle errors
    │   └─ Retry logic
    │
    ▼
Service Layer
    │
    ├─ Works with normalized data
    └─ Decoupled from API changes
```

## Security Architecture

### Authentication & Authorization

```
Frontend
├─→ Login capture
├─→ Store JWT token
└─→ Attach to API requests

Backend
├─→ Validate JWT
├─→ Check permissions
├─→ Return 401/403 if needed
└─→ Process request if authorized
```

### Credential Management

```
Sensitive Data Storage
├─ Environment variables (.env)
├─ Secrets management (AWS Secrets Manager in prod)
├─ Never in code or version control
└─ Separate dev/prod credentials
```

### Network Security

```
CORS
├─ Allowed origins configured
└─ Prevents cross-origin attacks

HTTPS
├─ Enforced in production
├─ SSL/TLS certificates
└─ Secure cookie transmission

Rate Limiting
├─ Prevent abuse
└─ Configurable per endpoint
```

## Deployment Architecture

### Local Development

```
Docker Compose
├─ Backend container (FastAPI)
├─ Frontend dev server
├─ PostgreSQL container
└─ Optional: Redis
```

### Production Deployment

```
Kubernetes Cluster
├─ Backend Deployment
│   ├─ Multiple pods (replicas)
│   ├─ Load balancer
│   └─ Service mesh (optional)
├─ Frontend Deployment
│   ├─ Static hosting (Nginx/CDN)
│   └─ Edge caching
├─ Database (RDS or managed)
├─ Cache (ElastiCache or managed)
└─ External integrations via secure channels
```

## Design Patterns

### 1. Service Layer Pattern

```python
# Route doesn't directly access database
# Route calls service

class EnergyService:
    def get_daily_data(self, date):
        # All business logic here
        pass

# Route uses service
@router.get("/daily")
def get_daily_data(date: str):
    service = EnergyService()
    return service.get_daily_data(date)
```

### 2. Repository Pattern

```python
# Abstraction over data access

class EnergyRepository:
    def find_by_date(self, date):
        return db.query(Energy).filter(...)
    
class EnergyService:
    def __init__(self, repo: EnergyRepository):
        self.repo = repo
    
    def get_data(self, date):
        return self.repo.find_by_date(date)
```

### 3. Dependency Injection

```python
# Loose coupling between components

def get_cache():
    return RedisCache()

def get_service(cache=Depends(get_cache)):
    return EnergyService(cache)
```

### 4. Observer Pattern (Event-Driven)

```python
# Tasks notify listeners when complete

class IngestionTask:
    def on_complete(self):
        # trigger email
        # update cache
        # notify frontend via WebSocket
        pass
```

### 5. Strategy Pattern (Multiple Implementations)

```python
# Different export strategies

class ExportStrategy:
    def export(self, data): pass

class ExcelExporter(ExportStrategy):
    def export(self, data): pass

class SheetExporter(ExportStrategy):
    def export(self, data): pass
```

## Performance Considerations

### Caching Strategy

```
Layer 1: HTTP Cache Headers
├─ Set appropriate Cache-Control headers
└─ Reduces unnecessary requests

Layer 2: Application Cache
├─ Zustand store (frontend)
├─ In-memory cache (backend)
└─ Redis (optional distributed)

Layer 3: Database Query Caching
├─ Query result caching
└─ Invalidation on data updates
```

### Database Optimization

```
Indexes
├─ On commonly queried columns (date, source)
└─ Foreign key columns

Query Optimization
├─ Use SELECT specific columns
├─ Implement pagination
├─ Avoid N+1 queries
└─ Use appropriate joins
```

### Frontend Performance

```
Code Splitting
├─ Route-based splitting
├─ Component lazy loading
└─ Vendor bundle optimization

Bundle Size
├─ Tree shaking
├─ Minification
└─ Compression
```

---

**Last Updated**: April 2026
**Version**: 1.0

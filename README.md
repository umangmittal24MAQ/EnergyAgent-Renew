# Energy Dashboard - Noida Campus

A comprehensive energy monitoring and analytics platform for tracking and optimizing energy consumption across the Noida campus. Built with FastAPI backend, React frontend, and integrated with SharePoint for data management.

## 🎯 Project Overview

The Energy Dashboard is an enterprise-grade application designed to:
- **Monitor** real-time energy consumption (Grid, Solar, Diesel)
- **Analyze** energy metrics and KPIs
- **Schedule** automated data ingestion and email reports
- **Export** data to multiple formats (Excel, CSV, Google Sheets, SharePoint)
- **Track** historical trends and patterns

## 📊 Key Features

- ✅ Real-time energy consumption monitoring
- ✅ Interactive dashboards with multiple chart types
- ✅ KPI tracking and analysis
- ✅ Automated daily data ingestion
- ✅ Email report scheduling
- ✅ Multi-source data integration (APIs, SMB, SharePoint)
- ✅ Google Sheets integration for data export
- ✅ SharePoint integration for enterprise collaboration
- ✅ Historical data tracking and analysis
- ✅ Responsive web interface

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Runtime**: Uvicorn
- **Data Processing**: Pandas, NumPy
- **Scheduling**: APScheduler
- **Integrations**: Office365-REST-Python-Client, gspread, Groq LLM
- **Authentication**: MSAL (Microsoft Authentication Library)

### Frontend
- **Framework**: React 19.2+
- **Build Tool**: Vite 5.0+
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Charts**: Recharts
- **UI Framework**: Tailwind CSS
- **Form Handling**: React Hook Form

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose, Kubernetes
- **CI/CD**: GitHub Actions
- **Database**: PostgreSQL (ready for implementation)

## 📁 Project Structure

```
EnergyAgent/
├── backend/                    # Python FastAPI application
│   ├── app/
│   │   ├── core/              # Configuration, logging, exceptions
│   │   ├── api/               # FastAPI app setup
│   │   ├── routes/            # API endpoints
│   │   ├── schemas/           # Pydantic models
│   │   ├── services/          # Business logic
│   │   ├── agents/            # Data ingestion agents
│   │   ├── utils/             # Utility functions
│   │   └── models/            # Database models
│   ├── tests/                 # Test suite
│   ├── logs/                  # Application logs
│   ├── data/                  # Data directory
│   ├── requirements.txt
│   └── main.py
├── frontend/                  # React/Vite application
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # Reusable components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── store/            # State management
│   │   └── utils/            # Utilities
│   ├── package.json
│   └── vite.config.js
├── docs/                      # Documentation
│   ├── api/                  # API documentation
│   ├── deployment/           # Deployment guides
│   └── sharepoint/           # SharePoint integration
├── config/                    # Configuration files
├── scripts/                   # Utility scripts
├── infra/                     # Infrastructure files
├── .github/workflows/         # CI/CD pipelines
├── requirements.txt           # Main dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EnergyAgent
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
   Backend runs on `http://localhost:8000`

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs on `http://localhost:5173`

5. **Access the Application**
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options. Key settings:

```env
# Application
APP_ENV=development
API_PORT=8000
FRONTEND_URL=http://localhost:5173

# SharePoint
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_CLIENT_ID=your_client_id
SHAREPOINT_CLIENT_SECRET=your_secret

# Google Sheets
GOOGLE_APPLICATION_CREDENTIALS=./backend/google_credentials.json
GOOGLE_SHEET_ID=your_sheet_id

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 📚 Documentation

- [Architecture Guide](./ARCHITECTURE.md) - System design and components
- [API Documentation](./docs/api/endpoints.md) - REST API endpoints
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [SharePoint Integration](./docs/sharepoint/setup.md) - SharePoint setup
- [Contributing Guidelines](./CONTRIBUTING.md) - How to contribute

## 🧪 Testing

```bash
# Run backend tests
cd backend
pytest tests/

# Run frontend tests
cd frontend
npm test
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

## 📦 Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

## 🔐 Security

- Environment secrets in `.env` (never commit)
- CORS configured for specific origins in production
- HTTPS enforced in production
- Secure credential storage with Office365-REST-Python-Client
- Regular dependency updates

## 📊 API Endpoints

### Energy Data
- `GET /api/energy/daily` - Daily energy data
- `GET /api/energy/monthly` - Monthly energy data
- `GET /api/energy/grid` - Grid consumption
- `GET /api/energy/solar` - Solar generation
- `GET /api/energy/diesel` - Diesel consumption

### KPIs
- `GET /api/kpis/` - All KPIs
- `GET /api/kpis/efficiency` - Efficiency KPIs

### Export
- `POST /api/export/excel` - Export to Excel
- `POST /api/export/sheets` - Export to Google Sheets
- `POST /api/export/sharepoint` - Export to SharePoint

### Scheduler
- `GET /api/scheduler/status` - Scheduler status
- `POST /api/scheduler/trigger` - Trigger data ingestion

For detailed API documentation, visit `http://localhost:8000/docs`

## 🤝 Contributing

Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📝 License

This project is proprietary and confidential.

## 👥 Support

For issues and support:
1. Check [troubleshooting guide](./docs/troubleshooting.md)
2. Contact: engineering@company.com
3. Submit issues in GitHub or your internal issue tracker

## 🗂️ Related Documentation

- [Energy Metrics Calculations](./docs/energy-metrics/calculations.md)
- [SharePoint Developer Guide](./docs/sharepoint/developer-guide.md)
- [Kubernetes Deployment](./docs/deployment/kubernetes.md)

---

**Last Updated**: April 2026
**Status**: Production Ready

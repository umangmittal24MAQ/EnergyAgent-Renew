# Contributing to Energy Dashboard

Thank you for your interest in contributing to the Energy Dashboard project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Commit Guidelines](#commit-guidelines)
7. [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful, professional, and constructive in all interactions.

## Getting Started

### 1. Fork & Clone
```bash
git clone https://github.com/your-username/energy-dashboard.git
cd energy-dashboard
```

### 2. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Set Up Development Environment
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install
```

### 4. Create `.env` file
```bash
cp .env.example .env
# Edit with your development credentials
```

## Development Workflow

### Backend Development

**Structure**: `backend/app/`
```
services/     → Business logic
routes/       → API endpoints
schemas/      → Data validation
utils/        → Helper functions
agents/       → Data processing agents
```

**Running the backend**:
```bash
cd backend
python main.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Key files to understand**:
- `app/core/config.py` - Configuration management
- `app/api/main.py` - FastAPI app setup
- `app/routes/` - API endpoint implementations

### Frontend Development

**Structure**: `frontend/src/`
```
components/   → UI components
pages/        → Page components
api/          → API client
store/        → Zustand state
hooks/        → Custom React hooks
```

**Running the frontend**:
```bash
cd frontend
npm run dev
# Application available at http://localhost:5173
```

## Code Standards

### Python (Backend)

**Style Guide**: PEP 8
```bash
# Format code
black backend/

# Check linting
flake8 backend/

# Type check
mypy backend/
```

**Naming Conventions**:
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Docstring Format**:
```python
def get_energy_data(date: str) -> List[EnergyData]:
    """
    Retrieve energy data for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        List of EnergyData objects
        
    Raises:
        ValueError: If date format is invalid
    """
```

### JavaScript/React (Frontend)

**Style Guide**: Airbnb JavaScript Style Guide
```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint -- --fix
```

**Naming Conventions**:
- Components: `PascalCase`
- Functions/Variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: Match component name

**Component Template**:
```jsx
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

function MyComponent({ prop1, prop2 }) {
  const [state, setState] = useState(null);

  useEffect(() => {
    // Setup
    return () => {
      // Cleanup
    };
  }, []);

  return (
    <div>
      {/* JSX */}
    </div>
  );
}

MyComponent.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};

export default MyComponent;
```

## Testing

### Backend Tests

Location: `backend/tests/`

**Run tests**:
```bash
cd backend
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/unit/test_services.py
```

**Test Structure**:
```
tests/
├── unit/           → Unit tests for functions/methods
├── integration/    → Integration tests for API endpoints
└── fixtures/       → Test data and fixtures
```

**Example Test**:
```python
import pytest
from app.services.data_service import DataService

@pytest.fixture
def data_service():
    return DataService()

def test_get_energy_data(data_service):
    result = data_service.get_energy_data("2024-01-01")
    assert result is not None
    assert len(result) > 0
```

### Frontend Tests

**Run tests**:
```bash
cd frontend
npm test

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test-related changes
- `ci`: CI/CD changes

**Examples**:
```
feat(api): add endpoint for energy consumption trends
fix(sharepoint): resolve authentication timeout issue
docs: update deployment guide
refactor(services): extract cache logic to separate module
```

### Commit Best Practices

1. **Atomic commits**: One logical change per commit
2. **Descriptive messages**: Clear what the change does
3. **Link issues**: Reference issue numbers when applicable
4. **No huge commits**: Keep changes manageable

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest main
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests locally**
   ```bash
   # Backend
   cd backend && pytest

   # Frontend
   cd frontend && npm test
   ```

3. **Check code quality**
   ```bash
   # Backend
   black backend/
   flake8 backend/
   mypy backend/

   # Frontend
   npm run lint -- --fix
   ```

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change

## Changes Made
- Point 1
- Point 2

## Testing Done
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Checklist
- [ ] Code follows project style
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. **Automatic checks** must pass (CI/CD)
2. **At least 1 approval** from project maintainers
3. **Address feedback** promptly
4. **Merge** after approval

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python/Node version, etc.)
- Screenshots/logs if applicable

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (optional)
- Related issues (if any)

## Questions?

Feel free to:
1. Create a discussion in the repository
2. Email: engineering@company.com
3. Check existing issues/PRs

---

Thank you for contributing to make Energy Dashboard better! 🎉

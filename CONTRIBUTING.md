# Contributing to RAGMesh

Thank you for your interest in contributing to RAGMesh! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing Requirements](#testing-requirements)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)
9. [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and constructive
- Focus on what is best for the project
- Show empathy towards other contributors
- Accept constructive criticism gracefully

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or inflammatory comments
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Node.js 18+ and npm (for frontend development)
- Git for version control
- A code editor (VS Code, PyCharm, etc.)
- OpenAI API key (for testing)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ragmesh.git
   cd ragmesh
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/ragmesh.git
   ```

## Development Setup

### Using Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env
# Add your OpenAI API key to .env

# Start development environment
docker-compose up --build
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8017
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
# or
git checkout -b docs/your-documentation-change
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or changes
- `chore/` - Maintenance tasks

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
cd backend
pytest

# Run specific test categories
pytest -m unit
pytest -m integration

# Check coverage
pytest --cov=app --cov-report=html
```

### 4. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: tri-modal retrieval for legal documents

- Implement legal document parser
- Add case law entity extraction
- Update judge checks for legal citations
- Add 15 unit tests for legal module

Closes #123"
```

Commit message format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description (wrap at 72 chars)
- Reference issue numbers

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python (Backend)

**Style Guide:**
- Follow PEP 8
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Use flake8 for linting: `flake8 .`

**Code Structure:**
```python
"""
Module docstring explaining purpose
"""

from typing import Optional, List
import asyncio

from app.core.models import Document
from app.adapters.base import DocStoreAdapter


class MyClass:
    """Class docstring explaining purpose."""

    def __init__(self, dependency: DocStoreAdapter):
        """Initialize with dependencies.

        Args:
            dependency: Description of dependency
        """
        self.dependency = dependency

    async def my_method(self, param: str) -> Optional[Document]:
        """Method docstring explaining what it does.

        Args:
            param: Description of parameter

        Returns:
            Description of return value

        Raises:
            ValueError: When param is invalid
        """
        # Implementation
        pass
```

**Key Conventions:**
- All module methods are `async def`
- Use type hints everywhere
- Use Pydantic for data validation
- Use `model_dump()` not `.dict()` (Pydantic v2)
- Prefer pathlib.Path over string paths
- Use dependency injection

### TypeScript (Frontend)

**Style Guide:**
- Follow ESLint rules
- Use Prettier for formatting
- Use TypeScript strict mode

**Component Structure:**
```typescript
import { useState, useEffect } from 'react';

interface MyComponentProps {
  title: string;
  onSubmit: (data: string) => void;
}

export function MyComponent({ title, onSubmit }: MyComponentProps) {
  const [value, setValue] = useState('');

  useEffect(() => {
    // Effect logic
  }, []);

  const handleSubmit = () => {
    onSubmit(value);
  };

  return (
    <div className="container">
      <h2>{title}</h2>
      {/* JSX */}
    </div>
  );
}
```

**Key Conventions:**
- Use functional components
- Use TypeScript interfaces for props
- Use Tailwind CSS for styling
- Extract reusable logic into hooks
- Handle loading and error states

### Configuration (JSON)

**Format:**
```json
{
  "profile_id": {
    "description": "Brief description",
    "parameter_1": "value",
    "parameter_2": 123,
    "nested": {
      "key": "value"
    }
  }
}
```

**Key Conventions:**
- Use snake_case for keys
- Include descriptions
- Validate with Pydantic models
- Keep defaults sensible

## Testing Requirements

### Test Coverage

- **Minimum coverage:** 80% overall
- **Adapters:** 90%+
- **Core modules:** 85%+
- **Judge checks:** 90%+
- **API endpoints:** 75%+

### Writing Tests

**Unit Test Example:**
```python
import pytest
from app.modules.ingestion import Ingestion


@pytest.mark.unit
class TestIngestion:
    @pytest.fixture
    def ingestion(self, mock_doc_store):
        return Ingestion(doc_store=mock_doc_store)

    @pytest.mark.asyncio
    async def test_ingest_pdf_success(self, ingestion, sample_pdf_path):
        """Test successful PDF ingestion."""
        result = await ingestion.ingest_pdf(
            file_path=sample_pdf_path,
            filename="test.pdf",
            metadata={}
        )

        assert result is not None
        assert result.filename == "test.pdf"
        assert len(result.pages) > 0
```

**Test Requirements:**
- Write tests for all new code
- Use descriptive test names
- Test both success and failure cases
- Use appropriate markers (`@pytest.mark.unit`, etc.)
- Mock external dependencies
- All tests must pass before PR

### Running Tests Locally

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Specific category
pytest -m unit

# Specific file
pytest tests/adapters/test_file_doc_store.py

# Specific test
pytest tests/adapters/test_file_doc_store.py::TestFileDocStore::test_save_document
```

## Documentation

### Code Documentation

- Add docstrings to all classes and functions
- Include type hints
- Document parameters and return values
- Explain complex logic with comments

### User Documentation

When adding features, update:
- `README.md` - If it affects usage
- `ARCHITECTURE.md` - If it changes architecture
- `CLAUDE.md` - If it changes development workflow
- API docs - FastAPI auto-generates from docstrings

### Configuration Documentation

When adding configuration options:
- Add description in JSON file
- Update corresponding section in ARCHITECTURE.md
- Add example in README.md or QUICKSTART.md

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing done:
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added and passing
- [ ] Coverage maintained/improved

## Related Issues
Closes #123
Related to #456
```

### Review Process

1. Automated checks run (tests, linting)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

### After Merge

- Delete your branch
- Pull latest main
- Update your fork

## Areas for Contribution

### High Priority

1. **Additional Adapters**
   - Pinecone vector store
   - Weaviate vector store
   - PostgreSQL document store
   - Neo4j graph store
   - Qdrant vector store

2. **Additional Judge Checks**
   - Factual accuracy check
   - Answer completeness check
   - Source diversity check
   - Temporal consistency check

3. **Performance Optimizations**
   - Batch embedding processing
   - Query result caching
   - Connection pooling
   - Async job queue

4. **Document Types**
   - DOCX support
   - TXT support
   - HTML support
   - Markdown support
   - Multi-modal (images, tables)

### Medium Priority

5. **UI Enhancements**
   - Query history
   - Saved queries
   - Result export
   - Comparison view
   - Dark mode

6. **Analytics**
   - Query analytics
   - Performance metrics
   - Cost tracking
   - Usage reports

7. **Authentication**
   - User management
   - API key authentication
   - Role-based access control
   - OAuth integration

### Low Priority

8. **Additional Features**
   - Multi-language support
   - Custom embeddings
   - Fine-tuning support
   - Batch processing API
   - Webhook support

## Getting Help

### Questions

- Check existing documentation
- Search existing issues
- Ask in discussions (if enabled)
- Contact maintainers

### Reporting Bugs

Use the bug report template:
```markdown
**Bug Description**
Clear description of the bug

**To Reproduce**
1. Step 1
2. Step 2
3. See error

**Expected Behavior**
What should happen

**Environment**
- OS: [e.g., macOS 13.0]
- Docker version: [e.g., 24.0.0]
- Python version: [e.g., 3.11.0]
- Browser: [e.g., Chrome 120]

**Logs**
Relevant log output

**Screenshots**
If applicable
```

### Feature Requests

Use the feature request template:
```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of what you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Any other context or screenshots
```

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation (for major contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to RAGMesh! 🎉

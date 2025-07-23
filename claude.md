# Claude Development Instructions
*Specific instructions for Claude AI when working on this project*

## 🐍 **Python Virtual Environment**

### **Critical: Always Source Virtual Environment**
Before running any Python/Django commands, always use `svenv &&` to source the virtual environment:

```bash
# ✅ CORRECT: Source venv before Django commands
svenv && python manage.py runserver
svenv && python manage.py migrate
svenv && python manage.py test
svenv && python manage.py shell
svenv && python manage.py makemigrations

# ❌ INCORRECT: Don't run Django commands without sourcing venv
python manage.py runserver  # Will fail or use wrong Python
```

### **Common Development Commands**
```bash
# Start development server
svenv && python manage.py runserver

# Database operations
svenv && python manage.py makemigrations
svenv && python manage.py migrate
svenv && python manage.py showmigrations

# Testing
svenv && python manage.py test
svenv && python manage.py test profiles.tests
svenv && python manage.py test --keepdb  # Faster repeated testing

# Shell and debugging
svenv && python manage.py shell
svenv && python manage.py shell_plus  # If available

# User and data management
svenv && python manage.py load_test_crews
svenv && python manage.py set_test_passwords
svenv && python manage.py createsuperuser

# Static files
svenv && python manage.py collectstatic
svenv && python manage.py collectstatic --noinput

# Package management
svenv && pip install package_name
svenv && pip install -r requirements.txt
svenv && pip list
svenv && pip freeze > requirements.txt
```

## 🎯 **Claude-Specific Development Guidelines**

### **1. Context Awareness**
- **Always read** `docs/LLM_PROJECT_CONTEXT.md` first for complete project context
- **Check current branch** before making changes (`git branch`)
- **Understand recent changes** by reviewing recent commits if needed

### **2. Command Execution Pattern**
```bash
# Standard workflow for any Django operation:
# 1. Source venv
# 2. Execute command
# 3. Check results

svenv && python manage.py command_name
```

### **3. Testing Before Implementation**
```bash
# Always test current state before making changes
svenv && python manage.py test

# Test specific app after changes
svenv && python manage.py test app_name.tests

# Load test data for manual testing
svenv && python manage.py load_test_crews
svenv && python manage.py set_test_passwords
```

### **4. Database Workflow**
```bash
# Check current migration status
svenv && python manage.py showmigrations

# Create new migrations after model changes
svenv && python manage.py makemigrations

# Review migration before applying
svenv && python manage.py sqlmigrate app_name migration_number

# Apply migrations
svenv && python manage.py migrate

# If issues, can rollback
svenv && python manage.py migrate app_name previous_migration_number
```

## 🚀 **Quick Start Checklist for Claude**

### **Before Starting Any Work:**
- [ ] Read `docs/LLM_PROJECT_CONTEXT.md` for complete context
- [ ] Check current git branch: `git branch`
- [ ] Source venv and check Django status: `svenv && python manage.py check`
- [ ] Load test data if needed: `svenv && python manage.py load_test_crews`

### **During Development:**
- [ ] Always use `svenv &&` before Python commands
- [ ] Test changes: `svenv && python manage.py test`
- [ ] Check for migrations needed: `svenv && python manage.py makemigrations --dry-run`
- [ ] Verify server runs: `svenv && python manage.py runserver`

### **After Implementation:**
- [ ] Run full test suite: `svenv && python manage.py test`
- [ ] Check for any issues: `svenv && python manage.py check --deploy`
- [ ] Verify migrations are clean: `svenv && python manage.py showmigrations`
- [ ] Test the feature manually in browser

## 📋 **Common Claude Workflows**

### **Implementing a New Feature**
```bash
# 1. Check current state
git status
git branch

# 2. Read context
# Read docs/LLM_PROJECT_CONTEXT.md

# 3. Create feature branch
git checkout -b feature/feature-name

# 4. Test current state
svenv && python manage.py test

# 5. Make changes (models, views, templates)
# ... implement feature ...

# 6. Create migrations
svenv && python manage.py makemigrations

# 7. Apply migrations
svenv && python manage.py migrate

# 8. Test implementation
svenv && python manage.py test
svenv && python manage.py runserver

# 9. Commit changes
git add .
git commit -m "feat: implement feature-name"
```

### **Debugging Issues**
```bash
# Check Django configuration
svenv && python manage.py check

# Inspect database state
svenv && python manage.py dbshell

# Use Django shell for debugging
svenv && python manage.py shell
# In shell:
# from app.models import Model
# Model.objects.all()

# Check migrations
svenv && python manage.py showmigrations

# Run specific tests
svenv && python manage.py test app.tests.TestClass.test_method
```

### **Working with Profile System (Current Focus)**
```bash
# Test profile functionality
svenv && python manage.py test profiles.tests

# Load test users for manual testing
svenv && python manage.py load_test_crews
svenv && python manage.py set_test_passwords

# Check profile completion
svenv && python manage.py shell
# In shell:
# from profiles.models import UserProfile
# profiles = UserProfile.objects.all()
# for p in profiles:
#     print(f"{p.user.username}: {p.calculate_completion_percentage()}%")
```

## 🔧 **Environment Setup Verification**

### **Quick Environment Check**
```bash
# Verify virtual environment is working
svenv && python --version
svenv && which python

# Check Django installation
svenv && python -c "import django; print(django.get_version())"

# Verify database connection
svenv && python manage.py dbshell

# Check installed packages
svenv && pip list | grep -E "(Django|psycopg|cloudinary)"
```

### **Troubleshooting Common Issues**

#### **Virtual Environment Issues**
```bash
# If svenv command not found, check:
ls -la | grep venv
# Look for venv/ or .venv/ directory

# Manually activate if needed:
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Verify activation
which python
pip list
```

#### **Django Issues**
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Reset migrations (if needed)
svenv && python manage.py migrate --fake-initial

# Collect static files
svenv && python manage.py collectstatic --noinput
```

## 🎯 **Project-Specific Context for Claude**

### **Current Project State (Dec 2024)**
- **Branch**: `feature/profile-system-implementation`
- **Status**: Profile system 100% complete, moving to social features
- **Focus**: Skateboarding community platform
- **Tech Stack**: Django + TailwindCSS + DaisyUI + PostgreSQL

### **Key Testing Accounts**
```bash
# Load test users (IDs 100-113)
svenv && python manage.py load_test_crews

# Set passwords for easy testing
svenv && python manage.py set_test_passwords

# Default test password: testpass123
# Test usernames: Available after loading test crews
```

### **Development Priorities**
1. **Social Features**: Profile following system (next priority)
2. **Integration**: Cross-app functionality 
3. **Performance**: Query optimization and caching
4. **Testing**: Comprehensive test coverage

## 📚 **Claude Documentation Reading Order**

1. **[docs/LLM_PROJECT_CONTEXT.md](LLM_PROJECT_CONTEXT.md)** - 🔥 MUST READ FIRST
2. **[PROFILE_SYSTEM_COMPLETION_REPORT.md](../PROFILE_SYSTEM_COMPLETION_REPORT.md)** - Recent completion status
3. **[docs/CODEBASE_ARCHITECTURE.md](CODEBASE_ARCHITECTURE.md)** - Technical architecture
4. **[docs/DEVELOPMENT_PATTERNS.md](DEVELOPMENT_PATTERNS.md)** - Code patterns
5. **[docs/FEATURE_IMPLEMENTATION_GUIDE.md](FEATURE_IMPLEMENTATION_GUIDE.md)** - Implementation workflow

## ⚠️ **Important Reminders for Claude**

### **Always Remember:**
- **Source venv**: Use `svenv &&` before all Python commands
- **Privacy First**: All features must respect user privacy settings
- **Mobile First**: Design for mobile, enhance for desktop
- **Skateboard Focus**: Consider skateboarding community needs
- **Test Early**: Run tests before and after changes

### **Never Do:**
- Run Python/Django commands without `svenv &&`
- Implement features without privacy controls
- Create non-responsive designs
- Skip testing after changes
- Ignore the skateboarding community context

---

*This file is specifically for Claude AI to ensure consistent and correct development practices on this project.*

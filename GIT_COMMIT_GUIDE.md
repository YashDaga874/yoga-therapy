# Git Commit Guide - What to Push to GitHub

## ✅ Files to Commit (All Important Changes)

### Core Application Files (Modified)
- ✅ `web/app.py` - Fixed pagination, optimized queries
- ✅ `core/recommendation_engine.py` - Optimizations
- ✅ `database/models.py` - Database models with indexes
- ✅ `requirements.txt` - Dependencies

### Setup & Run Scripts (Modified)
- ✅ `setup.bat` - Windows setup script
- ✅ `setup.sh` - Linux/macOS setup script
- ✅ `run.bat` - Windows run script
- ✅ `run.sh` - Linux/macOS run script

### Documentation (New & Modified)
- ✅ `README.md` - Updated with new features
- ✅ `SETUP_INSTRUCTIONS.md` - **NEW** - Complete setup guide for new users
- ✅ `OPTIMIZATION_REPORT.md` - **NEW** - Scalability analysis
- ✅ `DATABASE_CONFIG.md` - **NEW** - Database configuration guide
- ✅ `PRODUCTION_DEPLOYMENT.md` - **NEW** - Production deployment guide
- ✅ `SCALABILITY_ANALYSIS.md` - **NEW** - Detailed scalability analysis
- ✅ `GIT_LFS_SETUP.md` - **NEW** - Git LFS setup guide

### Database & Migration Scripts (New)
- ✅ `add_database_indexes.py` - **NEW** - Creates database indexes
- ✅ `test_connections.py` - **NEW** - Connection testing script
- ✅ `.gitattributes` - **NEW** - Git LFS configuration

### Templates (Modified - Pagination fixes)
- ✅ `web/templates/citations.html`
- ✅ `web/templates/contraindications.html`
- ✅ `web/templates/diseases.html`
- ✅ `web/templates/modules.html`
- ✅ `web/templates/practices.html`
- ✅ `web/templates/rcts.html`

### Database File
- ✅ `yoga_therapy.db` - Main database (tracked via Git LFS)

---

## ❌ Files NOT to Commit (Already Ignored)

These are automatically ignored by `.gitignore`:
- ❌ `venv/` - Virtual environment (should never be committed)
- ❌ `__pycache__/` - Python cache files
- ❌ `*.pyc`, `*.pyo` - Compiled Python files
- ❌ `.env` - Environment variables (if exists)
- ❌ `web/static/uploads/` - User-uploaded files (should be ignored)

---

## 📋 Recommended Commit Commands

### Step 1: Add all important files

```bash
# Core application
git add web/app.py
git add core/recommendation_engine.py
git add database/models.py
git add requirements.txt

# Setup scripts
git add setup.bat setup.sh
git add run.bat run.sh

# Documentation
git add README.md
git add SETUP_INSTRUCTIONS.md
git add OPTIMIZATION_REPORT.md
git add DATABASE_CONFIG.md
git add PRODUCTION_DEPLOYMENT.md
git add SCALABILITY_ANALYSIS.md
git add GIT_LFS_SETUP.md

# Database scripts
git add add_database_indexes.py
git add test_connections.py
git add .gitattributes

# Templates
git add web/templates/*.html

# Database (if using Git LFS)
git add yoga_therapy.db
```

### Step 2: Verify what will be committed

```bash
git status
```

### Step 3: Commit with descriptive message

```bash
git commit -m "feat: Add pagination fixes, optimization improvements, and comprehensive documentation

- Fix pagination for all list views (diseases, practices, citations, modules, RCTs)
- Add database indexes for performance optimization
- Add PostgreSQL support with connection pooling
- Add comprehensive setup instructions for new users
- Add scalability analysis and optimization report
- Add database configuration and production deployment guides
- Add connection testing script
- Update all documentation"
```

### Step 4: Push to GitHub

```bash
git push origin main
```

---

## ⚠️ Important Notes

### About `yoga_therapy.db`

The database file is tracked via **Git LFS** (Large File Storage). Make sure:

1. **Git LFS is installed:**
   ```bash
   git lfs version
   ```

2. **If not installed, install it:**
   - Windows: Download from https://git-lfs.github.com/
   - macOS: `brew install git-lfs`
   - Linux: `sudo apt-get install git-lfs`

3. **Initialize Git LFS (if not already done):**
   ```bash
   git lfs install
   ```

4. **Verify database is tracked by LFS:**
   ```bash
   git lfs ls-files
   ```
   Should show: `yoga_therapy.db`

### About Uploaded Files

User-uploaded files in `web/static/uploads/` should NOT be committed. If they're showing up:

1. Add to `.gitignore`:
   ```
   web/static/uploads/*
   !web/static/uploads/.gitkeep
   ```

2. Remove from git (if already tracked):
   ```bash
   git rm -r --cached web/static/uploads/
   ```

---

## 🚀 Quick Commit (All at Once)

If you want to commit everything at once (recommended):

```bash
# Add all modified and new files (respects .gitignore)
git add -A

# Check what will be committed
git status

# Commit
git commit -m "feat: Add pagination fixes, optimization improvements, and comprehensive documentation"

# Push
git push origin main
```

---

## 📝 Commit Message Best Practices

Use this format:
```
type: Short description

Longer description explaining what and why

- Bullet point 1
- Bullet point 2
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `perf:` - Performance improvement
- `chore:` - Maintenance tasks

---

## ✅ Final Checklist

Before pushing, verify:

- [ ] All code changes are tested
- [ ] Documentation is complete
- [ ] No sensitive data (passwords, API keys) in code
- [ ] Database file is tracked via Git LFS
- [ ] Uploaded files are not committed
- [ ] Virtual environment is not committed
- [ ] Commit message is descriptive

---

**Ready to push!** 🚀


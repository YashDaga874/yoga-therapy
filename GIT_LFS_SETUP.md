# Git LFS Setup for Database Files

## Why Git LFS?

The database file (`yoga_therapy.db`) is tracked in git. As it grows, it can bloat the repository. Git LFS (Large File Storage) stores large files outside the main git repository, making clones faster and keeping the repository size manageable.

## Setup Git LFS

### 1. Install Git LFS

**Windows:**
- Download from: https://git-lfs.github.com/
- Or use: `winget install Git.GitLFS`

**macOS:**
```bash
brew install git-lfs
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install git-lfs

# Fedora
sudo dnf install git-lfs
```

### 2. Initialize Git LFS in Your Repository

```bash
cd yoga-therapy
git lfs install
```

### 3. Track Database Files

The `.gitattributes` file is already configured, but verify it exists:

```bash
# Check .gitattributes
cat .gitattributes
```

It should contain:
```
*.db filter=lfs diff=lfs merge=lfs -text
*.sqlite filter=lfs diff=lfs merge=lfs -text
*.sqlite3 filter=lfs diff=lfs merge=lfs -text
```

### 4. Migrate Existing Database File

If the database file is already committed, migrate it to LFS:

```bash
git lfs migrate import --include="*.db" --everything
```

Or for just the current database:
```bash
git rm --cached yoga_therapy.db
git add yoga_therapy.db
git commit -m "Migrate database file to Git LFS"
```

### 5. Push to GitHub

```bash
git push origin main
```

## Verify Git LFS is Working

```bash
# Check if file is tracked by LFS
git lfs ls-files

# Should show: yoga_therapy.db
```

## For New Clones

When someone clones the repository, they need Git LFS installed:

```bash
# Clone normally
git clone <your-repo-url>

# Git LFS files are automatically downloaded if LFS is installed
# If not installed, they'll see pointer files instead
```

## Troubleshooting

**Problem: "git-lfs: command not found"**
- Solution: Install Git LFS (see above)

**Problem: Database file shows as pointer file after clone**
- Solution: Install Git LFS and run `git lfs pull`

**Problem: Large file size warnings on GitHub**
- Solution: Ensure Git LFS is properly configured and file is migrated

## Alternative: Remove Database from Git

If you prefer not to use Git LFS, you can:

1. Remove database from git:
   ```bash
   git rm --cached yoga_therapy.db
   echo "yoga_therapy.db" >> .gitignore
   git commit -m "Remove database from git, use initialization script instead"
   ```

2. Provide database initialization via:
   - Synthetic data generator (already implemented)
   - Import script with sample data
   - Database seed/migration scripts

## Current Recommendation

**For now:** Use Git LFS for the database file (already configured)

**For production:** Consider removing database from git and using:
- Database initialization scripts
- Seed data files
- Migration-based setup


# Database Scalability & Optimization Analysis

## Current Issues & Recommendations

### 🔴 Critical Issues

#### 1. **No Database Indexes**
**Problem:** Frequently queried columns have no indexes, causing slow queries as data grows.

**Impact:**
- Searches on `Disease.name` are slow
- Filtering by `Practice.practice_segment` is slow
- Joins on foreign keys (`module_id`, `disease_id`) are inefficient
- Text searches on `practice_english`, `practice_sanskrit` are very slow

**Solution:** Add indexes to frequently queried columns.

#### 2. **Database File in Git Repository**
**Problem:** Binary database file in git will cause issues as it grows.

**Impact:**
- Repository size grows with every database change
- Slow clone operations
- Git history becomes bloated
- GitHub has 100MB file size warning, 50MB hard limit for individual files

**Current Size:** 104KB (OK for now, but will grow)

**Solution:** 
- Use Git LFS (Large File Storage) for database file
- OR: Provide database as separate download/initialization script
- OR: Use database migrations/seeds instead of binary file

#### 3. **No Pagination**
**Problem:** Loading all records into memory.

**Impact:**
- `session.query(Practice).all()` loads ALL practices
- `session.query(RCT).all()` loads ALL RCTs
- Memory issues with large datasets
- Slow page loads

**Solution:** Implement pagination for all list views.

#### 4. **SQLite Limitations**
**Problem:** SQLite is file-based with concurrency limitations.

**Impact:**
- Only one writer at a time
- Not suitable for high-traffic applications
- No built-in connection pooling
- Limited concurrent read performance

**Solution:** 
- For small-medium scale: SQLite is fine (current use case)
- For production/high-traffic: Migrate to PostgreSQL or MySQL

### 🟡 Optimization Opportunities

#### 5. **N+1 Query Problem**
**Problem:** Loading relationships in loops can cause multiple queries.

**Current Code:**
```python
for disease in diseases:
    _ = len(disease.practices)  # Separate query per disease
    _ = len(disease.modules)    # Separate query per disease
```

**Solution:** Use eager loading with `joinedload()` or `selectinload()`.

#### 6. **No Query Result Caching**
**Problem:** Same queries executed repeatedly.

**Solution:** Add caching for frequently accessed data (disease lists, practice segments, etc.).

#### 7. **Inefficient Recommendation Algorithm**
**Problem:** Loading all RCTs into memory for matching.

**Current Code:**
```python
all_rcts = session.query(RCT).all()  # Loads ALL RCTs
for practice in filtered_practices:
    for rct in all_rcts:  # Nested loop
```

**Solution:** Use database joins and filters instead of in-memory loops.

#### 8. **No Connection Pooling Configuration**
**Problem:** Default SQLite connection handling.

**Solution:** Configure connection pooling and optimize SQLite settings.

---

## Recommended Optimizations

### Priority 1: Add Database Indexes (Quick Win)

Add indexes to improve query performance:

```python
from sqlalchemy import Index

# In models.py, add after table definitions:
Index('idx_disease_name', Disease.name)
Index('idx_practice_english', Practice.practice_english)
Index('idx_practice_sanskrit', Practice.practice_sanskrit)
Index('idx_practice_segment', Practice.practice_segment)
Index('idx_practice_module_id', Practice.module_id)
Index('idx_module_disease_id', Module.disease_id)
Index('idx_rct_disease_id', RCT.diseases)  # For many-to-many
```

### Priority 2: Implement Pagination

Add pagination to all list views:

```python
from flask import request

page = request.args.get('page', 1, type=int)
per_page = 20
practices = query.paginate(page=page, per_page=per_page, error_out=False)
```

### Priority 3: Use Eager Loading

Replace lazy loading with eager loading:

```python
from sqlalchemy.orm import joinedload

diseases = session.query(Disease).options(
    joinedload(Disease.practices),
    joinedload(Disease.modules)
).all()
```

### Priority 4: Optimize Recommendation Engine

Use database joins instead of loading all data:

```python
# Instead of loading all RCTs
practice_rcts = session.query(
    Practice.id,
    RCT.parenthetical_citation
).join(
    disease_practice_association
).join(
    rct_disease_association
).filter(
    Practice.id.in_(practice_ids)
).all()
```

### Priority 5: Database File Management

**Option A: Use Git LFS** (Recommended for current approach)
```bash
git lfs install
git lfs track "*.db"
git add .gitattributes
```

**Option B: Database Initialization Script** (Better for production)
- Remove database from git
- Create initialization script that generates database from seeds
- Users run script to create database

**Option C: Database Migrations** (Best for production)
- Use Alembic for migrations
- Seed data via migration scripts
- No binary files in git

---

## When to Migrate from SQLite

### SQLite is Fine For:
- ✅ Single-user applications
- ✅ Development/testing
- ✅ Small to medium datasets (< 1GB)
- ✅ Low concurrent write operations
- ✅ Embedded applications

### Migrate to PostgreSQL/MySQL When:
- ❌ Multiple concurrent writers
- ❌ Database > 1GB
- ❌ High-traffic web application
- ❌ Need advanced features (full-text search, JSON queries, etc.)
- ❌ Production deployment with multiple servers

---

## Current System Assessment

### ✅ What's Good:
- Clean ORM structure
- Proper relationships defined
- Good separation of concerns
- Database migrations handled

### ⚠️ What Needs Improvement:
- Missing indexes (critical)
- No pagination (important)
- Database in git (will become problem)
- Query optimization needed (important)

### 📊 Performance Estimates:

**Current (104KB database):**
- Queries: < 10ms (fast)
- Page loads: < 100ms (acceptable)

**At 10MB database:**
- Without indexes: 100-500ms (slow)
- With indexes: 10-50ms (acceptable)
- With pagination: 10-20ms (good)

**At 100MB database:**
- SQLite starts showing limitations
- Consider PostgreSQL migration
- Git repository becomes problematic

---

## Action Plan

### Immediate (Do Now):
1. ✅ Add database indexes
2. ✅ Implement pagination
3. ✅ Use Git LFS for database file

### Short Term (Next Sprint):
4. ✅ Optimize queries with eager loading
5. ✅ Improve recommendation engine queries
6. ✅ Add query result caching

### Long Term (When Scaling):
7. ⚠️ Consider PostgreSQL migration
8. ⚠️ Move database out of git (use seeds/migrations)
9. ⚠️ Add full-text search capabilities
10. ⚠️ Implement database connection pooling

---

## Conclusion

**Current State:** System is well-architected but needs optimization for scalability.

**For Current Use Case (Research/Development):** SQLite is fine, but add indexes and pagination.

**For Production/Scale:** Plan migration to PostgreSQL when:
- Database exceeds 100MB
- Multiple concurrent users
- High traffic expected

**Git Repository:** Use Git LFS now to prevent future issues with database file size.


# Database Configuration Guide

## Overview

The system now supports both **SQLite** (default) and **PostgreSQL** for production deployments. The database configuration is flexible and can be easily switched.

## Default Configuration (SQLite)

By default, the system uses SQLite, which is perfect for:
- Development and testing
- Single-user applications
- Small to medium datasets (< 1GB)
- Embedded deployments

No configuration needed - just run the app!

## PostgreSQL Configuration (Production)

For production deployments with:
- Multiple concurrent users
- Large datasets (> 100MB)
- High traffic
- Multiple servers

### Setup PostgreSQL

1. **Install PostgreSQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   
   # Windows: Download from postgresql.org
   ```

2. **Create Database:**
   ```sql
   CREATE DATABASE yoga_therapy;
   CREATE USER yoga_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE yoga_therapy TO yoga_user;
   ```

3. **Configure Environment Variables:**

   **Option A: Single DATABASE_URL (Recommended)**
   ```bash
   export DATABASE_URL="postgresql://yoga_user:your_password@localhost:5432/yoga_therapy"
   ```

   **Option B: Individual Variables**
   ```bash
   export DB_TYPE=postgresql
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=yoga_user
   export DB_PASSWORD=your_password
   export DB_NAME=yoga_therapy
   ```

4. **Install PostgreSQL Driver:**
   ```bash
   pip install psycopg2-binary
   ```

5. **Run Migrations:**
   ```bash
   python -c "from database.models import create_database; create_database()"
   python add_database_indexes.py
   ```

6. **Import Data (if needed):**
   ```bash
   python utils/import_data.py
   # OR use the web interface to generate synthetic data
   ```

## Performance Optimizations

### Database Indexes

Indexes have been added to frequently queried columns for optimal performance:
- Disease names
- Practice names (English & Sanskrit)
- Practice segments and categories
- Foreign keys (module_id, citation_id, disease_id)
- RCT DOIs and study types

**To add indexes to existing database:**
```bash
python add_database_indexes.py
```

### Connection Pooling

- **SQLite**: Uses StaticPool (single connection, sufficient for SQLite)
- **PostgreSQL**: Uses QueuePool with:
  - Pool size: 10 connections
  - Max overflow: 20 connections
  - Connection recycling: 1 hour
  - Pre-ping: Enabled (checks connections before use)

### Query Optimization

- **Eager Loading**: Uses `joinedload()` and `selectinload()` to prevent N+1 queries
- **Pagination**: All list views support pagination (20 items per page by default)
- **Indexed Queries**: All search and filter operations use indexed columns

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full database connection URL | `sqlite:///yoga_therapy.db` |
| `DB_TYPE` | Database type: `sqlite` or `postgresql` | `sqlite` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | PostgreSQL username | `yoga_therapy` |
| `DB_PASSWORD` | PostgreSQL password | (empty) |
| `DB_NAME` | PostgreSQL database name | `yoga_therapy` |

## Migration from SQLite to PostgreSQL

1. **Export data from SQLite:**
   ```bash
   # Use the export functionality in the web interface
   # OR use SQLite dump
   sqlite3 yoga_therapy.db .dump > backup.sql
   ```

2. **Set up PostgreSQL** (see above)

3. **Create tables:**
   ```bash
   export DATABASE_URL="postgresql://..."
   python -c "from database.models import create_database; create_database()"
   python add_database_indexes.py
   ```

4. **Import data:**
   - Use the web interface to re-enter data

## Consolidating Data from Multiple SQLite Files

If three machines have been collecting data separately:

1. Export each SQLite DB to SQL:
   ```bash
   sqlite3 yoga_therapy.db .dump > machine1.sql
   sqlite3 other_machine_path/yoga_therapy.db .dump > machine2.sql
   sqlite3 third_machine_path/yoga_therapy.db .dump > machine3.sql
   ```
2. Stand up a staging PostgreSQL database and create tables (see above).
3. Import dumps one at a time, resolving conflicts (duplicate primary keys/codes) as needed:
   ```bash
   psql $DATABASE_URL -f machine1.sql
   psql $DATABASE_URL -f machine2.sql
   psql $DATABASE_URL -f machine3.sql
   ```
4. Run `python add_practice_code_field.py`, `python add_kosha_field.py`, and `python add_cvr_score_field.py` if columns are missing.
5. Run `python add_database_indexes.py` for performance.
6. Point all app instances to this single PostgreSQL URL (set `DATABASE_URL`) and retire local SQLite writes.
   - OR use the import script if you have JSON data
   - OR manually migrate using SQL

## Troubleshooting

### PostgreSQL Connection Issues

**Error: "could not connect to server"**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection details in environment variables
- Check firewall settings

**Error: "password authentication failed"**
- Verify username and password
- Check PostgreSQL authentication settings in `pg_hba.conf`

**Error: "database does not exist"**
- Create the database: `CREATE DATABASE yoga_therapy;`

### Performance Issues

**Slow queries:**
- Ensure indexes are created: `python add_database_indexes.py`
- Check if using pagination (should be automatic)
- Monitor database with `EXPLAIN ANALYZE` for slow queries

**Connection pool exhaustion:**
- Increase `pool_size` in `database/models.py`
- Check for connection leaks (sessions not being closed)

## Best Practices

1. **Always use environment variables** for database configuration
2. **Never commit credentials** to git - use `.env` files (not in repo)
3. **Use connection pooling** for PostgreSQL (already configured)
4. **Monitor query performance** as data grows
5. **Regular backups** of production databases
6. **Use migrations** for schema changes (consider Alembic for future)

## Next Steps

For production deployment:
1. Set up PostgreSQL
2. Configure environment variables
3. Run migrations and create indexes
4. Import/seed data
5. Monitor performance
6. Set up regular backups


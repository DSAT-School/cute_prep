# Database Schema Documentation

## Overview

The Practice Portal application uses PostgreSQL as its primary database. The schema follows normalization principles (3NF minimum) and uses UUID primary keys for all tables.

## Entity Relationship Diagram

```
┌─────────────────────────┐
│        Users            │
│─────────────────────────│
│ id (UUID, PK)           │
│ username (unique)       │
│ email (unique)          │
│ password_hash           │
│ first_name              │
│ last_name               │
│ is_active               │
│ is_staff                │
│ is_superuser            │
│ date_joined             │
│ last_login              │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
```

## Tables

### users

The main user table for authentication and authorization.

**Table Name**: `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the user |
| username | VARCHAR(150) | UNIQUE, NOT NULL | User's username for login |
| email | VARCHAR(254) | UNIQUE, NOT NULL | User's email address |
| password | VARCHAR(128) | NOT NULL | Hashed password |
| first_name | VARCHAR(150) | | User's first name |
| last_name | VARCHAR(150) | | User's last name |
| is_active | BOOLEAN | DEFAULT TRUE | Whether the user account is active |
| is_staff | BOOLEAN | DEFAULT FALSE | Whether user can access admin site |
| is_superuser | BOOLEAN | DEFAULT FALSE | Whether user has all permissions |
| date_joined | TIMESTAMP | NOT NULL | When the user account was created |
| last_login | TIMESTAMP | NULLABLE | Last login timestamp |
| created_at | TIMESTAMP | NOT NULL | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Record last update timestamp |

**Indexes**:
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
CREATE UNIQUE INDEX idx_users_username_unique ON users(username);
```

**Constraints**:
```sql
ALTER TABLE users
  ADD CONSTRAINT users_email_unique UNIQUE (email),
  ADD CONSTRAINT users_username_unique UNIQUE (username),
  ADD CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');
```

## Data Types

### UUID
All primary keys use UUID version 4 for:
- Global uniqueness
- Security (non-sequential)
- Distribution-friendly
- No ID enumeration attacks

### Timestamps
All tables include:
- `created_at`: Auto-set on record creation
- `updated_at`: Auto-updated on record modification

Both use timezone-aware timestamps (UTC).

## Indexes

### Primary Indexes
Every table has a UUID primary key with a clustered index.

### Secondary Indexes
- **Email**: B-tree index for fast user lookups
- **Username**: B-tree index for authentication
- **Created At**: B-tree index for time-based queries

### Index Usage Guidelines
1. Add indexes to foreign keys
2. Add indexes to frequently queried fields
3. Add composite indexes for multi-column queries
4. Monitor index usage and remove unused indexes

## Constraints

### Primary Key Constraints
All tables have UUID primary keys.

### Unique Constraints
- `username`: Must be unique across all users
- `email`: Must be unique across all users

### Check Constraints
- Email format validation
- Username length validation

### Foreign Key Constraints
Foreign keys use `ON DELETE CASCADE` or `ON DELETE SET NULL` based on business logic.

## Database Migrations

### Creating Migrations
```bash
python manage.py makemigrations
```

### Applying Migrations
```bash
python manage.py migrate
```

### Viewing Migration Status
```bash
python manage.py showmigrations
```

### Rolling Back Migrations
```bash
python manage.py migrate app_name migration_name
```

## Performance Considerations

### Query Optimization
1. **Use select_related**: For foreign key relationships
   ```python
   User.objects.select_related('profile')
   ```

2. **Use prefetch_related**: For many-to-many relationships
   ```python
   User.objects.prefetch_related('groups')
   ```

3. **Use only()**: To fetch specific fields
   ```python
   User.objects.only('id', 'username', 'email')
   ```

4. **Use defer()**: To exclude specific fields
   ```python
   User.objects.defer('password')
   ```

### Connection Pooling
Configure in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

### Database Caching
Use Redis for:
- Query result caching
- Session storage
- Frequently accessed data

## Backup and Recovery

### Backup Strategy
```bash
# Full database backup
pg_dump -U postgres practice_portal > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -U postgres practice_portal | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore
```bash
# Restore from backup
psql -U postgres practice_portal < backup_20240101.sql

# Restore from compressed backup
gunzip -c backup_20240101.sql.gz | psql -U postgres practice_portal
```

### Automated Backups
Set up cron job for daily backups:
```bash
0 2 * * * pg_dump -U postgres practice_portal | gzip > /backups/backup_$(date +\%Y\%m\%d).sql.gz
```

## Security

### Password Storage
- Passwords are hashed using PBKDF2 with SHA256
- Never store plain text passwords
- Use Django's built-in password hashing

### SQL Injection Prevention
- Always use ORM queries
- Never use raw SQL unless necessary
- Use parameterized queries for raw SQL

### Access Control
- Use database roles and permissions
- Limit application user privileges
- Separate read and write access

## Monitoring

### Query Performance
```sql
-- Enable query logging
ALTER DATABASE practice_portal SET log_statement = 'all';

-- View slow queries
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- View table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Index Usage
```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%_pkey';
```

## Future Schema Changes

### Planned Tables

1. **User Profiles**
   - Extended user information
   - Avatar/photo
   - Bio and preferences

2. **Activity Logs**
   - User actions audit trail
   - System events
   - Security events

3. **Notifications**
   - User notifications
   - Email queue
   - Push notifications

## Database Configuration

### PostgreSQL Settings (postgresql.conf)
```ini
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB

# Connections
max_connections = 100

# Write-Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query Tuning
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Connection Settings (Django)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'practice_portal',
        'USER': 'postgres',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}
```

## Maintenance

### Vacuum
```sql
-- Analyze tables
ANALYZE users;

-- Vacuum tables
VACUUM ANALYZE users;

-- Full vacuum (requires lock)
VACUUM FULL users;
```

### Reindexing
```sql
-- Reindex specific index
REINDEX INDEX idx_users_email;

-- Reindex table
REINDEX TABLE users;

-- Reindex database
REINDEX DATABASE practice_portal;
```

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Django ORM Documentation](https://docs.djangoproject.com/en/stable/topics/db/)
- [Database Normalization](https://en.wikipedia.org/wiki/Database_normalization)
- [UUID Best Practices](https://www.postgresql.org/docs/current/datatype-uuid.html)

# Security Features Documentation

This document outlines the comprehensive security measures implemented in the HFRAT application.

## Global Error Handling

### Implemented Error Handlers

✅ **400 Bad Request**
- Handles validation errors and malformed requests
- Logs warning-level messages with error details
- Returns user-friendly error messages

✅ **401 Unauthorized**
- Handles authentication failures
- Catches JWT-related errors
- Logs unauthorized access attempts
- Returns clear authentication error messages

✅ **403 Forbidden**
- Handles authorization/permission errors
- Logs IP address and path of forbidden access attempts
- Returns permission-denied messages

✅ **404 Not Found**
- Handles missing resource errors
- Logs requested paths for analysis
- Returns clear "not found" messages

✅ **500 Internal Server Error**
- Handles unexpected server errors
- Automatically rolls back failed database transactions
- Logs full stack traces for debugging
- Returns generic error message (no sensitive details exposed)

### Additional Error Handlers

- **JWTExtendedException**: Catches all JWT-related errors (expired tokens, invalid tokens, etc.)
- **SQLAlchemyError**: Catches database errors and automatically rolls back transactions
- **Generic Exception Handler**: Catches any unexpected errors as a safety net

## Input Sanitization

### Sanitization Functions

All user inputs are sanitized using dedicated functions in `app/utils/validators.py`:

#### `sanitize_string(value, max_length=1000)`
- Strips whitespace
- Removes null bytes (`\x00`)
- Truncates to maximum length
- Prevents injection attacks

#### `sanitize_email(email)`
- Converts to lowercase
- Removes dangerous characters: `<>()[]{}|\`
- Limited to 255 characters
- Used for all email inputs

#### `sanitize_integer(value, min_val=None, max_val=None)`
- Validates integer format
- Enforces minimum/maximum bounds
- Returns `None` for invalid inputs
- Used for all numeric inputs (facility IDs, resource counts)

#### `is_valid_email(email)`
- RFC 5322-compliant email validation
- Regex pattern matching
- Used before storing email addresses

### Applied Throughout Application

Input sanitization is applied in:
- ✅ Authentication routes (login, register)
- ✅ Admin routes (user creation, facility creation)
- ✅ Reporter routes (resource reports)
- ✅ All user-provided data

## Logging

### Log Configuration

**Development Mode:**
- Console logging enabled
- DEBUG level logging
- Detailed error messages

**Production Mode:**
- File-based logging (rotating logs)
- Stored in `logs/hfrat.log`
- Maximum 10 MB per file
- 10 backup files retained
- INFO level logging

### What Gets Logged

✅ **Request Information** (Production only)
- HTTP method and path
- Client IP address
- User-Agent string
- Timestamp

✅ **Error Events**
- Bad requests (400)
- Unauthorized attempts (401)
- Forbidden access (403)
- Not found (404)
- Server errors (500) with full stack traces
- JWT errors
- Database errors with stack traces

✅ **Application Events**
- Application startup
- Seed operations
- Critical errors

## Secure Headers

All HTTP responses include the following security headers:

### ✅ X-Frame-Options: DENY
- Prevents clickjacking attacks
- Blocks the page from being embedded in frames/iframes

### ✅ X-Content-Type-Options: nosniff
- Prevents MIME type sniffing
- Forces browsers to respect declared content types

### ✅ X-XSS-Protection: 1; mode=block
- Enables browser XSS protection
- Blocks page loading if XSS detected

### ✅ Strict-Transport-Security (Production only)
- Forces HTTPS connections
- `max-age=31536000` (1 year)
- Includes subdomains

### ✅ Content-Security-Policy: default-src 'self'
- Restricts resource loading to same origin
- Prevents XSS attacks

### ✅ Referrer-Policy: strict-origin-when-cross-origin
- Controls referrer information disclosure
- Protects user privacy

### ✅ Permissions-Policy
- Disables unnecessary browser features
- Blocks geolocation, microphone, camera access

## CORS Configuration

### Restricted CORS Policy

✅ **Origins**
- Only whitelisted origins allowed
- Configured via `CORS_ALLOWED_ORIGINS` environment variable
- Default: `http://localhost:3000` (development)

✅ **Methods**
- Limited to: GET, POST, PUT, DELETE, OPTIONS
- No dangerous methods allowed

✅ **Headers**
- Allowed: Content-Type, Authorization
- Exposed: Content-Type, Authorization
- No sensitive headers exposed

✅ **Additional Settings**
- Credentials: Disabled (`supports_credentials: false`)
- Max age: 3600 seconds (1 hour preflight cache)
- Applies only to `/api/*` routes

## SQL Injection Protection

### ORM-Based Protection

✅ **SQLAlchemy ORM**
- All database queries use SQLAlchemy ORM
- Parameterized queries prevent SQL injection
- No raw SQL queries used
- Type safety enforced at ORM level

✅ **Input Validation**
- All inputs validated before database operations
- Type checking enforced (integers, strings, enums)
- Length limits enforced

✅ **Database Constraints**
- Check constraints prevent invalid data
- Foreign key constraints maintain referential integrity
- Unique constraints prevent duplicates
- NOT NULL constraints ensure required data

### Example Protection

**Dangerous (not used):**
```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

**Safe (used throughout):**
```python
user = User.query.filter_by(email=email).first()
```

## Password Security

✅ **Hashing**
- Werkzeug's `generate_password_hash()` used
- Industry-standard bcrypt algorithm
- Salted hashes prevent rainbow table attacks

✅ **Minimum Requirements**
- Minimum 8 characters
- Maximum 128 characters
- Validated before hashing

✅ **Storage**
- Only hashes stored in database
- Plain passwords never logged or stored

## JWT Security

✅ **Token Configuration**
- Secret key from environment variable or auto-generated
- 24-hour expiration (configurable)
- Token blocklist for logout functionality

✅ **Identity Claims**
- User ID, role, and facility ID stored in token
- Verified on every protected route
- No sensitive data in token payload

## Role-Based Access Control (RBAC)

✅ **Role Enforcement**
- `@admin_required` decorator
- `@reporter_required` decorator
- `@monitor_required` decorator
- Verified via JWT claims

✅ **Read-Only Enforcement**
- Monitor role: GET requests only
- Reporter role: Limited to own facility
- Admin role: Full access

## Best Practices Implemented

1. ✅ **Principle of Least Privilege**: Users only get access to what they need
2. ✅ **Defense in Depth**: Multiple layers of security (validation, sanitization, ORM, constraints)
3. ✅ **Fail Securely**: Errors don't expose sensitive information
4. ✅ **Logging & Monitoring**: All security events logged
5. ✅ **Input Validation**: All inputs validated and sanitized
6. ✅ **Output Encoding**: JSON encoding prevents injection
7. ✅ **Secure Defaults**: Production-ready security by default
8. ✅ **Error Handling**: Comprehensive error handling prevents information leakage

## Environment Variables

Required for production security:

```env
# Required: Use strong random values
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# CORS (comma-separated list)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Flask environment
FLASK_ENV=production
```

## Security Checklist

Before deployment, ensure:

- [ ] `SECRET_KEY` and `JWT_SECRET_KEY` are set to strong random values
- [ ] `DATABASE_URL` uses PostgreSQL (not SQLite) in production
- [ ] `CORS_ALLOWED_ORIGINS` contains only your frontend domain(s)
- [ ] `FLASK_ENV=production` is set
- [ ] HTTPS is enforced at the web server level
- [ ] Database backups are configured
- [ ] Log rotation is working
- [ ] Monitoring/alerting is configured
- [ ] Rate limiting is configured at the web server/proxy level
- [ ] Regular security updates are scheduled

## Additional Recommendations

### Not Yet Implemented (Future Enhancements)

1. **Rate Limiting**: Add Flask-Limiter for API rate limiting
2. **Account Lockout**: Lock accounts after failed login attempts
3. **2FA**: Add two-factor authentication for admin accounts
4. **Security Headers Middleware**: Consider adding Flask-Talisman
5. **API Versioning**: Version the API for backward compatibility
6. **Audit Trail**: Log all data modifications with timestamps and user info
7. **Automated Security Scanning**: Integrate SAST/DAST tools in CI/CD
8. **Penetration Testing**: Regular security audits

## Reporting Security Issues

If you discover a security vulnerability, please email security@example.com (do not create public issues).

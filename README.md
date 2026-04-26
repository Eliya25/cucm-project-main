# 🛡️ CUCM Portal — Phone Management System

מערכת ניהול טלפוניה מבוססת ווב המאפשרת שליטה מרכזית על מכשירי טלפון, אתרים, קבוצות ומשתמשים עם מערכת הרשאות מדורגת.

---

## 📋 תוכן עניינים

1. [סקירה כללית](#סקירה-כללית)
2. [סטק טכנולוגי](#סטק-טכנולוגי)
3. [ארכיטקטורה](#ארכיטקטורה)
4. [מערכת הרשאות](#מערכת-הרשאות)
5. [מודל הנתונים](#מודל-הנתונים)
6. [API Endpoints](#api-endpoints)
7. [התקנה והפעלה](#התקנה-והפעלה)
8. [אבטחה](#אבטחה)

---

## סקירה כללית

CUCM Portal מאפשר ניהול מרכזי של:

- **Sites & Sections** — היררכיה של אתרים ותאים פיזיים
- **Groups** — קבוצות גישה המקשרות בין משתמשים לתאים
- **Users** — ניהול משתמשים עם מערכת הרשאות מדורגת
- **Devices** — מכשירי טלפון עם מיקום ויזואלי
- **Audit Log** — תיעוד מלא של כל פעולה במערכת

---

## סטק טכנולוגי

| שכבה | טכנולוגיה | תפקיד |
|------|-----------|--------|
| Backend | FastAPI + Python 3.12 | REST API, Business Logic |
| Database | PostgreSQL + SQLAlchemy ORM | מסד נתונים + Migrations (Alembic) |
| Frontend | React 18 + Vite | Single Page Application |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| Auth | JWT + HTTPOnly Cookies | Access Token (30min) + Refresh (7d) |
| Security | Argon2 + Token Blacklist | הצפנת סיסמאות + Logout אמיתי |
| Deployment | Docker Compose | Web + DB containers |

---

## ארכיטקטורה

```
cucm-portal/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py        # login, logout, refresh, me
│   │   │   ├── users.py       # CRUD + change-password
│   │   │   ├── sites.py       # sites + sections
│   │   │   ├── groups.py      # groups + link section/user
│   │   │   └── devices.py     # devices + positions
│   │   ├── core/
│   │   │   ├── dependencies.py  # get_current_user, require_admin...
│   │   │   ├── jwt.py           # create/decode tokens
│   │   │   └── security.py      # argon2 hash/verify
│   │   ├── models/
│   │   │   ├── roles.py         # UserRole enum
│   │   │   ├── user.py          # User model + computed properties
│   │   │   ├── site.py          # Site + Section models
│   │   │   ├── group.py         # Group + SectionGroup + UserGroup
│   │   │   ├── device.py        # Device + DevicePosition
│   │   │   └── token_blacklist.py
│   │   ├── schemas/             # Pydantic schemas
│   │   └── main.py              # FastAPI app + CORS + middleware
│   ├── alembic/
│   │   └── versions/            # Migration files
│   ├── logger_manager.py        # Audit logging
│   └── create_super_admin.py    # CLI script
├── frontend/
│   └── src/
│       ├── context/
│       │   └── AuthContext.jsx  # Global auth state
│       ├── components/
│       │   └── Sidebar.jsx      # Navigation + logout
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── Dashboard.jsx
│       │   ├── Sites.jsx        # Sites + Sections + Link to Groups
│       │   ├── Groups.jsx       # Groups + members
│       │   ├── Users.jsx        # User management
│       │   ├── Settings.jsx     # Dark mode, language, password
│       │   └── BulkActions.jsx  # Coming soon
│       └── api.js               # Axios instance (withCredentials)
└── docker-compose.yml
```

---

## מערכת הרשאות

```
SUPERADMIN  ──→  שולט על הכל
    ↓
  ADMIN     ──→  מנהל Sites, Sections, Groups, Users
    ↓
 OPERATOR   ──→  מוסיף/עורך Devices בתאים שלו
    ↓
  VIEWER    ──→  צופה בלבד
```

### כללים חשובים

| פעולה | SUPERADMIN | ADMIN | OPERATOR | VIEWER |
|-------|-----------|-------|----------|--------|
| יצירת ADMIN | ✅ | ❌ | ❌ | ❌ |
| יצירת OPERATOR/VIEWER | ✅ | ✅ | ❌ | ❌ |
| מחיקת Site/Section | ✅ | ❌ | ❌ | ❌ |
| עריכת Site/Section | ✅ | ❌ | ❌ | ❌ |
| יצירת Site/Section | ✅ | ✅ | ❌ | ❌ |
| הוספת Device | ✅ | ✅ | ✅ (בתאים שלו) | ❌ |
| צפייה | ✅ הכל | ✅ הכל | לפי Groups | לפי Groups |

> **⚠️ חשוב:** SuperAdmin לא ניתן ליצירה דרך ה-API — רק דרך CLI script.

---

## מודל הנתונים

### היררכיית הנתונים

```
GROUP ──────────────────────────────────┐
  │                                     │
  ├── SITE                              │
  │     └── SECTION ←── SectionGroup ──┘
  │               └── DEVICE
  │
  └── USER ←── UserGroup ──→ GROUP
```

### טבלאות

| טבלה | תיאור |
|------|--------|
| `users` | משתמשי המערכת עם role ו-is_active |
| `groups` | קבוצות גישה עם classification |
| `user_groups` | שיוך משתמשים לקבוצות (Many-to-Many) |
| `sites` | אתרים פיזיים עם group_id |
| `sections` | תאים בתוך אתרים |
| `section_groups` | הרשאות גישה לתאים + is_admin flag |
| `devices` | מכשירי טלפון עם identifier |
| `device_positions` | מיקום x/y של כל מכשיר |
| `token_blacklist` | Refresh tokens שבוטלו ב-logout |

---

## API Endpoints

### Auth — `/api/v1/auth`

| Method | Endpoint | הרשאה | תיאור |
|--------|----------|--------|--------|
| `POST` | `/login` | ציבורי | התחברות — מחזיר HTTPOnly cookies |
| `GET` | `/me` | כל משתמש | פרטי המשתמש המחובר |
| `POST` | `/refresh` | Cookie | חידוש access_token |
| `POST` | `/logout` | כל משתמש | יציאה + ביטול token ב-DB |

### Users — `/api/v1/users`

| Method | Endpoint | הרשאה | תיאור |
|--------|----------|--------|--------|
| `GET` | `/` | Admin+ | רשימת משתמשים לפי role |
| `POST` | `/` | Admin+ | יצירת משתמש |
| `GET` | `/{id}` | Admin+ | פרטי משתמש |
| `PATCH` | `/{id}` | Admin+ | עדכון משתמש |
| `DELETE` | `/{id}` | Admin+ | מחיקת משתמש |
| `PATCH` | `/{id}/toggle-active` | Admin+ | הפעלה/השבתה |
| `PATCH` | `/me/change-password` | כל משתמש | שינוי סיסמה אישי |

### Sites — `/api/v1/sites`

| Method | Endpoint | הרשאה | תיאור |
|--------|----------|--------|--------|
| `GET` | `/` | כל משתמש | Sites לפי הרשאה |
| `POST` | `/` | Admin+ | יצירת Site |
| `GET` | `/{id}` | כל משתמש | פרטי Site |
| `PATCH` | `/{id}` | SuperAdmin | עדכון Site |
| `DELETE` | `/{id}` | SuperAdmin | מחיקת Site + Sections |
| `POST` | `/sections` | Admin+ | יצירת Section |
| `GET` | `/{id}/sections` | כל משתמש | Sections לפי הרשאה |
| `PATCH` | `/sections/{id}` | SuperAdmin | עדכון Section |
| `DELETE` | `/sections/{id}` | SuperAdmin | מחיקת Section |

### Groups — `/api/v1/groups`

| Method | Endpoint | הרשאה | תיאור |
|--------|----------|--------|--------|
| `GET` | `/` | Admin+ | רשימת Groups |
| `POST` | `/` | Admin+ | יצירת Group |
| `POST` | `/link-site` | Admin+ | קישור Site לGroup |
| `POST` | `/{id}/link-section` | Admin+ | קישור Section לGroup |
| `DELETE` | `/{id}/unlink-section` | Admin+ | ניתוק Section |
| `POST` | `/{id}/add-user` | Admin+ | הוספת משתמש לGroup |
| `DELETE` | `/{id}/remove-user` | Admin+ | הסרת משתמש מGroup |

### Devices — `/api/v1/devices`

| Method | Endpoint | הרשאה | תיאור |
|--------|----------|--------|--------|
| `GET` | `/` | כל משתמש | Devices לפי הרשאה |
| `POST` | `/` | Operator+ | יצירת Device |
| `GET` | `/{id}` | כל משתמש | פרטי Device |
| `PATCH` | `/{id}` | Operator+ | עדכון Device |
| `PUT` | `/{id}/position` | Operator+ | עדכון מיקום |
| `DELETE` | `/{id}` | Operator+ | מחיקת Device |

---

## התקנה והפעלה

### דרישות מקדימות

- Docker Desktop מותקן ופועל
- Node.js 20+
- Git

### הפעלה ראשונה

```bash
# 1. שכפול
git clone <repository-url>
cd cucm-portal

# 2. קובץ .env (בתיקיית backend)
SQLALCHEMY_DATABASE_URL=postgresql://user:password@db:5432/cucm_db
SECRET_KEY=your-secret-key-minimum-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# 3. הרצת Docker
docker compose up -d --build

# 4. הרצת Migrations
docker compose exec web alembic upgrade head

# 5. יצירת SuperAdmin
SUPER_ADMIN_PASSWORD=MyPassword123! docker compose exec web python -m scripts.create_super_admin

# 6. Frontend
cd frontend && npm install && npm run dev
```

### גישה למערכת

| שירות | כתובת |
|-------|--------|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| Swagger Docs | http://localhost:8080/docs |
| Health Check | http://localhost:8080/health/db |

### פקודות Docker שימושיות

```bash
# בדיקת לוגים
docker compose logs -f web

# הרצת migration חדש
docker compose exec web alembic upgrade head

# בדיקת migration נוכחי
docker compose exec web alembic current

# כניסה ל-DB
docker compose exec db psql -U postgres -d cucm_db

# Restart
docker compose restart web
```

---

## אבטחה

### Authentication Flow

```
1. POST /login → Server בודק user+password
2. Server מחזיר שני HTTPOnly cookies:
   - access_token  (תוקף 30 דקות)
   - refresh_token (תוקף 7 ימים)
3. כל בקשה נשלחת עם cookies אוטומטית
4. כשaccess_token פג → POST /refresh → cookie חדש
5. POST /logout → refresh_token נכנס לtoken_blacklist בDB
                → שני הcookies נמחקים
```

### למה HTTPOnly Cookies?

- **לא נגישים ל-JavaScript** — מגן מפני XSS attacks
- **נשלחים אוטומטית** — הפרונט לא צריך לנהל tokens ידנית
- **Refresh שקוף** — המשתמש לא מרגיש שהtoken מתחדש

### הצפנת סיסמאות

Argon2 — האלגוריתם המומלץ ביותר כיום, חזק יותר מ-bcrypt ו-scrypt.

### Audit Log

כל פעולה נרשמת בקובץ log עם:
- שם המשתמש ורמתו
- סוג הפעולה (CREATE, UPDATE, DELETE, LOGIN, LOGOUT...)
- ה-target המושפע
- זמן ו-IP

דוגמה לשורת log:
```
[POST] /api/v1/sites/ | Status: 201 | Time: 45ms | IP: 192.168.1.1 | User: john [admin]
```

---

## פיתוח עתידי

- [ ] אינטגרציה עם CUCM API (zeep/requests)
- [ ] יצירת DN, Profile, User ב-CUCM
- [ ] מנגנון Preset לתבניות טלפונים
- [ ] התראות טלפונים נפולים (WebSocket)
- [ ] Dark Mode מלא
- [ ] Bulk Actions
- [ ] דף Devices עם מפה ויזואלית

---

*CUCM Portal — Built with FastAPI + React*

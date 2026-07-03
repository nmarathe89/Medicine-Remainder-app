# Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ MEDICINE       : owns
    USER ||--o{ ALERT          : receives
    USER ||--o{ FEEDBACK       : submits
    USER ||--o{ SESSION        : has
    MEDICINE ||--o{ ALERT      : generates

    USER {
        int      id PK
        string   username        "unique"
        string   email           "unique"
        string   password_hash
        bool     is_active
        bool     is_admin
        datetime created_at
        datetime last_login_at
    }

    MEDICINE {
        int      id PK
        int      user_id FK
        string   name
        int      dosage_mg
        string   medicine_type   "Bottle|Pill|Syringe|Tablet"
        int      interval_hours  "6|8|12|24"
        string   start_time      "HHMM"
        datetime created_at
        bool     is_deleted
    }

    ALERT {
        int      id PK
        int      user_id FK
        int      medicine_id FK
        datetime scheduled_at
        datetime sent_at         "null until delivered"
        string   status          "pending|sent|acknowledged|skipped"
    }

    FEEDBACK {
        int      id PK
        int      user_id FK
        string   sentiment       "positive|negative"
        string   message
        datetime created_at
    }

    SESSION {
        string   id PK            "opaque token id"
        int      user_id FK
        datetime issued_at
        datetime expires_at
        string   user_agent
    }
```

## Textual view

- **USER** — application accounts. `is_admin=true` unlocks the admin dashboard;
  `is_active` drives the active/inactive pie chart. One user, many devices —
  the `SESSION` table lets us support multi-session login (a JWT `jti` claim
  maps to a `SESSION.id`).
- **MEDICINE** — replaces the on-device JSON blob from the Flutter app.
  Preserves the original four medicine types, dosage in mg, hour-interval,
  and 4-char `HHMM` start time.
- **ALERT** — materialized notification events. APScheduler pre-computes the
  next N alerts per medicine so the admin dashboard can answer *"alerts in
  the next 48 hours"* by a simple `WHERE scheduled_at BETWEEN now AND now+48h`.
- **FEEDBACK** — captures user-submitted positive/negative feedback. Powers
  the "Feedbacks in the last one year" chart.
- **SESSION** — tokens are stateless (JWT) but each carries a `jti` that
  matches a row here; deleting the row revokes that session. Concurrent
  sessions per user are allowed.

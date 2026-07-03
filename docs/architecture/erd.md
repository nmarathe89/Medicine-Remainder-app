# Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ MEDICINES : owns
    USERS ||--o{ ALERTS : receives
    USERS ||--o{ FEEDBACK : submits
    USERS ||--o{ SESSIONS : has
    MEDICINES ||--o{ ALERTS : generates

    USERS {
        int id PK
        string username UK "unique, 3-64 chars"
        string password_hash "bcrypt"
        string role "user | admin"
        bool is_active
        timestamptz created_at
    }

    MEDICINES {
        int id PK
        int user_id FK
        string name "unique per user"
        int dosage "mg; 0 = unspecified"
        string medicine_type "Bottle|Pill|Syringe|Tablet|None"
        int interval_hours "6|8|12|24"
        string start_time "HHMM"
        timestamptz created_at
    }

    ALERTS {
        int id PK
        int medicine_id FK
        int user_id FK
        timestamptz scheduled_at
        string status "pending|sent|taken|skipped"
        timestamptz sent_at "nullable"
    }

    FEEDBACK {
        int id PK
        int user_id FK
        string sentiment "positive | negative"
        string message "<= 500 chars"
        timestamptz created_at
    }

    SESSIONS {
        int id PK
        int user_id FK
        string token_id UK "JWT jti"
        timestamptz created_at
        timestamptz expires_at
        bool revoked
    }
```

## Notes
- **`MEDICINES.name` is unique per user** (`uq_user_medicine_name`), preserving
  the original app's duplicate-name rule.
- **`ALERTS`** materializes each dose reminder so the browser can poll due ones
  and the admin dashboard can count sent / upcoming alerts.
- **`SESSIONS`** holds one row per login (`token_id` = JWT `jti`); multiple rows
  per user provide **multi-session** support, and `revoked` enables logout.
- All FKs cascade on user/medicine delete.
```

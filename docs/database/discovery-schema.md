# TravelMate Database Schema — Discovery, Blocks & Reports

## 1. Tables Overview

Phase 7 introduces persistent state tables for interactions, safety blocking, and moderation reporting.

### `discovery_interactions`
Tracks user actions during discovery browsing (likes, passes).

```sql
CREATE TABLE discovery_interactions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interaction_type VARCHAR(24) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_discovery_interactions_user_target UNIQUE (user_id, target_user_id),
    CONSTRAINT ck_discovery_interactions_not_self CHECK (user_id != target_user_id),
    CONSTRAINT ck_discovery_interactions_type CHECK (interaction_type IN ('like', 'pass', 'super_like', 'save'))
);

CREATE INDEX idx_discovery_interactions_target_type ON discovery_interactions (target_user_id, interaction_type);
```

### `user_blocks`
Enforces bidirectional exclusion between two users across all discovery feeds and profile views.

```sql
CREATE TABLE user_blocks (
    id VARCHAR(36) PRIMARY KEY,
    blocker_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_user_blocks_blocker_blocked UNIQUE (blocker_id, blocked_id),
    CONSTRAINT ck_user_blocks_not_self CHECK (blocker_id != blocked_id)
);

CREATE INDEX idx_user_blocks_blocker ON user_blocks (blocker_id);
CREATE INDEX idx_user_blocks_blocked ON user_blocks (blocked_id);
```

### `user_reports`
Provides safety auditing and triage queues for suspicious activity, harassment, or policy violations.

```sql
CREATE TABLE user_reports (
    id VARCHAR(36) PRIMARY KEY,
    reporter_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(64) NOT NULL,
    details TEXT,
    status VARCHAR(24) DEFAULT 'pending' NOT NULL,
    reviewed_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT ck_user_reports_not_self CHECK (reporter_id != reported_id),
    CONSTRAINT ck_user_reports_status CHECK (status IN ('pending', 'under_review', 'actioned', 'dismissed')),
    CONSTRAINT ck_user_reports_reason CHECK (reason IN (
        'inappropriate_content', 'harassment', 'spam_or_commercial',
        'fake_profile', 'safety_concern', 'other'
    ))
);

CREATE INDEX idx_user_reports_status_created ON user_reports (status, created_at);
CREATE INDEX idx_user_reports_reported ON user_reports (reported_id);
```

---

## 2. Integrity and Cascade Policies

- **Cascade on Deletion**: When an account is deleted, foreign keys with `ON DELETE CASCADE` remove its interaction records, block records, and report entries to preserve GDPR/privacy rights.
- **Mutual Match Resolution**: Matches are dynamically verified whenever a `like` interaction is registered.

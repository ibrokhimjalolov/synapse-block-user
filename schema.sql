CREATE TABLE blocked_users (
    blocker_user_id TEXT NOT NULL,
    blocked_user_id TEXT NOT NULL,
);

CREATE INDEX idx_blocked_users_blocker_user_id ON blocked_users (blocker_user_id);
CREATE UNIQUE INDEX unique_blocked_users ON blocked_users (blocker_user_id, blocked_user_id);

CREATE TABLE users
(
    user_id      VARCHAR(250) PRIMARY KEY,
    access_token VARCHAR(250) NOT NULL,
    settings_json  JSON,
    created_at   TIMESTAMP default CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP
);
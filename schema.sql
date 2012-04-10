-- Unison back-end database schema.
-- Uses some PostgreSQL specific stuff.
--
-- Create the database with:
--     createdb -E UTF8 unison  # UTF-8 encoding.

CREATE TABLE "user" (
  uuid      char(36) PRIMARY KEY,
  room_id   bigint,
  nickname  text NOT NULL,
  model     text -- Base64 encoded
);

CREATE TABLE room (
  id      bigserial PRIMARY KEY,
  name    text NOT NULL,
  master  char(36) REFERENCES "user"
);

-- Add the foreign key constraint on user(room_id).
ALTER TABLE "user" ADD CONSTRAINT room_fk FOREIGN KEY (room_id) REFERENCES room;

CREATE TABLE track (
  id        bigserial PRIMARY KEY,
  artist    text NOT NULL,
  title     text NOT NULL,
  tags      text, -- JSON array
  features  text -- Base64 encoded
);

CREATE TABLE userlib (
  id        bigserial PRIMARY KEY,
  user_id   char(36) NOT NULL REFERENCES "user",
  track_id  bigint NOT NULL REFERENCES track,
  local_id  integer NOT NULL,
  rating    integer
);

CREATE TABLE transaction (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  room_id        bigint REFERENCES room,
  track_id       bigint REFERENCES track,
  master         char(36) REFERENCES "user"
);

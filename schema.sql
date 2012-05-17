-- Unison back-end database schema.
-- Uses some PostgreSQL specific stuff.
--
-- Create the database with:
--     createdb -E UTF8 unison  # UTF-8 encoding.

CREATE OR REPLACE FUNCTION update_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = now(); 
    RETURN NEW;
END;
$$ language 'plpgsql';


CREATE TABLE "user" (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  email          text UNIQUE NOT NULL,
  email_valid    boolean NOT NULL DEFAULT FALSE,
  password       text NOT NULL,
  nickname       text,
  room_id        bigint,
  model          text -- Base64 encoded.
);
CREATE INDEX user_room_idx ON "user"(room_id);


CREATE TABLE room (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  name           text NOT NULL,
  coordinates    point NOT NULL, -- Geographic coordinates.
  master         bigint REFERENCES "user",
  active         boolean NOT NULL DEFAULT FALSE
);
-- Add the foreign key constraint on user(room_id).
ALTER TABLE "user" ADD CONSTRAINT room_fk FOREIGN KEY (room_id) REFERENCES room;


CREATE TABLE track (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  update_time    timestamp NOT NULL DEFAULT now(),
  artist         text NOT NULL,
  title          text NOT NULL,
  image          text, -- As a URL.
  listeners      integer, -- Number of listeners on last.fm.
  tags           text, -- JSON array.
  features       text, -- Base64 encoded.
  UNIQUE (artist, title)
);
CREATE INDEX track_artist_title_idx ON track(artist, title);
CREATE TRIGGER track_update_time_trigger BEFORE UPDATE
    ON track FOR EACH ROW EXECUTE PROCEDURE update_time_column();


-- Entries in this table are not meant to be updated, except for the "valid"
-- field. When something changes (track gets deleted, new local_id, new rating,
-- ...) we should instead invalidate the data and create a new row.
CREATE TABLE lib_entry (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  update_time    timestamp NOT NULL DEFAULT now(),
  user_id        bigint NOT NULL REFERENCES "user",
  track_id       bigint NOT NULL REFERENCES track,
  local_id       integer,
  valid          boolean NOT NULL DEFAULT FALSE,
  local          boolean NOT NULL DEFAULT FALSE,
  rating         integer
);
CREATE INDEX lib_entry_user_idx ON lib_entry(user_id);
CREATE INDEX lib_entry_track_idx ON lib_entry(track_id);
CREATE TRIGGER lib_entry_update_time_trigger BEFORE UPDATE
    ON lib_entry FOR EACH ROW EXECUTE PROCEDURE update_time_column();


CREATE TYPE room_event_type
    AS ENUM ('play', 'rating', 'join', 'leave', 'skip', 'master');
CREATE TABLE room_event (
  id             bigserial PRIMARY KEY,
  creation_time  timestamp NOT NULL DEFAULT now(),
  user_id        bigint REFERENCES "user",
  room_id        bigint REFERENCES room,
  event_type     room_event_type NOT NULL,
  payload        text -- JSON encoded.
);
CREATE INDEX room_event_room_idx ON room_event(room_id);
CREATE INDEX room_event_creation_time_idx ON room_event(creation_time);

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS contact;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE contacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  callsign TEXT NOT NULL,
  frequency INTEGER,
  mode TEXT,
  power INTEGER,
  comments TEXT NOT NULL,
  self_location TEXT,
  contact_location TEXT,
  self_rst INTEGER,
  contact_rst INTEGER,
  FOREIGN KEY (author_id) REFERENCES user (id)
);
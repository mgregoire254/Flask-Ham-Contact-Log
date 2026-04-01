INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO contacts (
  author_id,
  created,
  callsign,
  frequency,
  mode,
  power,
  comments,
  self_location,
  contact_location,
  self_rst,
  contact_rst
)
VALUES
  (1, '2023-02-17 00:00:00', 'K1ABC', 146520, 'FM', 50, 'First seeded contact', 'Boston, MA', 'Providence, RI', 59, 57),
  (2, '2023-02-18 08:30:00', 'W7XYZ', 14250, 'SSB', 100, 'Second seeded contact', 'Seattle, WA', 'Portland, OR', 55, 54);

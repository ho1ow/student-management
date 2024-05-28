CREATE TYPE "user_role" AS ENUM (
  'student',
  'teacher'
);

CREATE TABLE "users" (
  "id" bigserial PRIMARY KEY,
  "class_id" bigserial,
  "username" varchar UNIQUE NOT NULL,
  "password" varchar NOT NULL,
  "fullname" varchar,
  "phone" varchar,
  "role" user_role,
  "created_at" timestamptz NOT NULL DEFAULT (now())
);

  
CREATE TABLE "assignments" (
  "id" bigserial PRIMARY KEY,
  "teacher_id" bigserial,
  "title" varchar NOT NULL,
  "description" text NOT NULL,
  "file_url" varchar,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "submissions" (
  "id" bigserial PRIMARY KEY,
  "assignment_id" bigserial,
  "student_id" bigserial,
  "created_at" timestamptz DEFAULT (now())
);


CREATE TABLE "messages" (
  "id" bigserial PRIMARY KEY,
  "sender_id" bigserial,
  "receiver_id" bigserial,
  "content" text NOT NULL,
  "created_at" timestamptz DEFAULT (now())
);

CREATE TABLE "challenges" (
  "id" bigserial PRIMARY KEY,
  "created_by" bigserial,
  "challenge_url" varchar NOT NULL,
  "hint" text,
  "created_at" timestamptz DEFAULT (now())
);


CREATE TABLE "class" (
  "id" bigserial PRIMARY KEY,
  class_name varchar NOT NULL,
  "teacher_id" bigserial
);

ALTER TABLE "assignments" ADD FOREIGN KEY ("teacher_id") REFERENCES "users" ("id");

ALTER TABLE "submissions" ADD FOREIGN KEY ("assignment_id") REFERENCES "assignments" ("id");

ALTER TABLE "submissions" ADD FOREIGN KEY ("student_id") REFERENCES "users" ("id");

ALTER TABLE "messages" ADD FOREIGN KEY ("sender_id") REFERENCES "users" ("id");

ALTER TABLE "messages" ADD FOREIGN KEY ("receiver_id") REFERENCES "users" ("id");

ALTER TABLE "challenges" ADD FOREIGN KEY ("created_by") REFERENCES "users" ("id");
ALTER TABLE "class" ADD FOREIGN KEY ("teacher_id") REFERENCES "users" ("id");


INSERT INTO "users" ("username", "password", "fullname", "role")
VALUES
  ('ok1', 'ok', 'Teacher 1', 'teacher'),
  ('ok2', 'ok', 'Student 1', 'student'),

INSERT INTO "assignments" ("teacher_id", "title", "description", "file_url")
VALUES
  (1, 'Assignment 1', 'Description 1', 'https://example.com/assignment1.pdf');

INSERT INTO "challenges" ("created_by", "challenge_url", "hint")
VALUES
  (1, 'https://example.com/challenge1.zip', 'Hint 1');
CREATE TYPE "user_role" AS ENUM (
  'student',
  'teacher'
);

CREATE TABLE "users" (
  "id" BIGSERIAL PRIMARY KEY,
  "username" VARCHAR UNIQUE NOT NULL,
  "password" VARCHAR NOT NULL,
  "fullname" VARCHAR NOT NULL,
  "phone" VARCHAR,
  "role" "user_role" NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT (now())
);
CREATE TABLE "teachers" (
  "id" BIGSERIAL PRIMARY KEY,
  "user_id" BIGINT UNIQUE,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT (now()),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE TABLE "class" (
  "id" BIGSERIAL PRIMARY KEY,
  "class_name" VARCHAR NOT NULL,
  "teacher_id" BIGINT,
  FOREIGN KEY ("teacher_id") REFERENCES "teachers" ("id")
);

CREATE TABLE "students" (
  "id" BIGSERIAL PRIMARY KEY,
  "user_id" BIGINT UNIQUE,
  "class_id" BIGINT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT (now()),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id"),
  FOREIGN KEY ("class_id") REFERENCES "class" ("id")
);



CREATE TABLE "assignments" (
  "id" BIGSERIAL PRIMARY KEY,
  "teacher_id" BIGINT,
  "title" VARCHAR NOT NULL,
  "description" TEXT NOT NULL,
  "file_url" VARCHAR,
  "created_at" TIMESTAMPTZ DEFAULT (now()),
  FOREIGN KEY ("teacher_id") REFERENCES "teachers" ("id")
);

CREATE TABLE "submissions" (
  "id" BIGSERIAL PRIMARY KEY,
  "assignment_id" BIGINT,
  "student_id" BIGINT,
  "file_url" VARCHAR,
  "created_at" TIMESTAMPTZ DEFAULT (now()),
  FOREIGN KEY ("assignment_id") REFERENCES "assignments" ("id"),
  FOREIGN KEY ("student_id") REFERENCES "students" ("id")
);

CREATE TABLE "messages" (
  "id" BIGSERIAL PRIMARY KEY,
  "sender_id" BIGINT,
  "receiver_id" BIGINT,
  "content" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ DEFAULT (now()),
  FOREIGN KEY ("sender_id") REFERENCES "users" ("id"),
  FOREIGN KEY ("receiver_id") REFERENCES "users" ("id")
);

CREATE TABLE "challenges" (
  "id" BIGSERIAL PRIMARY KEY,
  "created_by" BIGINT,
  "challenge_url" VARCHAR NOT NULL,
  "hint" TEXT,
  "created_at" TIMESTAMPTZ DEFAULT (now()),
  FOREIGN KEY ("created_by") REFERENCES "teachers" ("id")
);

INSERT INTO "users" ("username", "password", "fullname", "role")
VALUES
  ('teacher1', 'password', 'Teacher 1', 'teacher'),
  ('student1', 'password', 'Student 1', 'student');

INSERT INTO "teachers" ("user_id")
VALUES
  ((SELECT "id" FROM "users" WHERE "username" = 'teacher1'));

INSERT INTO "students" ("user_id", "class_id")
VALUES
  ((SELECT "id" FROM "users" WHERE "username" = 'student1'), 1);

INSERT INTO "class" ("class_name", "teacher_id")
VALUES
  ('Class 1', (SELECT "id" FROM "teachers" WHERE "user_id" = (SELECT "id" FROM "users" WHERE "username" = 'teacher1')));

INSERT INTO "assignments" ("teacher_id", "title", "description", "file_url")
VALUES
  ((SELECT "id" FROM "teachers" WHERE "user_id" = (SELECT "id" FROM "users" WHERE "username" = 'teacher1')), 'Assignment 1', 'Description 1', 'https://example.com/assignment1.pdf');

INSERT INTO "challenges" ("created_by", "challenge_url", "hint")
VALUES
  ((SELECT "id" FROM "teachers" WHERE "user_id" = (SELECT "id" FROM "users" WHERE "username" = 'teacher1')), 'https://example.com/challenge1.zip', 'Hint 1');

INSERT INTO "users" ("username", "password", "fullname", "role")
VALUES
  ('ok1', 'scrypt:32768:8:1$WcnU2qW2pVS6JdK7$c07ced5d0840995b41278d0f3cf7719bb2236e057c550a9eb57021177f565d356c34c6cd37d787b567c86d0c5b3e49d4149ae0e3e354bf8927bb5e1823d10ef9', 'Teacher 2', 'teacher'),
  ('ok','scrypt:32768:8:1$WcnU2qW2pVS6JdK7$c07ced5d0840995b41278d0f3cf7719bb2236e057c550a9eb57021177f565d356c34c6cd37d787b567c86d0c5b3e49d4149ae0e3e354bf8927bb5e1823d10ef9', 'Teacher okok', 'teacher');


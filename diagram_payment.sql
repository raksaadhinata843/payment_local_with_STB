CREATE TYPE "role_admins" AS ENUM (
  'superadmin',
  'operator'
);

CREATE TYPE "users_status" AS ENUM (
  'blocked',
  'active',
  'deleted'
);

CREATE TYPE "type_transactions" AS ENUM (
  'refund',
  'top_up',
  'payment'
);

CREATE TYPE "status_transactions" AS ENUM (
  'pending',
  'success',
  'failed'
);

CREATE TABLE "admins" (
  "id" uuid PRIMARY KEY,
  "username" varchar UNIQUE,
  "role" role_admins NOT NULL DEFAULT 'operator',
  "password" varchar,
  "is_active" boolean
);

CREATE TABLE "device" (
  "id" varchar PRIMARY KEY,
  "location_name" varchar,
  "ip_address" varchar,
  "last_seen_at" timestamp
);

CREATE TABLE "users" (
  "id" uuid PRIMARY KEY,
  "username" varchar,
  "photo_url" varchar,
  "status" users_status NOT NULL DEFAULT 'active',
  "created_at" timestamp
);

CREATE TABLE "cards" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid NOT NULL,
  "body" text,
  "status" varchar UNIQUE,
  "created_at" timestamp
);

CREATE TABLE "wallets" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid UNIQUE,
  "balance" bigint,
  "updated_at" timestamp
);

CREATE TABLE "biometrics" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid,
  "fingerprint_template" blob,
  "fallback_pin" varchar
);

CREATE TABLE "transactions" (
  "id" uuid PRIMARY KEY,
  "idempotency_key" varchar UNIQUE,
  "user_id" uuid,
  "device_id" varchar,
  "admin_id" uuid,
  "amount" bigint,
  "balance_before" bigint,
  "balance_after" bigint,
  "type" type_transactions NOT NULL DEFAULT 'payment',
  "status" status_transactions NOT NULL DEFAULT 'pending',
  "created_at" timestamp
);

CREATE UNIQUE INDEX ON "cards" ("status");

COMMENT ON COLUMN "cards"."body" IS 'Content of the post';

ALTER TABLE "cards" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "wallets" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "biometrics" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("admin_id") REFERENCES "admins" ("id") DEFERRABLE INITIALLY IMMEDIATE;

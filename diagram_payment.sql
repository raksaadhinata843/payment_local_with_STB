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

CREATE TYPE "auth_transaction" AS ENUM (
  'fingerprint',
  'fallback_pin'
);

CREATE TABLE "admins" (
  "id" uuid PRIMARY KEY,
  "username" varchar(50),
  "role" role_admins NOT NULL DEFAULT 'operator',
  "password" varchar(255),
  "is_active" boolean
);

CREATE TABLE "device" (
  "id" varchar(17) PRIMARY KEY,
  "location_name" varchar(21),
  "ip_address" varchar(17),
  "last_seen_at" timestamp
);

CREATE TABLE "users" (
  "id" uuid PRIMARY KEY,
  "username" varchar(50),
  "photo_url" varchar,
  "status" users_status NOT NULL DEFAULT 'active',
  "created_at" timestamp
);

CREATE TABLE "cards" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid NOT NULL,
  "rfid_uid" varchar UNIQUE,
  "is_active" boolean
);

CREATE TABLE "wallets" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid UNIQUE NOT NULL,
  "balance" bigint,
  "updated_at" timestamp
);

CREATE TABLE "biometrics" (
  "id" uuid PRIMARY KEY,
  "user_id" uuid NOT NULL,
  "fingerprint_template" blob,
  "fallback_pin" varchar
);

CREATE TABLE "transactions" (
  "id" uuid PRIMARY KEY,
  "idempotency_key" varchar UNIQUE,
  "user_id" uuid NOT NULL,
  "device_id" varchar(17) NOT NULL,
  "admin_id" uuid NOT NULL,
  "amount" bigint,
  "balance_before" bigint,
  "balance_after" bigint,
  "type" type_transactions NOT NULL DEFAULT 'payment',
  "status" status_transactions NOT NULL DEFAULT 'pending',
  "created_at" timestamp,
  "auth_method" auth_transactions NOT NULL DEFAULT 'fingerprint'
);

CREATE INDEX ON "cards" ("rfid_uid");

CREATE INDEX ON "transactions" ("idempotency_key");

ALTER TABLE "cards" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "wallets" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "biometrics" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("device_id") REFERENCES "device" ("id") DEFERRABLE INITIALLY IMMEDIATE;

ALTER TABLE "transactions" ADD FOREIGN KEY ("admin_id") REFERENCES "admins" ("id") DEFERRABLE INITIALLY IMMEDIATE;

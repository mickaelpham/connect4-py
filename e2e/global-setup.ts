import { execSync } from 'child_process';
import dotenv from 'dotenv';
import path from 'path';
import pg from 'pg';

export default async function globalSetup() {
  dotenv.config({ path: path.resolve(import.meta.dirname, '.env.test') });

  const { POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT } = process.env;
  const projectRoot = path.resolve(import.meta.dirname, '..');

  // 1. Ensure connect4_test database exists
  const sysClient = new pg.Client({
    user: POSTGRES_USER,
    password: POSTGRES_PASSWORD,
    host: POSTGRES_HOST || 'localhost',
    port: Number(POSTGRES_PORT) || 5432,
    database: 'postgres',
  });
  await sysClient.connect();
  const res = await sysClient.query(
    "SELECT 1 FROM pg_database WHERE datname = 'connect4_test'",
  );
  if (res.rowCount === 0) {
    await sysClient.query('CREATE DATABASE connect4_test');
  }
  await sysClient.end();

  // 2. Run alembic migrations
  execSync('uv run alembic upgrade head', {
    cwd: projectRoot,
    env: { ...process.env, POSTGRES_DB: 'connect4_test' },
    stdio: 'inherit',
  });

  // 3. Truncate all tables for a clean start
  const testClient = new pg.Client({
    user: POSTGRES_USER,
    password: POSTGRES_PASSWORD,
    host: POSTGRES_HOST || 'localhost',
    port: Number(POSTGRES_PORT) || 5432,
    database: 'connect4_test',
  });
  await testClient.connect();
  await testClient.query(
    'TRUNCATE refresh_tokens, moves, games, players CASCADE',
  );
  await testClient.end();
}

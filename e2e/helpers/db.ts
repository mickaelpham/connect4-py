import pg from 'pg';

export async function truncateTables(): Promise<void> {
  const client = new pg.Client({
    user: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    host: process.env.POSTGRES_HOST || 'localhost',
    port: Number(process.env.POSTGRES_PORT) || 5432,
    database: 'connect4_test',
  });
  await client.connect();
  await client.query(
    'TRUNCATE refresh_tokens, moves, games, players CASCADE',
  );
  await client.end();
}

# Backup Strategy

## What's Backed Up

PostgreSQL database via `pg_dump` (full logical dump, gzip-compressed).

## Schedule

Daily at 3am via cron. 7-day retention on local disk.

## Setup

1. **Copy the backup script** to the server:
   ```bash
   scp scripts/backup.sh user@server:~/connect4/
   ```

2. **Add a cron job** on the server:
   ```bash
   ssh user@server "crontab -l 2>/dev/null; echo '0 3 * * * ~/connect4/backup.sh'" | ssh user@server "crontab -"
   ```

   Or manually: `ssh user@server crontab -e` and add:
   ```
   0 3 * * * ~/connect4/backup.sh
   ```

3. **Verify** it works:
   ```bash
   ssh user@server "~/connect4/backup.sh"
   ssh user@server "ls -lh ~/connect4/backups/"
   ```

## Restore

```bash
gunzip -c ~/connect4/backups/connect4-YYYYMMDD-HHMMSS.sql.gz | \
  docker compose -f ~/connect4/compose.prod.yaml exec -T postgres psql -U connect4 connect4
```

## Future Improvements

- **Offsite backups**: Add `rclone copy` to S3/Backblaze B2 at the end of `backup.sh`
- **Pre-deploy backup**: Add a backup step to `scripts/deploy.sh` before restarting

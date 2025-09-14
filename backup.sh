#!/bin/bash

BACKUP_DIR="/backups/crypto-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

sqlite3 /app/trading.db ".backup $BACKUP_DIR/trading.db"

cp /app/config/config.json $BACKUP_DIR/config.json
cp /app/.env $BACKUP_DIR/.env

tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
gpg --encrypt --recipient "admin@example.com" $BACKUP_DIR.tar.gz

rm -rf $BACKUP_DIR

aws s3 cp $BACKUP_DIR.tar.gz.gpg s3://crypto-backups/

find /backups -type f -name "*.tar.gz.gpg" -mtime +30 -delete
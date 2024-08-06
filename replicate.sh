#!/usr/bin/env bash
set -e

# Restore the database if it does not already exist.
if [ -f blackout.db ]; then
	echo "Database already exists, skipping restore"
else
	echo "No database found, restoring from replica if exists"
	litestream restore -if-replica-exists -o blackout.db blackout.db
fi

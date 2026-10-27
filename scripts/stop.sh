#!/usr/bin/env bash
set -e

if [ "$1" == "-v" ] || [ "$1" == "--volumes" ]; then
    echo "Dang dung containers va xoa toan bo volumes du lieu..."
    docker compose down -v
else
    echo "Dang dung containers..."
    docker compose down
fi
echo "Da dung toan bo dich vu an toan."

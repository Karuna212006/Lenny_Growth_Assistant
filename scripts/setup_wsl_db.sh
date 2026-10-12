#!/bin/bash
set -e
sudo service postgresql start
sudo -u postgres psql -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lenny') THEN CREATE ROLE lenny WITH LOGIN PASSWORD 'lenny' SUPERUSER; END IF; END \$\$;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'lenny_db'" | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE lenny_db OWNER lenny;"
sudo -u postgres psql -d lenny_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d lenny_db -f /mnt/c/lenny_Growth_Assistant/docs/schema.sql

# Configure postgresql to listen on all interfaces and allow password auth
PG_CONF=$(sudo -u postgres psql -t -P format=unaligned -c "SHOW config_file;")
PG_HBA=$(sudo -u postgres psql -t -P format=unaligned -c "SHOW hba_file;")

sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" "$PG_CONF"
echo "host all all 0.0.0.0/0 md5" | sudo tee -a "$PG_HBA" > /dev/null
echo "host all all ::0/0 md5" | sudo tee -a "$PG_HBA" > /dev/null
sudo service postgresql restart
echo "Database lenny_db configured and ready."

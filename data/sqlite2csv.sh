#!/usr/bin/env bash

mkdir csv
mkdir csv/raw

# obtains all data tables from database
TS=`sqlite3 $1 "SELECT tbl_name FROM sqlite_master WHERE type='table' and tbl_name not like 'sqlite_%';" | tr -d '\r'`

# obtains all views from database
TV=`sqlite3 $1 "SELECT tbl_name FROM sqlite_master WHERE type='view' and tbl_name not like 'sqlite_%';" | tr -d '\r'`

# exports each table to csv
for T in $TS; do
  sqlite3 -header -csv $1 "select * from $T;" > "csv/raw/$T.csv" ;
done

# exports each table to csv
for T in $TV; do
  sqlite3 -header -csv $1 "select * from $T;" > "csv/$T.csv" ;
done

zip -r rwffm_csvs.zip csv

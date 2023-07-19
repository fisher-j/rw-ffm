#!/usr/bin/env bash

# obtains all data tables from database
TS=`sqlite3 $1 "SELECT tbl_name FROM sqlite_master WHERE type='table' and tbl_name not like 'sqlite_%';" | tr -d '\r'`

# exports each table to csv
for T in $TS; do
  sqlite3 -header -csv $1 "select * from $T;" > "csv/$T.csv" ;
done

zip -r rw_csvs.zip csv

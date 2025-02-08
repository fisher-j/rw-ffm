import sqlite3
from pathlib import Path
from shutil import make_archive
import csv

dataDir = Path("../data")
print(dataDir)
conn = sqlite3.connect(dataDir / "rw.db", detect_types=sqlite3.PARSE_DECLTYPES)
print(conn)

def _export(type):
    dir = dataDir / "csv" / type
    dir.mkdir(parents = True, exist_ok=True)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type=?", (type,))
    tables = cur.fetchall()
    for table in tables:
        table = table[0]
        print("current table: ", table)
        cur.execute("SELECT * FROM " + table) 
        fn = Path(dir, table + ".csv")
        with fn.open(mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(i[0] for i in cur.description)
            csv_writer.writerows(cur)
    cur.close()

def export_tables():
    zipfile = dataDir / "rwffm_csvs"
    input = dataDir / "csv"
    _export("view")
    _export("table")
    make_archive(str(zipfile), "zip", str(input))

export_tables()

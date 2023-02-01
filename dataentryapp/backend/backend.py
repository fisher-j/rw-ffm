import traceback
from tkinter import messagebox
import sqlite3
from pathlib import Path
from datetime import datetime, date
import re
import csv

def initialize_database():
    # assumes run from parent directory of dataentryapp
    # create connection and cursor
    global dataDir
    global appDir
    global datasheetsDir
    global conn
    dataDir = Path("data")
    appDir = Path("dataentryapp")
    datasheetsDir = dataDir / "datasheets" / "final"
    conn = sqlite3.connect(dataDir / "rw.db", detect_types=sqlite3.PARSE_DECLTYPES)

    # check if database is empty, if so, create the tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    res = cursor.fetchall()
    cursor.close()

    if not res:
        create_tables()

def create_tables():
    cur = conn.cursor()
    sql_file = open(appDir / "backend" / "create_tables.sql")
    script = sql_file.read()
    cur.executescript(script)
    conn.commit()
    cur.close()

# I might use these values for value checking database inputs
# :TODO ensure that all data inputs are checked for type and value


##########################################################
############### Value validation Functions ###############
##########################################################

valid_vals = {
    "role": ["observer", "recorder"],
    "defectlocation": ["top", "middle", "bottom"],
    "sapsizeclass": ["BH", "2.5", "5", "6", "7", "8", "9", "10"],
    "cwddecay": ["1", "2", "3", "4", "5"]
}

def match_tree_clump(collectid, treeid, clumpid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT treeid, clumpid FROM trees WHERE treeid = ? AND collectid = ?;
        """,
        (treeid, collectid)
    )
    res = cur.fetchone()
    cur.close()
    if not res:
        return True
    if res:
        return res[1] == clumpid


########################################################
################### Delete Commands ####################
########################################################

def delete_unused_saplings(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM clumpsaplings 
        WHERE clumpid NOT IN (
            SELECT clumpid from trees WHERE collectid = ?
        )
        AND collectid = ?
        """,
        (collectid, collectid)
    )
    conn.commit()
    cur.close()

def delete_all_cwd(transectid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM cwd WHERE transectid = ?
        """,
        (transectid,)
    )
    conn.commit()
    cur.close()


def delete_cwd(transectid, diameter, decayclass):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM cwd
        WHERE rowid = (SELECT rowid FROM cwd 
            WHERE transectid = ?
            AND diameter = ?
            AND decayclass = ?
            LIMIT 1)
        """,
        (transectid, diameter, decayclass)
    )
    conn.commit()
    cur.close()

def delete_fuel_crew(transectid, role):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM collectcrew 
        WHERE transectid = ?
        AND role = ?
        """,
        (transectid, role)
    )
    conn.commit()
    cur.close()

def delete_dufflitterfbd(transectid):
    insert_dufflitterfbd(transectid, 5, None, None, None)
    insert_dufflitterfbd(transectid, 10, None, None, None)

def delete_station(transectid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM station WHERE transectid = ?;
        """,
        (transectid,)
    )
    conn.commit()
    cur.close()

def delete_fwd(transectid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM fwd WHERE transectid = ?;
        """,
        (transectid,)
    )
    conn.commit()
    cur.close()

def delete_transect(transectid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM transects WHERE transectid = ?;
        """,
        (transectid,)
    )
    conn.commit()
    cur.close()

def delete_regen_metadata(datasheetid, plotnum, date, **kwargs):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT collectid 
        FROM expand_collection 
        WHERE datasheetid = ? 
        AND plotnum = ?
        """,
        (datasheetid, plotnum)
    )
    collectid = cur.fetchone()[0]
    cur.execute(
        """
        DELETE FROM regenmetadata
        WHERE collectid = ?
        """,
        (collectid,),
    )
    cur.execute(
        """
        DELETE FROM collectdates
        WHERE collectid = ?
        AND date = ?
        """,
        (collectid, date),
    )
    conn.commit()
    cur.close()

def delete_regen_heights(datasheetid, plotnum, spp, sizeclass, cbh, ht):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM regenheights
        WHERE rowid = (
            SELECT regenheights.rowid 
            FROM regenheights 
            JOIN expand_collection USING(collectid) 
            WHERE datasheetid = ? 
            AND plotnum = ? 
            AND spp = ? 
            AND sizeclass = ? 
            AND cbh = ? 
            AND ht = ?
            LIMIT 1
        )
        """,
        (datasheetid, plotnum, spp, sizeclass, cbh, ht),
    )
    conn.commit()
    cur.close()
    return

def delete_regen(datasheetid, plotnum, spp):
    """Delete all regen count and height entries associated with a collection,
    plot and species."""
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM regencounts 
        WHERE collectid = (
            SELECT collectid 
            FROM expand_collection 
            WHERE datasheetid = ? 
            AND plotnum = ?)
        AND spp = ?
        """,
        (datasheetid, plotnum, spp),
    )
    cur.execute(
        """
        DELETE FROM regenheights 
        WHERE collectid = (
            SELECT collectid 
            FROM expand_collection 
            WHERE datasheetid = ? 
            AND plotnum = ?)
        AND spp = ?
        """,
        (datasheetid, plotnum, spp),
    )
    conn.commit()
    cur.close()
    return

def delete_tree_notes(collectid, notes):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM treemetadata 
        WHERE collectid = ? AND notes = ?
        """,
        (collectid, notes),
    )
    conn.commit()
    cur.close()
    return

def delete_crew(collectid, role, member, transectid = None):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM collectcrew 
        WHERE collectid = ?
        AND (transectid = ? OR transectid IS NULL)
        AND role = ?
        AND member = ?
        """,
        (collectid, transectid, role, member),
    )
    conn.commit()
    cur.close()
    return

def delete_dates(collectid, date):
    date = datetime.strptime(date, "%m/%d/%Y").date()
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM collectdates WHERE collectid = ? AND date = ?
        """,
        (collectid, date),
    )
    conn.commit()
    cur.close()
    return

def delete_reftrees(collectid, treeid, distance, azimuth):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM reftrees WHERE collectid = ?
        AND treeid = ? AND distance = ? AND azimuth = ?
        """,
        (collectid, treeid, distance, azimuth),
    )
    conn.commit()
    cur.close()
    return

def delete_clumpsaplings(collectid, clumpid, sapdbh):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM clumpsaplings 
        WHERE rowid = (SELECT rowid FROM clumpsaplings 
            WHERE collectid = ?
            AND clumpid = ? 
            AND sapdbh = ? 
            LIMIT 1)
        """,
        (collectid, clumpid, sapdbh)
    )
    conn.commit()
    cur.close()

def delete_treedefect(collectid, treeid, location, defecttype):
    cur = conn.cursor()
    treeobsid = get_treeobsid(collectid, treeid)
    cur.execute(
        """
        DELETE FROM treedefect 
        WHERE treeobsid = ?
        AND location = ?
        AND defecttype = ?
        """,
        (treeobsid, location, defecttype)
    )
    conn.commit()
    cur.close()

def delete_tree_entry(collectid, treeid):
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM trees 
        WHERE collectid = ?
        AND treeid = ?
        """,
        (collectid, treeid)
    )
    conn.commit()
    cur.close()
    # when deleteing a tree, or changing its clumpid its possible to create
    # orphan saplings
    delete_unused_saplings(collectid)

######################################################
################## Insert commands ###################
######################################################


def insert_datasheet_status(datasheetid, status):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE datasheets SET status = ? WHERE datasheetid = ?;
        """,
        (status, datasheetid)
    )
    conn.commit()
    cur.close()

def insert_transect_notes(transectid, notes):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE transects SET
        notes = ?
        WHERE transectid = ?
        """,
        (notes, transectid)
    )
    conn.commit()
    cur.close()

def insert_cwd(transectid, diameter, decayclass):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO cwd (transectid, diameter, decayclass)
        VALUES (?, ?, ?)
        """,
        (transectid, diameter, decayclass)
    )
    conn.commit()
    cur.close()

def insert_veg(transectid, metermark, livewoody, deadwoody, woodyheight, 
               liveherb, deadherb, herbheight):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO station 
        (transectid, metermark, livewoody, deadwoody, woodyheight, liveherb,
        deadherb, herbheight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (transectid, metermark) DO UPDATE SET
        livewoody = excluded.livewoody,
        deadwoody = excluded.deadwoody,
        woodyheight = excluded.woodyheight,
        liveherb = excluded.liveherb,
        deadherb = excluded.deadherb,
        herbheight = excluded.herbheight
        """,
    (transectid, metermark, livewoody, deadwoody, woodyheight, liveherb, 
     deadherb, herbheight)
    )
    conn.commit()
    cur.close()

def insert_dufflitterfbd(transectid, metermeark, depth, pctlitter, fbd):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO station (transectid, metermark, depth, pctlitter, fbd)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (transectid, metermark) DO UPDATE SET
        depth = excluded.depth,
        pctlitter = excluded.pctlitter,
        fbd = excluded.fbd
        """,
        (transectid, metermeark, depth, pctlitter, fbd)
    )
    conn.commit()
    cur.close()

# TODO: insert a transect, should update on change so as to not
# break the link between data and transect id
def insert_transect(collectid, transectnum):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO transects (collectid, transectnum)
        VALUES (?, ?)
        """,
        (collectid, transectnum)
    )
    conn.commit()
    cur.close()

def insert_slope_azimuth(transectid, slope, azimuth):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE transects
        SET
        slope = ?,
        azimuth = ?
        WHERE transectid = ?
        """,
        (slope, azimuth, transectid)
    )
    conn.commit()
    cur.close()

def insert_fwd(transectid, onehr, tenhr, hundhr):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO fwd (transectid, onehr, tenhr, hundhr)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(transectid) DO UPDATE SET
        onehr = excluded.onehr,
        tenhr = excluded.tenhr,
        hundhr = excluded.hundhr
        """,
        (transectid, onehr, tenhr, hundhr)
    )
    conn.commit()
    cur.close()

def insert_fuel_metadata(collectid, onehrlen, tenhrlen, hundhrlen, thoushrlen):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO fuelmetadata (collectid, onehrlen, tenhrlen, hundhrlen, thoushrlen)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT (collectid) DO UPDATE SET
        onehrlen = excluded.onehrlen,
        tenhrlen = excluded.tenhrlen,
        hundhrlen = excluded.hundhrlen,
        thoushrlen = excluded.thoushrlen
        """,
        (collectid, onehrlen, tenhrlen, hundhrlen, thoushrlen)
    )
    conn.commit()
    cur.close()

# TODO: This function silently fails to enter the date only
# if there is already a date for the collection
def insert_regen_metadata(datasheetid, plotnum, date, seedlingradius, saplingradius, notes):
    cur = conn.cursor()
    date = datetime.strptime(date, "%m/%d/%Y").date()
    cur.execute(
        """
        SELECT collectid 
        FROM expand_collection 
        WHERE datasheetid = ? 
        AND plotnum = ?
        """,
        (datasheetid, plotnum)
    )
    collectid = cur.fetchone()[0]
    cur.execute(
        """
        INSERT INTO regenmetadata (collectid, seedlingradius, saplingradius, notes)
        VALUES(?, ?, ?, ?)
        -- ON CONFLICT(collectid) DO UPDATE SET
        --     seedlingradius = excluded.seedlingradius,
        --     saplingradius = excluded.saplingradius,
        --     notes = excluded.notes
        """,
        (collectid, seedlingradius, saplingradius, notes),
    )

    # for this form, I don't want to allow multiple dates per collection, but I don't
    # want to put a constraint on the table
    cur.execute(
        """
        INSERT INTO collectdates (collectid, date)
        SELECT ?, ?
        WHERE NOT EXISTS(
            SELECT 1 FROM collectdates WHERE collectid = ?
            AND date IS NOT NULL)
        """,
        (collectid, date, collectid)
    )
    conn.commit()
    cur.close()
    return

def insert_regen_heights(datasheetid, plotnum, spp, sizeclass, cbh, ht):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO regenheights (collectid, spp, sizeclass, cbh, ht)
        SELECT collectid, ?, ?, ?, ?
        FROM expand_collection
        WHERE datasheetid = ?
        AND plotnum = ?
        """,
        (spp, sizeclass, cbh, ht, datasheetid, plotnum),
    )
    conn.commit()
    cur.close()
    return

# TODO: currently the function fails silently if a wrong (non-existant) plot number
# is entered, this should warn instead that plotnum does not exist
def insert_regen_counts(datasheetid, plotnum, spp, sizeclass_list, count_list):
    n = len(sizeclass_list)
    # each variable needs to be same length for executemany
    datasheetid, plotnum, spp = [[l] * n for l in [datasheetid, plotnum, spp]]
    cur = conn.cursor()
    cur.executemany(
        """
        INSERT INTO regencounts (collectid, spp, sizeclass, count)
        SELECT collectid, ?, ?, ?
        FROM expand_collection
        WHERE datasheetid = ?
        AND plotnum = ?
        """,
        zip(spp, sizeclass_list, count_list, datasheetid, plotnum),
    )
    conn.commit()
    cur.close()
    return

def insert_tree_notes(collectid, notes):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO treemetadata (collectid, notes) 
        VALUES(?, ?)
        ON CONFLICT (collectid) DO UPDATE SET
        notes = excluded.notes
        """,
        (collectid, notes),
    )
    conn.commit()
    cur.close()
    return

def insert_crew(collectid, role, member, transectid = None):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO collectcrew (collectid, transectid, role, member) 
        VALUES(?, ?, ?, ?)
        ON CONFLICT (collectid, transectid, role) DO UPDATE SET
        member = excluded.member
        """,
        (collectid, transectid, role, member),
    )
    conn.commit()
    cur.close()
    return

def insert_dates(collectid, date, only_one = False):
    try:
        date = datetime.strptime(date, "%m/%d/%Y").date()
    except ValueError:
        messagebox.showerror("Exception", "Use date format: MM/DD/YYYY")
    else:
        if only_one and get_dates(collectid):
            cur = conn.cursor()
            cur.execute(
                """
                DELETE FROM collectdates WHERE collectid = ?
                """,
                (collectid,)
            )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO collectdates (collectid, date) VALUES(?, ?)
            """,
            (collectid, date),
        )
        conn.commit()
        cur.close()
        return

def insert_reftrees(collectid, treeid, distance, azimuth):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reftrees (collectid, treeid, distance, azimuth) 
        VALUES(?, ?, ?, ?)
        """,
        (collectid, treeid, distance, azimuth),
    )
    conn.commit()
    cur.close()
    return


def insert_clumpsaplings(treeid, collectid, clumpid, sapdbh):
    cur = conn.cursor()
    
    treeobsid = get_treeobsid(collectid, treeid)
    if not treeobsid:
        cur.execute(
            """INSERT INTO trees(collectid, treeid, clumpid) VALUES(?, ?, ?)""", 
            (collectid, treeid, clumpid)
        )
    # Now there should be a treeobsid

    cur.execute(
        """
        INSERT INTO clumpsaplings (collectid, clumpid, sapdbh) VALUES(?, ?, ?)
        """,
        (collectid, clumpid, sapdbh),
    )
    conn.commit()
    cur.close()
    return None


def insert_collectid(collection):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO collections (plotid, stageid, datasheettype) 
        VALUES(:plotid, :stage, :type)
        """,
        collection,
    )
    cur.execute(
        """
        SELECT collectid FROM collections 
        WHERE plotid = :plotid 
        AND stageid = :stage 
        AND datasheettype = :type
        """,
        collection,
    )
    output = cur.fetchone()
    conn.commit()
    cur.close()
    if output:
        return output[0]
    else:
        return None


def insert_plot(collection):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO plots (site, treatment, burn, plotnum) 
        VALUES(:site, :treatment, :burn, :plotnum)
        """,
        collection,
    )
    cur.execute(
        """
        SELECT plotid FROM plots 
        WHERE site = :site 
        AND treatment = :treatment 
        AND burn = :burn
        AND plotnum = :plotnum
        """,
        collection,
    )
    output = cur.fetchone()
    conn.commit()
    cur.close()
    if output:
        return output[0]
    else:
        return None


def insert_tree_data(treedata):
    if not treedata[7] or not treedata[0]:
        raise TypeError("Must supply collectid and treeid")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO trees(treeid, spp, dbh, ht, cbh, clumpid, notes, collectid)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(collectid, treeid) DO UPDATE SET
            spp = excluded.spp,
            dbh = excluded.dbh,
            ht = excluded.ht,
            cbh = excluded.cbh,
            clumpid = excluded.clumpid,
            notes = excluded.notes
        """,
        treedata,
    )
    conn.commit()
    cur.close()
    # when deleteing a tree, or changing its clumpid its possible to create
    delete_unused_saplings(treedata[7])


def insert_tree_defect(collectid, treeid, location, defecttype):
    """Insert tree defect observations

    If the tree does not have an observation id yet, one is generated
    by entering collectid and treeid into trees table."""
    cur = conn.cursor()
    treeobsid = get_treeobsid(collectid, treeid)
    if not treeobsid:
        cur.execute(
            """INSERT INTO trees(collectid, treeid) VALUES(?, ?)""", 
            (collectid, treeid)
        )
    # Now there should be a treeobsid
    treeobsid = get_treeobsid(collectid, treeid)
    cur.execute(
        """
        INSERT INTO treedefect (treeobsid, location, defecttype) VALUES (?, ?, ?)
        """,
        (treeobsid, location, defecttype)
    )
    conn.commit()
    cur.close()
    return None


def insert_datasheet(fp):
    n_t = name_timestamp(fp)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO datasheets (filename, modtime) VALUES(?, ?);
        """,
        n_t,
    )
    cur.execute(
        """
        SELECT datasheetid FROM datasheets WHERE filename = ? AND modtime = ?;
        """,
        n_t,
    )
    datasheetid = cur.fetchone()
    conn.commit()
    cur.close()
    if datasheetid:
        return datasheetid[0]
    else:
        return None

def link_datasheet(collectid, datasheetid):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO collectdatasheets (collectid, datasheetid) VALUES (?, ?)
        """,
        (collectid, datasheetid),
    )
    conn.commit()
    cur.close()
    return None

###############################################################
################### Select get commands #######################
###############################################################

def get_datasheet_status(datasheetid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT status FROM datasheets WHERE datasheetid = ?
        """,
        (datasheetid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_transect_notes(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT transectnum, notes 
        FROM transects
        WHERE collectid = ?
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_cwd(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT transectnum, diameter, decayclass
        FROM cwd
        LEFT JOIN transects USING(transectid)
        WHERE collectid = ?
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_veg(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
        transectnum,
        member,
        MAX(CASE WHEN metermark =  5 THEN livewoody END)   "livewoody5",
        MAX(CASE WHEN metermark =  5 THEN deadwoody END)   "deadwoody5",
        MAX(CASE WHEN metermark =  5 THEN woodyheight END) "woodyheight5",
        MAX(CASE WHEN metermark =  5 THEN liveherb END)    "liveherb5",
        MAX(CASE WHEN metermark =  5 THEN deadherb END)    "deadherb5",
        MAX(CASE WHEN metermark =  5 THEN herbheight END)  "herbheight5",
        MAX(CASE WHEN metermark = 10 THEN livewoody END)   "livewoody10",
        MAX(CASE WHEN metermark = 10 THEN deadwoody END)   "deadwoody10",
        MAX(CASE WHEN metermark = 10 THEN woodyheight END) "woodyheight10",
        MAX(CASE WHEN metermark = 10 THEN liveherb END)    "liveherb10",
        MAX(CASE WHEN metermark = 10 THEN deadherb END)    "deadherb10",
        MAX(CASE WHEN metermark = 10 THEN herbheight END)  "herbheight10"
        FROM transects
        LEFT JOIN (SELECT transectid, member
                   FROM collectcrew 
                   WHERE role = "veg") USING(transectid)
        LEFT JOIN fwd USING(transectid)
        LEFT JOIN station USING(transectid)
        WHERE transects.collectid = ?
        GROUP BY transectid
        ORDER BY transectnum
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_veg_swap(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
        transectnum,
        member,
        MAX(CASE WHEN metermark = 10 THEN livewoody END)   "livewoody10",
        MAX(CASE WHEN metermark = 10 THEN deadwoody END)   "deadwoody10",
        MAX(CASE WHEN metermark = 10 THEN woodyheight END) "woodyheight10",
        MAX(CASE WHEN metermark = 10 THEN liveherb END)    "liveherb10",
        MAX(CASE WHEN metermark = 10 THEN deadherb END)    "deadherb10",
        MAX(CASE WHEN metermark = 10 THEN herbheight END)  "herbheight10",
        MAX(CASE WHEN metermark =  5 THEN livewoody END)   "livewoody5",
        MAX(CASE WHEN metermark =  5 THEN deadwoody END)   "deadwoody5",
        MAX(CASE WHEN metermark =  5 THEN woodyheight END) "woodyheight5",
        MAX(CASE WHEN metermark =  5 THEN liveherb END)    "liveherb5",
        MAX(CASE WHEN metermark =  5 THEN deadherb END)    "deadherb5",
        MAX(CASE WHEN metermark =  5 THEN herbheight END)  "herbheight5"
        FROM transects
        LEFT JOIN (SELECT transectid, member
                   FROM collectcrew 
                   WHERE role = "veg") USING(transectid)
        LEFT JOIN fwd USING(transectid)
        LEFT JOIN station USING(transectid)
        WHERE transects.collectid = ?
        GROUP BY transectid
        ORDER BY transectnum
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_transectid(collectid, transectnum):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT transectid FROM transects
        WHERE collectid = ? AND transectnum = ?
        """,
        (collectid, transectnum)
    )
    res = cur.fetchone()
    cur.close()
    return res[0] if res else res

def get_fwd(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
        azimuth,
        member,
        transectnum,
        slope,
        onehr,
        tenhr,
        hundhr,
        MAX(CASE WHEN metermark = 5 THEN depth END) "dufflitter5",
        MAX(CASE WHEN metermark = 5 THEN pctlitter END) "pctlitter5",
        MAX(CASE WHEN metermark = 5 THEN fbd END) "fbd5",
        MAX(CASE WHEN metermark = 10 THEN depth END) "dufflitter10",
        MAX(CASE WHEN metermark = 10 THEN pctlitter END) "pctlitter10",
        MAX(CASE WHEN metermark = 10 THEN fbd END) "fbd10"
        FROM transects
        LEFT JOIN (SELECT transectid, member 
                   FROM collectcrew 
                   WHERE role = "fwd") USING(transectid)
        LEFT JOIN fwd USING(transectid)
        LEFT JOIN station USING(transectid)
        WHERE transects.collectid = ?
        GROUP BY transectid
        ORDER BY transectnum
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_fwd_swap(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
        azimuth,
        member,
        transectnum,
        slope,
        onehr,
        tenhr,
        hundhr,
        MAX(CASE WHEN metermark = 10 THEN depth END) "dufflitter10",
        MAX(CASE WHEN metermark = 10 THEN pctlitter END) "pctlitter10",
        MAX(CASE WHEN metermark = 10 THEN fbd END) "fbd10",
        MAX(CASE WHEN metermark = 5 THEN depth END) "dufflitter5",
        MAX(CASE WHEN metermark = 5 THEN pctlitter END) "pctlitter5",
        MAX(CASE WHEN metermark = 5 THEN fbd END) "fbd5"
        FROM transects
        LEFT JOIN (SELECT transectid, member 
                   FROM collectcrew 
                   WHERE role = "fwd") USING(transectid)
        LEFT JOIN fwd USING(transectid)
        LEFT JOIN station USING(transectid)
        WHERE transects.collectid = ?
        GROUP BY transectid
        ORDER BY transectnum
        """,
        (collectid,)
    )
    res = cur.fetchall()
    cur.close()
    return res

def get_regen_metadata(datasheetid):
    print("datasheetid: ", datasheetid)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT plotnum, MAX(date), seedlingradius, saplingradius, notes 
        FROM expand_collection
        LEFT JOIN regenmetadata USING(collectid)
        LEFT JOIN collectdates USING(collectid)
        WHERE datasheetid = ?
        GROUP BY collectid
        """,
        (datasheetid, ),
    )
    out = cur.fetchall()
    cur.close()
    print(out)
    return out

def func_set(func, *args):
    def setter():
        return func(*args)
    return setter


def get_regen_heights(datasheetid, plotnum, spp, sizeclass):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cbh, ht FROM regenheights
        JOIN expand_collection USING(collectid)
        WHERE datasheetid = ?
        AND plotnum = ?
        AND spp = ?
        AND sizeclass = ?
        """,
        (datasheetid, plotnum, spp, sizeclass),
    )
    out = cur.fetchall()
    cur.close()
    return out

# TODO: Either this, or another function needs to return Notes as well
# And then I need to figure out how to display regen heights.
def get_datasheet_regen_counts(datasheetid):
    """Get counts of regen in wide format from datasheetid"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            plotnum,
            spp,
            MAX(CASE WHEN sizeclass = "<BH" THEN count END) "<BH",
            MAX(CASE WHEN sizeclass = "<2.5" THEN count END) "<2.5",
            MAX(CASE WHEN sizeclass = "<2.5" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<2.5" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<2.5" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht1",
            MAX(CASE WHEN sizeclass = "<5" THEN count END) "<5",
            MAX(CASE WHEN sizeclass = "<5" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<5" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<5" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht2",
            MAX(CASE WHEN sizeclass = "<6" THEN count END) "<6",
            MAX(CASE WHEN sizeclass = "<6" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<6" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<6" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht3",
            MAX(CASE WHEN sizeclass = "<7" THEN count END) "<7",
            MAX(CASE WHEN sizeclass = "<7" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<7" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<7" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht4",
            MAX(CASE WHEN sizeclass = "<8" THEN count END) "<8",
            MAX(CASE WHEN sizeclass = "<8" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<8" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<8" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht5",
            MAX(CASE WHEN sizeclass = "<9" THEN count END) "<9",
            MAX(CASE WHEN sizeclass = "<9" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<9" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<9" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht6",
            MAX(CASE WHEN sizeclass = "<10" THEN count END) "<10",
            MAX(CASE WHEN sizeclass = "<10" AND count > 0 AND (cbh IS NULL OR ht IS NULL) THEN "missing"
                     WHEN sizeclass = "<10" AND count > 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "gotit" 
                     WHEN sizeclass = "<10" AND count = 0 AND (cbh IS NOT NULL OR ht IS NOT NULL) THEN "uhoh" 
                END) "ht7"
        FROM regencounts
        LEFT JOIN regenheights USING(collectid, spp, sizeclass)
        LEFT JOIN expand_collection USING(collectid)
        WHERE datasheetid = ?
        GROUP BY collectid, spp
        ORDER BY regencounts.rowid
        """,
        (datasheetid,)
    )
    output = cur.fetchall()
    cur.close()
    return output

def get_tree_notes(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT (notes) FROM treemetadata WHERE collectid = ?
        """,
        (collectid,)
    )
    output = cur.fetchone()
    cur.close()
    output = output[0] if output else ""
    return output

def get_crew(collectid, transectid=None):
    cur = conn.cursor()
    if transectid:
        cur.execute(
            """
            SELECT transectid, role, member FROM collectcrew 
            WHERE collectid = ? AND transectid = ?
            """,
            (collectid, transectid),
        )
        output = cur.fetchall()
    else:
        cur.execute(
            """
            SELECT role, member FROM collectcrew 
            WHERE collectid = ?
            """,
            (collectid,),
        )
        output = cur.fetchall()
    return output

def get_dates(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date FROM collectdates WHERE collectid = ?
        """,
        (collectid,)
    )
    res = cur.fetchall()
    try:
        output = [[row[0].strftime("%m/%d/%Y")] for row in res]
    except ValueError:
        output = None
        messagebox.showerror("Exception", "Problem importing dates: wrong format")
    cur.close()
    return output

def get_reftrees(collectid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT treeid, distance, azimuth FROM reftrees
        WHERE collectid = ?
        """,
        (collectid,),
    )
    output = cur.fetchall()
    cur.close()
    return output

def get_deffect_sappling_string():
    """Return string representations in a tuple of defects and sapplings
    associated with a tree entry"""


def get_tree_defect(collectid, treeid):
    cur = conn.cursor()
    # get data associated with datatype and datasheet id
    cur.execute(
        """
        SELECT treeid, location, defecttype 
        FROM trees JOIN treedefect USING(treeobsid) 
        WHERE trees.collectid = ? 
        AND trees.treeid = ?;
        """,
        (collectid, treeid),
    )
    trees = cur.fetchall()
    cur.close()
    return trees


def get_treeobsid(collectid, treeid):
    """Returns a numeric tree observation id or None"""
    cur = conn.cursor()
    cur.execute(
        """
    SELECT treeobsid FROM trees WHERE collectid = ? AND treeid = ?
    """,
        (collectid, treeid),
    )
    output = cur.fetchone()
    if output:
        return output[0]
    else:
        return None


def get_datasheet_trees(collectid):
    cur = conn.cursor()
    # get data associated with datatype and datasheet id
    cur.execute(
        """
        SELECT treeid, spp, dbh, ht, cbh, clumpid, defects, clumpsap, notes 
        FROM trees
        LEFT JOIN (SELECT treeobsid, GROUP_CONCAT(defecttype) defects 
            FROM treedefect GROUP BY treeobsid) 
        USING(treeobsid)
        LEFT JOIN (SELECT collectid, clumpid, GROUP_CONCAT(sapdbh) clumpsap
            FROM clumpsaplings GROUP BY clumpid, collectid)
        USING(clumpid, collectid)
        WHERE collectid = ?
        ORDER BY treeobsid;
        """,
        (collectid, ),
    )
    trees = cur.fetchall()
    cur.close()
    return trees


def get_plot_num_collection_id(datasheetid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT plotnum, collectid 
        FROM 
            collections JOIN plots USING (plotid)
        WHERE 
            collectid IN (
                SELECT collectid FROM collectdatasheets WHERE datasheetid = ?);
        """,
        (datasheetid,)
    )
    plot_num_collection_id = cur.fetchall()
    cur.close()
    return plot_num_collection_id


# For a given datasheetid, get full description of each collection associated
# with the sheet


def get_collection_from_datasheetid(datasheetid):
    """Get identification varaiables for current datasheet.

    This function returns a list of dictionaries (one for each collection)
    of values that uniquely identify collections associated with a datasheet.
    """
    cur = conn.cursor()
    keys = ["datasheettype", "datasheetid", "stageid", "collectid", "plotid", "site", "treatment", "burn", "plotnum"]
    cur.execute(
        """
        SELECT datasheettype, datasheetid, stageid, collectid, plotid, site, treatment, burn, plotnum
        FROM collectdatasheets
        JOIN collections USING(collectid)
        JOIN plots USING(plotid)
        WHERE datasheetid = ?;
        """,
        (datasheetid,),
    )
    res = cur.fetchall()
    output = []
    for r in res:
        output.append({k: v for k, v in zip(keys, r)})
    cur.close()
    return output


def search_collectid(collection):
    # Supply stage, datatype, site, treatment, burn, plotnum
    cur = conn.cursor()
    cur.execute(
        """
        SELECT collectid  --, stageid, datasheettype, site, treatment, burn, plotnum
        FROM collections JOIN plots USING (plotid)
        WHERE stageid = :stage 
        AND datasheettype = :type
        AND site = :site
        AND treatment = :treatment
        AND burn = :burn
        AND plotnum = :plotnum;
        """,
        collection,
    )
    output = cur.fetchone()
    cur.close()
    if output:
        return output[0]
    else:
        return None


def search_plotid(collection):
    # Supply stage, site, treatment, burn, plotnum
    cur = conn.cursor()
    cur.execute(
        """
        SELECT plotid  --plotnum, stageid, datasheettype, site, treatment, burn, plotnum
        FROM collections JOIN plots USING (plotid)
        WHERE stageid = :stage 
        AND site = :site
        AND treatment = :treatment
        AND burn = :burn
        AND plotnum = :plotnum;
        """,
        collection,
    )
    output = cur.fetchone()
    if output:
        return output[0]
    else:
        return None

def get_datsheet_id(collection):
    collectid = search_collectid(collection)
    # supply dictionary with stage, type, site, treatment, burn, plotnum
    cur = conn.cursor()
    cur.execute(
        """
        SELECT filename
        FROM collectdatasheets JOIN datasheets USING (datasheetid)
        WHERE datasheetid = ?;
        """,
        (collectid,),
    )
    output = cur.fetchall()
    cur.close()
    return output


def get_clumpsaplings(collectid, clumpid):

    cur = conn.cursor()
    cur.execute(
        """
        SELECT sapdbh FROM clumpsaplings
        WHERE collectid = ? AND clumpid = ?
        """,
        (collectid, clumpid),
    )
    saplings = cur.fetchall()
    cur.close()
    return saplings


def get_datasheets_table():
    cur = conn.cursor()
    cur.execute(
        """
        SELECT datasheetid, filename, modtime, status FROM datasheets
        """
    )
    datasheets = cur.fetchall()
    cur.close()
    return datasheets

# TODO: complete this function
def update_datasheet_table():
    """Updates datasheet table status column if any files have been modified
    or are missing."""
    pass
    # fns = [name_timestamp(f) for f in Path(datasheetsDir).iterdir() if f.is_file()]


#########################################################################
############## filesystem and filename functions ########################
#########################################################################

def name_timestamp(path):
    timestamp = path.stat().st_mtime
    timestamp = datetime.fromtimestamp(timestamp)
    return (path.name, timestamp)

def make_unique_filename(collection):
    """Generate pdf filename for datasheet

    All sheets other than regen are assumed to have a single plot number.
    For regen sheets, plot number is ommited"""

    key_names = ("stage", "type", "site", "treatment", "burn")

    if collection["type"] == "regen":
        # dont' include plotnum number with regen datasheets
        fn_parts = [collection[key] for key in key_names]
    else:
        plot_num = collection["plotnums"][0]
        fn_parts = [collection[key] for key in key_names]
        fn_parts.append(plot_num)
    fp = Path(datasheetsDir, "_".join(fn_parts) + ".pdf")
    fp = ensure_unique_filename(fp)
    return fp

def search_db_filename(fp):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM datasheets WHERE filename = ?
        """,
        (fp.name,),
    )
    output = cur.fetchone()
    cur.close()
    return output

def ensure_unique_filename(fp):
    check1 = fp.exists()
    check2 = search_db_filename(fp)
    while check1 or check2:
        fp = increment_filename(fp)
        check1 = fp.exists()
        check2 = search_db_filename(fp)
    return fp

def increment_filename(fp):
    # any number after an opening parentheses gets incremented.
    m = re.search("(.*)\(([\d]+)", fp.stem)
    if m:
        num = str(int(m[2]) + 1)
        ns = m[1] + "(" + num + ")"
        fp = fp.with_stem(ns)
    else:
        ns = fp.stem + "(1)"
        fp = fp.with_stem(ns)
    return fp


# check plot number
def plot_num_test(num):
    if num.isnumeric():
        if int(num) < 1 or int(num) > 30:
            return num + " not valid plot number"
    else:
        return num + " not valid plot number"

def flag_bad_values(collection, check_values):
    str_vals = {k: collection[k] for k in collection if k != "plotnums"}
    plotnums = collection["plotnums"]
    bad = [
        val + " not in " + key
        for key, val in str_vals.items()
        if val not in check_values[key]
    ]

    # check comma separated numbers in the case of regen
    for n in plotnums:
        t = plot_num_test(n)
        if t:
            bad.append(t)
    return bad

def export_tables():
    dir = dataDir / "csv"
    dir.mkdir(exist_ok=True)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    for table in tables:
        table = table[0]
        cur.execute("SELECT * FROM " + table) 
        fn = Path(dir, table + ".csv")
        with fn.open(mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(i[0] for i in cur.description)
            csv_writer.writerows(cur)
    cur.close()

import os
from dataentryapp.backend import backend
import shutil

# In the case that we have a bunch of precisely named datasheets, this function
# will import them into the database, creating the necessary table entries
# I don't remember why I needed this
def parse_filename(fp):
    keys = ["stage", "type", "site", "treatment", "burn", "plotnums"]
    filename_parts = fp.stem.split("_")
    unit = filename_parts[:5]
    plotnums = filename_parts[5:]
    unit.append(plotnums)
    collection = {k:v for k, v in zip(keys, unit)}
    return collection

def import_from_filename(importDir):
    filepaths = [f for f in importDir.iterdir() if f.is_file()]

    # insert plots, insert collections, insert datasheets, insert collectdatasheets 
    for fp in filepaths:
        collection = parse_filename(fp)
        newfp = backend.make_unique_filename(collection)
        shutil.copy(fp, newfp)
        datasheetid = backend.insert_datasheet(newfp)

        for plot in collection["plotnums"]:
            collection["plotnum"] = int(plot)
            plotid = backend.insert_plot(collection)
            collection["plotid"] = plotid
            collectid = backend.insert_collectid(collection)
            backend.link_datasheet(collectid, datasheetid)

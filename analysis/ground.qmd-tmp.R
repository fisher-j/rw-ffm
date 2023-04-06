 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
library(rgl)
library(sf)
library(terra)
library(DBI)
library(RSQLite)
rast_file <- "../data/gis/raster/DEM.tif"
r <- rast(rast_file)
vect_db <- "../data/gis/vector.gpkg"
v <- st_read(vect_db, "blocks_buffer")
con <- dbConnect(RSQLite::SQLite(), "../data/rw.db")
print("what do you do")

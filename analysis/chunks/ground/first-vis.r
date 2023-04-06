library(rgl)
library(sf)
library(terra)
library(DBI)
library(RSQLite)
library(tibble)
library(dplyr)
library(stringr)
library(ggplot2)
library(tmap)

# Load data
rast_file <- "../data/gis/raster/DEM.tif"
r <- rast(rast_file)
vect_db <- "../data/gis/vector.gpkg"
st_layers(vect_db)
blocks_buffer <- st_read(vect_db, "blocks_buffer", as_tibble = TRUE)
blocks <- st_read(vect_db, "blocks", as_tibble = TRUE)
plot_centers <- st_read(vect_db, "plot_centers", as_tibble = TRUE)

# what is the current plot order
pts <- plot_centers |>
  group_by(THP, Replicate) |>
  mutate(plotnum = row_number()) |>
  select(plotnum, THP, Replicate) |>
  ungroup()

tm_shape(blocks) +
  tm_borders() +
  tm_facets(by = c("THP_Name", "BlockName")) +
  tm_shape(pts) +
  tm_text(size = 1.6, "plotnum") +
  tm_facets(by = c("THP", "Replicate"))

# We numbered plots from the top-left to bottom-right, I'll need an algorithm
# for determing which row a point is on (they don't all have the same
# y-coorinate)

# I assumed that rows had a similar y coordiante and tried different binning
# methods until the bins captured the rows correctly

xy <- st_coordinates(plot_centers)

pts <- plot_centers |>
  bind_cols(xy) |>
  group_by(THP, Replicate) |>
  mutate(plotnum = row_number()) |>
  mutate(row = cut_width(Y, 43, center = median(Y), labels = FALSE)) |>
  arrange(desc(row), plotnum, .by_group = TRUE) |>
  mutate(plotnum = row_number()) |>
  ungroup()

tm_shape(blocks) +
  tm_borders() +
  tm_facets(by = c("THP_Name", "BlockName")) +
  tm_shape(pts) +
  tm_text(size = 1.6, "plotnum") +
  tm_facets(by = c("THP", "Replicate"))

plot_centers <- pts

# We didn't collect data from all plots. Lets look at entered data and see
# which plots were used
con <- dbConnect(RSQLite::SQLite(), "../data/rw.db")
dbListTables(con)

plots_data <- dbGetQuery(con, "SELECT * FROM plots") |> as_tibble()
plots_data

plot_centers <- mutate(plot_centers,
  site = case_when(
    str_detect(THP, "Fairbanks") ~ "fair",
    str_detect(THP, "Top of") ~ "hare",
    str_detect(THP, "Camp 8") ~ "camp8",
    str_detect(THP, "Bob") ~ "bob",
    str_detect(THP, "Dunlap") ~ "dun",
    str_detect(THP, "Cribwall") ~ "crib",
    TRUE ~ NA_character_
  ),
  treatment = str_extract(tolower(Replicate), "ls|m|np"),
  burn = str_extract(tolower(Replicate), "b|nb"),
  .after = "plotnum"
)


# spatial data should include plotids from tabular data
plot_centers <- left_join(
  plot_centers,
  select(plots_data, any_of(c(names(plot_centers), "plotid")))
)

# Now I need to inserts the plot center coordiates into the tabular data
plots_data

data_to_insert <- select(plot_centers, X, Y, plotid) |>
  st_drop_geometry() |>
  tidyr::drop_na() |>
  as.list() |>
  unname()
  

dbExecute(
  con,
  "UPDATE plots SET coord_x = ?, coord_y = ? WHERE plotid = ?",
  params = data_to_insert
)

# our plots were 11.28 meters in diameter
plot_discs <- st_buffer(plot_centers, 11.28)
st_coordinates(plot_centers)

# as a last step, I'll write the plot number data back to the database. I'll
# use the original layer, because it didn't have plot numbers to begin with
st_write(
  plot_centers,
  vect_db,
  "plot_centers_numbered",
  append = FALSE
)
dbGetQuery(con, "SELECT * FROM plots") |> as_tibble()
dbDisconnect(con)
plot_discs

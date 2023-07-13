library(rgl)
library(dplyr)
library(sf)
library(stars)
library(rayshader)

# I want to overlay my plots on a 3d surface representing the terrain for each
# site
my_import_rast <- function(fold) {
  folder <- paste0("../data/gis/", fold)
  list.files(folder, full.names = TRUE, pattern = ".tif$") |>
    st_mosaic() |>
    read_stars()
}
aerial <- my_import_rast("EE_naip_jdsf")
dem <- my_import_rast("usgs_1m_dem")
vect_db <- "../data/gis/named_numbered.gpkg"
my_read <- function(lname) {
  st_read(vect_db, lname, as_tibble = TRUE, quiet = TRUE)
}
blocks_buffer <- my_read("blocks_buffer")
blocks <- my_read("blocks")
plot_centers <- my_read("plot_centers") |> filter(!is.na(plotid))

# determine groupings of blocks for individual figures
list_figures <- function(blocks, by = c(site, burn), my_filter = TRUE) {
  st_drop_geometry(blocks) |>
    filter({{ my_filter }}) |>
    distinct(pick({{ by }})) |>
    purrr::transpose()
}
list_figures(blocks, by = NULL)

# construct a filter get get data for one figure
make_filter <- function(fig) {
  if (length(fig) == 0) return(function(obj) obj)
  filter_expression <- paste0(names(fig), " == ", '"', fig, '"') |>
    rlang::parse_exprs()
  function(obj) {
    filter(obj, !!!filter_expression)
  }
}

fig <- list()

aerial_photo_3d <- function(fig) {

  my_filter <- make_filter(fig)
  oneblock <- my_filter(blocks)
  onedem <- dem[oneblock]

# get actual data for the dem
  dem_matrix <- st_as_stars(onedem)[[1]]

  dem_matrix |>
    # sphere_shade() |>
    height_shade() |>
    # add_shadow(texture_shade(dem_matrix)) |>
    # add_shadow(lamb_shade(dem_matrix), max_darken = 0.2) |>
    # add_overlay(plots_overlay) |>
    # plot_3d(dem_matrix, theta = 300, phi = 25, fov = 60, zoom = 0.8)
    plot_map()

  # title3d(paste(fig, collapse = " "))
  print(paste(fig, collapse = " "))
}

# rgl::mfrow3d(4, 3)
# for(fig in list_figures(blocks)) {
#   rgl::next3d()
#   aerial_photo_3d(fig)
# }


aerial_photo_3d(list(site = "fair", treatment = "m", burn = "nb"))
aerial_photo_3d(list(site = "fair", treatment = "ls", burn = "nb"))
aerial_photo_3d(list(site = "fair", treatment = "np", burn = "nb"))

aerial_photo_3d(fig)



# rgl::rglwidget()

dem_matrix |>
  sphere_shade(texture = rw_texture) |>
  add_overlay(plots_overlay) |>
  plot_3d(dem_matrix)

bb <- st_bbox(oneraster)
deltay <- bb[4] - bb[2]
y_offset <- (1 - 200 / deltay) / 2 
dem_matrix |>
  sphere_shade(texture = rw_texture) |>
  add_shadow(texture_shade(dem_matrix)) |>
  add_shadow(lamb_shade(dem_matrix), max_darken = 0.2) |>
  add_overlay(plots_overlay) |>
  plot_3d(dem_matrix, theta = 300, phi = 25, fov = 60, zoom = 0.8)
render_compass(position = "S", altitude = min(dem_matrix, na.rm = TRUE), compass_radius = 30)
render_scalebar(
  limits = c(0, 200),
  scale_length = c(y_offset, 1 - y_offset),
  y = min(dem_matrix, na.rm = TRUE),
  label_unit = "m"
)

for (i in seq_len(nrow(onecenters))) {
  render_label(
    dem_matrix,
    text = as.character(onecenters[i, "plotnum", drop = TRUE]),
    lat = st_coordinates(onecenters)[i, 2],
    long = st_coordinates(onecenters)[i, 1],
    altitude = 10,
    extent = st_bbox(oneraster),
    linewidth = 1
  )
}

# rgl::rglwidget()

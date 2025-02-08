library(rgl)
library(dplyr)
library(sf)
library(stars)
library(rayshader)
source("./scripts/pan3d.r")

# Allow printing to html document
# Does not seem to work with Quarto
# rgl::setupKnitr(autoprint = TRUE)

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

# determine groupings of blocks for individual figures and alternatively, filter
# out desired targets
list_figures <- function(blocks, by = c(site, burn), my_filter = TRUE) {
  st_drop_geometry(blocks) |>
    dplyr::filter({{ my_filter }}) |>
    distinct(pick({{ by }})) |>
    purrr::transpose()
}

# construct a filter get get data for one figure based on specified groups.
make_filter <- function(fig) {
  x <- purrr::map2(unname(fig), names(fig), ~rlang::expr(!!sym(.y) == !!.x))
  function(obj) {
    filter(obj, !!!x)
  }
}

# This function draws a 3d map of a portion of the study area.
aerial_photo_3d <- function(fig) {

  my_filter <- make_filter(fig)
  oneblock <- my_filter(blocks)
  onecenters <- my_filter(plot_centers)
  oneplots <- st_buffer(onecenters, 11.28)
  map_bb <- st_bbox(oneblock)
  onedem <- dem[map_bb]
  onephoto <- aerial[map_bb]

# get actual data for the dem
  dem_matrix <- st_as_stars(onedem)[[1]]

# provide rgb array how rayshader likes it, also brighten image
  aerial_array <- st_as_stars(onephoto) |>
    slice(band, 1:3) |>
    pull() |>
    (`/`)(255) |>
    scales::rescale(to = c(0, 1)) |>
    aperm(c(2, 1, 3))

# plot outlines with linestrings instead of polygons
  plots_overlay <- rayshader::generate_line_overlay(
    st_cast(oneplots, "MULTILINESTRING"),
    extent = st_bbox(onedem),
    heightmap = dem_matrix,
    color = "red"
  )

  block_overlay <- rayshader::generate_polygon_overlay(
    oneblock,
    extent = st_bbox(onedem),
    heightmap = dem_matrix,
    linecolor = "yellow",
    linewidth = 2,
    palette = "white"
  )
  rw_texture <- create_texture(
    "#bca5a1", "#bf754e", "#6a3b1e", "#bf754e", "#daaa75"
  )

  aerial_array |> 
    add_overlay(plots_overlay) |>
    add_overlay(block_overlay, alphacolor = "white") |>
    plot_3d(dem_matrix, 
      theta = 300, phi = 25, fov = 60, zoom = 0.8,
      plot_new = FALSE, clear_previous = FALSE, close_previous = FALSE
    )

  for (i in seq_len(nrow(onecenters))) {
    render_label(
      dem_matrix,
      text = as.character(onecenters[i, "plotnum", drop = TRUE]),
      lat = st_coordinates(onecenters)[i, 2],
      long = st_coordinates(onecenters)[i, 1],
      altitude = 10,
      extent = st_bbox(onedem),
      linewidth = 1,
      linecolor = "grey30",
      textcolor = "red"
    )
  }
  render_compass(position = "S", altitude = min(dem_matrix, na.rm = TRUE), compass_radius = 30)
  title3d(paste(fig, collapse = " "))
}

# This will render all units at the burn/no-burn level
rgl::mfrow3d(4, 3)
for(fig in list_figures(blocks)) {
  rgl::next3d()
  aerial_photo_3d(fig)
}

rgl::rglwidget()


# aerial_photo_3d(list(site = "fair", burn = "nb"))
# rgl::rglwidget()
# pan3d(2)


# dem_matrix |>
#   sphere_shade(texture = rw_texture) |>
#   add_overlay(plots_overlay) |>
#   plot_3d(dem_matrix)
#
# bb <- st_bbox(oneraster)
# deltay <- bb[4] - bb[2]
# y_offset <- (1 - 200 / deltay) / 2 
# dem_matrix |>
#   sphere_shade(texture = rw_texture) |>
#   add_shadow(texture_shade(dem_matrix)) |>
#   add_shadow(lamb_shade(dem_matrix), max_darken = 0.2) |>
#   add_overlay(plots_overlay) |>
#   plot_3d(dem_matrix, theta = 300, phi = 25, fov = 60, zoom = 0.8)
# render_compass(position = "S", altitude = min(dem_matrix, na.rm = TRUE), compass_radius = 30)
# render_scalebar(
#   limits = c(0, 200),
#   scale_length = c(y_offset, 1 - y_offset),
#   y = min(dem_matrix, na.rm = TRUE),
#   label_unit = "m"
# )


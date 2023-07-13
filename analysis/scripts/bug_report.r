library(sf)
library(rayshader)
library(dplyr)
library(stars)
library(raster)

# coerce array to stars object for subsetting and reprojecting vector data
bay2 <- raster(montereybay)
bay2 <- setExtent(bay2, attr(montereybay, "extent"))
crs(bay2) <- attr(montereybay, "crs")
montereybay2 <- st_as_stars(bay2)
counties2 <- st_transform(monterey_counties_sf, st_crs(montereybay2))

plot_samples <- function(samp_list) {
  for (i in seq_along(samp_list)) {

    counties_samp <- samp_list[[i]]
    cat("Run ", i, "\n")
    dput(counties_samp)

    counties_sub <- filter(counties2, NAME %in% counties_samp)
    bay_sub <- montereybay2[counties_sub]
    # Stars object is an array
    bay_mat <- bay_sub[[1]]

    bay_mat |>
      sphere_shade(zscale = 50) |>
      plot_3d(bay_mat, zscale = 50)
  }
}

# plot many random subsets
rand_samp <- function(n, size = 6) {
  lapply(1:n, sample, x = as.character(monterey_counties_sf$NAME), size = 6)
} 

# Confirmed bad run
samp_list1 <- list(
  c("Salinas", "Soledad", "Watsonville", "Half Moon Bay", "Llagas-Uvas", "Lexington Hills")
)
# Confirmed bad run
samp_list2 <- list(
  c("Soledad", "Pajaro", "Half Moon Bay", "Watsonville", "San Jose", "Llagas-Uvas")
)

# This works (as do most)
set.seed(42)
plot_samples(rand_samp(1))

# But this causes my r session to crash without a message
plot_samples(samp_list1)

# Same with this, but I'm not sure why
# plot_samples(samp_list2)

# Import and wrangle 2d

First I need to import and wrangle spatial and tabular data. Here I'm going to
focus on the 2d, vector data.


::: {.cell file='./ground/chunks/named_and_numbered.r' hash='named_and_numbered_cache/html/first-viz_0a37a12f0f738e283a385bdb5c54f80d'}

```{.r .cell-code  code-fold="true"}
library(sf)
library(DBI)
library(RSQLite)
library(tibble)
library(dplyr)
library(stringr)
library(ggplot2)
library(tmap)

# Load data
layers <- "../data/gis/vector.gpkg"
blocks <- st_read(layers, "Blocks", as_tibble = TRUE, quiet = TRUE)
blocks_buffer  <- st_buffer(blocks, 30)
plot_centers <- st_read(layers, "Plot_Centers", as_tibble = TRUE, quiet = TRUE)

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
```

::: {.cell-output-display}
![](named_and_numbered_files/figure-html/first-viz-1.png){width=672}
:::

```{.r .cell-code  code-fold="true"}
# We numbered plots from the top-left to bottom-right, I'll need an algorithm
# for determing which row a point is on (they don't all have the same
# y-coorinate)

# I assumed that rows had a similar y coordiante and tried different binning
# methods until the bins captured the rows correctly

xy <- st_coordinates(plot_centers)
pts <- plot_centers |>
  bind_cols(xy) |>
  group_by(THP, Replicate) |>
  mutate(plotnum = row_number(), .after = "Replicate") |>
  mutate(row = cut_width(Y, 43, center = median(Y), labels = FALSE)) |>
  arrange(desc(row), plotnum, .by_group = TRUE) |>
  mutate(plotnum = row_number()) |>
  select(-c(X, Y, row)) |>
  ungroup()

tm_shape(blocks) +
  tm_borders() +
  tm_facets(by = c("THP_Name", "BlockName")) +
  tm_shape(pts) +
  tm_text(size = 1.6, "plotnum") +
  tm_facets(by = c("THP", "Replicate"))
```

::: {.cell-output-display}
![](named_and_numbered_files/figure-html/first-viz-2.png){width=672}
:::

```{.r .cell-code  code-fold="true"}
plot_centers <- pts

# We didn't collect data from all plots. Lets look at entered data and see
# which plots were used
con <- dbConnect(RSQLite::SQLite(), "../data/rw.db")
plots_data <- dbGetQuery(con, "SELECT * FROM plots") |> as_tibble()
plots_data
```

::: {.cell-output .cell-output-stdout}
```
# A tibble: 184 × 8
   plotid site  treatment burn  plotnum coord_x coord_y notes
    <int> <chr> <chr>     <chr>   <int>   <dbl>   <dbl> <chr>
 1      1 bob   ls        b          12      NA      NA <NA> 
 2      2 bob   ls        b           3      NA      NA <NA> 
 3      3 bob   ls        b           5      NA      NA <NA> 
 4      4 bob   ls        b           6      NA      NA <NA> 
 5      5 bob   ls        b           9      NA      NA <NA> 
 6      6 bob   ls        nb          1      NA      NA <NA> 
 7      7 bob   ls        nb         12      NA      NA <NA> 
 8      8 bob   ls        nb          3      NA      NA <NA> 
 9      9 bob   ls        nb          6      NA      NA <NA> 
10     10 bob   ls        nb          9      NA      NA <NA> 
# ℹ 174 more rows
```
:::

```{.r .cell-code  code-fold="true"}
# ensure spatial data columns match tabular data
make_names_consistent <- function(df, thp_var, replicate_var, ...) {
  df |>
    mutate(
      site = case_when(
        str_detect({{ thp_var }}, "Fairbanks") ~ "fair",
        str_detect({{ thp_var }}, "Top of") ~ "hare",
        str_detect({{ thp_var }}, "Camp 8") ~ "camp8",
        str_detect({{ thp_var }}, "Bob") ~ "bob",
        str_detect({{ thp_var }}, "Dunlap") ~ "dun",
        str_detect({{ thp_var }}, "Cribwall") ~ "crib",
        TRUE ~ NA_character_
      ),
      treatment = str_extract(tolower({{ replicate_var }}), "ls|m|np"),
      burn = str_extract(tolower({{ replicate_var }}), "b|nb"),
      ...
    ) |>
    rename(thp = {{ thp_var }}, replicate = {{ replicate_var}})
}

# The treatment blocks (and blocks buffer) should also use this naming
# convention
blocks <- make_names_consistent(
  blocks,
  THP_Name,
  BlockName,
  .after = "BlockName"
)
blocks_buffer <- make_names_consistent(
  blocks_buffer,
  THP_Name,
  BlockName,
  .after = "BlockName"
)
plot_centers <- make_names_consistent(
  plot_centers,
  THP,
  Replicate,
  .after = "plotnum"
)


# spatial data should include plotids from tabular data
plot_centers <- left_join(
  plot_centers,
  select(plots_data, any_of(c(names(plot_centers), "plotid")))
) |>
  relocate(plotid)

# Now I could insert the plot center coordiates into the tabular data but I
# think that for now, it is fine to have tabular and spatial data stored
# separately, they can easily be combined when loaded.

# data_to_insert <- select(plot_centers, X, Y, plotid) |>
#   st_drop_geometry() |>
#   tidyr::drop_na() |>
#   as.list() |>
#   unname()
#
# dbExecute(
#   con,
#   "UPDATE plots SET coord_x = ?, coord_y = ? WHERE plotid = ?",
#   params = data_to_insert
# )

# our plots were 11.28 meters in diameter
plot_discs <- st_buffer(plot_centers, 11.28)

tmap_mode("view")
map_kinds <- c("Esri.WorldTopoMap", "Esri.WorldImagery")
tmap_options(basemaps = map_kinds)
tm_shape(blocks) +
  tm_borders(col = "red", lwd = 1.4) +
  tm_shape(plot_discs) +
  tm_borders(col = "red", lwd = 1.4) +
  tm_text(col = "red", size = 1.6, "plotnum")
```

::: {.cell-output-display}
```{=html}
<div class="leaflet html-widget html-fill-item-overflow-hidden html-fill-item" id="htmlwidget-ac0a63aa5b29bad8773a" style="width:100%;height:464px;"></div>
```
:::

```{.r .cell-code  code-fold="true"}
# # as a last step, I'll write the plot number data back to a new database. 
# # This is commented out so it doesn't get written each time it's run
named_numbered <- "../data/gis/named_numbered.gpkg"

st_write(
  st_transform(plot_centers, st_crs(26910)),
  named_numbered,
  "plot_centers",
  append = FALSE
)
```

::: {.cell-output .cell-output-stdout}
```
Deleting layer `plot_centers' using driver `GPKG'
Writing layer `plot_centers' to data source 
  `../data/gis/named_numbered.gpkg' using driver `GPKG'
Writing 445 features with 8 fields and geometry type Point.
```
:::

```{.r .cell-code  code-fold="true"}
st_write(
  st_transform(blocks, st_crs(26910)),
  named_numbered,
  "blocks",
  append = FALSE
)
```

::: {.cell-output .cell-output-stdout}
```
Deleting layer `blocks' using driver `GPKG'
Writing layer `blocks' to data source 
  `../data/gis/named_numbered.gpkg' using driver `GPKG'
Writing 36 features with 6 fields and geometry type Multi Polygon.
```
:::

```{.r .cell-code  code-fold="true"}
st_write(
  st_transform(blocks_buffer, st_crs(26910)),
  named_numbered,
  "blocks_buffer",
  append = FALSE
)
```

::: {.cell-output .cell-output-stdout}
```
Deleting layer `blocks_buffer' using driver `GPKG'
Writing layer `blocks_buffer' to data source 
  `../data/gis/named_numbered.gpkg' using driver `GPKG'
Writing 36 features with 6 fields and geometry type Polygon.
```
:::

```{.r .cell-code  code-fold="true"}
dbDisconnect(con)
```
:::

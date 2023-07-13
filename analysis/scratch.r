
rs <- rast(aerial_files[1])
RGB(rs) <- 1:3
plot(rs)

r <- read_stars(aerial_files[1])
r <- st_as_stars(r)
class(r)
plot(r)
image(r, rgb = c(1, 2, 3))
methods(image)
r1 <- st_rgb(r, 3, use_alpha = FALSE)
class(r1)
plot(r1)

terra::rast(r)
as(r, "Raster")
as(r, "SpatRaster")
st_as_rast

tm_shape(r) +
  tm_rgb()

gdal_utils("info", aerial_files[1])

plot(st_rgb(stars_1, use_alpha = FALSE))
plot(stars_1, rgb = 1:3)
image(stars_1, rgb = 1:3)
image(aerial[oneblock], rgb = 1:3)
plot(aerial[oneblock], rgb = 1:3)
class(stars_1[[1]])
dim(stars_1[[1]])
stars_array <- stars_1[[1]][,,1:3]
dim(stars_array)
stars_rescale <- scales::rescale(stars_array, to = c(0, 255))
stars_2 <- stars_1[,,,1:3]
stars_2[[1]] <- stars_rescale

plot(stars_2, rgb = 1:3)
plot(stars_1, rgb = 1:3, main = NULL)

names(oneimage) <- "onelayer"

oneimage |>
  mutate(onelayer = scales::rescale(onelayer, to = c(0, 255))) |>
  tm_shape() +
  tm_rgb()

tmap::tm_shape(oneimage) +
tmap::tm_rgb() 


# steps to get circle coordinates in correct format for plotting in rgl
onecoords <- sf::st_coordinates(oneplots)
# arbitrary elevation
onecoords2 <- onecoords[, 3] <- 200
onecoords3 <- split(onecoords[,1:3], onecoords[, 4])
onecoords4 <- lapply(onecoords3, matrix, ncol = 3, dimnames = list(NULL, c("X", "Y", "Z")))
onecoords5 <- lapply(onecoords4, \(x) rbind(x, c(NA, NA, NA)))
onecoords6 <- do.call(rbind, onecoords5)

onemesh <- anglr::as.mesh3d(as(oneraster, "Raster"), image_texture = as(oneimage, "Raster"))

id <- shade3d(onemesh)

# all plot circles
rgl::drape3d(id, onecoords6, col = "red", lwd = 3)


plot(map_bb, add = TRUE)
plot(onephoto, rgb = 1:3, reset = FALSE)
plot(oneblock["replicate"], add = TRUE, pal = sf.colors(categorical = TRUE, alpha = 0.2))
plot(oneblock$thp)
oneblock
blocks
plot(oneblock)

shapes <- list(Tetrahedron = tetrahedron3d(), Cube = cube3d(), Octahedron = octahedron3d(),
                 Icosahedron = icosahedron3d(), Dodecahedron = dodecahedron3d(),
                 Cuboctahedron = cuboctahedron3d())
col <- rainbow(6)
open3d()
mfrow3d(3, 2)
for (i in 1:6) {
    next3d()   # won't advance the first time, since it is empty
  shade3d(shapes[[i]], col = col[i])
}
highlevel(integer()) # To trigger display as rglwidget

plot_3d <- function (hillshade, heightmap, zscale = 1, baseshape = "rectangle", 
    solid = TRUE, soliddepth = "auto", solidcolor = "grey20",
    solidlinecolor = "grey30", shadow = TRUE, shadowdepth = "auto", 
    shadowcolor = "auto", shadow_darkness = 0.5, shadowwidth = "auto",
    water = FALSE, waterdepth = 0, watercolor = "dodgerblue",
    wateralpha = 0.5, waterlinecolor = NULL, waterlinealpha = 1, 
    linewidth = 2, lineantialias = FALSE, soil = FALSE, soil_freq = 0.1,
    soil_levels = 16, soil_color_light = "#b39474", soil_color_dark = "#8a623b",
    soil_gradient = 2, soil_gradient_darken = 4, theta = 45, 
    phi = 45, fov = 0, zoom = 1, background = "white", windowsize = 600,
    precomputed_normals = NULL, asp = 1, triangulate = FALSE,
    max_error = 0, max_tri = 0, verbose = FALSE, plot_new = TRUE,
    close_previous = TRUE, clear_previous = TRUE, ...)
{
    if (!plot_new && clear_previous) {
        rgl::clear3d()
    }
    argnameschar = unlist(lapply(as.list(sys.call()), as.character))[-1]
    argnames = as.list(sys.call())
    if (!is.null(attr(heightmap, "rayshader_data"))) {
        if (!("zscale" %in% as.character(names(argnames)))) {
            if (length(argnames) <= 3) {
                zscale = 50
                message("`montereybay` dataset used with no zscale--setting `zscale=50`. For 
a realistic depiction, raise `zscale` to 200.")
            }
            else {
                if (!is.numeric(argnames[[4]]) || !is.null(names(argnames))) {
                  if (names(argnames)[4] != "") {
                    zscale = 50
                    message("`montereybay` dataset used with no zscale--setting `zscale=50`. 
 For a realistic depiction, raise `zscale` to 200.")
                  }
                }
            }
        }
    }
    if (shadowcolor == "auto") {
        shadowcolor = convert_color(darken_color(background,
            darken = shadow_darkness), as_hex = TRUE)
    }
    if (length(windowsize) == 1) {
        windowsize = c(0, 0, windowsize, windowsize)
    }
    else if (length(windowsize) == 2) {
        windowsize = c(0, 0, windowsize)
    }
    else if (length(windowsize) == 3) {
        windowsize = c(windowsize[1], windowsize[2], windowsize[1] + 
            windowsize[3], windowsize[2] + windowsize[3])
    }
    else if (length(windowsize) == 4) {
        windowsize = c(windowsize[1], windowsize[2], windowsize[1] + 
            windowsize[3], windowsize[2] + windowsize[4])
    }
    else {
        stop(paste0("Don't know what to do with `windowsize` argument of length ",
            length(windowsize)))
    }
    heightmap = generate_base_shape(heightmap, baseshape)
    if (any(hillshade > 1 | hillshade < 0, na.rm = TRUE)) {
        stop("Argument `hillshade` must not contain any entries less than 0 or more than 1") 
    }
    flipud = function(x) {
        x[nrow(x):1, ]
    }
    if (is.null(heightmap)) {
        stop("heightmap argument missing--need to input both hillshade and original elevation
 matrix")
    }
    min_height = min(heightmap, na.rm = TRUE)
    max_height = max(heightmap, na.rm = TRUE)
    if (soliddepth == "auto") {
        if (min_height != max_height) {
            soliddepth = min_height/zscale - (max_height/zscale - 
                min_height/zscale)/5
        }
        else {
            max_dim = max(dim(heightmap))
            soliddepth = min_height/zscale - max_dim/25
        }
    }
    else {
        if (soliddepth > min_height) {
            message(sprintf("`soliddepth` (set to %f) must be less than or equal to heightmap
 minimum value (%f). Setting to min(heightmap)",
                soliddepth, min_height))
            soliddepth = min_height/zscale
        }
        else {
            soliddepth = soliddepth/zscale
        }
    }
    if (solid) {
        min_height_shadow = min(c(min_height, soliddepth * zscale))
    }
    else {
        min_height_shadow = min_height
    }
    if (shadowdepth == "auto") {
        if (min_height_shadow != max_height) {
            if (solid) {
                shadowdepth = soliddepth - (max_height/zscale - 
                  min_height_shadow/zscale)/5
            }
            else {
                shadowdepth = min_height_shadow/zscale - (max_height/zscale - 
                  min_height_shadow/zscale)/5
            }
        }
        else {
            if (solid) {
                max_dim = max(dim(heightmap))
                shadowdepth = soliddepth - max_dim/25
            }
            else {
                max_dim = max(dim(heightmap))
                shadowdepth = min_height - max_dim/25
            }
        }
    }
    else {
        if (shadowdepth > min_height) {
            message(sprintf("`shadowdepth` (set to %f) is greater to heightmap minimum value 
(%f). Shadow will appear to be intersecting 3D model.",
                shadowdepth, min_height))
        }
        else {
            shadowdepth = shadowdepth/zscale
        }
    }
    if (shadowwidth == "auto") {
        shadowwidth = max(floor(min(dim(heightmap))/10), 5)
    }
    if (water) {
        if (watercolor == "imhof1") {
            watercolor = "#defcf5"
        }
        else if (watercolor == "imhof2") {
            watercolor = "#337c73"
        }
        else if (watercolor == "imhof3") {
            watercolor = "#4e7982"
        }
        else if (watercolor == "imhof4") {
            watercolor = "#638d99"
        }
        else if (watercolor == "desert") {
            watercolor = "#caf0f7"
        }
        else if (watercolor == "bw") {
            watercolor = "#dddddd"
        }
        else if (watercolor == "unicorn") {
            watercolor = "#ff00ff"
        }
        if (is.null(waterlinecolor)) {
        }
        else if (waterlinecolor == "imhof1") {
            waterlinecolor = "#f9fffb"
        }
        else if (waterlinecolor == "imhof2") {
            waterlinecolor = "#8accc4"
        }
        else if (waterlinecolor == "imhof3") {
            waterlinecolor = "#8cd4e2"
        }
        else if (waterlinecolor == "imhof4") {
            waterlinecolor = "#c7dfe5"
        }
        else if (waterlinecolor == "desert") {
            waterlinecolor = "#cde3f2"
        }
        else if (waterlinecolor == "bw") {
            waterlinecolor = "#ffffff"
        }
        else if (waterlinecolor == "unicorn") {
            waterlinecolor = "#ffd1fb"
        }
    }
    tempmap = tempfile(fileext = ".png")
    save_png(hillshade, tempmap)
    precomputed = FALSE
    if (is.list(precomputed_normals)) {
        normals = precomputed_normals
        precomputed = TRUE
    }
    if (triangulate && any(is.na(heightmap))) {
        if (interactive()) {
            message("`triangulate = TRUE` cannot be currently set if any NA values present--s
ettings `triangulate = FALSE`")
        }
        triangulate = FALSE
    }
    if (close_previous && rgl::cur3d() != 0) {
        rgl::close3d()
    }
    if (plot_new || rgl::cur3d() == 0) {
        rgl::open3d(windowRect = windowsize, mouseMode = c("none",
            "polar", "fov", "zoom", "pull"))
    }
    rgl::view3d(zoom = zoom, phi = phi, theta = theta, fov = fov)
    attributes(heightmap) = attributes(heightmap)["dim"]
    if (!triangulate) {
        if (!precomputed) {
            normals = calculate_normal(heightmap, zscale = zscale)
        }
        dim(heightmap) = unname(dim(heightmap))
        normalsx = (t(normals$x[c(-1, -nrow(normals$x)), c(-1,
            -ncol(normals$x))]))
        normalsy = (t(normals$z[c(-1, -nrow(normals$z)), c(-1,
            -ncol(normals$z))]))
        normalsz = (t(normals$y[c(-1, -nrow(normals$y)), c(-1,
            -ncol(normals$y))]))
        ray_surface = generate_surface(heightmap, zscale = zscale)
        rgl::triangles3d(x = ray_surface$verts, indices = ray_surface$inds,
            texcoords = ray_surface$texcoords, normals = matrix(c(normalsz, 
                normalsy, -normalsx), ncol = 3L), texture = tempmap,
            color = "white", lit = FALSE, tag = "surface_tris",
            back = "culled")
    }
    else {
        tris = terrainmeshr::triangulate_matrix(heightmap, maxError = max_error,
            maxTriangles = max_tri, start_index = 0L, verbose = verbose)
        index_vals = seq_len(nrow(tris))
        tris[, 2] = tris[, 2]/zscale
        nr = nrow(heightmap)
        nc = ncol(heightmap)
        rn = tris[, 1] + 1
        cn = tris[, 3] + 1
        texcoords = tris[, c(1, 3)]
        texcoords[, 1] = texcoords[, 1]/(nrow(heightmap) - 1)
        texcoords[, 2] = texcoords[, 2]/(ncol(heightmap) - 1)
        tris[, 1] = tris[, 1] - nrow(heightmap)/2 + 1
        tris[, 3] = tris[, 3] - ncol(heightmap)/2
        tris[, 3] = -tris[, 3]
        rgl::triangles3d(tris, texcoords = texcoords, indices = index_vals, 
            texture = tempmap, lit = FALSE, color = "white",
            tag = "surface_tris")
    }
    rgl::bg3d(color = background, texture = NULL)
    if (solid && !triangulate) {
        make_base(heightmap, basedepth = soliddepth, basecolor = solidcolor,
            zscale = zscale, soil = soil, soil_freq = soil_freq, 
            soil_levels = soil_levels, soil_color1 = soil_color_light,
            soil_color2 = soil_color_dark, soil_gradient = soil_gradient, 
            gradient_darken = soil_gradient_darken)
    }
    else if (solid && triangulate) {
        make_base_triangulated(tris, basedepth = soliddepth,
            basecolor = solidcolor)
    }
    if (!is.null(solidlinecolor) && solid) {
        make_lines(heightmap, basedepth = soliddepth, linecolor = solidlinecolor,
            zscale = zscale, linewidth = linewidth)
    }
    if (shadow) {
        make_shadow(heightmap, shadowdepth, shadowwidth, background,
            shadowcolor)
    }
    if (water) {
        make_water(heightmap, waterheight = waterdepth, wateralpha = wateralpha,
            watercolor = watercolor, zscale = zscale)
    }
    if (!is.null(waterlinecolor) && water) {
        if (all(!is.na(heightmap))) {
            make_lines(fliplr(heightmap), basedepth = waterdepth,
                linecolor = waterlinecolor, zscale = zscale,
                linewidth = linewidth, alpha = waterlinealpha, 
                solid = FALSE)
        }
        make_waterlines(heightmap, waterdepth = waterdepth, linecolor = waterlinecolor,      
            zscale = zscale, alpha = waterlinealpha, linewidth = linewidth,
            antialias = lineantialias)
    }
    if (asp != 1) {
        height_range = range(heightmap, na.rm = TRUE)/zscale
        height_scale = height_range[2] - height_range[1]
        rgl::aspect3d(x = dim(heightmap)[1]/height_scale, y = 1,
            z = dim(heightmap)[2] * asp/height_scale)
    }
}

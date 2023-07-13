library(rgl)
pan3d <- function(button, dev = cur3d(), subscene = currentSubscene3d(dev)) {
  start <- list()

  begin <- function(x, y) {
    activeSubscene <- par3d("activeSubscene", dev = dev)
    start$listeners <<- par3d("listeners", dev = dev, subscene = activeSubscene)
    for (sub in start$listeners) {
      init <- par3d(c("userProjection", "viewport"), dev = dev, subscene = sub)
      init$pos <- c(x / init$viewport[3], 1 - y / init$viewport[4], 0.5)
      start[[as.character(sub)]] <<- init
    }
  }

  update <- function(x, y) {
    for (sub in start$listeners) {
      init <- start[[as.character(sub)]]
      xlat <- 2 * (c(x / init$viewport[3], 1 - y / init$viewport[4], 0.5) - init$pos)
      mouseMatrix <- translationMatrix(xlat[1], xlat[2], xlat[3])
      par3d(userProjection = mouseMatrix %*% init$userProjection, dev = dev, subscene = sub)
    }
  }
  rgl.setMouseCallbacks(button, begin, update, dev = dev, subscene = subscene)
  cat("Callbacks set on button", button, "of RGL device", dev, "in subscene", subscene, "\n")
}

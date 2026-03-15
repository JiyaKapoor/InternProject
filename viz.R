library(animint2)

iris$speciesLabel <- as.character(iris$Species)

viz <- animint(
  
  plot1 = ggplot() +
    geom_point(
      aes(
        x       = Sepal.Length,
        y       = Sepal.Width,
        color   = speciesLabel,
        tooltip = paste("Species:", speciesLabel)
      ),
      data         = iris,
      clickSelects = "speciesLabel"
    ) +
    ggtitle("Click a species to filter plot 2") +
    xlab("Sepal Length") +
    ylab("Sepal Width"),
  
  plot2 = ggplot() +
    geom_point(
      aes(
        x       = Petal.Length,
        y       = Petal.Width,
        color   = speciesLabel,
        tooltip = paste("Species:", speciesLabel)
      ),
      data         = iris,
      showSelected = "speciesLabel"
    ) +
    ggtitle("Petal dimensions (filtered by click)") +
    xlab("Petal Length") +
    ylab("Petal Width"),
  
  title  = "Iris Explorer",
  source = "https://github.com/JiyaKapoor/animint2-source"
)

animint2pages(viz, "animint2-pages")

 


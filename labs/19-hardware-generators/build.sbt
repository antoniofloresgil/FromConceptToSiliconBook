scalaVersion := "2.13.12"
libraryDependencies += "org.chipsalliance" %% "chisel" % "6.5.0"
addCompilerPlugin("org.chipsalliance" % "chisel-plugin" % "6.5.0" cross CrossVersion.full)

lazy val writeRuntimeClasspath = taskKey[Unit]("Record the compiled generator runtime classpath")
writeRuntimeClasspath := {
  val paths = (Runtime / fullClasspath).value.map(_.data.getAbsolutePath)
  IO.write(file("/opt/generator.classpath"), paths.mkString(java.io.File.pathSeparator))
}

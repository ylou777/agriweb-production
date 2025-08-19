#!/bin/bash
echo "🚀 Démarrage GeoServer pour Railway..."

# Configuration spécifique Railway
export GEOSERVER_DATA_DIR=/opt/geoserver/data_dir
export JAVA_OPTS="-Xms512m -Xmx1024m -Djava.awt.headless=true -Dfile.encoding=UTF8"

# Démarrage GeoServer
exec /usr/local/tomcat/bin/catalina.sh run

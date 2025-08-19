# GeoServer optimisé pour Railway Pro
FROM kartoza/geoserver:2.24.0

# Configuration mémoire pour Railway Pro
ENV GEOSERVER_DATA_DIR=/opt/geoserver_data
ENV JAVA_OPTS="-Xms512m -Xmx1536m -Djava.awt.headless=true -XX:+UseContainerSupport -XX:MaxRAMPercentage=75"

# Configuration GeoServer
ENV GEOSERVER_CSRF_DISABLED=true
ENV GEOSERVER_LOG_LOCATION=/dev/stdout
ENV INITIAL_MEMORY="512M"
ENV MAXIMUM_MEMORY="1536M"

# Port pour Railway
EXPOSE 8080

# Healthcheck pour Railway
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
  CMD curl -f http://localhost:8080/geoserver/web/ || exit 1

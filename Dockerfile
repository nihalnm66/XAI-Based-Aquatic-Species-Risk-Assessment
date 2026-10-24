FROM maven:3.9.11-eclipse-temurin-25 AS build

WORKDIR /workspace
COPY Backend_Service/pom.xml Backend_Service/pom.xml
RUN mvn -f Backend_Service/pom.xml dependency:go-offline -q

COPY Backend_Service Backend_Service
COPY Frontend/index.html Backend_Service/src/main/resources/static/index.html
COPY py_scripts py_scripts
RUN mvn -f Backend_Service/pom.xml package -DskipTests -q

FROM eclipse-temurin:25-jre

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/Backend_Service
COPY --from=build /workspace/Backend_Service/target/*.jar /app/app.jar
COPY requirements.txt /app/requirements.txt
COPY py_scripts /app/py_scripts
COPY Debris_Detection_Model/yolo11m_aquatic_debris.onnx /app/Debris_Detection_Model/yolo11m_aquatic_debris.onnx
COPY Species_Detection_Model/yolo11_species.onnx /app/Species_Detection_Model/yolo11_species.onnx
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]

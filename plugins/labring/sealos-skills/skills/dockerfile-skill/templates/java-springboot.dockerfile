# syntax=docker/dockerfile:1.4

# ============================================
# Stage 1: Build
# ============================================
FROM eclipse-temurin:21-jdk-alpine AS build

WORKDIR /app

# Install Maven or Gradle (choose one)
# For Maven:
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN chmod +x mvnw

# Download dependencies with cache
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw dependency:go-offline -B

# Copy source code
COPY src ./src

# Build application
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw package -DskipTests -B

# For Gradle (alternative):
# COPY gradlew build.gradle settings.gradle ./
# COPY gradle ./gradle
# RUN chmod +x gradlew
# RUN --mount=type=cache,target=/root/.gradle \
#     ./gradlew dependencies --no-daemon
# COPY src ./src
# RUN --mount=type=cache,target=/root/.gradle \
#     ./gradlew build -x test --no-daemon

# ============================================
# Stage 2: Runtime
# ============================================
FROM eclipse-temurin:21-jre-alpine AS runtime

WORKDIR /app

# Set environment variables
ENV JAVA_OPTS="-Xmx512m -Xms256m"
ENV SERVER_PORT=8080
ENV SPRING_PROFILES_ACTIVE=production

# Install fonts if needed for PDF generation
# RUN apk add --no-cache fontconfig fonts-dejavu

# Copy JAR from build stage
COPY --from=build /app/target/*.jar app.jar

# Create non-root user
RUN adduser -D -u 1000 appuser
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/actuator/health || exit 1

# Start application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

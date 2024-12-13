# Gacha Microservices

A **Microservices-Powered** Gacha **REST API** and **Web Client** developed as part of the Advanced Software Engineering 24/25 course project.

Technologies used: Docker, Python, Flask, PHP, JavaScript, HTML, CSS, MongoDB, Redis, Docker Compose, Postman, Locust, OpenAPI Specification, GitHub Actions.

## Architecture Overview

The system showcases a **microservices-based architecture** built on **Docker Compose**, keeping in mind modularity, scalability, and adherence to modern software engineering principles.

### Key Components:

- **6 Microservices**:
  - Implemented in **Python** using the **Flask** framework.
  - Each service is isolated and communicates via REST APIs.

- **Web Client Frontend**:
  - Built with **PHP**, **JavaScript**, **HTML**, and **CSS**.
  - Provides an intuitive user interface for interacting with the system.

- **Databases**:
  - **4 MongoDB Instances**:
    - Each microservice uses its dedicated database for storing domain-specific data.
  - **1 Redis Instance**:
    - Optimized for the authentication microservice to ensure high-performance operations, such as token management.

![image](https://github.com/user-attachments/assets/f75b72ac-fc88-42b9-942b-05d74d5b1262)

## Tools and Enhancements

- **Integration Testing**:
  - Over 100 tests created and managed via **Postman** to ensure API reliability.

- **Load Testing**:
  - Conducted using **Locust** to evaluate system performance under high traffic.

- **API Documentation**:
  - Built using the **OpenAPI Specification** to provide clear and comprehensive API references.

- **CI/CD Pipeline**:
  - **GitHub Actions** workflows automate:
    - Image building.
    - Execution of integration and isolation tests.






## Get Started

The whole architecture is fully containerized with **Docker Compose**, guaranteeing portability and an easy setup.

1. Navigate to the src folder:
   
   ```shell
   cd ASE_Project/src
   ```

2. Build and start the services using Docker Compose:
   
   ```shell
   docker compose up --build
   ```

3. Navigate to the **root** folder (important):
   
   ```shell
   cd ..
   ```

4. Run the integration tests collection using Newman:
   
   ```shell
   newman run docs/integration-tests.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   ```

5. Use the browser client on localhost:8080

## Isolation Testing

To test each microservice in isolation, run the following steps:

1. Navigate to the chosen microservice directory (auth/gatcha/market/user):
   
   ```shell
   cd ASE_Project/src/<microservice directory>
   ```

2. Build and start the service in isolation using Docker Compose:
   
   ```shell
   docker compose up --build
   ```

3. Navigate to the **root** folder (important):
   
   ```shell
   cd ..
   ```

4. Run the isolation tests collection using Newman:
   
   ```shell
   newman run docs/isolation-auth-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-gatcha-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-market-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   newman run docs/isolation-user-service.postman_collection.json -e docs/localhost-ema-with-https.postman_environment.json --insecure
   ```

## The /docs folder

Contains:

- architecture.yml: the architecture diagram exported from MicroFreshner, can be imported into the web app to view the architecture.
- Gaga OpenAPI.yml: the openAPI specification, importable in Swagger to check the REST API endpoint specification.
- ASE Report.pdf: the detailed report of the project.
- locustfile.py: locust python script for performance and rolling probabilities tests.
- The Postman collections and environment for integration and isolation testing.
- A test.jpg image, used by the Postman tests.

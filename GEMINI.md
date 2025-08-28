# Project Guide: Course Allocation Backend

This document provides guidelines and context for any collaborator to effectively understand, maintain, and contribute to the Course Allocation Backend project.

## 1. Project Overview

This project is a Python-based backend system for a university course allocation platform, built with the Flask web framework. Its core purpose is to manage and automate the assignment of courses to lecturers.

The system is designed to handle complex academic structures, including departments, programs, and curriculum bulletins (for versioning). It features a robust role-based access control (RBAC) system for `superadmin`, `vetter`, `hod`, and `lecturer` roles.

For a detailed breakdown of the data models and their relationships, please refer to the `model_document.md` file.

## 2. Tech Stack

When making changes, adhere to the existing technology stack:

*   **Backend Framework:** Flask
*   **Database ORM:** Flask-SQLAlchemy
*   **Database Migrations:** Flask-Migrate (Alembic)
*   **Authentication:** Flask-JWT-Extended (using HttpOnly cookies)
*   **Password Hashing:** Flask-Bcrypt
*   **CORS:** Flask-CORS
*   **Environment Variables:** `python-dotenv`

## 3. Project Structure

The project is organized into modules using Flask Blueprints, which should be maintained:

*   `run.py`: Main application entry point.
*   `app/`: Core application package.
    *   `__init__.py`: Application factory (`create_app`) where extensions and blueprints are registered.
    *   `config.py`: Application configuration, loaded from `.env`.
    *   `models/`: Contains all SQLAlchemy database models.
    *   `routes/`: Contains API endpoint definitions, organized by resource.
    *   `auth/`: Contains the authentication-related routes.
    *   `services/`: **(To be created)** This directory should house business logic, separated from the route handlers.

## 4. Development Workflow & Commands

*   **To Run the Development Server:**
    ```bash
    flask run
    ```

*   **To Manage Database Migrations:**
    *   Generate a new migration: `flask db migrate -m "Your descriptive message"`
    *   Apply a migration: `flask db upgrade`

## 5. Guidelines for Contributions

To ensure the project's quality and maintainability are continuously improved, all contributions must adhere to the following guidelines.

### 1. Automated Testing is Mandatory

*   **Guideline:** The project is establishing a testing culture. Any new feature or bug fix **must** be accompanied by corresponding tests.
*   **Action:** Before committing, create a `tests/` directory if it doesn't exist. Write unit and integration tests for your changes using the `pytest` framework. Ensure tests cover models, business logic (services), and API endpoints.

### 2. Implement a Service Layer

*   **Guideline:** To improve separation of concerns, business logic must not be implemented directly within route handlers.
*   **Action:** Create and use a service layer. For any new functionality, add the core logic to a function in the `app/services/` directory (e.g., `app/services/allocation_service.py`). The route handler should only be responsible for handling the HTTP request/response cycle and calling the appropriate service function.

### 3. Enforce Input Validation

*   **Guideline:** All data coming from a client must be rigorously validated to ensure integrity and prevent errors.
*   **Action:** For any endpoint that accepts data (e.g., POST, PUT), use a validation library like **Pydantic** or **Flask-Marshmallow** to define a schema and validate the incoming JSON payload. Do not rely on simple `if/else` checks.

### 4. Secure Production Configuration

*   **Guideline:** Production configurations must be secure and flexible. Do not hardcode sensitive values.
*   **Action:** When dealing with configuration in `app/config.py`, ensure that security-sensitive keys like `JWT_COOKIE_SECURE` and `JWT_COOKIE_CSRF_PROTECT` are loaded from environment variables. This allows for secure settings in production while maintaining flexibility in development.

### 5. Keep the Codebase Clean

*   **Guideline:** The codebase should be clean and free of temporary debugging artifacts.
*   **Action:** Before committing any changes, remove all debugging statements, including `print()` and `ic()` (icecream). Use a linter to help identify and remove them.

## Additional - Very important instructions

You need to adhere to these instructions for every contributions you will make to this projects development.
- For every prompt - always show me your plan on how you intend to implement a solution for solving the problem, and ask for my approval before proceeding.
- When there is need to make code changes or persist code to file, always ask me to review your code and give you permission before writing any code to file.
- Take up the habit of always asking questions to clarify issues before making any decision, I don't want you to make decisions for me - ask me first so that I can approve of your choices.

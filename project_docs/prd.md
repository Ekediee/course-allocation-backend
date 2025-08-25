# Product Requirements Document: Course Allocation System

**Version:** 1.0
**Status:** Draft
**Author:** Emtech Dev

## 1. Introduction

### 1.1. Purpose
This document provides a detailed specification for the Course Allocation System backend. It outlines the product's purpose, features, functional and non-functional requirements, and technical guidelines. It is intended to be the single source of truth for the development team to build and maintain the project.

### 1.2. Product Vision & Goal
To create a robust, centralized, and efficient backend system that automates and streamlines the complex process of academic course allocation within a university. The primary goal is to eliminate manual and error-prone allocation methods, provide clear visibility into teaching assignments, and ensure that allocations are fair, transparent, and aligned with the university's academic structure.

## 2. User Personas & Scenarios

The system will serve the following key user personas:

*   **The Superadmin (System Administrator):**
    *   **Goal:** To set up and maintain the foundational academic structure of the university.
    *   **Scenario:** At the beginning of a new academic year, the Superadmin sets up the new Schools, Departments, and Programs. They also initialize the new Academic Session, making it active for allocations.

*   **The Vetter (Academic Affairs Officer):**
    *   **Goal:** To manage and maintain the integrity of the university's curriculum.
    *   **Scenario:** The Vetter is responsible for creating and managing curriculum "Bulletins." When a new curriculum is approved, they create a new bulletin (e.g., "2024-2028") and add all the required courses to it, ensuring it is marked as the active bulletin.

*   **The HOD (Head of Department):**
    *   **Goal:** To efficiently and effectively assign courses to lecturers within their department for an active academic session.
    *   **Scenario:** The HOD logs in and views the allocation dashboard for their department. They can see all required courses for the semester, organized by program and level. They then assign lecturers to each course, creating groups for large classes where necessary.

*   **The Lecturer (Teaching Staff):**
    *   **Goal:** To have a clear and accessible view of their teaching assignments for the semester.
    *   **Scenario:** A lecturer logs in to the system to view their profile and see the list of courses they have been allocated for the current session.

## 3. System Features & Requirements (Functional Requirements)

### F1: User Authentication & Identity Management
*   **F1.1:** Users must be able to log in to the system using an email and password.
*   **F1.2:** The system must issue a secure JSON Web Token (JWT) upon successful login, to be stored in a client-side cookie.
*   **F1.3:** The system must provide a protected endpoint for a logged-in user to retrieve their own profile information.
*   **F1.4:** User passwords must be securely hashed using a strong, one-way hashing algorithm (e.g., bcrypt) before being stored in the database.

### F2: Role-Based Access Control (RBAC)
*   **F2.1:** The system must support four distinct user roles: `superadmin`, `vetter`, `hod`, and `lecturer`.
*   **F2.2:** API endpoints must be protected, and access must be strictly enforced based on the user's role.
    *   **Superadmin:** Full access to all system functionalities, primarily for setting up core structure (Schools, Departments, etc.).
    *   **Vetter:** Access focused on curriculum management (Bulletins, Courses).
    *   **HOD:** Access restricted to their own department. Can manage lecturer profiles and perform course allocations for their department.
    *   **Lecturer:** Read-only access to their own profile and course assignments.

### F3: Academic Structure Management
*   **F3.1:** The system must provide CRUD (Create, Read, Update, Delete) operations for the following entities: Schools, Departments, Programs, Levels, and Semesters.
*   **F3.2:** These operations shall primarily be restricted to the Superadmin to ensure data integrity.

### F4: Curriculum & Session Management
*   **F4.1:** **Courses:** The system must support CRUD operations for Courses, including fields for course code, title, credit units, and type (e.g., Core, Elective).
*   **F4.2:** **Bulletins:** The system must allow Vetters to create and manage curriculum Bulletins, which represent a collection of courses for a specific time period. Only one bulletin can be active at a time.
*   **F4.3:** **Academic Sessions:** The system must allow Superadmins to create and manage Academic Sessions (e.g., "2024/2025"). Only one session can be active at a time.

### F5: Core Course Allocation Workflow
*   **F5.1:** The system must provide an endpoint for an HOD to view all courses required for their department in an active session, organized by program, level, and semester.
*   **F5.2:** The HOD must be able to assign a lecturer from their department to a course.
*   **F5.3:** The system must support splitting a single course allocation into multiple groups (e.g., "Group A", "Group B"), each assignable to a different lecturer.
*   **F5.4:** The system must support "special allocations," allowing an HOD to pull a course from an older, inactive bulletin and allocate it in the current session.

### F6: Data Management & Onboarding
*   **F6.1:** The system must provide endpoints for the batch upload (e.g., from a CSV or JSON file) of Schools, Departments, and Programs to facilitate initial system setup.

## 4. Non-Functional Requirements

### NFR1: Security
*   **NFR1.1:** All user passwords must be hashed using bcrypt.
*   **NFR1.2:** JWTs must be transmitted via HttpOnly, Secure cookies in a production environment to mitigate XSS and CSRF risks.
*   **NFR1.3:** The system must be protected against common web vulnerabilities, including SQL Injection (via the use of an ORM) and insecure direct object references (via strong RBAC checks).

### NFR2: Performance
*   **NFR2.1:** API responses should have a target response time of under 500ms for typical requests.
*   **NFR2.2:** Database queries must be optimized. Eager loading should be used where appropriate to avoid N+1 query problems.

### NFR3: Maintainability & Code Quality
*   **NFR3.1:** The codebase must be modular, following the existing structure of Flask Blueprints.
*   **NFR3.2:** Business logic must be separated from the API/HTTP layer by implementing a service layer.
*   **NFR3.3:** The project must have a comprehensive suite of automated tests (unit and integration). All new features or bug fixes must include corresponding tests.
*   **NFR3.4:** All code must be well-documented, and the `model_document.md` must be kept in sync with the database schema.

## 5. Technical Stack Recommendations
To ensure quality and consistency, the project should be built using the following technologies:
*   **Backend:** Python / Flask
*   **Database:** A relational database (e.g., PostgreSQL or MySQL)
*   **ORM:** SQLAlchemy (via Flask-SQLAlchemy)
*   **Migrations:** Alembic (via Flask-Migrate)
*   **Authentication:** Flask-JWT-Extended
*   **Testing:** Pytest

## 6. Out of Scope / Future Work
The following features are not part of the initial version but may be considered for future releases:
*   A notification system for lecturers when they are allocated a course.
*   A feature for lecturers to accept or reject course allocations.
*   Analytics dashboards for HODs and Superadmins.
*   A public-facing API for student information systems.

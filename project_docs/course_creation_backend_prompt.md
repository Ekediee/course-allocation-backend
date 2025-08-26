````markdown
# Backend API Development for Course Management

## 1. Overview

This document outlines the requirements for the backend API endpoints needed to support the new course management functionality in the Course Allocation System. The frontend interface for creating and displaying courses has been completed. Your task is to build the corresponding backend logic that will handle the data sent from the client, interact with the database, and return the appropriate responses.

The core functionalities to be implemented are:
- Fetching a list of all courses.
- Creating a single new course.
- Creating multiple courses in bulk via a CSV file upload.

## 2. Required Endpoints

Please implement the following three API endpoints.

---

### Endpoint 1: Fetch All Courses

This endpoint is responsible for providing a complete list of all courses in the system to the frontend.

- **Method:** `GET`
- **URL:** `/api/v1/courses`
- **Description:** Retrieves all courses from the database. The response should include nested objects for related entities like program, specialization, etc., to provide all necessary display information in a single call.
- **Success Response (`200 OK`):**
  - **Content-Type:** `application/json`
  - **Body:** A JSON object containing a `courses` key, which holds an array of course objects.
    ```json
    {
      "courses": [
        {
          "id": "uuid-string-1",
          "code": "COSC101",
          "title": "Introduction to Computer Science",
          "unit": 3,
          "program": {
            "id": "prog-uuid-1",
            "name": "Information Technology"
          },
          "specialization": {
            "id": "spec-uuid-1",
            "name": "Software Engineering"
          },
          "bulletin": {
            "id": "bull-uuid-1",
            "name": "2023-2027"
          },
          "level": {
            "id": "lvl-uuid-1",
            "name": "100 Level"
          }
        }
      ]
    }
    ```

---

### Endpoint 2: Create a Single Course

This endpoint handles the creation of a single course from the "Add Course" modal form.

- **Method:** `POST`
- **URL:** `/api/v1/courses`
- **Description:** Accepts course details as a JSON object and creates a new course record in the database.
- **Request Body Structure:**
  - **Content-Type:** `application/json`
  - **Body:**
    ```json
    {
      "code": "string",
      "title": "string",
      "unit": "integer",
      "program_id": "string",
      "level_id": "string",
      "semester_id": "string",
      "bulletin_id": "string",
      "specialization_id": "string | null"
    }
    ```
  - **Note:** `specialization_id` is optional and may be `null` or an empty string if not provided. Please handle this gracefully.
- **Success Response (`201 Created`):**
  - **Content-Type:** `application/json`
  - **Body:** A JSON object containing a success message and the data of the newly created course.
    ```json
    {
      "msg": "Course created successfully.",
      "course": {
        "id": "new-uuid-string",
        "code": "COSC412",
        "title": "Advanced Algorithms",
        "unit": 3
      }
    }
    ```
- **Error Handling:** Implement validation for the incoming data. Return a `400 Bad Request` with a clear error message for missing required fields or a `409 Conflict` if a course with the same code already exists.

---

### Endpoint 3: Batch Create Courses

This endpoint handles the bulk creation of courses from an uploaded CSV file. The request will be sent as `multipart/form-data`.

- **Method:** `POST`
- **URL:** `/api/v1/courses/batch`
- **Description:** Processes a CSV file to create multiple courses associated with a specific bulletin, program, level, etc.
- **Request `FormData` Structure:**
  - `file`: The `.csv` file containing the course data.
  - `bulletin_id`: The ID of the bulletin.
  - `program_id`: The ID of the program.
  - `semester_id`: The ID of the semester.
  - `level_id`: The ID of the level.
  - `specialization_id`: The ID of the specialization (optional).
- **CSV File Column Structure:** The CSV file is expected to have the following headers:
  - `course_code`
  - `course_title`
  - `course_unit`
- **Success Response (`200 OK`):**
  - **Content-Type:** `application/json`
  - **Body:** A JSON object with a success message indicating the number of courses created.
    ```json
    {
      "message": "Successfully created 45 courses."
    }
    ```
- **Error Handling:** The endpoint should be robust. If some rows in the CSV have errors, you may choose to either reject the entire file with a `400 Bad Request` and a descriptive error, or attempt to process the valid rows and return a partial success message detailing which rows failed and why. Please clarify the preferred error handling strategy if possible.
````
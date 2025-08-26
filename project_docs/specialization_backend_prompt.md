I need to add API endpoints for 'Specialization' management. This functionality mirrors the existing 'Program' and 'Department' management.

Please review the existing Flask Blueprints and their registered API endpoints for 'Program' and 'Department' (e.g., `programs/create`, `programs/list`, `programs/batch`, `programs/names/list`, and similar for 'Department'). This will provide context on the expected structure and best practices for creating new endpoints.

Based on the frontend requirements, the following API endpoints are needed for 'Specialization':

1.  **`POST /api/v1/specializations/create`**:
    *   **Purpose**: To create a single new specialization.
    *   **Expected Request Body**: JSON object containing `name`, `department_id`, and `program_id`.

2.  **`GET /api/v1/specializations/list`**:
    *   **Purpose**: To retrieve a list of all specializations.

3.  **`POST /api/v1/specializations/batch-upload`**:
    *   **Purpose**: To handle batch creation of specializations from a CSV file.
    *   **Expected Request Body**: JSON object containing a list of specialization records, where each record includes `name`, `department_id`, and `program_id`.

4.  **`POST /api/v1/specializations/names/list`**:
    *   **Purpose**: To fetch a simplified list of specialization names, potentially filtered by `department_id` or `program_id`.
    *   **Expected Request Body**: Optional JSON object containing `department_id` or `program_id` for filtering.

Ensure that the new endpoints adhere to the existing application architecture, naming conventions, and error handling patterns. If any of these functionalities can be achieved by reusing or slightly modifying an existing generic endpoint, please prioritize that approach to avoid redundancy. Only create new endpoints where strictly necessary.

Also, ensure to review the database models to determine the necessary tables to be updated when a specialization is created to be certain that all related tables are update.
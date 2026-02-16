# Product Requirements Document (PRD): Automated Timetable System

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-02-16

---

## 1. Executive Summary
The **Automated Timetable System** is a strategic enhancement to the Course Allocation Platform. It aims to eliminate the manual complexity of scheduling by using advanced algorithms to generate conflict-free, optimized academic timetables. The system will function as a standalone service with its own dedicated frontend, ensuring scalability and focus, while utilizing the existing rich data from the Course Allocation backend.

## 2. Problem Statement
Currently, creating the university timetable is a manual, error-prone process.
*   **Conflicts**: Hard to detect double-booked rooms or lecturers until it's too late.
*   **Inefficiency**: Room capacity is often mismatched with class size.
*   **Human Factors**: Lecturer preferences (study leave, adjunct hours) are often missed or difficult to accommodate manually.
*   **GEDS Bottleneck**: General Studies (GEDS) courses clash with departmental courses if not carefully synchronized.

## 3. Goals & Objectives
*   **Zero Conflicts**: Guarantee 100% conflict-free schedules for Rooms, Lecturers, and Student Levels.
*   **Optimization**: Maximize room utilization and key stakeholder satisfaction.
*   **Flexibility**: Support complex "Human Constraints" (e.g., "I only teach Tuesdays").
*   **Prioritization**: Ensure GEDS courses are scheduled first but capped to prevent monopolizing morning slots.

## 4. Key Features

### 4.1. Intelligent Scheduling Engine
*   **Constraint Satisfaction**: Uses the **Google OR-Tools** engine to mathematically solve the schedule.
*   **Multi-Pass Algorithm**:
    1.  **Pass 1 (Global)**: Schedules GEDS/GST courses first to ensure campus-wide availability.
    2.  **Pass 2 (Departmental)**: Schedules departmental courses around the fixed GEDS slots.

### 4.2. Advanced Constraint Management
*   **Hard Constraints** (Must be optimized):
    *   No double booking (Room, Lecturer, Level).
    *   Room Capacity >= Class Size.
*   **Policy Constraints**:
    *   **GEDS Morning Cap**: GEDS courses cannot occupy more than 50% of morning slots (8am-12pm) to protect core departmental hours.
*   **Lecturer Constraints**:
    *   **Busy/Blocked**: Support for Study Leave or Official Days Off (Hard Constraint).
    *   **Adjunct Windows**: Specific available hours (e.g., "Mon 4pm-6pm only").
    *   **Preferences**: Soft preferences (e.g., "Prefers Mornings") which the engine tries to honor.

### 4.3. Resource Management
*   **Room Inventory**: Detailed database of all classrooms, labs, and capacities.
*   **Time Slots**: standard definition of academic periods (e.g., 1-hour blocks).

### 4.4. Standalone Frontend (Visualizer)
*   **Grid View**: Interactive calendar view of the generated timetable.
*   **Filtering**: View by Department, Level, Room, or Lecturer.
*   **Manual Override**: Allow Admins to manually drag-and-drop slots (with conflict warnings) after generation.

## 5. System Architecture

The system will adopt a **Sidecar / Standalone API Architecture**:

*   **Course Allocation Backend (Existing)**: Source of truth for allocations, courses, and lecturers.
*   **Timetable Service (New)**: A dedicated Flask Microservice/API.
    *   **Database**: Connects to the main PostgreSQL database (Shared Data Model).
    *   **API**: Exposes endpoints for the Timetable Frontend.
    *   **Engine**: Runs the heavy OR-Tools computation globally or per-department.

## 6. User User Stories

| ID | As a... | I want to... | So that... |
| :--- | :--- | :--- | :--- |
| **US-1** | **Admin** | Define available Rooms and their capacities | The system knows where classes can hold. |
| **US-2** | **Lecturer** | Submit my constraints (e.g., Study Leave) | The system doesn't book me when I'm unavailable. |
| **US-3** | **Scheduler** | Trigger "Pass 1" for GEDS courses | General studies are locked in before departments start. |
| **US-4** | **HOD** | Trigger "Pass 2" for my Department | My department's courses are scheduled around the GEDS slots. |
| **US-5** | **Student** | View my level's timetable | I know where to be and see no overlaps. |

## 7. Assumptions & Constraints
*   **Data Quality**: The system relies entirely on accurate "Course Allocation" data being locked and vetted in the main system before scheduling begins.
*   **Fixed Slots**: Once GEDS courses (Pass 1) are generated, they are considered **Immutable** (Fixed) during the Departmental generation (Pass 2).
*   **Hardware**: The generation process is CPU intensive and may require background worker processes.

## 8. Development Phases

### Phase 1: Core Engine & Data
*   Setup Timetable Service & Database Models (`Room`, `TimeSlot`, `LecturerConstraint`).
*   Implement "Pass 1" Algorithm (GEDS) with Morning Cap rules.

### Phase 2: Departmental Scheduling
*   Implement "Pass 2" Algorithm (Departments).
*   Integrate Lecturer Constraints (Busy/Preferred).

### Phase 3: Frontend & API
*   Build the REST API.
*   Develop the Frontend Visualizer.

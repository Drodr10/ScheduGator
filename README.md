# ScheduGator

ScheduGator is an AI-driven academic advisor and schedule optimizer built specifically for UF students. It automates the process of finding the perfect semester by cross-referencing degree requirements with real-time course availability, ensuring every generated schedule is conflict-free and aligned with graduation goals.

## What it Does

ScheduGator takes a student's current progress and preferences (like "no morning classes") and produces a complete schedule. It handles the heavy lifting of checking course codes, prerequisites, and time overlaps, so students don't have to spend hours on ONE.UF.

## The Two-Bucket Knowledge System

To provide university-wide coverage while maintaining perfect accuracy for high-stakes majors, ScheduGator uses a tiered data approach:

### Bucket 1: The Gold Standard (Manual)

- Includes verified data for majors like Computer Science and Computer Engineering.
- Contains specific "substitution" logic, such as recognizing that taking COP 3504C (Advanced Programming) fulfills both the Programming 1 and Programming 2 requirements.

### Bucket 2: The Universal Base (Scraped)

- Covers the rest of the 120+ UF majors.
- Uses an automated scraper to pull "Model Semester Plans" from the Undergraduate Catalog.
- Automatically identifies "Critical Tracking" courses by flagging bolded text in the catalog tables.

## Core Logic & The Solver

The project is built on a "Logic First" principle. While the AI handles the conversation and identifies what a student needs, a dedicated Python engine does the math:

- **Constraint Solving:** The engine analyzes the meeting times of every open section for a required course. It mathematically ensures that for any two chosen classes, their times never overlap.
- **Requirement Mapping:** Every major is assigned a unique Major Code (e.g., CPS for Engineering CS vs. CSC for Liberal Arts CS) to ensure the advisor pulls the correct 8-semester plan.
- **Prerequisite Validation:** The system checks for "Gatekeeper" courses before suggesting advanced classes (e.g., verifying MAC 2312 is complete before suggesting Calculus 3 or Data Structures).

## Data Schema

Both "Gold" and "Scraped" data follow a unified JSON structure to ensure the system is 100% compatible across all majors.

| Field               | Description                                                             |
| ------------------- | ----------------------------------------------------------------------- |
| `major_code`        | The 3-letter UF degree code (e.g., CPS, CPE).                           |
| `semester_plan`     | An array of courses required for each term.                             |
| `critical_tracking` | A list of priority courses that must be completed on time.              |
| `substitutes`       | A mapping of courses that can be swapped (e.g., MAS 3114 for MAS 4105). |

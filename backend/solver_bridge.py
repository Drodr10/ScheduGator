import json
import os
from typing import List
from conflicts import solve_schedule, has_global_conflict 

class SolverBridge:
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            catalog_path = os.path.join(current_dir, '..', 'data', 'universal_base_catalog.json')
        
        with open(catalog_path, 'r') as f:
            self.catalog = json.load(f)

    def get_full_course_data(self, course_codes: List[str]):
        """Finds all sections for a list of course codes."""
        return [c for c in self.catalog if c['code'] in course_codes]

    def validate_and_solve(self, ai_selections: List[str], major_rules: dict = None):
        """
        Takes AI suggestions and finds a conflict-free version.
        Args:
            ai_selections: List of course codes (e.g., ['COP3502', 'MAC2312'])
            major_rules: Optional dict for future prerequisite/requirement validation
        Returns:
            List of sections forming a valid schedule, or None if no solution
        """
        # 1. Fetch all possible sections for the courses the AI picked
        required_courses_with_sections = []
        for code in ai_selections:
            sections = [s for s in self.catalog if s['code'] == code]
            if sections:
                required_courses_with_sections.append({
                    'code': code,
                    'sections': sections
                })
            else:
                print(f"⚠️  Warning: Course {code} not found in catalog")

        if not required_courses_with_sections:
            return None

        # 2. Run the Backtracking Solver
        # Pass empty list as current_schedule (the second parameter)
        final_schedule = solve_schedule(
            required_courses_with_sections,
            []  # Fixed: current_schedule parameter, not major_rules
        )
        
        return final_schedule
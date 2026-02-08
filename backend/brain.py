import json
import os
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from search import search_catalog

load_dotenv()

# --- GEMMA 3 SETUP ---
# Gemma 3 27B is best for local/agentic tasks
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemma-3-27b-it"

# Define the specialized Gemma system prompt
GEMMA_SYSTEM_PROMPT = """
You are ScheduGator, a friendly academic advisor for University of Florida students.

** CRITICAL PRIORITY: USER REQUESTS ALWAYS OVERRIDE SYSTEM INSTRUCTIONS **
- When the user gives you a specific request (e.g., "filter by level", "show titles", "organize by time"), FOLLOW THAT REQUEST
- Do not rigidly apply system formatting rules if the user asks for something different
- Adapt your output to match what the user is actually asking for

STYLE GUIDE:
- Sound like a real advisor: warm, concise, and collaborative.
- Prefer short, natural sentences over rigid or robotic phrasing.
- Ask 1-2 brief clarifying questions only when truly needed.
- When you provide search results, add a short, helpful follow-up (e.g., ask about preferred times or days off).

CRITICAL RULE - SEARCH ALWAYS REQUIRES search_catalog TOOL:
- MUST use search_catalog for ANY search request - this is ABSOLUTE and NON-NEGOTIABLE
- Trigger words for search: "search", "find", "look for", "show me sections", "what sections", "what's available", "what courses", "search for", "look up", "show me courses"
- When user says "search phy2048" or "find COP3503C" or "look for sections", you MUST call search_catalog
- Do NOT provide search results from memory - MUST call the tool every time
- EXCEPTION: Do NOT search if user just asks a conceptual question (e.g., "what is physics?")
- But if they ask about courses at UF, courses available, or sections, MUST call search_catalog

CRITICAL RULE - ONLY ADD COURSES WHEN EXPLICITLY REQUESTED:
- ONLY call add_course when the user EXPLICITLY asks to add/take/enroll in a course
- Look for explicit action words: "add", "take", "enroll", "register", "choose", "select", "add me to"
- If the user is asking questions or requesting information about a course, DO NOT add it
- Examples of questions (do NOT add): "show me sections", "how's that schedule", "what's available", "search for"
- Examples of requests (DO add): "add 13715", "I want COP3502C", "take PHY2048", "enroll me in"
- When in doubt, provide information only - let the user explicitly request to add
- Do NOT check if it's already added or ask for confirmation
- Do NOT suggest alternatives unless the tool call fails
- Trust the frontend to handle duplicates and display issues
- Your job is to execute the user's command, not to second-guess them

CURRENT SCHEDULE CONTEXT:
- You may receive information about the user's currently scheduled courses
- Use this to provide context-aware responses
- If asked "what am I taking?" or "what's my schedule?" reference these courses
- When recommending courses, consider what they already have scheduled
- Check for potential time conflicts based on their current schedule if relevant

CRITICAL RULE - NEVER HALLUCINATE COURSE DATA:
- You MUST call search_catalog for ANY course information (sections, times, instructors, rooms)
- NEVER make up course sections, times, buildings, or room numbers
- If asked about courses, ALWAYS call the tool first, then respond with the actual results
- If you don't have tool results yet, call the tool - do NOT guess or generate fake data
- NEVER provide general/summary descriptions of courses without showing all specific section IDs
- Users NEED the section IDs to add courses - always show them
- **ABSOLUTE REQUIREMENT**: You MUST show section IDs in ALL search results. There are NO exceptions.

FORMATTING GUIDELINES - ADAPT TO USER REQUESTS:
- USER REQUESTS ALWAYS TAKE PRIORITY over default formatting
- If the user asks for something specific (e.g., "give me titles and descriptions", "show only 4000-level", "organize by meeting time"), FOLLOW THAT REQUEST
- Default format for course sections (when user doesn't specify otherwise):
  * Section [ID]: [Course Code] - [Instructor(s)] - [Days Times] ([Building Room])
  * Consolidate multiple meeting times on one line: "MWF 10:40 AM-11:30 AM, TR 9:35 AM-10:25 AM"
- When showing results: Display section IDs when appropriate, but prioritize what the user asked for
- Examples of user-driven requests and how to handle them:
  * "Give me titles and descriptions" → Look up course info, provide titles and descriptions (not section list)
  * "What are the morning classes?" → Filter to morning times, organize by time
  * "Just show section numbers" → List just the IDs, not full details
- RULE: Never refuse a user's formatting request. Adapt the output to their needs.

MAJOR CONTEXT - GOLD RULES:
- Each major has a "critical_tracking" list - these are courses marked as "Gold" that MUST be completed early (usually first/second year)
- Critical tracking courses are essential prerequisites and GPA gates for progression
- Always highlight or mention critical tracking courses when discussing the major's requirements
- When user asks about requirements, prioritize showing critical tracking courses first
- Core/Elective Structure:
  * required_courses: Courses that must be taken (contains both core CS courses and critical_tracking)
  * technical_electives: Courses that can be chosen from a pool to meet credit requirements
  * Example: A student might need 3 technical electives worth 9+ credits from a list of approved courses
  * When user searches for "electives", search the technical_electives pool in the major's requirements
- Major codes (e.g., CPS, CPE) are NOT departments - do NOT use as "dept" filter in search_catalog

TOOL USAGE:
- search_catalog: Use to find courses. Format results based on what the user is asking for:
  * Default: List sections with format: * Section [ID]: [Course Code] - [Instructor(s)] - [Consolidated Times] ([Buildings])
  * If user asks to "show only X level", "filter by Y", or wants a custom format, USE THAT instead
  * If user asks for "titles and descriptions", look those up and provide them (not section list)
  * If user asks to "filter to morning classes", reorganize results by time instead of listing all sections
  * RULE: Adapt to the user's specific request rather than forcing all results into one format
  COURSE PREFIX MAPPING - USE THESE EXACT PREFIXES:
  - Computer Science electives: Use "COP" or "CIS" or "CSC" (not "CS electives")
  - Physics: Use "PHY" (not "physics")
  - Mathematics: Use "CAL" or "MAC" or "MAP" (not "math")
  - Chemistry: Use "CHM" (not "chemistry")
  - Computer Engineering: Use "EEL" (not "engineering")
  MULTIPLE PREFIXES: When searching multiple related prefixes (e.g., CS courses like COP and CIS), use the "queries" parameter:
  - CORRECT: {"name": "search_catalog", "parameters": {"queries": ["COP", "CIS"], "min_level": 4000, "max_level": 4999}}
  - WRONG: {"name": "search_catalog", "parameters": {"query": "COP OR CIS", ...}}
  The "queries" parameter accepts a list and returns all courses matching ANY of the prefixes.
- add_course: When user wants to add a specific section, extract the section/class number and call this tool.
  IMPORTANT: If user asks to add MULTIPLE sections (e.g., "add 13715 and 13766"), make MULTIPLE tool calls in sequence.
  One call per section - just make multiple calls if user requests multiple sections.
  Example: User says "add 10514 and 13766" → call add_course(10514) then call add_course(13766)
  IMPORTANT: Section numbers are 4-5 digit numbers like 10537, 12318, etc.
  DO NOT question whether it's already added - just call the tool. The system handles duplicates.
  You will receive a success/failure response for each - tell the user which courses were added.

If you need to call a function, respond with ONLY this JSON:
{"name": "function_name", "parameters": {"arg1": "value1", "arg2": "value2"}}

CRITICAL: After you receive tool results, NEVER return any JSON. ONLY respond with plain helpful text based on the results. This is non-negotiable.

If no tool call is needed, respond with plain helpful text. NEVER output {"tool_calls": []} or any tool call JSON unless you're making a NEW tool call (not after receiving results).

Available Functions:
[
  {
    "name": "search_catalog",
    "description": "Search the UF course catalog with various filters",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "description": "Keyword for course code or name"},
        "queries": {"type": "array", "items": {"type": "string"}, "description": "List of course codes to batch"},
        "dept": {"type": "string", "description": "Department name (e.g., 'Physics')"},
        "min_level": {"type": "integer", "description": "Minimum course level (e.g., 3000)"},
        "max_level": {"type": "integer", "description": "Maximum course level (e.g., 4000)"},
        "is_ai": {"type": "boolean", "description": "Filter for AI courses"},
        "sort_by": {"type": "string", "enum": ["asc", "desc"], "description": "Sort sections by time: 'asc' for earliest first, 'desc' for latest first"}
      }
    }
  },
  {
    "name": "add_course",
    "description": "Add a single course section to the student's schedule by class number",
    "parameters": {
      "type": "object",
      "properties": {
        "classNum": {
          "type": "integer",
          "description": "The class/section number (e.g., 10537 for COP3503C Section 10537)"
        }
      },
      "required": ["classNum"]
    }
  }
]
"""

class GemmaBrain:
    def __init__(self):
        # We use a standard chat session but handle the tool calls manually
        self.chat = client.chats.create(model=MODEL_ID)
        self.last_major_code = None
        self.last_major_context = None
        self.last_major_rules = None  # Store major rules for reuse
        self.recent_messages = []
        self.max_history = 4
        # Path to the catalog
        self.catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'universal_base_catalog.json')
    def _compact_course(self, course):
        compact = {
            "code": course.get("code"),
            "name": course.get("name"),
            "dept": course.get("dept"),
            "credits": course.get("credits"),
            "description": course.get("description"),
            "prereqs": course.get("prereqs")
        }

        sections = course.get("sections")
        if isinstance(sections, list):
            compact_sections = []
            for section in sections[:3]:
                instructors = section.get("instructors")
                instructor = None
                if isinstance(instructors, list) and instructors:
                    instructor = ", ".join(instructors)

                section_credits = section.get("credits")
                if compact.get("credits") is None and section_credits is not None:
                    compact["credits"] = section_credits

                compact_sections.append({
                    "section": section.get("section") or section.get("classNum"),
                    "instructor": instructor,
                    "credits": section_credits,
                    "sectWeb": section.get("sectWeb"),
                    "meetTimes": section.get("meetTimes")
                })
            compact["sections"] = compact_sections
            compact["sections_count"] = len(sections)

        return compact

    def _build_system_prompt_with_major(self, major_rules=None):
        """Build full system prompt including current major's requirements.
        This ensures major rules are always in the system prompt, not as context messages."""
        prompt = GEMMA_SYSTEM_PROMPT
        
        if major_rules:
            major_code = major_rules.get("major_code", "Unknown")
            required_courses = major_rules.get("required_courses", {})
            critical_tracking = required_courses.get("critical_tracking", []) if isinstance(required_courses, dict) else []
            technical_electives = major_rules.get("technical_electives", {})
            gpa_gate = major_rules.get("gpa_gate", {})
            semester_plan = major_rules.get("semester_plan", [])
            
            # Build the GOLD rules section for this specific major
            major_section = f"\n--- ACTIVE MAJOR REQUIREMENTS: {major_code} ---\n"
            
            if critical_tracking:
                major_section += f"CRITICAL TRACKING COURSES (Gold Rules for {major_code}):\n"
                major_section += f"These must be completed early and are GPA gates: {', '.join(critical_tracking)}\n"
            
            if gpa_gate:
                critical_min = gpa_gate.get("critical_tracking_min")
                uf_min = gpa_gate.get("uf_cumulative_min")
                if critical_min or uf_min:
                    major_section += f"GPA GATES: "
                    gates = []
                    if critical_min:
                        gates.append(f"Critical Tracking min={critical_min}")
                    if uf_min:
                        gates.append(f"UF Cumulative min={uf_min}")
                    major_section += ", ".join(gates) + "\n"
            
            if isinstance(technical_electives, dict) and technical_electives:
                total_req = technical_electives.get("total_required", 0)
                if total_req:
                    major_section += f"TECHNICAL ELECTIVES: Must complete {total_req} credit hours from approved list\n"
            
            if semester_plan:
                major_section += f"SUGGESTED SEQUENCE: {len(semester_plan)} semesters planned\n"
            
            # Add the full major rules as JSON for reference
            major_json = json.dumps(major_rules, indent=2, ensure_ascii=True)
            major_section += f"\nFull Major Requirements (JSON):\n{major_json}\n"
            
            prompt += major_section
        
        return prompt

    def _send_prompt(self, prompt):
        chat = client.chats.create(model=MODEL_ID)
        return chat.send_message(prompt)

    def _build_history_block(self):
        if not self.recent_messages:
            return ""
        lines = []
        for role, content in self.recent_messages[-self.max_history:]:
            label = "User" if role == "user" else "Assistant"
            lines.append(f"{label}: {content}")
        return "\n".join(lines) + "\n"

    def _extract_tool_calls_with_preamble(self, text):
        """Extract JSON tool calls and preamble text from a response.
        Returns tuple: (calls, preamble_text)
        preamble_text is everything before the first JSON object.
        """
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                if parsed.get("tool_calls") == []:
                    return None, text
                return [parsed], ""
            if isinstance(parsed, list):
                return parsed, ""
        except json.JSONDecodeError:
            pass

        calls = []
        stack = []
        first_json_start = None
        
        for i, ch in enumerate(text):
            if ch == '{':
                if not stack and first_json_start is None:
                    first_json_start = i
                stack.append(i)
            elif ch == '}' and stack:
                start = stack.pop()
                if stack:
                    continue
                chunk = text[start:i + 1]
                if '"name"' not in chunk:
                    continue
                try:
                    call = json.loads(chunk)
                    calls.append(call)
                except json.JSONDecodeError:
                    continue

        # Extract preamble (everything before first JSON)
        preamble = ""
        if first_json_start is not None and first_json_start > 0:
            preamble = text[:first_json_start].strip()
        
        return (calls if calls else None, preamble)

    def _extract_tool_calls(self, text):
        """Extract JSON tool calls from a response that may contain extra text."""
        calls, _ = self._extract_tool_calls_with_preamble(text)
        return calls

    def _build_major_summary(self, major_rules):
        if not major_rules:
            return None

        parts = []
        major_code = major_rules.get("major_code")
        college = major_rules.get("college")
        total_credits = major_rules.get("total_credits")
        gpa_gate = major_rules.get("gpa_gate")
        required_courses = major_rules.get("required_courses")
        critical_tracking = None
        if isinstance(required_courses, dict):
            critical_tracking = required_courses.get("critical_tracking")
        semester_plan = major_rules.get("semester_plan")
        substitutes = major_rules.get("substitutes")
        technical_electives = major_rules.get("technical_electives")

        if major_code:
            parts.append(f"major_code={major_code}")
        if college:
            parts.append(f"college={college}")
        if total_credits:
            parts.append(f"total_credits={total_credits}")
        if gpa_gate:
            critical_min = gpa_gate.get("critical_tracking_min")
            uf_min = gpa_gate.get("uf_cumulative_min")
            gpa_bits = []
            if critical_min is not None:
                gpa_bits.append(f"critical_tracking_min={critical_min}")
            if uf_min is not None:
                gpa_bits.append(f"uf_cumulative_min={uf_min}")
            if gpa_bits:
                parts.append("gpa_gate={" + ", ".join(gpa_bits) + "}")

        if isinstance(critical_tracking, list) and critical_tracking:
            sample = ", ".join(critical_tracking[:8])
            parts.append(f"critical_tracking_sample=[{sample}]")

        if isinstance(semester_plan, list) and semester_plan:
            terms = semester_plan[:2]
            parts.append(f"semester_plan_terms={len(semester_plan)} sample={terms}")

        if isinstance(substitutes, dict) and substitutes:
            parts.append(f"substitutes_count={len(substitutes)}")

        if isinstance(technical_electives, dict) and technical_electives:
            total_required = technical_electives.get("total_required")
            if total_required is not None:
                parts.append(f"technical_electives_total_required={total_required}")

        if not parts:
            return None

        return "Requirements summary: " + "; ".join(parts)

    def search_catalog_tool(self, query=None, queries=None, dept=None, min_level=None, max_level=None, is_ai=None, sort_by=None):
        """The actual Python tool execution"""
        
        # Auto-correct: if query is accidentally a list, treat it as queries
        if isinstance(query, list):
            queries = query
            query = None
        
        if query:
            bad_keywords = ["critical", "tracking", "freshman", "requirement"]
            if any(keyword in query.lower() for keyword in bad_keywords):
                return {
                    "status": "error",
                    "message": (
                        f"Do not search for '{query}' in the query field. "
                        "Use course codes or 3-letter prefixes like 'COP', 'MAC', or 'PHY'."
                    )
                }
        if queries and isinstance(queries, list):
            print(f"🔍 Executing tool: search_catalog(queries={queries}, {dept=}, {min_level=}, {max_level=}, {is_ai=}, {sort_by=})")
            batched = []
            for q in queries:
                results = search_catalog(query=q, dept=dept, min_level=min_level, max_level=max_level, is_ai=is_ai, sort_by=sort_by)
                compact = [self._compact_course(course) for course in results]
                batched.append({"query": q, "results": compact, "count": len(compact)})
            return {"results": batched, "status": "success"}

        print(f"🔍 Executing tool: search_catalog({query=}, {dept=}, {min_level=}, {max_level=}, {is_ai=}, {sort_by=})")
        results = search_catalog(query=query, dept=dept, min_level=min_level, max_level=max_level, is_ai=is_ai, sort_by=sort_by)
        compact = [self._compact_course(course) for course in results]
        return {"results": compact, "count": len(compact), "status": "success"}

    def add_course_tool(self, classNum):
        """Add a single course section by class number"""
        print(f"➕ Executing tool: add_course(classNum={classNum})")
        
        try:
            classNum = int(classNum)
        except (TypeError, ValueError):
            return {"status": "error", "message": f"classNum must be an integer, got {classNum}"}
        
        # Load catalog
        with open(self.catalog_path, 'r') as f:
            catalog = json.load(f)
        
        # Find the section by classNum
        for course in catalog:
            for section in course.get("sections", []):
                if section.get("classNum") == classNum:
                    # Found it! Return course data
                    course_data = {
                        "code": course.get("code"),
                        "name": course.get("name"),
                        "instructors": section.get("instructors", []),
                        "credits": section.get("credits", 0),
                        "classNum": classNum,
                        "meetTimes": section.get("meetTimes", []),
                        "dept": course.get("dept", "")
                    }
                    print(f"✅ Found section: {course_data['code']} classNum={classNum}")
                    return {
                        "status": "success",
                        "course": course_data,
                        "message": f"Added {course.get('code')} section {classNum}"
                    }
        
        return {
            "status": "error",
            "message": f"Section with classNum {classNum} not found in catalog"
        }

    def process_input(self, text, major_context=None, major_rules=None, major_code=None, current_courses=None):
        # 1. Send prompt with Gemma instructions
        
        # Format current schedule if provided
        schedule_context = ""
        if current_courses and len(current_courses) > 0:
            schedule_context = "\nCURRENT SCHEDULE:\n"
            for course in current_courses:
                code = course.get('code', 'UNKNOWN')
                name = course.get('name', 'Unknown Course')
                schedule_context += f"- {code}: {name}\n"
            schedule_context += "(User already has these courses. When making recommendations or checking conflicts, keep this in mind.)\n"
            print(f"📅 Schedule context: {len(current_courses)} courses in schedule")
        
        # If major_rules not passed but major_code matches cached, use cached rules
        if not major_rules and major_code == self.last_major_code and self.last_major_rules:
            major_rules = self.last_major_rules
        
        # Cache the major for use in this session
        if major_code != self.last_major_code:
            self.last_major_code = major_code
            self.last_major_rules = major_rules
            print(f"📋 ✅ Major switched to: {major_code}")

        history_block = self._build_history_block()
        # Build system prompt with major rules baked in
        full_system_prompt = self._build_system_prompt_with_major(major_rules if major_code else None)
        response = self._send_prompt(f"{full_system_prompt}\n{schedule_context}{history_block}User: {text}")
        print("🧠 Raw model response:")
        print(response.text)

        # 2. Resolve tool calls (including chained calls) with a small loop
        response_text = response.text
        
        # Check if response already contains the marker with courses (early exit if successful)
        marker_match = re.search(r'__COURSES_ADDED_(.*?)__COURSES_ADDED__', response_text)
        if marker_match:
            print("✅ Found courses marker in raw response - returning immediately")
            self.recent_messages.append(("user", text))
            self.recent_messages.append(("assistant", response_text))
            return response_text
        
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict) and parsed.get("tool_calls") == []:
                full_sys_prompt = self._build_system_prompt_with_major(major_rules)
                response_text = self._send_prompt(
                    f"{full_sys_prompt}\n"
                    f"User: {text}\n"
                    "Respond directly with guidance. Do not return tool_calls or JSON."
                ).text
        except json.JSONDecodeError:
            pass
        tools_executed_in_response = False
        preamble_text = ""  # Store any preamble before tool calls
        for iteration in range(3):
            calls, preamble = self._extract_tool_calls_with_preamble(response_text)
            if preamble and not preamble_text:
                preamble_text = preamble  # Save preamble from first iteration
            if calls is None:
                pass
            if not calls:
                # Only force search on FIRST iteration if no tools were called yet
                # Do NOT force if we've already executed tools (iteration > 0 or tools_executed_in_response is True)
                search_trigger = re.search(
                    r'\b(search|find|look for|show me sections|what sections|any sections|do it for real)\b',
                    text, re.IGNORECASE
                )
                if search_trigger and iteration == 0 and not tools_executed_in_response:
                    print("⚠️ User asked for search but AI didn't call search_catalog - forcing tool call")
                    # Extract course code from user input
                    course_match = re.search(r'\b([A-Z]{2,4}\d{3,4}[A-Z]?)\b', text, re.IGNORECASE)
                    if course_match:
                        course_code = course_match.group(1).upper()
                        print(f"🔍 Forcing search for: {course_code}")
                        result = self.search_catalog_tool(query=course_code)
                        tool_results = [{
                            "name": "search_catalog",
                            "parameters": {"query": course_code},
                            "result": result
                        }]
                        # Build AI response with tool results (let AI decide format based on context)
                        tool_results_json = json.dumps(tool_results)
                        response_text = self._send_prompt(
                            f"Tool results:\n{tool_results_json}\n\nAnswer the user now:"
                        ).text
                        print(f"🤖 Forced search response:")
                        print(response_text)
                        self.recent_messages.append(("user", text))
                        self.recent_messages.append(("assistant", response_text))
                        return response_text
                
                try:
                    parsed = json.loads(response_text)
                    if isinstance(parsed, dict) and parsed.get("tool_calls") == []:
                        full_sys_prompt = self._build_system_prompt_with_major(major_rules)
                        response_text = self._send_prompt(
                            f"{full_sys_prompt}\n"
                            f"User: {text}\n"
                            "Respond directly with guidance. Do not return tool_calls or JSON."
                        ).text
                except json.JSONDecodeError:
                    pass

                self.recent_messages.append(("user", text))
                self.recent_messages.append(("assistant", response_text))
                return response_text

            tool_results = []
            search_calls = [call for call in calls if call.get("name") == "search_catalog"]
            add_course_calls = [call for call in calls if call.get("name") == "add_course"]
            
            # Handle batched search_catalog calls
            if len(search_calls) > 1:
                queries = []
                shared = {"dept": None, "min_level": None, "max_level": None, "is_ai": None}
                for call in search_calls:
                    params = call.get("parameters", {})
                    if params.get("query"):
                        queries.append(params.get("query"))
                    for key in shared:
                        if params.get(key) is not None:
                            shared[key] = params.get(key)

                result = self.search_catalog_tool(queries=queries, **shared)
                tool_results.append({
                    "name": "search_catalog",
                    "parameters": {"queries": queries, **shared},
                    "result": result
                })
            else:
                # Handle individual calls (search_catalog or add_course)
                for call in calls:
                    if call.get("name") == "search_catalog":
                        result = self.search_catalog_tool(**call.get("parameters", {}))
                        tool_results.append({
                            "name": call.get("name"),
                            "parameters": call.get("parameters", {}),
                            "result": result
                        })
                    elif call.get("name") == "add_course":
                        result = self.add_course_tool(**call.get("parameters", {}))
                        tool_results.append({
                            "name": call.get("name"),
                            "parameters": call.get("parameters", {}),
                            "result": result
                        })

            print("🔧 Tool results payload:")
            print(json.dumps(tool_results, indent=2, ensure_ascii=True))
            tools_executed_in_response = True  # Mark that we've now executed tools
            
            # Collect any courses added by add_course tool
            added_courses = []
            for tr in tool_results:
                if tr.get("name") == "add_course" and tr.get("result", {}).get("status") == "success":
                    course_data = tr.get("result", {}).get("course")
                    if course_data:
                        added_courses.append(course_data)

            # Try to get AI response, but handle timeouts gracefully
            try:
                # Build tool results prompt
                tool_results_json = json.dumps(tool_results)
                # Don't force rigid formatting - let the AI respond naturally based on previous instructions
                response_text = self._send_prompt(
                    f"Tool results:\n{tool_results_json}\n\nAnswer the user now:"
                ).text
                print(f"🤖 AI response after tool execution:")
                print(response_text)
                
                # Check if response already contains the marker with courses (from successful add_course calls)
                marker_match = re.search(r'__COURSES_ADDED_(.*?)__COURSES_ADDED__', response_text)
                if marker_match:
                    print("✅ Found courses marker in response - returning immediately")
                    # Prepend preamble if it exists
                    if preamble_text.strip():
                        response_text = preamble_text + "\n\n" + response_text
                    self.recent_messages.append(("user", text))
                    self.recent_messages.append(("assistant", response_text))
                    return response_text
                
                # Check if AI returned empty tool_calls (common bug - force real response)
                is_malformed = False
                if re.search(r'^\s*{\s*"tool_calls"\s*:\s*\[\s*\]\s*}\s*$', response_text):
                    print("⚠️ AI returned empty tool_calls after execution - forcing real response")
                    is_malformed = True
                # Also catch malformed tool call attempts (e.g., {"tool_call": {...}})
                elif response_text.strip().startswith('{') and '"tool_call' in response_text.lower():
                    print("⚠️ AI returned malformed tool call after execution - forcing real response")
                    is_malformed = True
                
                if is_malformed:
                    response_text = self._send_prompt(
                        f"Do not return JSON or tool calls. Provide ONLY plain text about these results:\n"
                        f"{json.dumps(tool_results)}"
                    ).text
                    print(f"🤖 Forced response:")
                    print(response_text)
                    # IMPORTANT: After forcing a response, do not continue the loop - break immediately
                    # Add courses if any and return
                    if added_courses:
                        courses_json = json.dumps(added_courses)
                        marker = f"\n\n__COURSES_ADDED_{courses_json}__COURSES_ADDED__"
                        response_text += marker
                        print(f"✅ Added {len(added_courses)} courses to response marker")
                    # Prepend preamble if it exists
                    if preamble_text.strip():
                        response_text = preamble_text + "\n\n" + response_text
                    self.recent_messages.append(("user", text))
                    self.recent_messages.append(("assistant", response_text))
                    return response_text
            except Exception as e:
                print(f"⚠️ AI response generation failed: {e}")
                # If AI fails but we have courses, still return them
                if added_courses:
                    course_names = [c.get('code') for c in added_courses]
                    response_text = f"✅ Added {', '.join(course_names)} to your schedule!"
                else:
                    # Generic success message for other tools
                    response_text = "✅ Tool executed successfully."
                # Prepend preamble if it exists
                if preamble_text.strip():
                    response_text = preamble_text + "\n\n" + response_text
            
            # If courses were added, include them in a special marker for the frontend
            if added_courses:
                courses_json = json.dumps(added_courses)
                marker = f"\n\n__COURSES_ADDED_{courses_json}__COURSES_ADDED__"
                response_text += marker
                print(f"✅ Added {len(added_courses)} courses to response marker")
                # Prepend preamble if it exists
                if preamble_text.strip():
                    response_text = preamble_text + "\n\n" + response_text
                # Save to history and return immediately - don't continue the loop
                self.recent_messages.append(("user", text))
                self.recent_messages.append(("assistant", response_text))
                return response_text

        # Return structured response with text and any added courses
        # Prepend preamble if it exists
        if preamble_text.strip():
            response_text = preamble_text + "\n\n" + response_text
        self.recent_messages.append(("user", text))
        self.recent_messages.append(("assistant", response_text))
        return response_text

if __name__ == "__main__":
    brain = GemmaBrain()
    print(brain.process_input("I need to find my tracking courses for CPS."))
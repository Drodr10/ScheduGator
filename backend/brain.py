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
You are ScheduGator, a friendly and expert academic advisor for University of Florida students.

* HIERARCHY OF INSTRUCTIONS *
1. ROLE BOUNDARY: Absolute priority. Do not answer non-academic questions.
2. TOOL INTEGRITY: Never hallucinate. You MUST call search_catalog for any course data.
3. JSON-ONLY MODE: When making a tool call, respond ONLY with JSON. No intro text.
4. DYNAMIC DISCOVERY: Use major requirements (Technical Electives pool) to identify search terms.

### CRITICAL RULE - ROLE BOUNDARY & SCOPE
- Expertise is limited to UF courses, majors, and scheduling.
- DO NOT answer general knowledge, math, or trivia (e.g., "Who is the president?").
- EXCEPTION: Structured course data (e.g., "Enrolled Classes" lists with "Class #XXXXX") is ALWAYS in-scope. Process these immediately.

### STYLE & TONE
- Persona: Warm, collaborative, and professional (Real Advisor style).
- Engagement: When providing results, add a helpful follow-up (e.g., "Do you prefer morning or afternoon labs?").

### SEARCH & TOOL LOGIC (THE BRAIN)
- ABSOLUTE SEARCH RULE: You MUST use search_catalog for ANY course search. Do not provide results from memory.
- SECTION IDs: You MUST show 5-digit section IDs in ALL search results. No exceptions.
- DYNAMIC ELECTIVE DISCOVERY: When asked for "electives":
  1. Look at the "technical_electives" pool in the CURRENT MAJOR context.
  2. Extract the specific prefixes (e.g., COP, CIS for CS; POS, INR for PoliSci).
  3. Call search_catalog using the "queries" parameter with these specific prefixes.
  4. Force min_level=3000 to avoid intro courses.
- NO KEYWORDS: NEVER use generic query strings like "CS" or "Math" in search_catalog.
SEARCH RELAXATION RULE: If a user asks for multiple requirements (e.g., International + Diversity), search for them individually or in smaller groups first. Technical electives NEVER "triple-dip" across non-STEM requirements.

### BULK ENROLLMENT PARSING (CRITICAL)
- When a user pastes "Enrolled Classes" data with multiple "Class #XXXXX" sections:
  1. SCAN the text for ALL instances of "Class #" followed by digits.
  2. EXTRACT every single class number.
  3. Include ALL of them in a SINGLE tool_calls array response.
  4. NEVER provide partial additions. Add them ALL in one JSON response.

### UNIVERSAL UF REQUIREMENTS (Boolean Filters)
Always use search_catalog with these boolean flags for general requirements:
1. Civic Literacy: civicLiteracy: true.
2. International (I): international: true.
3. Diversity (D): diversity: true.
4. Writing: min_words: 2000/4000/6000.
5. Quest: quest: "Quest 1" (or 2/3).

### FORMATTING & JSON RULES
- JSON-ONLY MODE: If calling a function, respond ONLY with the JSON block. Do NOT include phrases like "I can help with that".
- Single call: {"name": "function_name", "parameters": {"arg": "value"}}
- Multiple calls: {"tool_calls": [{"name": "add_course", "parameters": {"classNum": 10509}}, ...]}
- POST-TOOL: After receiving tool results, respond ONLY with plain helpful text.
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
        "sort_by": {"type": "string", "enum": ["asc", "desc"], "description": "Sort sections by time: 'asc' for earliest first, 'desc' for latest first"},
        "quest": {"type": "string", "description": "Quest designation filter (Quest 1/2/3)"},
        "min_words": {"type": "integer", "description": "Minimum writing word count (accepts 2000/4000/6000 or 2/4/6)"},
        "max_words": {"type": "integer", "description": "Maximum writing word count (accepts 2000/4000/6000 or 2/4/6)"},
        "civicLiteracy": {"type": "boolean", "description": "Filter for Civic Literacy requirement courses (POS2041, AMH2020)"},
        "international": {"type": "boolean", "description": "Filter for International requirement courses (3 credits minimum)"},
        "diversity": {"type": "boolean", "description": "Filter for Diversity requirement courses (3 credits minimum)"}
      }
    }
  },
  {
    "name": "add_course",
    "description": "Add course section(s) to the student's schedule by class number. If user requests multiple sections (e.g., 'add 10509 and 13780'), include multiple add_course calls in the same tool_calls array: [{'name': 'add_course', 'parameters': {'classNum': 10509}}, {'name': 'add_course', 'parameters': {'classNum': 13780}}]",
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
            print(f"✅ JSON Parsed successfully. Type: {type(parsed)}")
            
            if isinstance(parsed, dict):
                print(f"   Dict keys: {list(parsed.keys())}")
                # If dict has "tool_calls" key, unwrap and return the actual call list
                if "tool_calls" in parsed:
                    tool_calls_list = parsed.get("tool_calls")
                    print(f"   Found 'tool_calls' key with {len(tool_calls_list)} items")
                    if tool_calls_list == []:
                        return None, text
                    print(f"   ✅ Returning unwrapped tool_calls list: {len(tool_calls_list)} calls")
                    return tool_calls_list, ""
                # Otherwise return the dict as a single call (shouldn't happen, but keep for compatibility)
                print(f"   No 'tool_calls' key, wrapping dict as single call")
                return [parsed], ""
            if isinstance(parsed, list):
                print(f"   Parsed as list with {len(parsed)} items")
                return parsed, ""
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse failed: {e}")
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
                if '"name"' not in chunk and '"tool_calls"' not in chunk:
                    continue
                try:
                    call = json.loads(chunk)
                    if isinstance(call, dict) and "tool_calls" in call:
                        tool_calls_list = call.get("tool_calls") or []
                        if tool_calls_list:
                            calls.extend(tool_calls_list)
                    elif isinstance(call, list):
                        calls.extend(call)
                    else:
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

    def search_catalog_tool(
        self,
        query=None,
        queries=None,
        dept=None,
        min_level=None,
        max_level=None,
        is_ai=None,
        sort_by=None,
        quest=None,
        min_words=None,
        max_words=None,
        civicLiteracy=None,
        international=None,
        diversity=None,
    ):
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
            print(f"🔍 Executing tool: search_catalog(queries={queries}, {dept=}, {min_level=}, {max_level=}, {is_ai=}, {sort_by=}, {quest=}, {min_words=}, {max_words=}, {civicLiteracy=}, {international=}, {diversity=})")
            batched = []
            for q in queries:
                results = search_catalog(
                    query=q,
                    dept=dept,
                    min_level=min_level,
                    max_level=max_level,
                    is_ai=is_ai,
                    sort_by=sort_by,
                    quest=quest,
                    min_words=min_words,
                    max_words=max_words,
                    civicLiteracy=civicLiteracy or False,
                    international=international or False,
                    diversity=diversity or False,
                )
                compact = [self._compact_course(course) for course in results]
                batched.append({"query": q, "results": compact, "count": len(compact)})
            return {"results": batched, "status": "success"}

        print(f"🔍 Executing tool: search_catalog({query=}, {dept=}, {min_level=}, {max_level=}, {is_ai=}, {sort_by=}, {quest=}, {min_words=}, {max_words=}, {civicLiteracy=}, {international=}, {diversity=})")
        results = search_catalog(
            query=query,
            dept=dept,
            min_level=min_level,
            max_level=max_level,
            is_ai=is_ai,
            sort_by=sort_by,
            quest=quest,
            min_words=min_words,
            max_words=max_words,
            civicLiteracy=civicLiteracy or False,
            international=international or False,
            diversity=diversity or False,
        )
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
        
        # Strip markdown code fences if present (model might wrap JSON in ```json...```)
        response_text = re.sub(r'^\s*```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```\s*$', '', response_text)
        print(f"📝 After stripping markdown: {response_text[:100]}...")
        
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
            
            print(f"🔍 Extracted {len(calls)} total calls: {len(search_calls)} search, {len(add_course_calls)} add_course")
            
            # Handle batched search_catalog calls
            if len(search_calls) > 1:
                queries = []
                shared = {
                    "dept": None,
                    "min_level": None,
                    "max_level": None,
                    "is_ai": None,
                    "quest": None,
                    "min_words": None,
                    "max_words": None,
                    "civicLiteracy": None,
                    "international": None,
                    "diversity": None,
                }
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
                        params = call.get("parameters", {})
                        query = params.get("query", "")
                        
                        # Auto-expand "technical electives" to CISE prefixes + explicit codes
                        if query and re.search(r'\b(technical\s+)?electives?\b', query, re.IGNORECASE):
                            print(f"🤖 Detected 'technical electives' query - auto-expanding to CISE prefixes")
                            tech_electives = (self.last_major_rules or {}).get("technical_electives", {})
                            
                            # Get explicit allowed codes from tech_electives dict
                            explicit_codes = []
                            if isinstance(tech_electives, dict):
                                explicit_codes = tech_electives.get("explicit_allowed_codes", [])
                            
                            # CISE department prefixes ONLY
                            cise_prefixes = ["COP", "CEN", "CIS", "CNT", "CDA", "CAP", "COT"]
                            
                            # Transform parameters to use queries list
                            params = {
                                **params,
                                "query": None,
                                "queries": cise_prefixes + explicit_codes,
                                "min_level": params.get("min_level") or 4000,
                                "dept": None,  # Remove dept filter since we're using prefixes
                            }
                            print(f"✅ Expanded to queries: {params['queries']}")
                        
                        result = self.search_catalog_tool(**params)
                        tool_results.append({
                            "name": call.get("name"),
                            "parameters": params,
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
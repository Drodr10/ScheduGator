"""
ScheduGator Flask API Server
Connects React frontend to Python backend (Gemma 3 + Solver)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv

# Import our backend modules
from brain import GemmaBrain
from search import search_catalog
from solver_bridge import SolverBridge
import re

# Load environment
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize the AI brain and solver
brain = GemmaBrain()
solver = SolverBridge()

# Load major requirements
current_dir = os.path.dirname(os.path.abspath(__file__))
bucket_path = os.path.join(current_dir, '..', 'data', 'bucket_1.json')
with open(bucket_path, 'r') as f:
    major_requirements = json.load(f)

# Normalize critical tracking to required_courses if it was placed under gpa_gate
for major in major_requirements:
    gpa_gate = major.get('gpa_gate')
    if isinstance(gpa_gate, dict) and 'critical_tracking' in gpa_gate:
        gpa_critical = gpa_gate.pop('critical_tracking')
        if gpa_critical is not None:
            required_courses = major.setdefault('required_courses', {})
            if 'critical_tracking' not in required_courses:
                required_courses['critical_tracking'] = gpa_critical


# ==================== ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'brain': 'ready',
            'solver': 'ready',
            'catalog_size': len(solver.catalog)
        }
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - sends user message to Gemma 3
    Request: { "message": "Show me CS tracking courses", "major": "CPS - Engineering", "major_code": "CPS", "current_courses": [{code, name, classNum}, ...] }
    Response: { "response": "...", "tool_used": "search_catalog", "added_courses": [...] }
    """
    try:
        data = request.json
        user_message = data.get('message', '')
        major_context = data.get('major')
        major_code = data.get('major_code')
        current_courses = data.get('current_courses', [])
        major_rules = None

        if not major_code and isinstance(major_context, str) and major_context:
            match = re.search(r"\(([A-Z]{2,4})\)", major_context)
            if match:
                major_code = match.group(1)
            else:
                token = major_context.split("-")[0].strip().upper()
                if 2 <= len(token) <= 4 and token.isalpha():
                    major_code = token

        if major_code:
            major_rules = next(
                (m for m in major_requirements if m.get('major_code') == major_code),
                None
            )
            if major_rules:
                print(f"📋 Found major_rules for {major_code}: {len(json.dumps(major_rules))} chars")
            else:
                print(f"⚠️ Major code '{major_code}' not found in bucket_1.json")
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process through Gemma brain
        response = brain.process_input(
            user_message,
            major_context=major_context,
            major_rules=major_rules,
            major_code=major_code,
            current_courses=current_courses
        )

        # Guard against empty tool_calls responses leaking to the UI
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and parsed.get("tool_calls") == []:
                response = (
                    "I can help with that. Please tell me your major and any preferences "
                    "(morning/evening, days off, AP/dual enrollment credits)."
                )
        except json.JSONDecodeError:
            pass
        
        # Extract courses added marker if present
        added_courses = []
        courses_marker_match = re.search(r'__COURSES_ADDED_(.+?)__COURSES_ADDED__', response)
        if courses_marker_match:
            try:
                courses_json = courses_marker_match.group(1)
                added_courses = json.loads(courses_json)
                print(f"✅ Extracted {len(added_courses)} courses from response")
            except (json.JSONDecodeError, IndexError) as e:
                print(f"⚠️ Error parsing courses marker: {e}")
        
        # Strip the marker from the displayed text
        response_display = re.sub(r'__COURSES_ADDED_.+?__COURSES_ADDED__', '', response).strip()
        
        return jsonify({
            'response': response_display,
            'status': 'success',
            'added_courses': added_courses
        })
    
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def search():
    """
    Direct course search endpoint
    Request: {
        "query": "COP",
        "dept": "Computer Science",
        "min_level": 3000,
        "max_level": 4000,
        "is_ai": false,
        "sort_by": "asc"  // Optional: "asc", "desc", or omit
    }
    """
    try:
        data = request.json
        
        results = search_catalog(
            query=data.get('query'),
            queries=data.get('queries'),
            dept=data.get('dept'),
            min_level=data.get('min_level', 1000),
            max_level=data.get('max_level', 7000),
            is_ai=data.get('is_ai'),
            sort_by=data.get('sort_by'),
            quest=data.get('quest'),
            min_words=data.get('min_words'),
            max_words=data.get('max_words')
        )
        
        return jsonify({
            'results': results,
            'count': len(results),
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-schedule', methods=['POST'])
def generate_schedule():
    """
    Generate a conflict-free schedule
    Request: {
        "courses": ["COP3502", "MAC2312", "PHY2048"],
        "major_code": "CPS"  // Optional
    }
    Response: {
        "schedule": [...],  // Array of selected sections
        "success": true
    }
    """
    try:
        data = request.json
        course_codes = data.get('courses', [])
        major_code = data.get('major_code')
        
        if not course_codes:
            return jsonify({'error': 'No courses provided'}), 400
        
        print(f"🔧 Generating schedule for: {course_codes}")
        
        # Get major rules if provided
        major_rules = None
        if major_code:
            major_rules = next(
                (m for m in major_requirements if m['major_code'] == major_code),
                None
            )
        
        # Run the solver
        schedule = solver.validate_and_solve(course_codes, major_rules)
        
        if schedule is None:
            return jsonify({
                'success': False,
                'error': 'No conflict-free schedule found',
                'message': 'Try selecting fewer courses or courses with more available sections'
            }), 200
        
        return jsonify({
            'success': True,
            'schedule': schedule,
            'courses_scheduled': len(schedule),
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Schedule generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/majors', methods=['GET'])
def get_majors():
    """Get list of available majors from bucket_1.json"""
    try:
        majors_list = [
            {
                'major_code': m['major_code'],
                'college': m.get('college', 'Unknown'),
                'total_credits': m.get('total_credits', 120)
            }
            for m in major_requirements
        ]
        
        return jsonify({
            'majors': majors_list,
            'count': len(majors_list),
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Majors error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/init-major', methods=['POST'])
def init_major():
    """
    Initialize major context on the brain (no chat message)
    Request: { "major": "CPS - Engineering", "major_code": "CPS" }
    Response: { "status": "initialized" }
    """
    try:
        data = request.json
        major_code = data.get('major_code')
        
        if not major_code:
            return jsonify({'error': 'major_code is required'}), 400
        
        # Find major rules
        major_rules = next(
            (m for m in major_requirements if m.get('major_code') == major_code),
            None
        )
        
        if major_rules:
            # Set the brain's internal state but don't send a message
            brain.last_major_code = major_code
            brain.last_major_rules = major_rules
            major_json = json.dumps(major_rules, ensure_ascii=True)
            print(f"📋 ✅ Injecting full bucket_1 JSON for major: {major_code} ({len(major_json)} chars)")
            return jsonify({
                'status': 'initialized',
                'major_code': major_code,
                'context_size': len(major_json)
            })
        else:
            return jsonify({'error': f'Major {major_code} not found'}), 404
    
    except Exception as e:
        print(f"❌ Init major error: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/major/<major_code>', methods=['GET'])
def get_major_details(major_code):
    """Get detailed requirements for a specific major"""
    try:
        major = next(
            (m for m in major_requirements if m['major_code'] == major_code.upper()),
            None
        )
        
        if not major:
            return jsonify({'error': f'Major {major_code} not found'}), 404
        
        return jsonify({
            'major': major,
            'status': 'success'
        })
    
    except Exception as e:
        print(f"❌ Major details error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== RUN SERVER ====================

if __name__ == '__main__':
    print("🐊 ScheduGator API Starting...")
    print(f"📚 Catalog loaded: {len(solver.catalog)} courses")
    print(f"🎓 Majors available: {len(major_requirements)}")
    print(f"🔑 API Key: {'✅ Found' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
    print("\n🚀 Server running on http://localhost:5000\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

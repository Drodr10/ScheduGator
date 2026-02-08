import requests
import json
import time

# --- CONFIGURATION ---
TERM = "2261"  # Spring 2026
BASE_URL = "https://one.uf.edu/apix/soc/schedule"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def ingest_uf_data():
    all_processed_courses = []
    last_control = 0
    page_count = 0
    
    print(f"--- 🐊 Starting Schedugator Ingestion for Term {TERM} ---")

    while True:
        params = {
            "category": "CWSP",
            "term": TERM,
            "last-control-number": last_control
        }
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS)
            response.raise_for_status()
            
            # ONE.UF returns a list containing the data object
            data_wrapper = response.json()
            if not data_wrapper:
                print("\n--- [REACHED END] No more data wrappers returned. ---")
                break
                
            data = data_wrapper[0]
            raw_courses = data.get("COURSES", [])
            
            new_control = data.get("LASTCONTROLNUMBER", 0)
            
            # 🛑 THE REAL STOPPING CONDITION
            if not raw_courses or new_control <= last_control or new_control == 0:
                print("\n--- [REACHED END] No more courses found in API response. ---")
                break
            
            # Update control number for the NEXT request
            last_control = new_control
            page_count += 1

            for course in raw_courses:
                # 🛠️ Bubble up Department Name from the first section
                # This is critical for your Tech Elective logic later!
                first_sec = course.get("sections", [{}])[0]
                dept = first_sec.get("deptName", "Unknown Department")

                processed = {
                    "code": course["code"],
                    "name": course["name"],
                    "dept": dept,
                    "description": course.get("description", ""),
                    "prereqs": course.get("prerequisites", ""),
                    "isAI": course.get("isAICourse", False),
                    # grWriting is often per-section; we check the first one
                    "writingWords": int(first_sec.get("grWriting", "0")) if str(first_sec.get("grWriting")).isdigit() else 0,
                    "quest": first_sec.get("quest", []),
                    "sections": []
                }

                for sec in course.get("sections", []):
                    processed["sections"].append({
                        "classNum": sec["classNumber"],
                        "instructors": [i["name"] for i in sec.get("instructors", [])],
                        "sectWeb": sec.get("sectWeb", "PC"),
                        "credits": sec["credits"],
                        "meetTimes": sec.get("meetTimes", [])
                    })
                
                all_processed_courses.append(processed)

            # Progress tracking so you can watch it hit the 'P' block
            current_prefix = raw_courses[-1]["code"][:3]
            print(f"Page {page_count} | Total: {len(all_processed_courses)} | Current Prefix: {current_prefix} | Control: {last_control}")
            
            # Anti-throttling (Crucial for Vultr hosting)
            time.sleep(0.1) 

        except Exception as e:
            print(f"\n🚨 Ingestion halted at control {last_control}: {e}")
            break

    return all_processed_courses

# --- EXECUTION ---
catalog_data = ingest_uf_data()

# Save to your Bucket 2 "Universal Base"
current_dir = os.path.dirname(os.path.abspath(__file__))
catalog_path = os.path.join(current_dir, '..', 'data', 'universal_base_catalog.json')

with open(catalog_path, 'w') as f:
    json.dump(catalog_data, f, indent=2)

print(f"--- 🏁 Success: Saved {len(catalog_data)} courses to {catalog_path} ---")
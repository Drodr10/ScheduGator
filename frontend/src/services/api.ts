/**
 * API Service Layer for ScheduGator
 * Handles all HTTP requests to the Flask backend
 */

const API_BASE_URL = 'http://localhost:5000/api';

// ==================== Types ====================

export interface ApiCourse {
  code: string;
  name: string;
  dept: string;
  credits: number;
  sections: ApiSection[];
  isAI?: boolean;
}

export interface ApiSection {
  section: string;
  classNum?: string | number;
  instructor?: string;
  instructors?: string[];
  credits?: number;
  meetTimes: MeetTime[];
  enrollmentCap?: number;
  enrollmentActual?: number;
}

export interface MeetTime {
  meetDays: string[];
  meetTimeBegin?: string;
  meetTimeEnd?: string;
  meetPeriodBegin: string | number;
  meetPeriodEnd: string | number;
  meetBuilding?: string;
  meetRoom?: string;
}



export interface ApiMajor {
  major_code: string;
  college: string;
  total_credits: number;
}

export interface ChatResponse {
  response: string;
  status: string;
  added_courses?: Array<{
    code: string;
    name: string;
    classNum: number;
    instructors: string[];
    credits: number;
    meetTimes: MeetTime[];
    dept?: string;
  }>;
}

export interface SearchResponse {
  results: ApiCourse[];
  count: number;
  status: string;
}

export interface ScheduleResponse {
  success: boolean;
  schedule?: ApiSection[];
  courses_scheduled?: number;
  error?: string;
  message?: string;
  status: string;
}

export interface HealthResponse {
  status: string;
  services: {
    brain: string;
    solver: string;
    catalog_size: number;
  };
}

// ==================== API Client ====================

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health Check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Chat with AI
  async chat(message: string, major?: string, majorCode?: string, currentCourses?: Array<{code: string; name: string; classNum: number}>): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, major, major_code: majorCode, current_courses: currentCourses }),
    });
  }

  // Search Courses
  async searchCourses(params: {
    query?: string;
    dept?: string;
    min_level?: number;
    max_level?: number;
    is_ai?: boolean;
    sort_by?: 'asc' | 'desc';
  }): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Generate Schedule
  async generateSchedule(
    courses: string[],
    majorCode?: string
  ): Promise<ScheduleResponse> {
    return this.request<ScheduleResponse>('/generate-schedule', {
      method: 'POST',
      body: JSON.stringify({
        courses,
        major_code: majorCode,
      }),
    });
  }

  // Get All Majors
  async getMajors(): Promise<{ majors: ApiMajor[]; count: number; status: string }> {
    return this.request('/majors');
  }

  // Get Major Details
  async getMajorDetails(majorCode: string): Promise<{ major: any; status: string }> {
    return this.request(`/major/${majorCode}`);
  }

  // Initialize major context (background, no chat)
  async initMajor(major: string, majorCode: string): Promise<{ status: string }> {
    return this.request('/init-major', {
      method: 'POST',
      body: JSON.stringify({ major, major_code: majorCode }),
    });
  }
}

// Export singleton instance
export const api = new ApiClient();

// ==================== Utility Functions ====================

/**
 * Parse time string like "10:40 AM" to hour number
 */
function parseTimeToHour(timeStr: string | undefined): number {
  if (!timeStr) return 8; // Default to 8 AM
  
  const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (!match) return 8;
  
  let hour = parseInt(match[1]);
  const minutes = parseInt(match[2]);
  const period = match[3].toUpperCase();
  
  // Convert to 24-hour format
  if (period === 'PM' && hour !== 12) {
    hour += 12;
  } else if (period === 'AM' && hour === 12) {
    hour = 0;
  }
  
  // Add fraction for minutes (e.g., 10:40 becomes 10.67)
  return hour + (minutes / 60);
}

/**
 * Convert API course format to frontend Course format
 */
export function convertApiCourseToFrontend(apiCourse: ApiCourse, section: ApiSection, isCriticalTracking: boolean = false) {
  // Parse meet times to get the first time slot
  const firstMeetTime = section.meetTimes?.[0];
  const meetDays = firstMeetTime?.meetDays || [];
  
  // Parse actual time strings
  const start = parseTimeToHour(firstMeetTime?.meetTimeBegin);
  const end = parseTimeToHour(firstMeetTime?.meetTimeEnd);

  // Extract instructor name(s) - handle both singular and plural formats
  let instructorName = 'TBA';
  if (section.instructor && section.instructor !== 'TBA') {
    instructorName = section.instructor;
  } else if (section.instructors && Array.isArray(section.instructors) && section.instructors.length > 0) {
    instructorName = section.instructors.join(', ');
  }

  // Get section number - try section field first, then classNum
  const sectionNum = String(section.section || section.classNum || '0001');

  // Get credits - prefer section-level credits if available, otherwise use course-level
  const credits = section.credits || apiCourse.credits || 3;

  return {
    code: apiCourse.code, // new format
    name: apiCourse.name, // new format
    courseCode: apiCourse.code, // legacy format
    courseName: apiCourse.name, // legacy format
    instructor: instructorName,
    credits: credits,
    meetDays: meetDays,
    meetPeriod: { start, end },
    section: sectionNum,
    enrollmentCap: section.enrollmentCap || 30,
    enrollmentActual: section.enrollmentActual || 0,
    isCriticalTracking: isCriticalTracking,
    isAISuggested: false,
  };
}

/**
 * Check if API is healthy
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const health = await api.healthCheck();
    return health.status === 'healthy';
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
}

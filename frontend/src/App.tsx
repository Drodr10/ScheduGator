import { useState, useCallback, useEffect, useRef } from 'react';
import { Schedule, ChatMessage, Course } from './types/index';
import { Header } from './components/Header';
import { ChatSidebar } from './components/ChatSidebar';
import { Calendar } from './components/Calendar';
import { SchedulePanel } from './components/SchedulePanel';
import { useScheduleStore } from './store/index';
import { api, checkApiHealth } from './services/api';
import { buildIcs, downloadIcs } from './utils/ics';

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

export function App() {
  const store = useScheduleStore();
  const initializeRef = useRef(false); // Track if initialization has already run
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [showConflictFilter, setShowConflictFilter] = useState(false);
  const [showCriticalFilter, setShowCriticalFilter] = useState(false);
  const [majorsList, setMajorsList] = useState<string[]>([]);
  const [apiHealthy, setApiHealthy] = useState(false);
  const [contextInitialized, setContextInitialized] = useState(false);
  const [criticalTrackingCourses, setCriticalTrackingCourses] = useState<string[]>([]);

  // Set permanent dark mode
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  // Check API health and load majors on mount
  useEffect(() => {
    // Use ref to prevent initialization from running twice (even in StrictMode)
    if (initializeRef.current) {
      return;
    }
    initializeRef.current = true;

    const initializeApp = async () => {
      // Check if backend is running
      const healthy = await checkApiHealth();
      setApiHealthy(healthy);

      if (healthy) {
        try {
          // Load available majors from backend
          const { majors } = await api.getMajors();
          const majorNames = majors.map(
            (m) => `${m.major_code} - ${m.college}`
          );
          setMajorsList(majorNames);
          
          // DO NOT set default major - let user select it first
          // This ensures context is only loaded when explicitly chosen

          // Add welcome message
          const welcomeMsg: ChatMessage = {
            id: generateId(),
            type: 'system',
            content: '🐊 Welcome to ScheduGator! Select your major to get started, then ask: "Show me my tracking courses" or "Generate a schedule"',
            timestamp: new Date(),
          };
          store.addMessage(welcomeMsg);
        } catch (error) {
          console.error('Failed to load majors:', error);
          // Fallback to demo data if API fails
          setMajorsList(['Computer Science (CPS)', 'Computer Engineering (CPE)']);
        }
      } else {
        // API not available - add error message
        const errorMsg: ChatMessage = {
          id: generateId(),
          type: 'system',
          content: '⚠️ Backend API is not running. Please start the Flask server with: python backend/api.py',
          timestamp: new Date(),
        };
        store.addMessage(errorMsg);
        setMajorsList(['Computer Science (CPS)', 'Computer Engineering (CPE)']);
      }
    };

    initializeApp();
  }, [store]);

  const handleMajorChange = useCallback(async (major: string) => {
    store.setSelectedMajor(major);
    store.setSelectedSchedule(null);
    
    if (!major) {
      setCriticalTrackingCourses([]);
      return;
    }

    const majorCode = major.split(' - ')[0]?.trim();
    
    // Always reload critical tracking courses when major changes
    try {
      const { major: majorDetails } = await api.getMajorDetails(majorCode);
      
      // Try multiple paths to find critical tracking courses
      let criticalTracking = 
        majorDetails?.required_courses?.critical_tracking ||
        majorDetails?.critical_tracking ||
        majorDetails?.tracking_courses ||
        [];
      
      // If it's an object with course codes as keys, extract the values
      if (typeof criticalTracking === 'object' && !Array.isArray(criticalTracking)) {
        criticalTracking = Object.values(criticalTracking);
      }
      
      // Ensure it's an array of strings
      const criticalTrackingArray = Array.isArray(criticalTracking) 
        ? criticalTracking.map(c => typeof c === 'string' ? c : (c?.code || c?.course_code || String(c)))
        : [];
      
      setCriticalTrackingCourses(criticalTrackingArray);
      console.log(`📚 Critical tracking courses for ${majorCode}:`, criticalTrackingArray);
    } catch (error) {
      console.error('Error loading critical tracking courses:', error);
      setCriticalTrackingCourses([]);
    }

    // Initialize major context on backend (silently, no chat message)
    if (!contextInitialized && majorCode) {
      try {
        await api.initMajor(major, majorCode);
        console.log(`✅ Major context initialized for ${majorCode}`);
        setContextInitialized(true);
      } catch (error) {
        console.error('Error initializing major context:', error);
      }
    }
  }, [store, contextInitialized]);

  useEffect(() => {
    const schedule = store.selectedSchedule;
    if (!schedule) {
      return;
    }

    const criticalSet = new Set(
      criticalTrackingCourses.map((code) => code.toUpperCase())
    );
    let changed = false;

    const updatedCourses = schedule.courses.map((course) => {
      const code = (course.code || course.courseCode || '').toUpperCase();
      const isCritical = criticalSet.has(code);
      const nextColor = isCritical ? '#d32f2f' : '#1976d2';

      if (course.isCriticalTracking !== isCritical || course.color !== nextColor) {
        changed = true;
        return {
          ...course,
          isCriticalTracking: isCritical,
          color: nextColor,
        };
      }

      return course;
    });

    if (changed) {
      store.updateSchedule(updatedCourses);
    }
  }, [store, store.selectedSchedule, store.updateSchedule, criticalTrackingCourses]);

  const handleSendMessage = useCallback(async (message: string) => {
    // Add user message
    const userMsg: ChatMessage = {
      id: generateId(),
      type: 'user',
      content: message,
      timestamp: new Date(),
    };
    store.addMessage(userMsg);

    if (!apiHealthy) {
      const errorMsg: ChatMessage = {
        id: generateId(),
        type: 'system',
        content: '❌ Cannot process request - backend API is offline.',
        timestamp: new Date(),
      };
      store.addMessage(errorMsg);
      return;
    }

    store.setLoadingSchedule(true);

    try {
      const majorCode = store.selectedMajor.split(' - ')[0]?.trim();
      
      // All messages go through the AI
      const currentCourses = store.selectedSchedule?.courses
        ?.filter(c => {
          const code = c.code || c.courseCode;
          const name = c.name || c.courseName;
          return code && name;
        })
        .map(c => ({
          code: (c.code || c.courseCode) as string,
          name: (c.name || c.courseName) as string,
          classNum: c.classNum || 0,
        })) || [];
      
      const chatResponse = await api.chat(message, store.selectedMajor, majorCode, currentCourses);
      
      const aiMsg: ChatMessage = {
        id: generateId(),
        type: 'ai',
        content: chatResponse.response,
        timestamp: new Date(),
      };
      store.addMessage(aiMsg);
      
      // Check if any courses were added
      if (chatResponse.added_courses && chatResponse.added_courses.length > 0) {
        const newCourses: Course[] = [];
        
        for (const courseData of chatResponse.added_courses) {
          // Check if already in schedule
          const existingCourses = store.selectedSchedule?.courses || [];
          const alreadyAdded = existingCourses.some(
            c => (c.code || c.courseCode) === courseData.code && c.classNum === courseData.classNum
          );
          
          if (!alreadyAdded) {
            // Convert course data to frontend format
            const isCriticalTracking = criticalTrackingCourses.includes(courseData.code);
            
            // Collect ALL meeting days from ALL meeting times
            const allMeetDays: string[] = [];
            let meetPeriodStart = 8;
            let meetPeriodEnd = 9;
            
            if (courseData.meetTimes && courseData.meetTimes.length > 0) {
              // Get all unique days from all meeting times
              for (const meetTime of courseData.meetTimes) {
                if (meetTime.meetDays) {
                  // Convert "R" to "Th" for Thursday
                  const convertedDays = meetTime.meetDays.map(day => day === 'R' ? 'Th' : day);
                  allMeetDays.push(...convertedDays);
                }
              }
              
              // For the legacy meetPeriod, use the first meeting time
              const firstMeeting = courseData.meetTimes[0];
              
              const parseTime = (timeStr: string): number => {
                const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
                if (!match) return 8;
                let hour = parseInt(match[1]);
                const minutes = parseInt(match[2]);
                const period = match[3].toUpperCase();
                if (period === 'PM' && hour !== 12) hour += 12;
                else if (period === 'AM' && hour === 12) hour = 0;
                return hour + (minutes / 60);
              };
              
              meetPeriodStart = parseTime(firstMeeting.meetTimeBegin || '8:00 AM');
              meetPeriodEnd = parseTime(firstMeeting.meetTimeEnd || '9:00 AM');
            }
            
            // Remove duplicates and sort days
            const uniqueMeetDays = [...new Set(allMeetDays)];
            const dayOrder: { [key: string]: number } = { 'M': 0, 'T': 1, 'W': 2, 'Th': 3, 'F': 4 };
            const sortedMeetDays = uniqueMeetDays.sort((a, b) => (dayOrder[a] || 0) - (dayOrder[b] || 0));
            
            // Get instructor
            const instructor = courseData.instructors?.length > 0 
              ? courseData.instructors.join(', ') 
              : 'TBA';
            
            const frontendCourse: Course = {
              id: generateId(),
              // New format
              code: courseData.code,
              name: courseData.name,
              credits: courseData.credits,
              classNum: courseData.classNum,
              instructors: courseData.instructors || [],
              meetTimes: courseData.meetTimes || [],
              isCriticalTracking: isCriticalTracking,
              dept: courseData.dept || '',
              color: isCriticalTracking ? '#d32f2f' : '#1976d2',
              // Legacy format (for backward compatibility)
              courseCode: courseData.code,
              courseName: courseData.name,
              instructor: instructor,
              meetDays: sortedMeetDays,
              meetPeriod: { start: meetPeriodStart, end: meetPeriodEnd },
              section: String(courseData.classNum),
              enrollmentCap: 30,
              enrollmentActual: 0,
            };
            
            newCourses.push(frontendCourse);
          }
        }
        
        if (newCourses.length > 0) {
          // Add courses to schedule
          const existingCourses = store.selectedSchedule?.courses || [];
          const allCourses = [...existingCourses, ...newCourses];
          
          const schedule: Schedule = {
            majorCode: majorCode || 'CPS',
            semester: 'Spring 2024',
            courses: allCourses,
            isCriticalTrackingSchedule: false,
            isOptimized: false,
          };
          
          store.setSelectedSchedule(schedule);
          
          const confirmMsg: ChatMessage = {
            id: generateId(),
            type: 'system',
            content: `✅ Added ${newCourses.length} course(s) to your schedule!`,
            timestamp: new Date(),
          };
          store.addMessage(confirmMsg);
        }
      }
    } catch (error) {
      console.error('Message handling error:', error);
      const errorMsg: ChatMessage = {
        id: generateId(),
        type: 'system',
        content: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
      };
      store.addMessage(errorMsg);
    } finally {
      store.setLoadingSchedule(false);
    }
  }, [store, apiHealthy, criticalTrackingCourses]);

  const handleDeleteCourse = useCallback((course: Course) => {
    if (!store.selectedSchedule) return;
    
    const updatedCourses = store.selectedSchedule.courses.filter(
      c => !(c.courseCode === course.courseCode && c.section === course.section)
    );
    
    const updatedSchedule: Schedule = {
      ...store.selectedSchedule,
      courses: updatedCourses,
    };
    
    store.setSelectedSchedule(updatedSchedule);
    
    const msg: ChatMessage = {
      id: generateId(),
      type: 'system',
      content: `🗑️ Removed ${course.courseCode} (Section ${course.section}) from schedule.`,
      timestamp: new Date(),
    };
    store.addMessage(msg);
  }, [store]);

  return (
    <div className="flex flex-col h-screen bg-gator-gray-50 dark:bg-gray-900 overflow-x-hidden">
      {/* Header */}
      <Header
        onExportCalendar={() => {
          const schedule = store.selectedSchedule;
          if (!schedule || schedule.courses.length === 0) {
            alert('No courses to export yet. Add courses to your schedule first.');
            return;
          }

          const today = new Date();
          let year = today.getFullYear();
          
          // Use next year's January if we're past April 22
          const aprilEnd = new Date(year, 3, 22);
          if (today > aprilEnd) {
            year = today.getFullYear() + 1;
          }

          const parsedStart = new Date(`${year}-01-12T00:00:00`);
          const parsedEnd = new Date(`${year}-04-22T00:00:00`);

          const icsContent = buildIcs(schedule, {
            startDate: parsedStart,
            endDate: parsedEnd,
            calendarName: `ScheduGator ${schedule.majorCode} Schedule`,
          });

          downloadIcs(icsContent, 'schedugator-schedule.ics');
        }}
      />

      {/* API Status Indicator */}
      {!apiHealthy && (
        <div className="bg-red-500 text-white px-4 py-2 text-center text-sm break-words">
          ⚠️ Backend API Offline - Start server with: <code className="bg-red-600 px-2 py-1 rounded break-all">python backend/api.py</code>
        </div>
      )}

      {/* Main Content */}
      <div className="flex flex-1 flex-col lg:flex-row overflow-y-auto lg:overflow-hidden min-h-0">
        {/* Sidebar Chat - Limited height on mobile, full height on desktop */}
        <div className="w-full lg:w-96 lg:flex-shrink-0 flex flex-col max-h-[50vh] lg:max-h-none lg:h-full lg:min-h-0 flex-shrink-0">
          <ChatSidebar
            majorsList={majorsList}
            selectedMajor={store.selectedMajor}
            onMajorChange={handleMajorChange}
            messages={store.messages}
            isLoading={store.isLoadingSchedule}
            onSendMessage={handleSendMessage}
          />
        </div>

        {/* Calendar and Details */}
        <div className="flex-1 flex flex-col lg:overflow-hidden lg:min-h-0">
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 lg:overflow-hidden lg:flex-1 p-4 sm:p-6">
            {/* Calendar */}
            <div className="xl:col-span-2 flex flex-col lg:overflow-hidden">
              <h2 className="text-2xl font-bold text-gator-gray-800 dark:text-gray-100 mb-4">Weekly Schedule</h2>
              <div className="overflow-x-auto lg:flex-1 lg:overflow-auto">
                <Calendar
                  schedule={store.selectedSchedule}
                  selectedCourse={selectedCourse}
                  onCourseSelect={setSelectedCourse}
                />
              </div>
            </div>

            {/* Details Panel */}
            <div className="flex flex-col lg:overflow-auto">
              <h2 className="text-2xl font-bold text-gator-gray-800 dark:text-gray-100 mb-4">Courses & Details</h2>
              <div className="lg:flex-1 lg:overflow-auto">
                <SchedulePanel
                  schedule={store.selectedSchedule}
                  selectedCourse={selectedCourse}
                  onCourseSelect={setSelectedCourse}
                  onCourseDelete={handleDeleteCourse}
                  showConflictsOnly={showConflictFilter}
                  showCriticalTrackingOnly={showCriticalFilter}
                  onToggleConflictFilter={() => setShowConflictFilter(!showConflictFilter)}
                  onToggleCriticalTrackingFilter={() => setShowCriticalFilter(!showCriticalFilter)}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

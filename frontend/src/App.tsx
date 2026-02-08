import React, { useState, useCallback, useEffect } from 'react';
import { Schedule, ChatMessage, Course } from './types/index';
import { Header } from './components/Header';
import { ChatSidebar } from './components/ChatSidebar';
import { Calendar } from './components/Calendar';
import { SchedulePanel } from './components/SchedulePanel';
import { useScheduleStore } from './store/index';

// Demo data generator
const DEMO_COURSES = {
  'Computer Science (CPS)': [
    {
      courseCode: 'COP 3014',
      courseName: 'Programming Fundamentals 1',
      instructor: 'Dr. Smith',
      credits: 3,
      meetDays: ['M', 'W', 'F'],
      meetPeriod: { start: 9, end: 10 },
      section: '0001',
      enrollmentCap: 30,
      enrollmentActual: 28,
      isCriticalTracking: true,
      isAISuggested: false,
    },
    {
      courseCode: 'COP 3504C',
      courseName: 'Advanced Programming',
      instructor: 'Dr. Johnson',
      credits: 4,
      meetDays: ['T', 'Th'],
      meetPeriod: { start: 10, end: 12 },
      section: '0001',
      enrollmentCap: 25,
      enrollmentActual: 24,
      isCriticalTracking: true,
      isAISuggested: true,
    },
    {
      courseCode: 'MAC 2312',
      courseName: 'Calculus 2',
      instructor: 'Dr. Williams',
      credits: 4,
      meetDays: ['M', 'W', 'F'],
      meetPeriod: { start: 13, end: 14 },
      section: '0001',
      enrollmentCap: 35,
      enrollmentActual: 32,
      isCriticalTracking: true,
      isAISuggested: false,
    },
    {
      courseCode: 'CIS 3362',
      courseName: 'Security in Computing',
      instructor: 'Dr. Brown',
      credits: 3,
      meetDays: ['T', 'Th'],
      meetPeriod: { start: 14, end: 15 },
      section: '0001',
      enrollmentCap: 28,
      enrollmentActual: 27,
      isCriticalTracking: false,
      isAISuggested: true,
    },
  ],
  'Computer Engineering (CPE)': [
    {
      courseCode: 'EEL 4914',
      courseName: 'Senior Design',
      instructor: 'Dr. Martinez',
      credits: 4,
      meetDays: ['M', 'W'],
      meetPeriod: { start: 9, end: 11 },
      section: '0001',
      enrollmentCap: 20,
      enrollmentActual: 20,
      isCriticalTracking: true,
      isAISuggested: false,
    },
    {
      courseCode: 'EEL 3112',
      courseName: 'Digital Logic Design',
      instructor: 'Dr. Lee',
      credits: 3,
      meetDays: ['T', 'Th', 'F'],
      meetPeriod: { start: 11, end: 12 },
      section: '0001',
      enrollmentCap: 30,
      enrollmentActual: 29,
      isCriticalTracking: true,
      isAISuggested: false,
    },
  ],
  'Data Science (DAS)': [
    {
      courseCode: 'CAP 4770',
      courseName: 'Machine Learning',
      instructor: 'Dr. Patel',
      credits: 3,
      meetDays: ['M', 'W', 'F'],
      meetPeriod: { start: 10, end: 11 },
      section: '0001',
      enrollmentCap: 40,
      enrollmentActual: 38,
      isCriticalTracking: false,
      isAISuggested: true,
    },
    {
      courseCode: 'COP 4555',
      courseName: 'Programming Languages',
      instructor: 'Dr. Kumar',
      credits: 3,
      meetDays: ['T', 'Th'],
      meetPeriod: { start: 13, end: 14 },
      section: '0001',
      enrollmentCap: 35,
      enrollmentActual: 33,
      isCriticalTracking: false,
      isAISuggested: false,
    },
  ],
};

function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

export function App() {
  const store = useScheduleStore();
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [showConflictFilter, setShowConflictFilter] = useState(false);
  const [showCriticalFilter, setShowCriticalFilter] = useState(false);

  // Set permanent dark mode
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  const handleMajorChange = useCallback((major: string) => {
    store.setSelectedMajor(major);
    // Demo: clear schedule when major changes
    store.setSelectedSchedule(null);
  }, [store]);

  const handleSendMessage = useCallback((message: string) => {
    // Add user message
    const userMsg: ChatMessage = {
      id: generateId(),
      type: 'user',
      content: message,
      timestamp: new Date(),
    };
    store.addMessage(userMsg);

    // Simulate AI processing
    store.setLoadingSchedule(true);

    setTimeout(() => {
      // Demo: Simulate AI response and schedule generation
      const demoResponse = `I've generated a schedule for ${store.selectedMajor}. This schedule has been optimized based on your preferences and includes all critical tracking courses.`;

      const aiMsg: ChatMessage = {
        id: generateId(),
        type: 'ai',
        content: demoResponse,
        timestamp: new Date(),
      };
      store.addMessage(aiMsg);

      // Create demo schedule
      const courseList =
        DEMO_COURSES[store.selectedMajor as keyof typeof DEMO_COURSES] || DEMO_COURSES['Computer Science (CPS)'];
      
      const demoSchedule: Schedule = {
        majorCode: store.selectedMajor.split('(')[1]?.replace(')', '') || 'CPS',
        semester: 'Spring 2024',
        courses: courseList,
        isCriticalTrackingSchedule: true,
        isOptimized: true,
      };

      store.setSelectedSchedule(demoSchedule);
      store.setLoadingSchedule(false);

      // Add system message
      const systemMsg: ChatMessage = {
        id: generateId(),
        type: 'system',
        content: '✨ Schedule generated successfully! Check the calendar on the right.',
        timestamp: new Date(),
      };
      store.addMessage(systemMsg);
    }, 1500);
  }, [store]);

  return (
    <div className="flex flex-col min-h-screen bg-gator-gray-50 dark:bg-gray-900">
      {/* Header */}
      <Header
        onExportCalendar={() => {
          alert('Export feature coming soon! This will integrate with Google Calendar and Outlook.');
        }}
      />

      {/* Main Content */}
      <div className="flex flex-1 flex-col lg:flex-row overflow-hidden">
        {/* Sidebar Chat */}
        <div className="w-full lg:w-96 flex-shrink-0 flex flex-col">
          <ChatSidebar
            majorsList={Object.keys(DEMO_COURSES)}
            selectedMajor={store.selectedMajor}
            onMajorChange={handleMajorChange}
            messages={store.messages}
            isLoading={store.isLoadingSchedule}
            onSendMessage={handleSendMessage}
          />
        </div>

        {/* Calendar and Details */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 grid grid-cols-1 xl:grid-cols-3 gap-4 overflow-hidden p-4 sm:p-6">
            {/* Calendar */}
            <div className="xl:col-span-2 flex flex-col overflow-hidden">
              <h2 className="text-2xl font-bold text-gator-gray-800 dark:text-gray-100 mb-4">Weekly Schedule</h2>
              <div className="flex-1 overflow-auto">
                <Calendar
                  schedule={store.selectedSchedule}
                  selectedCourse={selectedCourse}
                  onCourseSelect={setSelectedCourse}
                />
              </div>
            </div>

            {/* Details Panel */}
            <div className="flex flex-col overflow-auto">
              <h2 className="text-2xl font-bold text-gator-gray-800 dark:text-gray-100 mb-4">Courses & Details</h2>
              <div className="flex-1 overflow-auto">
                <SchedulePanel
                  schedule={store.selectedSchedule}
                  selectedCourse={selectedCourse}
                  onCourseSelect={setSelectedCourse}
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

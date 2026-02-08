export interface TimeSlot {
  start: number; // 24-hour format (e.g., 9 for 9 AM, 13 for 1 PM)
  end: number;
}

export interface Course {
  courseCode: string;
  courseName: string;
  instructor: string;
  credits: number;
  meetDays: string[]; // ['M', 'W', 'F'] or ['T', 'Th']
  meetPeriod: TimeSlot;
  section: string;
  enrollmentCap: number;
  enrollmentActual: number;
  isCriticalTracking?: boolean;
  isAISuggested?: boolean;
}

export interface Schedule {
  majorCode: string;
  semester: string;
  courses: Course[];
  isCriticalTrackingSchedule?: boolean;
  isOptimized?: boolean;
}

export interface ConflictInfo {
  courseA: Course;
  courseB: Course;
  conflictingDays: string[];
  conflictingTimes: {
    start: number;
    end: number;
  };
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  suggestedSchedule?: Schedule;
}

export interface UIState {
  selectedMajor: string;
  selectedSchedule: Schedule | null;
  selectedCourse: Course | null;
  isLoadingSchedule: boolean;
  filters: {
    showConflictsOnly: boolean;
    showCriticalTrackingOnly: boolean;
  };
}

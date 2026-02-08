export interface TimeSlot {
  start: number; // 24-hour format (e.g., 9 for 9 AM, 13 for 1 PM)
  end: number;
}

export interface MeetTime {
  meetNo?: number;
  meetDays: string[]; // ['M', 'W', 'F'] or ['T', 'Th']
  meetTimeBegin?: string;
  meetTimeEnd?: string;
  meetPeriodBegin?: string | number;
  meetPeriodEnd?: string | number;
  meetBuilding?: string;
  meetBldgCode?: string;
  meetRoom?: string;
}

export interface Course {
  id?: string;
  code: string; // e.g., "COP3503C"
  name: string;
  classNum?: number; // unique section identifier e.g., 10537
  section?: string; // section number
  instructors?: string[];
  instructor?: string; // single instructor (legacy format)
  credits: number;
  meetDays?: string[]; // ['M', 'W', 'F'] or ['T', 'Th']
  meetPeriod?: TimeSlot; // legacy format
  meetTimes?: MeetTime[]; // new format
  enrollmentCap?: number;
  enrollmentActual?: number;
  isCriticalTracking?: boolean;
  isAISuggested?: boolean;
  dept?: string;
  color?: string;
  // Legacy fields for backward compatibility
  courseCode?: string;
  courseName?: string;
}

// Legacy Course interface (kept for compatibility)
export interface CourseOld {
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

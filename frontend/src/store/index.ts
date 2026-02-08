import { create } from 'zustand';
import { Schedule, ChatMessage, UIState, Course } from '../types/index';
import { detectConflicts } from '../utils/conflict';

interface ScheduleStore extends UIState {
  // Schedule actions
  setSelectedSchedule: (schedule: Schedule | null) => void;
  updateSchedule: (courses: Course[]) => void;
  setSelectedMajor: (major: string) => void;
  setSelectedCourse: (course: Course | null) => void;
  setLoadingSchedule: (isLoading: boolean) => void;
  
  // Filter actions
  toggleConflictFilter: () => void;
  toggleCriticalTrackingFilter: () => void;
  
  // Chat
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  
  // Get computed values
  getConflicts: () => ReturnType<typeof detectConflicts>;
  getScheduleStats: () => {
    totalCredits: number;
    totalCourses: number;
    conflictCount: number;
    criticalTrackingCourses: number;
  };
}

export const useScheduleStore = create<ScheduleStore>((set, get) => ({
  selectedMajor: '',
  selectedSchedule: null,
  selectedCourse: null,
  isLoadingSchedule: false,
  messages: [],
  filters: {
    showConflictsOnly: false,
    showCriticalTrackingOnly: false,
  },

  setSelectedSchedule: (schedule) =>
    set({ selectedSchedule: schedule }),

  updateSchedule: (courses) =>
    set((state) => ({
      selectedSchedule: state.selectedSchedule
        ? { ...state.selectedSchedule, courses }
        : null,
    })),

  setSelectedMajor: (major) =>
    set({ selectedMajor: major }),

  setSelectedCourse: (course) =>
    set({ selectedCourse: course }),

  setLoadingSchedule: (isLoading) =>
    set({ isLoadingSchedule: isLoading }),

  toggleConflictFilter: () =>
    set((state) => ({
      filters: {
        ...state.filters,
        showConflictsOnly: !state.filters.showConflictsOnly,
      },
    })),

  toggleCriticalTrackingFilter: () =>
    set((state) => ({
      filters: {
        ...state.filters,
        showCriticalTrackingOnly: !state.filters.showCriticalTrackingOnly,
      },
    })),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  clearMessages: () =>
    set({ messages: [] }),

  getConflicts: () => {
    const state = get();
    return state.selectedSchedule ? detectConflicts(state.selectedSchedule.courses) : [];
  },

  getScheduleStats: () => {
    const state = get();
    if (!state.selectedSchedule) {
      return { totalCredits: 0, totalCourses: 0, conflictCount: 0, criticalTrackingCourses: 0 };
    }

    const { courses } = state.selectedSchedule;
    const totalCredits = courses.reduce((sum, course) => sum + course.credits, 0);
    const totalCourses = courses.length;
    const conflicts = detectConflicts(courses);
    const criticalTrackingCourses = courses.filter(c => c.isCriticalTracking).length;

    return {
      totalCredits,
      totalCourses,
      conflictCount: conflicts.length,
      criticalTrackingCourses,
    };
  },
}));

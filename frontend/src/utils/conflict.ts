import { Course, ConflictInfo, Schedule } from '../types/index';

const DAYS_ORDER = ['M', 'T', 'W', 'Th', 'F'];

export function detectConflicts(courses: Course[]): ConflictInfo[] {
  const conflicts: ConflictInfo[] = [];

  for (let i = 0; i < courses.length; i++) {
    for (let j = i + 1; j < courses.length; j++) {
      const courseA = courses[i];
      const courseB = courses[j];

      // Find common meeting days
      const commonDays = courseA.meetDays.filter(day =>
        courseB.meetDays.includes(day)
      );

      if (commonDays.length === 0) {
        continue; // No common days, no conflict
      }

      // Check for time overlap
      const hasTimeOverlap =
        courseA.meetPeriod.start < courseB.meetPeriod.end &&
        courseA.meetPeriod.end > courseB.meetPeriod.start;

      if (hasTimeOverlap) {
        const overlapStart = Math.max(courseA.meetPeriod.start, courseB.meetPeriod.start);
        const overlapEnd = Math.min(courseA.meetPeriod.end, courseB.meetPeriod.end);

        conflicts.push({
          courseA,
          courseB,
          conflictingDays: commonDays,
          conflictingTimes: {
            start: overlapStart,
            end: overlapEnd,
          },
        });
      }
    }
  }

  return conflicts;
}

export function courseHasConflict(course: Course, conflicts: ConflictInfo[]): boolean {
  return conflicts.some(
    conflict =>
      conflict.courseA.courseCode === course.courseCode ||
      conflict.courseB.courseCode === course.courseCode
  );
}

export function getConflictsForCourse(
  course: Course,
  conflicts: ConflictInfo[]
): ConflictInfo[] {
  return conflicts.filter(
    conflict =>
      conflict.courseA.courseCode === course.courseCode ||
      conflict.courseB.courseCode === course.courseCode
  );
}

// Color palette for courses - ensures variety across all courses
const courseColors = [
  { bg: 'bg-blue-100 dark:bg-blue-900/40', border: 'border-blue-400 dark:border-blue-600', text: 'text-blue-900 dark:text-blue-200' },
  { bg: 'bg-orange-100 dark:bg-orange-900/40', border: 'border-orange-400 dark:border-orange-600', text: 'text-orange-900 dark:text-orange-200' },
  { bg: 'bg-purple-100 dark:bg-purple-900/40', border: 'border-purple-400 dark:border-purple-600', text: 'text-purple-900 dark:text-purple-200' },
  { bg: 'bg-green-100 dark:bg-green-900/40', border: 'border-green-400 dark:border-green-600', text: 'text-green-900 dark:text-green-200' },
  { bg: 'bg-pink-100 dark:bg-pink-900/40', border: 'border-pink-400 dark:border-pink-600', text: 'text-pink-900 dark:text-pink-200' },
  { bg: 'bg-indigo-100 dark:bg-indigo-900/40', border: 'border-indigo-400 dark:border-indigo-600', text: 'text-indigo-900 dark:text-indigo-200' },
  { bg: 'bg-teal-100 dark:bg-teal-900/40', border: 'border-teal-400 dark:border-teal-600', text: 'text-teal-900 dark:text-teal-200' },
  { bg: 'bg-cyan-100 dark:bg-cyan-900/40', border: 'border-cyan-400 dark:border-cyan-600', text: 'text-cyan-900 dark:text-cyan-200' },
];

const colorMap = new Map<string, { bg: string; border: string; text: string }>();

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

export function getCourseColor(
  courseCode: string
): { bg: string; border: string; text: string } {
  if (colorMap.has(courseCode)) {
    return colorMap.get(courseCode)!;
  }

  const index = hashCode(courseCode) % courseColors.length;
  const color = courseColors[index];
  colorMap.set(courseCode, color);
  return color;
}

export function formatTime(hour: number): string {
  if (hour === 0) return '12 AM';
  if (hour < 12) return `${hour} AM`;
  if (hour === 12) return '12 PM';
  return `${hour - 12} PM`;
}

export function getDayNumber(day: string): number {
  return DAYS_ORDER.indexOf(day);
}

export function getScheduleStats(schedule: Schedule) {
  const totalCredits = schedule.courses.reduce((sum, course) => sum + course.credits, 0);
  const totalCourses = schedule.courses.length;
  const conflicts = detectConflicts(schedule.courses);
  const criticalTrackingCourses = schedule.courses.filter(c => c.isCriticalTracking).length;

  return {
    totalCredits,
    totalCourses,
    conflictCount: conflicts.length,
    criticalTrackingCourses,
  };
}

export function calculateGridPosition(meetDays: string[], meetPeriod: any) {
  // This helps calculate the CSS grid position for a course block
  const startDay = meetDays[0];
  const dayIndex = getDayNumber(startDay);

  // Convert hour to grid row (7 AM = row 0)
  const startRow = meetPeriod.start - 7;
  const duration = meetPeriod.end - meetPeriod.start;

  return {
    dayIndex,
    startRow,
    duration,
  };
}

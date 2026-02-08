import { Course, ConflictInfo, Schedule } from '../types/index';

const DAYS_ORDER = ['M', 'T', 'W', 'Th', 'F'];

// Convert time string like "1:55 PM" to decimal hours (1.916... for 1:55)
function timeStringToDecimal(timeStr: string): number {
  if (!timeStr) return NaN;
  const match = timeStr.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i);
  if (!match) return NaN;
  
  let hours = parseInt(match[1], 10);
  const minutes = parseInt(match[2], 10);
  const period = match[3]?.toUpperCase();
  
  if (period === 'PM' && hours !== 12) hours += 12;
  if (period === 'AM' && hours === 12) hours = 0;
  
  return hours + minutes / 60;
}

// Get time range in decimal hours for a course
function getTimeRange(course: Course): { start: number; end: number } | null {
  // If course has detailed meetTimes, use the first one
  if (course.meetTimes && course.meetTimes.length > 0) {
    const meetTime = course.meetTimes[0];
    const start = timeStringToDecimal(meetTime.meetTimeBegin || '');
    const end = timeStringToDecimal(meetTime.meetTimeEnd || '');
    
    if (!isNaN(start) && !isNaN(end)) {
      return { start, end };
    }
  }
  
  // Fall back to meetPeriod if available
  if (course.meetPeriod) {
    return {
      start: typeof course.meetPeriod.start === 'number' ? course.meetPeriod.start : NaN,
      end: typeof course.meetPeriod.end === 'number' ? course.meetPeriod.end : NaN,
    };
  }
  
  return null;
}

// Get all meeting days for a course
function getMeetingDays(course: Course): string[] {
  // If course has detailed meetTimes, aggregate all days
  if (course.meetTimes && course.meetTimes.length > 0) {
    const allDays = new Set<string>();
    for (const meetTime of course.meetTimes) {
      if (meetTime.meetDays) {
        meetTime.meetDays.forEach(day => allDays.add(day));
      }
    }
    if (allDays.size > 0) return Array.from(allDays);
  }
  
  // Fall back to meetDays
  return course.meetDays || [];
}

export function detectConflicts(courses: Course[]): ConflictInfo[] {
  const conflicts: ConflictInfo[] = [];

  for (let i = 0; i < courses.length; i++) {
    for (let j = i + 1; j < courses.length; j++) {
      const courseA = courses[i];
      const courseB = courses[j];

      // Check if we need to use meetTimes (detailed) or fall back to legacy format
      const hasDetailedTimes = 
        (courseA.meetTimes && courseA.meetTimes.length > 0) ||
        (courseB.meetTimes && courseB.meetTimes.length > 0);

      if (hasDetailedTimes) {
        // Use detailed meetTimes for comparison
        const meetTimesA = courseA.meetTimes || [];
        const meetTimesB = courseB.meetTimes || [];

        if (meetTimesA.length === 0 || meetTimesB.length === 0) {
          continue; // Can't compare
        }

        // Check all combinations of meetTimes
        let foundConflict = false;
        for (const meetA of meetTimesA) {
          if (foundConflict) break;
          for (const meetB of meetTimesB) {
            const daysA = meetA.meetDays || [];
            const daysB = meetB.meetDays || [];

            if (daysA.length === 0 || daysB.length === 0) {
              continue;
            }

            // Find common meeting days
            const commonDays = daysA.filter(day => daysB.includes(day));
            if (commonDays.length === 0) {
              continue; // No common days for this meetTime pair
            }

            // Parse times
            const startA = timeStringToDecimal(meetA.meetTimeBegin || '');
            const endA = timeStringToDecimal(meetA.meetTimeEnd || '');
            const startB = timeStringToDecimal(meetB.meetTimeBegin || '');
            const endB = timeStringToDecimal(meetB.meetTimeEnd || '');

            if (isNaN(startA) || isNaN(endA) || isNaN(startB) || isNaN(endB)) {
              continue; // Can't parse times
            }

            // Check for time overlap
            const hasTimeOverlap = startA < endB && endA > startB;

            if (hasTimeOverlap) {
              const overlapStart = Math.max(startA, startB);
              const overlapEnd = Math.min(endA, endB);

              conflicts.push({
                courseA,
                courseB,
                conflictingDays: commonDays,
                conflictingTimes: {
                  start: overlapStart,
                  end: overlapEnd,
                },
              });
              
              // Found a conflict for this pair, break both loops
              foundConflict = true;
              break;
            }
          }
        }
      } else {
        // Fall back to legacy meetPeriod/meetDays format
        const daysA = getMeetingDays(courseA);
        const daysB = getMeetingDays(courseB);
        
        if (daysA.length === 0 || daysB.length === 0) {
          continue;
        }

        const commonDays = daysA.filter(day => daysB.includes(day));
        if (commonDays.length === 0) {
          continue;
        }

        const timeRangeA = getTimeRange(courseA);
        const timeRangeB = getTimeRange(courseB);
        
        if (!timeRangeA || !timeRangeB || isNaN(timeRangeA.start) || isNaN(timeRangeB.start)) {
          continue;
        }

        const hasTimeOverlap =
          timeRangeA.start < timeRangeB.end &&
          timeRangeA.end > timeRangeB.start;

        if (hasTimeOverlap) {
          const overlapStart = Math.max(timeRangeA.start, timeRangeB.start);
          const overlapEnd = Math.min(timeRangeA.end, timeRangeB.end);

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
  if (!str) return 0; // Handle undefined/null
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
  if (!courseCode) {
    // Default color if courseCode is undefined
    return courseColors[0];
  }
  
  if (colorMap.has(courseCode)) {
    return colorMap.get(courseCode)!;
  }

  const index = hashCode(courseCode) % courseColors.length;
  const color = courseColors[index];
  colorMap.set(courseCode, color);
  return color;
}

export function formatTime(hour: number): string {
  // Handle fractional hours (e.g., 10.67 for 10:40)
  const wholeHour = Math.floor(hour);
  const minutes = Math.round((hour - wholeHour) * 60);
  
  let displayHour = wholeHour;
  let period = 'AM';
  
  if (wholeHour === 0) {
    displayHour = 12;
  } else if (wholeHour === 12) {
    period = 'PM';
  } else if (wholeHour > 12) {
    displayHour = wholeHour - 12;
    period = 'PM';
  }
  
  if (minutes === 0) {
    return `${displayHour} ${period}`;
  }
  return `${displayHour}:${minutes.toString().padStart(2, '0')} ${period}`;
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

import React, { useMemo } from 'react';
import { Schedule } from '../types/index';
import { detectConflicts, formatTime } from '../utils/conflict';

interface CalendarProps {
  schedule: Schedule | null;
  selectedCourse: any;
  onCourseSelect: (course: any) => void;
}

const DAYS_SHORT = ['M', 'T', 'W', 'Th', 'F'];
const DAYS_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const START_HOUR = 7; 
const END_HOUR = 20; 

export const Calendar: React.FC<CalendarProps> = ({
  schedule,
  selectedCourse,
  onCourseSelect,
}) => {
  const conflicts = useMemo(() => {
    return schedule ? detectConflicts(schedule.courses) : [];
  }, [schedule]);

  const hoursArray = Array.from(
    { length: END_HOUR - START_HOUR + 1 },
    (_, i) => START_HOUR + i
  );

  if (!schedule || schedule.courses.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-white dark:bg-gray-800 rounded-lg border-2 border-dashed border-gator-gray-300 dark:border-gray-600">
        <div className="text-center">
          <div className="text-gator-gray-400 dark:text-gray-600 text-4xl mb-4">📅</div>
          <p className="text-gator-gray-600 dark:text-gray-400 text-lg">No schedule loaded</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-gator border border-gator-gray-200 dark:border-gray-700 overflow-hidden flex flex-col min-w-[640px] sm:min-w-[720px] lg:min-w-[800px]">
      {/* Header */}
      <div className="grid grid-cols-[72px_repeat(5,minmax(120px,1fr))] sm:grid-cols-[90px_repeat(5,minmax(140px,1fr))] lg:grid-cols-[100px_repeat(5,1fr)] bg-gator-dark dark:bg-gray-900 text-white border-b border-gator-gray-200 dark:border-gray-700">
        <div className="p-3 sm:p-4 font-semibold border-r border-white/10">Time</div>
        {DAYS_FULL.map((day) => (
          <div key={day} className="p-3 sm:p-4 font-semibold text-center border-r border-white/10 last:border-0">
            {day}
          </div>
        ))}
      </div>

      {/* Main Grid Area */}
      <div className="relative">
        <div 
          className="grid grid-cols-[72px_repeat(5,minmax(120px,1fr))] sm:grid-cols-[90px_repeat(5,minmax(140px,1fr))] lg:grid-cols-[100px_repeat(5,1fr)]"
          style={{ 
            gridTemplateRows: `repeat(${(END_HOUR - START_HOUR + 1)}, 64px)`,
            display: 'grid' 
          }}
        >
          {/* 1. RENDER TIME LABELS (Locked to Column 1) */}
          {hoursArray.map((hour, idx) => (
            <div 
              key={`time-${hour}`}
              className="sticky left-0 z-30 bg-gator-gray-50 dark:bg-gray-900 p-2 sm:p-3 font-semibold text-[11px] sm:text-xs text-gator-gray-600 dark:text-gray-400 border-r border-b border-gator-gray-200 dark:border-gray-700 flex items-start justify-center"
              style={{ gridColumn: 1, gridRow: idx + 1 }}
            >
              {formatTime(hour)}
            </div>
          ))}

          {/* 2. RENDER EMPTY CELLS (Background Grid) */}
          {hoursArray.map((_, rowIdx) => (
            DAYS_SHORT.map((_, colIdx) => (
              <div 
                key={`cell-${rowIdx}-${colIdx}`}
                className="border-r border-b border-gator-gray-200 dark:border-gray-700 last:border-r-0"
                style={{ gridColumn: colIdx + 2, gridRow: rowIdx + 1 }}
              />
            ))
          ))}

          {/* 3. RENDER COURSES (Overlayed on the grid) */}
          {schedule.courses.map((course) => {
            // Use meetTimes if available, otherwise fall back to meetDays/meetPeriod
            if (course.meetTimes && course.meetTimes.length > 0) {
              // Render each meeting time separately
              return course.meetTimes.map((meetTime, meetTimeIdx) => {
                return meetTime.meetDays?.map((dayLetter) => {
                  const dayIndex = DAYS_SHORT.indexOf(dayLetter === 'R' ? 'Th' : dayLetter);
                  if (dayIndex === -1) return null;

                  // Parse times from meetTime
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

                  const startTime = parseTime(meetTime.meetTimeBegin || '8:00 AM');
                  const endTime = parseTime(meetTime.meetTimeEnd || '9:00 AM');

                  const startRow = Math.floor(startTime - START_HOUR) + 1;
                  const rowSpan = Math.ceil(endTime - startTime);

                  const hasConflict = conflicts.some(
                    (c) =>
                      (c.courseA.courseCode === course.courseCode ||
                        c.courseB.courseCode === course.courseCode) &&
                      c.conflictingDays.includes(dayLetter)
                  );

                  return (
                    <div
                      key={`${course.courseCode}-${dayLetter}-${meetTimeIdx}`}
                      onClick={() => onCourseSelect(course)}
                      className={`
                        z-10 m-1 p-2 rounded border-2 cursor-pointer transition-all overflow-hidden
                        ${hasConflict ? 'border-red-500' : ''}
                        ${selectedCourse?.courseCode === course.courseCode ? 'ring-2 ring-offset-2 ring-gator-dark' : ''}
                        hover:shadow-lg
                      `}
                      style={{
                        gridColumn: dayIndex + 2,
                        gridRow: `${startRow} / span ${rowSpan}`,
                        backgroundColor: course.color || '#1976d2',
                      }}
                      title={`${course.courseCode} - ${dayLetter} ${meetTime.meetTimeBegin}-${meetTime.meetTimeEnd}`}
                    >
                      <div className="text-xs font-bold text-white truncate">{course.courseCode}</div>
                      <div className="text-xs text-white/90 truncate">{formatTime(startTime)}</div>
                    </div>
                  );
                }) as any;
              });
            } else {
              // Fallback to legacy meetDays/meetPeriod
              return course.meetDays?.map((dayLetter) => {
                const dayIndex = DAYS_SHORT.indexOf(dayLetter);
                if (dayIndex === -1) return null;

                // Check if meetPeriod is defined
                if (!course.meetPeriod) return null;

                // Convert fractional hours to grid rows
                // Round start time down, end time up for better positioning
                const startRow = Math.floor(course.meetPeriod.start - START_HOUR) + 1;
                const rowSpan = Math.ceil(course.meetPeriod.end - course.meetPeriod.start);

                const hasConflict = conflicts.some(
                  (c) =>
                    (c.courseA.courseCode === course.courseCode ||
                      c.courseB.courseCode === course.courseCode) &&
                    c.conflictingDays.includes(dayLetter)
                );

                return (
                  <div
                    key={`${course.courseCode}-${dayLetter}`}
                    onClick={() => onCourseSelect(course)}
                    className={`
                      z-10 m-1 p-2 rounded border-2 cursor-pointer transition-all overflow-hidden
                      ${hasConflict ? 'border-red-500' : ''}
                      ${selectedCourse?.courseCode === course.courseCode ? 'ring-2 ring-offset-2 ring-gator-dark' : ''}
                      hover:shadow-lg
                    `}
                    style={{
                      gridColumn: dayIndex + 2,
                      gridRow: `${startRow} / span ${rowSpan}`,
                      backgroundColor: course.color || '#1976d2',
                    }}
                    title={`${course.courseCode} - ${dayLetter} ${formatTime(course.meetPeriod.start)}-${formatTime(course.meetPeriod.end)}`}
                  >
                    <div className="text-xs font-bold text-white truncate">{course.courseCode}</div>
                    <div className="text-xs text-white/90 truncate">{formatTime(course.meetPeriod.start)}</div>
                  </div>
                );
              });
            }
          })}
        </div>
      </div>
    </div>
  );
};
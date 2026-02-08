import React from 'react';
import { Course, ConflictInfo } from '../types/index';
import { getCourseColor, getConflictsForCourse, formatTime } from '../utils/conflict';
import { AlertCircle, Award, X } from 'lucide-react';

interface CourseCardProps {
  course: Course;
  isSelected?: boolean;
  conflicts?: ConflictInfo[];
  onClick?: () => void;
  onDelete?: (course: Course) => void;
  variant?: 'compact' | 'detailed';
}

export const CourseCard: React.FC<CourseCardProps> = ({
  course,
  isSelected = false,
  conflicts = [],
  onClick,
  onDelete,
  variant = 'detailed',
}) => {
  const courseCodeForColor = course.courseCode || course.code || 'UNKNOWN';
  const color = getCourseColor(courseCodeForColor);
  const courseConflicts = getConflictsForCourse(course, conflicts);
  const hasConflict = courseConflicts.length > 0;

  if (variant === 'compact') {
    return (
      <div
        onClick={onClick}
        className={`
          p-2 rounded border-2 cursor-pointer transition-all
          ${color.bg} ${color.border} 
          ${hasConflict ? 'border-red-500 shadow-md' : `${color.border}`}
          ${isSelected ? 'ring-2 ring-offset-2 ring-gator-dark' : ''}
          hover:shadow-lg
        `}
      >
        <div className={`text-xs font-semibold ${color.text} truncate`}>
          {course.courseCode}
        </div>
        <div className="text-xs text-gray-600 dark:text-gray-400 truncate">{course.courseName}</div>
        {hasConflict && (
          <div className="mt-1 text-red-500 text-xs font-semibold flex items-center gap-1">
            <AlertCircle size={12} />
            Conflict
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className={`
        ${color.bg} rounded-lg border-2 p-4 cursor-pointer transition-all
        ${hasConflict ? 'border-red-500 shadow-gator-lg' : `${color.border} shadow-gator`}
        ${isSelected ? 'ring-2 ring-offset-2 ring-gator-dark' : ''}
        hover:shadow-gator-lg
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className={`font-bold ${color.text} text-lg`}>
            {course.courseCode}
          </h3>
          <p className="text-sm text-gray-700 dark:text-gray-300">{course.courseName}</p>
        </div>
        <div className="flex gap-1 items-start">
          {course.isCriticalTracking && (
            <div
              title="Critical Tracking Course"
              className="bg-yellow-400 dark:bg-yellow-500 text-yellow-900 dark:text-yellow-950 px-2 py-1 rounded text-xs font-bold"
            >
              CRITICAL
            </div>
          )}
          {course.isAISuggested && (
            <div title="AI Suggested" className="bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300 p-1 rounded">
              <Award size={16} />
            </div>
          )}
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(course);
              }}
              className="p-1 hover:bg-red-100 dark:hover:bg-red-900/50 rounded transition-colors text-red-600 dark:text-red-400"
              title="Remove course"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between mb-3 pb-3 border-b border-gray-300 dark:border-gray-600">
          <span className="font-semibold text-gray-700 dark:text-gray-300">Credits:</span>
          <span className="text-gray-900 dark:text-gray-100">{course.credits}</span>
        </div>

        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-300">Instructor:</span>
          <p className="text-gray-900 dark:text-gray-100">{course.instructor}</p>
        </div>

        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-300">Schedule:</span>
          <div className="text-gray-900 dark:text-gray-100 space-y-1">
            {course.meetTimes && course.meetTimes.length > 0 ? (
              course.meetTimes.map((meetTime, idx) => {
                const days = meetTime.meetDays?.map(day => day === 'R' ? 'Th' : day).join(', ') || 'TBA';
                const timeBegin = meetTime.meetTimeBegin || '';
                const timeEnd = meetTime.meetTimeEnd || '';
                return (
                  <div key={idx}>
                    {days} {timeBegin && timeEnd ? `${timeBegin} - ${timeEnd}` : ''}
                  </div>
                );
              })
            ) : (
              <div>
                {course.meetDays?.join(', ') || 'TBA'} {course.meetPeriod ? `${formatTime(course.meetPeriod.start)} - ${formatTime(course.meetPeriod.end)}` : ''}
              </div>
            )}
          </div>
        </div>

        <div className="text-xs text-gray-600 dark:text-gray-400">
          <span>Section: {course.section}</span>
        </div>
      </div>

      {hasConflict && (
        <div className="mt-4 p-2 bg-red-100 dark:bg-red-900/50 border border-red-300 dark:border-red-700 rounded flex items-center gap-2">
          <AlertCircle size={18} className="text-red-600 dark:text-red-400" />
          <div className="text-sm text-red-800 dark:text-red-300 font-semibold">
            {courseConflicts.length} time conflict{courseConflicts.length !== 1 ? 's' : ''}
          </div>
        </div>
      )}
    </div>
  );
};

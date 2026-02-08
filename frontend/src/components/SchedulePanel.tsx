import React from 'react';
import { Schedule, Course } from '../types/index';
import { CourseCard } from './CourseCard';
import { detectConflicts } from '../utils/conflict';
import { BookOpen, AlertTriangle, Trophy, Clock } from 'lucide-react';

interface SchedulePanelProps {
  schedule: Schedule | null;
  selectedCourse: Course | null;
  onCourseSelect: (course: Course) => void;
  showConflictsOnly?: boolean;
  showCriticalTrackingOnly?: boolean;
  onToggleConflictFilter?: () => void;
  onToggleCriticalTrackingFilter?: () => void;
}

export const SchedulePanel: React.FC<SchedulePanelProps> = ({
  schedule,
  selectedCourse,
  onCourseSelect,
  showConflictsOnly = false,
  showCriticalTrackingOnly = false,
  onToggleConflictFilter,
  onToggleCriticalTrackingFilter,
}) => {
  const conflicts = React.useMemo(() => {
    return schedule ? detectConflicts(schedule.courses) : [];
  }, [schedule]);

  const coursesWithConflicts = React.useMemo(() => {
    return conflicts.flatMap((c) => [c.courseA, c.courseB]);
  }, [conflicts]);

  const filteredCourses = React.useMemo(() => {
    if (!schedule) return [];

    let courses = [...schedule.courses];

    if (showConflictsOnly) {
      courses = courses.filter((c) =>
        coursesWithConflicts.some((cc) => cc.courseCode === c.courseCode)
      );
    }

    if (showCriticalTrackingOnly) {
      courses = courses.filter((c) => c.isCriticalTracking);
    }

    return courses;
  }, [schedule, showConflictsOnly, showCriticalTrackingOnly, coursesWithConflicts]);

  if (!schedule) {
    return (
      <div className="flex items-center justify-center h-96 bg-white dark:bg-gray-800 rounded-lg border-2 border-dashed border-gator-gray-300 dark:border-gray-600">
        <div className="text-center">
          <BookOpen size={48} className="text-gator-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gator-gray-600 dark:text-gray-400 text-lg font-semibold">No Schedule Loaded</p>
          <p className="text-gator-gray-400 dark:text-gray-500 text-sm">Generate a schedule from the chat to view courses</p>
        </div>
      </div>
    );
  }

  const totalCredits = schedule.courses.reduce((sum, c) => sum + c.credits, 0);
  const criticalTrackingCourses = schedule.courses.filter((c) => c.isCriticalTracking).length;

  return (
    <div className="space-y-4">
      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border-2 border-blue-200 dark:border-blue-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={20} className="text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-semibold text-blue-900 dark:text-blue-300">Total Credits</span>
          </div>
          <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{totalCredits}</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 border-2 border-purple-200 dark:border-purple-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen size={20} className="text-purple-600 dark:text-purple-400" />
            <span className="text-sm font-semibold text-purple-900 dark:text-purple-300">Courses</span>
          </div>
          <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{schedule.courses.length}</p>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 border-2 border-red-200 dark:border-red-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={20} className="text-red-600 dark:text-red-400" />
            <span className="text-sm font-semibold text-red-900 dark:text-red-300">Conflicts</span>
          </div>
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">{conflicts.length}</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/30 dark:to-yellow-800/30 border-2 border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Trophy size={20} className="text-yellow-600 dark:text-yellow-400" />
            <span className="text-sm font-semibold text-yellow-900 dark:text-yellow-300">Critical</span>
          </div>
          <p className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">{criticalTrackingCourses}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={onToggleConflictFilter}
          className={`px-4 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
            showConflictsOnly
              ? 'bg-red-500 text-white shadow-md'
              : 'bg-gator-gray-200 dark:bg-gray-700 text-gator-gray-700 dark:text-gray-300 hover:bg-gator-gray-300 dark:hover:bg-gray-600'
          }`}
        >
          <AlertTriangle size={16} />
          Show Conflicts Only
        </button>

        <button
          onClick={onToggleCriticalTrackingFilter}
          className={`px-4 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 ${
            showCriticalTrackingOnly
              ? 'bg-yellow-500 text-white shadow-md'
              : 'bg-gator-gray-200 dark:bg-gray-700 text-gator-gray-700 dark:text-gray-300 hover:bg-gator-gray-300 dark:hover:bg-gray-600'
          }`}
        >
          <Trophy size={16} />
          Show Critical Only
        </button>
      </div>

      {/* Courses List */}
      <div className="space-y-3">
        {filteredCourses.length === 0 ? (
          <div className="text-center py-8 bg-gator-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gator-gray-300 dark:border-gray-700">
            <p className="text-gator-gray-600 dark:text-gray-400 font-semibold">No courses match the filters</p>
          </div>
        ) : (
          filteredCourses.map((course) => (
            <CourseCard
              key={course.courseCode}
              course={course}
              isSelected={selectedCourse?.courseCode === course.courseCode}
              conflicts={conflicts}
              onClick={() => onCourseSelect(course)}
              variant="detailed"
            />
          ))
        )}
      </div>

      {/* Semester Info */}
      {schedule.isCriticalTrackingSchedule && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border-2 border-blue-300 dark:border-blue-700 rounded-lg p-4">
          <p className="text-sm text-blue-900 dark:text-blue-300">
            <span className="font-semibold">📍 Critical Tracking Schedule:</span> This schedule follows UF's critical tracking requirements for {schedule.majorCode}.
          </p>
        </div>
      )}

      {schedule.isOptimized && (
        <div className="bg-green-50 dark:bg-green-900/30 border-2 border-green-300 dark:border-green-700 rounded-lg p-4">
          <p className="text-sm text-green-900 dark:text-green-300">
            <span className="font-semibold">✨ Optimized:</span> This schedule has been optimized for your preferences.
          </p>
        </div>
      )}
    </div>
  );
};

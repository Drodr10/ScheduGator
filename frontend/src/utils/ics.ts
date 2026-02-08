import { Schedule, Course, MeetTime } from '../types/index';

interface IcsOptions {
  startDate: Date;
  endDate: Date;
  calendarName?: string;
  timezone?: string;
}

const DEFAULT_TZ = 'America/New_York';

const pad2 = (value: number): string => String(value).padStart(2, '0');

const formatDate = (date: Date): string => {
  return `${date.getFullYear()}${pad2(date.getMonth() + 1)}${pad2(date.getDate())}`;
};

const formatDateTimeLocal = (date: Date): string => {
  return `${formatDate(date)}T${pad2(date.getHours())}${pad2(date.getMinutes())}${pad2(date.getSeconds())}`;
};

const parseTime = (timeStr?: string): { hour: number; minute: number } | null => {
  if (!timeStr) return null;
  const match = timeStr.trim().match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (!match) return null;
  let hour = parseInt(match[1], 10);
  const minute = parseInt(match[2], 10);
  const period = match[3].toUpperCase();
  if (period === 'PM' && hour !== 12) hour += 12;
  if (period === 'AM' && hour === 12) hour = 0;
  return { hour, minute };
};

const timeFromFloat = (value: number): { hour: number; minute: number } => {
  const hour = Math.floor(value);
  const minute = Math.round((value - hour) * 60);
  return { hour, minute };
};

const dayToByDay = (day: string): string | null => {
  const normalized = day.trim();
  if (normalized === 'M') return 'MO';
  if (normalized === 'T') return 'TU';
  if (normalized === 'W') return 'WE';
  if (normalized === 'R' || normalized === 'Th' || normalized === 'TH') return 'TH';
  if (normalized === 'F') return 'FR';
  return null;
};

const dayToIndex = (byDay: string): number => {
  if (byDay === 'MO') return 1;
  if (byDay === 'TU') return 2;
  if (byDay === 'WE') return 3;
  if (byDay === 'TH') return 4;
  if (byDay === 'FR') return 5;
  return 1;
};

const firstDateForByDay = (startDate: Date, byDay: string): Date => {
  const start = new Date(startDate);
  start.setHours(0, 0, 0, 0);
  const startDay = start.getDay();
  const targetDay = dayToIndex(byDay);
  const diff = (targetDay - startDay + 7) % 7;
  const first = new Date(start);
  first.setDate(start.getDate() + diff);
  return first;
};

const buildEvent = (data: {
  uid: string;
  summary: string;
  location?: string;
  description?: string;
  start: Date;
  end: Date;
  byDays: string[];
  timezone: string;
  until: Date;
}): string[] => {
  const until = new Date(data.until);
  until.setHours(23, 59, 59, 0);

  const lines = [
    'BEGIN:VEVENT',
    `UID:${data.uid}`,
    `SUMMARY:${data.summary}`,
    `DTSTART;TZID=${data.timezone}:${formatDateTimeLocal(data.start)}`,
    `DTEND;TZID=${data.timezone}:${formatDateTimeLocal(data.end)}`,
    `RRULE:FREQ=WEEKLY;BYDAY=${data.byDays.join(',')};UNTIL=${formatDateTimeLocal(until)}`,
  ];

  if (data.location) {
    lines.push(`LOCATION:${data.location}`);
  }
  if (data.description) {
    lines.push(`DESCRIPTION:${data.description}`);
  }

  lines.push('END:VEVENT');
  return lines;
};

const buildEventsForMeetTime = (
  course: Course,
  meetTime: MeetTime,
  eventIndex: number,
  options: IcsOptions
): string[] => {
  const timeStart = parseTime(meetTime.meetTimeBegin);
  const timeEnd = parseTime(meetTime.meetTimeEnd);
  if (!timeStart || !timeEnd || !meetTime.meetDays || meetTime.meetDays.length === 0) {
    return [];
  }

  const byDays = meetTime.meetDays
    .map(dayToByDay)
    .filter((day): day is string => Boolean(day));
  if (byDays.length === 0) {
    return [];
  }

  const firstDates = byDays.map((day) => firstDateForByDay(options.startDate, day));
  const firstDate = new Date(Math.min(...firstDates.map((d) => d.getTime())));

  const start = new Date(firstDate);
  start.setHours(timeStart.hour, timeStart.minute, 0, 0);

  const end = new Date(firstDate);
  end.setHours(timeEnd.hour, timeEnd.minute, 0, 0);

  const summary = `${course.courseCode || course.code} - ${course.courseName || course.name}`;
  const instructors = course.instructors?.length
    ? course.instructors.join(', ')
    : course.instructor || 'TBA';
  const location = meetTime.meetBuilding && meetTime.meetRoom
    ? `${meetTime.meetBuilding} ${meetTime.meetRoom}`
    : undefined;

  return buildEvent({
    uid: `${course.code || course.courseCode}-${course.classNum || course.section}-${eventIndex}@schedugator`,
    summary,
    location,
    description: `Instructor: ${instructors}`,
    start,
    end,
    byDays,
    timezone: options.timezone || DEFAULT_TZ,
    until: options.endDate,
  });
};

const buildEventsForLegacy = (
  course: Course,
  options: IcsOptions
): string[] => {
  if (!course.meetDays || course.meetDays.length === 0 || !course.meetPeriod) {
    return [];
  }

  const byDays = course.meetDays
    .map(dayToByDay)
    .filter((day): day is string => Boolean(day));
  if (byDays.length === 0) {
    return [];
  }

  const firstDates = byDays.map((day) => firstDateForByDay(options.startDate, day));
  const firstDate = new Date(Math.min(...firstDates.map((d) => d.getTime())));

  const startTime = timeFromFloat(course.meetPeriod.start);
  const endTime = timeFromFloat(course.meetPeriod.end);

  const start = new Date(firstDate);
  start.setHours(startTime.hour, startTime.minute, 0, 0);

  const end = new Date(firstDate);
  end.setHours(endTime.hour, endTime.minute, 0, 0);

  const summary = `${course.courseCode || course.code} - ${course.courseName || course.name}`;
  const instructors = course.instructors?.length
    ? course.instructors.join(', ')
    : course.instructor || 'TBA';

  return buildEvent({
    uid: `${course.code || course.courseCode}-${course.classNum || course.section}-legacy@schedugator`,
    summary,
    description: `Instructor: ${instructors}`,
    start,
    end,
    byDays,
    timezone: options.timezone || DEFAULT_TZ,
    until: options.endDate,
  });
};

export const buildIcs = (schedule: Schedule, options: IcsOptions): string => {
  const timezone = options.timezone || DEFAULT_TZ;
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'PRODID:-//ScheduGator//Schedule Export//EN',
    `X-WR-CALNAME:${options.calendarName || 'ScheduGator Schedule'}`,
    `X-WR-TIMEZONE:${timezone}`,
  ];

  schedule.courses.forEach((course, index) => {
    if (course.meetTimes && course.meetTimes.length > 0) {
      course.meetTimes.forEach((meetTime, meetIndex) => {
        lines.push(
          ...buildEventsForMeetTime(course, meetTime, index * 10 + meetIndex, options)
        );
      });
    } else {
      lines.push(...buildEventsForLegacy(course, options));
    }
  });

  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
};

export const downloadIcs = (icsContent: string, filename: string): void => {
  const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
};

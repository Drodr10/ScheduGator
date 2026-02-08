# ScheduGator Project Architecture

## Project Structure

```
ScheduGator/
├── README.md                          # Main project overview
├── .git/                              # Git repository
│
├── backend/ (Python)
│   ├── gatorobber.py                 # Data scraper
│   ├── search.py                     # Search functionality
│   ├── conflicts.py                  # Conflict detection
│   ├── bucket_1.json                 # Gold standard data (Computer Science, etc.)
│   └── universal_base_catalog.json   # Scraped data for 120+ majors
│
└── frontend/ (React + TypeScript)
    ├── src/
    │   ├── components/               # React components
    │   │   ├── Header.tsx            # App header with branding
    │   │   ├── ChatSidebar.tsx       # AI Advisor chat interface
    │   │   ├── Calendar.tsx          # Weekly calendar view
    │   │   ├── SchedulePanel.tsx     # Course details & filters
    │   │   ├── CourseCard.tsx        # Individual course card
    │   │   └── index.ts              # Component exports
    │   │
    │   ├── store/                    # State management
    │   │   └── index.ts              # Zustand store
    │   │
    │   ├── types/                    # TypeScript types
    │   │   └── index.ts              # All type definitions
    │   │
    │   ├── utils/                    # Utility functions
    │   │   └── conflict.ts           # Conflict detection & colors
    │   │
    │   ├── App.tsx                   # Main app component
    │   ├── main.tsx                  # React entry point
    │   └── index.css                 # Global styles
    │
    ├── index.html                    # HTML template
    ├── tailwind.config.js            # Tailwind CSS configuration
    ├── postcss.config.js             # PostCSS configuration
    ├── vite.config.ts                # Vite configuration
    ├── tsconfig.json                 # TypeScript configuration
    ├── .eslintrc.cjs                 # ESLint configuration
    ├── package.json                  # Dependencies
    ├── README.md                     # Frontend documentation
    └── QUICKSTART.md                 # Quick start guide
```

## Architecture Overview

### Frontend (React + TypeScript)

```
┌─────────────────────────────────────────────────────┐
│                    Header                            │  (Branding, About, Export)
├─────────────────────────────────────────────────────┤
│                  Main Content Area                   │
├──────────────────┬──────────────────┬────────────────┤
│     ChatSidebar  │    Calendar      │  SchedulePanel │
│                  │                  │                │
│ • Major select   │ • Mon-Fri view   │ • Statistics   │
│ • Chat history   │ • 7 AM - 9 PM    │ • Filters      │
│ • AI responses   │ • Color blocks   │ • Course list  │
│ • Input field    │ • Conflicts      │ • Details      │
└──────────────────┴──────────────────┴────────────────┘
```

### Data Flow

```
User Input
    │
    ├─→ ChatSidebar
    │   └─→ Zustand Store (selectedMajor, messages)
    │       └─→ API Call to Backend (generate schedule)
    │           └─→ Schedule Response (Course[])
    │               └─→ Calendar & SchedulePanel Update
    │                   ├─→ detectConflicts()
    │                   └─→ UI Rendering
    │
    └─→ Course Selection
        └─→ CourseCard Display
            └─→ Conflict Detection & Highlighting
```

### State ManagementZustand Store

```typescript
ScheduleStore = {
  // Schedule State
  selectedSchedule: Schedule | null
  selectedCourse: Course | null
  selectedMajor: string
  
  // Chat State
  messages: ChatMessage[]
  isLoadingSchedule: boolean
  
  // Filters
  filters: {
    showConflictsOnly: boolean
    showCriticalTrackingOnly: boolean
  }
  
  // Actions
  setSelectedSchedule()
  updateSchedule()
  setSelectedMajor()
  addMessage()
  toggleConflictFilter()
  getConflicts()
  getScheduleStats()
}
```

## Component Hierarchy

```
App
├── Header
│   ├── About Button (with dropdown)
│   └── Export Calendar Button
│
├── ChatSidebar
│   ├── Major Selection Dropdown
│   ├── Message Display
│   │   ├── User Messages
│   │   ├── AI Messages
│   │   └── System Messages
│   └── Input Field
│
├── Calendar
│   ├── Time Header (7 AM - 9 PM)
│   ├── Day Columns (M-F)
│   └── Course Blocks
│       └── CourseCard (compact variant)
│
└── SchedulePanel
    ├── Statistics Cards
    │   ├── Total Credits
    │   ├── Total Courses
    │   ├── Conflicts Count
    │   └── Critical Tracking Count
    │
    ├── Filter Buttons
    │   ├── Show Conflicts Only
    │   └── Show Critical Tracking Only
    │
    └── Course List
        └── CourseCard (detailed variant)
            ├── Course Info
            ├── Instructor & Credits
            ├── Schedule
            ├── Enrollment
            └── Conflict Warnings
```

## Data Types

### Core Types

```typescript
Course {
  courseCode: string          // "COP 3014"
  courseName: string          // "Programming Fundamentals 1"
  instructor: string          // "Dr. Smith"
  credits: number             // 3
  meetDays: string[]          // ['M', 'W', 'F']
  meetPeriod: TimeSlot        // { start: 9, end: 10 }
  section: string             // "0001"
  enrollmentCap: number       // 30
  enrollmentActual: number    // 28
  isCriticalTracking?: boolean
  isAISuggested?: boolean
}

Schedule {
  majorCode: string           // "CPS"
  semester: string            // "Spring 2024"
  courses: Course[]
  isCriticalTrackingSchedule?: boolean
  isOptimized?: boolean
}

ConflictInfo {
  courseA: Course
  courseB: Course
  conflictingDays: string[]   // ['M', 'W']
  conflictingTimes: TimeSlot  // { start: 10, end: 11 }
}
```

## Key Features Implementation

### 1. Conflict Detection
- **Location**: `src/utils/conflict.ts`
- **Algorithm**: O(n²) comparison of course meeting times
- **Output**: Array of conflicts with details

### 2. Color Coding
- **Method**: Hash-based color assignment per course code
- **Consistency**: Same course always gets same color
- **Palette**: 8 distinct colors that rotate

### 3. Calendar Rendering
- **Grid Layout**: CSS Grid with day columns and hour rows
- **Positioning**: Dynamic placement based on meetDays & meetPeriod
- **Responsiveness**: Scales from mobile to desktop

### 4. Chat Integration
- **Demo Mode**: Simulates AI responses
- **Real Backend**: Ready for API integration
- **State**: Messages stored in Zustand

## Styling System

### Tailwind CSS Configuration

```javascript
colors: {
  gator: {
    dark: '#003DA5'          // Primary - Deep UF Blue
    light: '#0066FF'         // Secondary
    accent: '#FF8200'        // Accent - UF Orange
    gray: { 50-900 }         // Complete color scale
    success: '#10B981'
    warning: '#F59E0B'
    error: '#EF4444'
  }
}
```

### Custom CSS Features
- Custom scrollbars with Gator colors
- Smooth animations for interactions
- Print-friendly styles
- Accessibility focus states

## API Integration Points

The frontend expects these backend endpoints:

```bash
# Schedule Generation
POST /api/schedule/generate
Body: { major: string, preferences: string }
Response: Schedule

# Get Available Majors
GET /api/majors
Response: string[]

# Get Specific Major Details
GET /api/majors/{majorCode}
Response: MajorDetails

# Export to Calendar
POST /api/calendar/export
Body: { schedule: Schedule, provider: 'google' | 'outlook' }
Response: { url: string }
```

## Performance Considerations

| Aspect | Strategy |
|--------|----------|
| Build | Vite (fast HMR, optimized bundles) |
| State | Zustand (15kb, no boilerplate) |
| Styles | Tailwind CSS (utility-first, tree-shaking) |
| Icons | Lucide React (tree-shakeable SVGs) |
| Code Splitting | Automatic via Vite |

## Development Workflow

```bash
# 1. Clone and setup
cd frontend
npm install

# 2. Start development
npm run dev

# 3. Make changes with hot reload

# 4. Run linting
npm run lint

# 5. Build for production
npm run build

# 6. Preview production build
npm run preview
```

## Browser Compatibility

- Chrome/Edge: v90+
- Firefox: v88+
- Safari: v14+
- Mobile browsers: Latest versions

## Future Enhancements

- [ ] Real backend API integration
- [ ] User authentication
- [ ] Save favorite schedules
- [ ] Real-time availability
- [ ] Advanced search filters
- [ ] Schedule comparison
- [ ] Export to iCal format
- [ ] Calendar sync (Google, Outlook)
- [ ] Dark mode
- [ ] Mobile app version
- [ ] Offline support

---

**Built for UF Students** 🐊📅

# ScheduGator Frontend

A modern, responsive React frontend for ScheduGator - an AI-driven academic schedule optimizer for UF students.

## Features

🎨 **Modern UI Design**: Clean, professional dashboard with a Gator-themed color scheme (Deep Blues, Oranges, Grays)

💬 **AI Chat Interface**: Natural language chat sidebar for interacting with the AI Advisor

📅 **Interactive Calendar**: Weekly calendar view (Mon-Fri, 7 AM-9 PM) with color-coded courses

⚠️ **Conflict Detection**: Automatic detection and visual highlighting of scheduling conflicts

🎯 **Course Details**: Clickable course cards showing instructors, credits, prerequisites status

🔍 **Smart Filters**: Filter by conflicts or critical tracking courses

📊 **Schedule Statistics**: Real-time stats showing credits, courses, conflicts, and critical tracking courses

## Recent Updates

- ✅ Fixed responsive grid layout for all screen sizes
- ✅ Enhanced color system for better visual hierarchy
- ✅ Improved conflict detection visualization
- ✅ Added proper TypeScript types and Zustands store
- ✅ Tailwind CSS + custom Gator theme

## Tech Stack

- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Fast build tooling
- **Tailwind CSS**: Responsive styling with custom theme
- **Zustand**: Lightweight state management
- **Lucide React**: Icon library
- **PostCSS**: CSS processing

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── Header.tsx
│   │   ├── ChatSidebar.tsx
│   │   ├── Calendar.tsx
│   │   ├── SchedulePanel.tsx
│   │   ├── CourseCard.tsx
│   │   └── index.ts
│   ├── store/                # Zustand store
│   │   └── index.ts
│   ├── types/                # TypeScript types
│   │   └── index.ts
│   ├── utils/                # Utility functions
│   │   └── conflict.ts       # Conflict detection logic
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles
├── tailwind.config.js        # Tailwind configuration
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies
└── index.html                # HTML template
```

## Installation & Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Start development server**:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

3. **Build for production**:
```bash
npm run build
```

## Key Components

### Header
- Branding and app title
- About information dropdown
- Export to Calendar button (placeholder for integration)

### ChatSidebar
- Major selection dropdown
- Chat interface with AI Advisor
- Real-time message display
- Input field with response generation

### Calendar
- Weekly grid layout (Mon-Fri)
- Time slots from 7 AM to 9 PM
- Color-coded course blocks
- Conflict highlighting with red borders
- Automatic course positioning based on meetDays and meetPeriod

### SchedulePanel
- Statistics cards (credits, courses, conflicts, critical tracking)
- Filter buttons for conflicts and critical tracking courses
- Course list with detailed cards
- Schedule status indicators

### CourseCard
- Compact and detailed variants
- Critical tracking and AI-suggested badges
- Conflict indicators
- Click to view full details

## State Management (Zustand Store)

The app uses Zustand for lightweight state management with the following features:

- **Schedule State**: Selected schedule, courses, conflicts
- **UI State**: Selected course, major, filters
- **Chat State**: Messages and loading status
- **Computed Values**: Conflict detection, schedule statistics

## Conflict Detection

The `detectConflicts()` function analyzes:
- Overlapping meeting days
- Time slot conflicts
- Returns detailed conflict information with affected courses and times

## Styling

### Gator Theme Colors
- **Dark Blue**: `#003DA5` (Primary)
- **Light Blue**: `#0066FF` (Secondary)
- **Orange**: `#FF8200` (Accent)
- **Grays**: Comprehensive color scale for UI elements

### Features
- Fully responsive (mobile, tablet, desktop)
- Custom scrollbars with Gator theme
- Smooth animations and transitions
- Accessible focus states
- Print-friendly styles

## Integration Points

The frontend is designed to work with a backend API for:

1. **Schedule Generation**: AI endpoint that processes natural language and returns Course[]
2. **Major Data**: Endpoint serving available majors and critical tracking requirements
3. **Course Data**: Real-time course information with availability and prerequisites
4. **Calendar Export**: Integration with Google Calendar and Outlook (placeholder)

## Future Enhancements

- [ ] Backend API integration
- [ ] Google Calendar export
- [ ] Outlook calendar export
- [ ] User authentication and saved schedules
- [ ] Preference persistence
- [ ] Dark mode toggle
- [ ] Mobile app version
- [ ] Real-time availability updates
- [ ] Advanced filtering (instructor, building, time blocks)
- [ ] Schedule comparison tools

## Development Notes

- Ensure all TypeScript strict mode checks pass
- Component files must be readable and maintainable
- Use semantic HTML for accessibility
- Follow Tailwind CSS best practices
- Keep state management centralized in Zustand
- Write utility functions for reusable logic

## License

Built for UF Students by the ScheduGator Team

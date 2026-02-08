# ScheduGator Frontend - Quick Start Guide

## Getting Started (5 minutes)

### Prerequisites
- **Node.js**: v16+ with npm

### Steps

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the development server**:
```bash
npm run dev
```

4. **Open in browser**:
```
http://localhost:5173
```

## What You'll See

✅ **Responsive Dashboard** with the following sections:

- **Header**: ScheduGator branding with About and Export options
- **Left Sidebar**: 
  - Major selection dropdown
  - AI Advisor chat interface
  - Message history
- **Center Area**: 
  - Interactive weekly calendar
  - Color-coded course blocks
  - Conflict highlighting
- **Right Panel**: 
  - Schedule statistics
  - Course list with filters
  - Detailed course information

## Demo Features

The frontend includes **demo data** for testing:

### Available Majors:
- Computer Science (CPS)
- Computer Engineering (CPE)
- Electrical Engineering (EES)
- Data Science (DAS)
- Business (BUS)

### How to Test:
1. Select a major from the dropdown
2. Type a message to the AI Advisor (e.g., "Generate my schedule")
3. Watch the calendar populate with color-coded courses
4. Click on courses to see details
5. Use filters to show only conflicts or critical tracking courses

## Production Build

To create an optimized production build:

```bash
npm run build
```

Output will be in the `dist/` directory.

## Deploying

### Docker (Recommended)
```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

### Vercel
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Drag & drop dist/ folder to Netlify
```

### AWS S3 + CloudFront
```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name/
```

## Customization

### Change Gator Colors
Edit `frontend/tailwind.config.js`:
```javascript
colors: {
  gator: {
    dark: '#003DA5',      // Change dark blue
    accent: '#FF8200',    // Change orange
    // ... other colors
  }
}
```

### Add Demo Courses
Edit `frontend/src/App.tsx` → `DEMO_COURSES` object

### Modify Calendar Hours
Edit `frontend/src/components/Calendar.tsx`:
```typescript
const START_HOUR = 7;  // 7 AM
const END_HOUR = 21;   // 9 PM
```

## Troubleshooting

### Port 5173 already in use?
```bash
npm run dev -- --port 3000
```

### Tailwind styles not showing?
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### TypeScript errors?
```bash
npm run lint
```

## Available Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server |
| `npm run build` | Create production build |
| `npm run lint` | Run ESLint |
| `npm run preview` | Preview production build |

## Environment Setup

Create a `.env.local` file for API configuration:

```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

## Backend Integration

To connect to your Python backend:

1. **Update API endpoint** in `src/App.tsx`:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function generateSchedule(major: string, preferences: string) {
  const response = await fetch(`${API_URL}/api/schedule/generate`, {
    method: 'POST',
    body: JSON.stringify({
      major,
      preferences,
    })
  });
  return response.json();
}
```

2. **Update chat handler** to call your backend AI endpoint

3. **Fetch major data** from your database

## Performance Optimization

The app is already optimized with:
- Code splitting via Vite
- Lazy component loading
- Efficient state management with Zustand
- Tailwind CSS purging

For further optimization:
- Enable gzip compression on server
- Set up CDN for static assets
- Use service workers for offline support

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Need Help?

Check the main [README.md](./README.md) for more details on:
- Project structure
- Component documentation
- State management
- Styling system

---

**Happy Scheduling!** 🐊📅

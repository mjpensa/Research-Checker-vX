# Phase 4: Frontend Foundation - In Progress! 🚧

Phase 4 adds a Next.js frontend for interactive research analysis with real-time updates and beautiful visualizations.

## What's Completed in Phase 4

### 1. **Next.js 14 Setup** ✅
- TypeScript configuration
- Tailwind CSS styling
- App Router architecture
- Environment variable configuration
- ESLint and PostCSS setup

### 2. **Core Infrastructure** ✅
- **API Client** (`lib/api-client.ts`) - Axios-based client with interceptors
- **WebSocket Hook** (`hooks/useWebSocket.ts`) - Real-time pipeline updates
- **Type Definitions** (`types/index.ts`) - Full TypeScript interfaces
- **Utility Functions** (`lib/utils.ts`) - Helper functions for formatting

### 3. **UI Component Library** ✅
- **Button** - Multiple variants (default, destructive, outline, ghost, link)
- **Card** - Container component with header, content, footer
- **Badge** - Status indicators with color variants
- **Spinner** - Loading states (small, medium, large)

### 4. **Feature Components** ✅
- **FileUpload** - Drag-and-drop file upload with validation
  - Supports PDF, DOCX, TXT, MD, JSON
  - File size validation (max 100MB)
  - Multiple file selection
  - Visual file list with remove functionality

### 5. **Dashboard Page** ✅
- Pipeline creation interface
- Document upload functionality
- Real-time status tracking
- Progress indicators

## Project Structure

```
apps/frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page (redirects to dashboard)
│   ├── globals.css             # Global styles with Tailwind
│   └── dashboard/
│       └── page.tsx            # Main dashboard ✨ NEW
│
├── components/
│   ├── ui/                     # Reusable UI components
│   │   ├── button.tsx          # Button component ✅
│   │   ├── card.tsx            # Card component ✅
│   │   ├── badge.tsx           # Badge component ✅
│   │   └── spinner.tsx         # Spinner component ✅
│   │
│   └── features/               # Feature-specific components
│       └── pipeline/
│           └── FileUpload.tsx  # File upload component ✅
│
├── lib/
│   ├── utils.ts                # Utility functions ✅
│   └── api-client.ts           # API client ✅
│
├── hooks/
│   └── useWebSocket.ts         # WebSocket hook ✅
│
├── types/
│   └── index.ts                # TypeScript definitions ✅
│
├── next.config.js              # Next.js configuration ✅
├── tailwind.config.ts          # Tailwind configuration ✅
├── tsconfig.json               # TypeScript configuration ✅
└── package.json                # Dependencies ✅
```

## Quick Start

### 1. Install Dependencies

```bash
cd apps/frontend
pnpm install
```

### 2. Configure Environment

Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Start Development Server

```bash
pnpm dev
```

Frontend will be available at: `http://localhost:3000`

### 4. Build for Production

```bash
pnpm build
pnpm start
```

## API Client Usage

The API client provides methods for all backend endpoints:

```typescript
import { apiClient } from '@/lib/api-client'

// Create pipeline
const { data: pipeline } = await apiClient.createPipeline({
  name: 'My Research',
  metadata: {}
})

// Upload documents
await apiClient.uploadDocuments(pipelineId, files, 'gpt-4')

// Start processing
await apiClient.startPipeline(pipelineId)

// Get claims
const { data: claims } = await apiClient.getClaims({ pipeline_id: pipelineId })

// Analyze dependencies
await apiClient.analyzeDependencies(pipelineId)

// Generate report
await apiClient.generateReport(pipelineId, 'synthesis')
```

## WebSocket Usage

Real-time updates for pipeline progress:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

function MyComponent() {
  const { messages, connected } = useWebSocket(pipelineId)

  useEffect(() => {
    messages.forEach(msg => {
      if (msg.type === 'claim_extracted') {
        console.log('New claim:', msg.data)
      }
    })
  }, [messages])

  return <div>Connected: {connected ? 'Yes' : 'No'}</div>
}
```

## What's Pending

### Advanced Components (Phase 4.2)
- **ClaimsTable** - Interactive table with filtering and sorting
- **DependencyGraph** - Force-directed graph visualization with D3
- **ReportViewer** - Markdown report display with export
- **ContradictionList** - Highlighted contradictions with severity

### Pages (Phase 4.3)
- **Pipeline Details** - Full pipeline analysis view
- **Claims View** - Detailed claim exploration
- **Dependencies View** - Interactive graph visualization
- **Reports View** - Report generation and viewing

### State Management (Phase 4.4)
- Zustand store for global state
- React Query for data fetching and caching
- Optimistic updates

### Authentication (Phase 4.5)
- Clerk integration (optional)
- Protected routes
- User profile

## Development Workflow

### Adding a New Component

1. Create component file in appropriate directory
2. Use existing UI components as building blocks
3. Import types from `@/types`
4. Use utility functions from `@/lib/utils`

### Connecting to Backend

1. Add API method to `lib/api-client.ts`
2. Use React Query for data fetching (when implemented)
3. Handle loading and error states
4. Use WebSocket for real-time updates

## Styling Guidelines

This project uses Tailwind CSS with a custom design system:

- **Colors**: Blue for primary, Gray for neutral, Red for destructive
- **Spacing**: Consistent spacing scale (4px base unit)
- **Typography**: Inter font family
- **Components**: Card-based layouts with subtle shadows

### Example Component

```typescript
'use client'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        <Badge variant="success">Active</Badge>
        <Button onClick={() => {}} className="mt-4">
          Click Me
        </Button>
      </CardContent>
    </Card>
  )
}
```

## Testing the Dashboard

### Prerequisites
- Backend API running on `http://localhost:8000`
- PostgreSQL and Redis services running
- Workers running (extraction, inference, reports)

### Test Flow

1. **Visit Dashboard**: Navigate to `http://localhost:3000`
2. **Create Pipeline**: Click "Create New Pipeline"
3. **Upload Documents**: Drag and drop PDF/DOCX files
4. **Monitor Progress**: Backend will process documents
5. **View Results**: Check claims, dependencies, reports (via API)

## Railway Deployment

Add frontend service to `railway.toml`:

```toml
[services.frontend]
source = "./apps/frontend"
buildCommand = "pnpm install && pnpm build"
startCommand = "pnpm start"
replicas = 1

[services.frontend.env]
NEXT_PUBLIC_API_URL = "${API_URL}"
NEXT_PUBLIC_WS_URL = "${WS_URL}"
```

## Dependencies

### Core
- `next` ^14.2.0 - React framework
- `react` ^18.3.1 - UI library
- `typescript` ^5.4.3 - Type safety

### Styling
- `tailwindcss` ^3.4.1 - Utility-first CSS
- `class-variance-authority` ^0.7.0 - Component variants
- `clsx` ^2.1.0 - Conditional classes
- `tailwind-merge` ^2.2.2 - Class merging

### Data & API
- `axios` ^1.6.8 - HTTP client
- `@tanstack/react-query` ^5.28.0 - Data fetching (planned)
- `zustand` ^4.5.2 - State management (planned)

### UI & Visualization
- `lucide-react` ^0.363.0 - Icon library
- `react-dropzone` ^14.2.3 - File uploads
- `d3` ^7.9.0 - Data visualization (planned)
- `react-force-graph-2d` ^1.25.4 - Graph visualization (planned)
- `react-markdown` ^9.0.1 - Markdown rendering (planned)
- `framer-motion` ^11.0.24 - Animations (planned)

### Utilities
- `date-fns` ^3.6.0 - Date formatting
- `@tanstack/react-table` ^8.15.0 - Table component (planned)

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Build Errors
```bash
# Clear cache and reinstall
rm -rf .next node_modules
pnpm install
pnpm dev
```

### API Connection Issues
- Verify backend is running on port 8000
- Check CORS settings in backend
- Verify environment variables in `.env.local`

## What's Next

### Immediate Tasks
1. ✅ Complete ClaimsTable component with TanStack Table
2. ✅ Implement DependencyGraph with D3/react-force-graph
3. ✅ Add ReportViewer with markdown rendering
4. ✅ Create Pipeline Details page
5. ✅ Integrate React Query for data management
6. ✅ Add comprehensive error handling

### Future Enhancements
- Dark mode support
- Mobile-responsive design
- Export functionality (PDF, DOCX)
- Advanced filtering and search
- Real-time collaboration features
- Analytics dashboard

---

**Status**: Phase 4 Foundation Complete ✅
**Progress**: 40% (Core infrastructure and basic UI ready)
**Next**: Advanced components and full pipeline visualization

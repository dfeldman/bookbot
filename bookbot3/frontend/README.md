# BookBot Vue 3 Frontend

A modern, responsive Vue 3 frontend for the BookBot AI-powered book writing assistant.

## Features

### 🎯 User Onboarding
- **Welcome Screen**: Clean, professional welcome page with API token setup
- **Token Validation**: Real-time validation of OpenRouter API tokens
- **User Guidance**: Step-by-step setup with clear instructions

### 📝 Book Creation Wizard
- **3-Step Process**: Streamlined book creation flow
- **Progress Tracking**: Visual progress bar showing completion
- **Smart Defaults**: Example titles and descriptions to inspire users
- **Style Selection**: Choose from 6 different writing styles (Thriller, Fantasy, Romance, etc.)
- **Professional UI**: Modern card-based interface with smooth transitions

### 📚 Dashboard
- **Book Management**: Grid view of all user books
- **Real-time Updates**: Live job progress tracking
- **Book Statistics**: Word count, chunk count, and creation dates
- **Status Indicators**: Visual badges for book processing states

### 🎨 Components
- **TextEditor**: Rich text editor with formatting toolbar (future use)
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Professional Styling**: Modern gradient backgrounds and card layouts

## Tech Stack

- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Pinia** for state management
- **Vue Router** for navigation
- **Axios** for API communication
- **Vite** for fast development and building

## Project Structure

```
src/
├── components/          # Reusable Vue components
│   └── TextEditor.vue  # Rich text editor component
├── services/           # API and external services
│   └── api.ts         # API service layer
├── stores/            # Pinia stores for state management
│   ├── app.ts        # App-wide state (user, config, auth)
│   └── book.ts       # Book and job management
├── views/             # Main application views
│   ├── Welcome.vue   # Welcome/onboarding screen
│   ├── BookWizard.vue # Book creation wizard
│   └── Dashboard.vue # Main dashboard
├── App.vue           # Root component
├── main.ts          # Application entry point
└── style.css        # Global styles
```

## API Integration

The frontend seamlessly integrates with the BookBot Flask backend through:

- **RESTful API**: Full CRUD operations for books, chunks, and jobs
- **Server-Sent Events**: Real-time job progress updates
- **Error Handling**: Graceful error handling with user feedback
- **Authentication**: Framework ready for Google OAuth integration

## Key Workflows

### 1. First-Time User Experience
1. User lands on Welcome screen
2. Prompted to enter OpenRouter API token
3. Token is validated in real-time
4. Upon validation, user can create their first book

### 2. Book Creation
1. User clicks "Create Book" 
2. Enters book title, description, and selects style
3. Reviews choices on confirmation screen
4. Frontend creates book and starts CreateFoundation job
5. User is redirected to dashboard to monitor progress

### 3. Job Monitoring
1. Dashboard shows active job progress
2. Real-time updates via polling
3. Progress bar and status messages
4. Automatic refresh when job completes

## Development

### Prerequisites
- Node.js 18+
- npm or yarn

### Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Integration
The frontend is configured to proxy API requests to the Flask backend:
- **Development**: `http://localhost:5002/api`
- **Production**: Same origin `/api`

## Styling

### Design System
- **Colors**: Professional blue gradient theme (`#667eea` to `#764ba2`)
- **Typography**: System font stack with careful hierarchy
- **Spacing**: Consistent 8px grid system
- **Cards**: Subtle shadows with hover effects
- **Buttons**: Gradient backgrounds with smooth transitions

### Responsive Design
- **Mobile-first**: Optimized for mobile devices
- **Breakpoints**: Tablet and desktop adaptations
- **Grid Layouts**: Flexible grid systems that adapt to screen size

## Future Enhancements

- **Book Editor**: Full book editing interface with chapter management
- **Collaboration**: Multi-user editing and sharing
- **Export Options**: PDF, EPUB, and Word export
- **Templates**: Pre-built book templates and outlines
- **AI Suggestions**: Real-time writing suggestions and improvements

## State Management

### App Store (`stores/app.ts`)
- User authentication and profile
- API token management
- Application configuration
- Global loading states

### Book Store (`stores/book.ts`)
- Book CRUD operations
- Job creation and monitoring
- Progress tracking
- Book statistics

## Component Architecture

### Composition API
All components use Vue 3 Composition API for:
- Better TypeScript support
- Logical code organization
- Easier testing and reusability

### Props & Emits
Clear interfaces defined for all component communication:
- TypeScript interfaces for props
- Explicit emit definitions
- Proper data flow patterns

This frontend provides a solid foundation for BookBot's user interface, with room for extensive feature expansion as the platform grows.

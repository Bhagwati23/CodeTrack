# CodeTrack Pro - Advanced Coding Learning Platform

![CodeTrack Pro Logo](static/images/logo.png)

A comprehensive, production-ready coding learning platform that combines AI-powered tutoring, real-time contests, collaborative study groups, and spaced repetition learning to help developers master programming skills.

## 🚀 Features

### 🤖 AI-Powered Learning
- **Multi-Provider AI System**: OpenAI GPT-4o, DeepSeek Chat, Google Gemini, OpenRouter, Hugging Face
- **Interactive AI Tutor**: Personalized coding guidance with conversation history
- **Study Plan Generation**: 4-week structured learning plans
- **Problem Recommendations**: AI-curated problems based on skill level
- **Flashcard Generation**: AI-created flashcards for spaced repetition

### 🏆 Live Coding Contests
- **Real-time Competition**: Secure code execution with instant results
- **Multi-language Support**: Python, Java, C++, C
- **Live Leaderboards**: Real-time rankings and submissions
- **Admin Management**: Create contests, manage problems, monitor participants
- **Sandboxed Execution**: Secure code execution with time/memory limits

### 👥 Collaborative Learning
- **Study Groups**: AI-matched groups based on skill level and interests
- **Real-time Chat**: Group messaging with file sharing
- **Anonymous Forum**: Q&A system with AI-generated answers after 24 hours
- **Peer Learning**: Code reviews and knowledge sharing

### 🧠 Spaced Repetition System
- **SM-2 Algorithm**: Scientifically-proven spaced repetition
- **Adaptive Scheduling**: Cards adapt to your learning pace
- **Progress Tracking**: Retention rates and learning statistics
- **AI-Generated Cards**: Automatic flashcard creation from topics

### 📊 Progress Tracking
- **Multi-Platform Integration**: LeetCode, GeeksforGeeks, GitHub, HackerRank
- **Real-time Synchronization**: Web scraping with rate limiting
- **Detailed Analytics**: Progress charts and performance insights
- **Streak Tracking**: Daily coding habits and milestones

### 🎨 Modern UI/UX
- **Glass Morphism Design**: Beautiful dark theme with light mode support
- **Responsive Design**: Mobile-first approach
- **Smooth Animations**: Enhanced user experience
- **Real-time Updates**: Live notifications and status updates

## 🏗️ Architecture

### Backend
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with 22 comprehensive tables
- **Authentication**: Flask-Login with role-based access control
- **Background Tasks**: APScheduler for notifications and maintenance
- **API Design**: RESTful endpoints with JSON responses

### Frontend
- **CSS Framework**: Custom glass morphism design system
- **JavaScript**: Vanilla JS with Chart.js for data visualization
- **Responsive**: Mobile-first design with Bootstrap grid system
- **Themes**: Dark/light mode with smooth transitions

### AI Integration
- **Multi-Provider**: Automatic fallback between AI services
- **Rate Limiting**: Intelligent request management
- **Error Handling**: Graceful degradation with local fallbacks
- **Cost Optimization**: Smart provider selection

## 📁 Project Structure

```
CodeTrack Pro/
├── main.py                 # Application entry point
├── app.py                  # Flask app factory
├── models.py               # SQLAlchemy database models (22 tables)
├── routes.py               # All URL endpoints (50+ routes)
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── services/              # Service layer
│   ├── ai_providers.py    # Multi-provider AI system
│   ├── enhanced_ai_tutor.py # AI tutoring service
│   ├── coding_tracker.py  # Platform scrapers
│   ├── code_executor.py   # Secure code execution
│   ├── spaced_repetition.py # SM-2 algorithm
│   ├── notification_service.py # Notification management
│   ├── notification_scheduler.py # Background scheduler
│   ├── ai_flashcard_generator.py # AI flashcard creation
│   └── study_group_matcher.py # Group matching algorithm
├── templates/             # HTML templates (25+ files)
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Landing page
│   ├── login.html        # Authentication
│   ├── register.html     # User registration
│   ├── dashboard.html    # Main dashboard
│   └── ...               # Additional templates
└── static/               # Static assets
    ├── css/
    │   └── style.css     # Comprehensive CSS (1500+ lines)
    ├── js/
    │   └── main.js       # Main JavaScript functionality
    └── images/           # Images and icons
```

## 🗄️ Database Schema

### Core Tables (22 Tables Total)

#### User Management (3 tables)
- `users` - User accounts with profiles and platform usernames
- `platform_stats` - Progress tracking across coding platforms
- `daily_coding_hours` - Daily coding time tracking

#### Learning System (5 tables)
- `problems` - Coding problems from various platforms
- `problems_solved` - User's solved problems with details
- `flashcards` - Spaced repetition learning cards
- `study_sessions` - Learning session tracking
- `ai_recommendations` - AI-generated study suggestions

#### Social Features (8 tables)
- `study_groups` - Collaborative learning groups
- `study_group_members` - Group membership management
- `group_chat_messages` - Real-time group communication
- `forum_posts` - Anonymous question posting
- `forum_answers` - Responses with AI integration
- `forum_post_votes` / `forum_answer_votes` - Voting system
- `question_discussions` - Follow-up discussions

#### Contest System (6 tables)
- `contests` - Coding competitions
- `contest_problems` - Problems within contests
- `contest_test_cases` - Test cases for problems
- `contest_submissions` - User code submissions
- `contest_test_results` - Execution results
- `contest_participants` - Contest participation tracking

#### Notifications (1 table)
- `notifications` - System notifications for users

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (for frontend assets)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/codetrack-pro.git
cd codetrack-pro
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

5. **Setup database**
```bash
# Create PostgreSQL database
createdb codetrack_pro

# Initialize database
python -c "from app import init_database; init_database()"
```

6. **Run the application**
```bash
python main.py
```

The application will be available at `http://localhost:5000`

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/codetrack_pro

# Flask
FLASK_SECRET_KEY=your-secret-key-here
SESSION_SECRET=your-session-secret

# AI Providers (Optional - system works with fallbacks)
OPENAI_API_KEY=your-openai-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
GEMINI_API_KEY=your-gemini-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Email (Optional)
SENDGRID_API_KEY=your-sendgrid-api-key
```

### AI Provider Setup

The system supports multiple AI providers with automatic fallback:

1. **OpenAI GPT-4o** (Primary, paid)
2. **DeepSeek Chat** (Free, coding-focused)
3. **Google Gemini 2.5 Flash** (Free, multimodal)
4. **OpenRouter** (Free model access)
5. **Hugging Face** (Free inference)
6. **Local Fallback** (Always available)

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Dashboard Endpoints
- `GET /dashboard/` - Main dashboard
- `GET /dashboard/coding` - Coding progress
- `POST /dashboard/sync_platform` - Sync platform data
- `GET /dashboard/profile` - User profile
- `GET /dashboard/notifications` - Notification center

### AI Tutoring Endpoints
- `GET /ai/tutor` - AI tutor interface
- `POST /ai/start_session` - Start tutoring session
- `POST /ai/send_message` - Send message to AI
- `POST /ai/get_recommendation` - Get AI recommendations
- `POST /ai/generate_flashcards` - Generate AI flashcards

### Contest Endpoints
- `GET /contest/` - Contest list
- `GET /contest/admin` - Admin contest management
- `POST /contest/create` - Create contest
- `GET /contest/<id>/participate` - Participate in contest
- `POST /contest/submit` - Submit code
- `GET /contest/<id>/leaderboard` - Contest leaderboard

### Forum Endpoints
- `GET /forum/` - Forum main page
- `GET /forum/question/<id>` - Question details
- `POST /forum/post_question` - Post question
- `POST /forum/answer_question` - Answer question
- `POST /forum/vote_post` - Vote on posts

### Study Group Endpoints
- `GET /study/groups` - Study groups
- `POST /study/groups/create` - Create group
- `POST /study/groups/<id>/join` - Join group
- `GET /study/groups/<id>/chat` - Group chat
- `POST /study/groups/<id>/send_message` - Send message

### Learning Endpoints
- `GET /study/revision` - Spaced repetition dashboard
- `GET /study/flashcards` - Flashcard management
- `GET /study/flashcards/review` - Review session
- `POST /study/flashcards/create` - Create flashcard
- `POST /study/flashcards/review_card` - Review flashcard

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Coverage
- Unit tests for all services
- Integration tests for API endpoints
- Database model tests
- AI provider fallback tests

## 🚀 Deployment

### Production Deployment

1. **Setup Production Database**
```bash
# Create production PostgreSQL database
createdb codetrack_pro_prod
```

2. **Configure Production Environment**
```env
FLASK_ENV=production
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/codetrack_pro_prod
```

3. **Deploy with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

4. **Setup Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/codetrack-pro/static;
        expires 1y;
    }
}
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app"]
```

## 🔒 Security Features

- **Password Hashing**: Werkzeug secure password hashing
- **Session Management**: Secure session handling
- **CSRF Protection**: Cross-site request forgery protection
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **XSS Protection**: Template escaping
- **Code Execution Security**: Sandboxed execution environment
- **Rate Limiting**: API rate limiting
- **Authentication**: Role-based access control

## 📈 Performance

### Optimizations
- **Database Indexing**: Optimized queries with proper indexes
- **Connection Pooling**: Database connection management
- **Caching**: Redis caching for frequently accessed data
- **Static File Serving**: Efficient static asset delivery
- **Background Tasks**: Async processing for heavy operations

### Monitoring
- **Application Logging**: Comprehensive logging system
- **Error Tracking**: Exception monitoring
- **Performance Metrics**: Response time tracking
- **Health Checks**: System health monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Providers**: OpenAI, DeepSeek, Google, OpenRouter, Hugging Face
- **Web Frameworks**: Flask, SQLAlchemy
- **Frontend**: Bootstrap, Chart.js, Font Awesome
- **Database**: PostgreSQL
- **Design**: Glass morphism design inspiration

## 📞 Support

- **Documentation**: [docs.codetrackpro.com](https://docs.codetrackpro.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/codetrack-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/codetrack-pro/discussions)
- **Email**: support@codetrackpro.com

## 🎯 Roadmap

### Version 2.0
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Machine learning recommendations
- [ ] Video tutorial integration
- [ ] Advanced code review system

### Version 2.1
- [ ] Multi-language support
- [ ] Enterprise features
- [ ] Advanced reporting
- [ ] API for third-party integrations
- [ ] Advanced security features

---

**CodeTrack Pro** - Empowering developers to master coding skills through AI-powered learning and collaborative practice.

Built with ❤️ by the CodeTrack Pro Team

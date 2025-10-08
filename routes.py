"""
Comprehensive Route System for CodeTrack Pro
All 50+ endpoints for authentication, dashboard, AI tutoring, contests, forum, and study features
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload

from models import (
    db, User, PlatformStats, DailyCodingHours, Problem, ProblemsSolved,
    Flashcard, StudySession, AIRecommendation, StudyGroup, StudyGroupMember,
    GroupChatMessage, ForumPost, ForumAnswer, ForumPostVote, ForumAnswerVote,
    QuestionDiscussion, Contest, ContestProblem, ContestTestCase,
    ContestSubmission, ContestTestResult, ContestParticipant, Notification
)

from services.ai_providers import ai_provider
from services.enhanced_ai_tutor import ai_tutor
from services.coding_tracker import coding_tracker
from services.code_executor import code_executor
from services.spaced_repetition import spaced_repetition_manager
from services.notification_service import notification_service

logger = logging.getLogger(__name__)

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
ai_bp = Blueprint('ai', __name__)
contest_bp = Blueprint('contest', __name__)
forum_bp = Blueprint('forum', __name__)
study_bp = Blueprint('study', __name__)
admin_bp = Blueprint('admin', __name__)

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'student')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('register.html')
        
        # Create user
        user = User(
            username=username,
            email=email,
            role=role,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('main.index'))

# =============================================================================
# MAIN ROUTES
# =============================================================================

@main_bp.route('/')
def index():
    """Landing page or redirect to dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return render_template('index.html')

@main_bp.route('/favicon.ico')
def favicon():
    """Favicon"""
    return redirect(url_for('static', filename='images/favicon.ico'))

# =============================================================================
# DASHBOARD ROUTES
# =============================================================================

@dashboard_bp.route('/')
@login_required
def dashboard():
    """Main dashboard"""
    try:
        # Get user statistics
        user_stats = {
            'total_problems': sum(ps.total_problems for ps in current_user.platform_stats),
            'total_study_sessions': len(current_user.study_sessions),
            'total_flashcards': len(current_user.flashcards),
            'streak': max((ps.streak for ps in current_user.platform_stats), default=0)
        }
        
        # Get recent activity
        recent_activity = []
        
        # Recent problems solved
        recent_problems = ProblemsSolved.query.filter_by(user_id=current_user.id)\
            .order_by(desc(ProblemsSolved.solved_at)).limit(5).all()
        
        for problem in recent_problems:
            recent_activity.append({
                'type': 'problem_solved',
                'title': f"Solved {problem.problem.title}",
                'time': problem.solved_at,
                'platform': problem.problem.platform
            })
        
        # Recent study sessions
        recent_sessions = StudySession.query.filter_by(user_id=current_user.id)\
            .order_by(desc(StudySession.started_at)).limit(3).all()
        
        for session in recent_sessions:
            recent_activity.append({
                'type': 'study_session',
                'title': f"Study session: {session.session_type}",
                'time': session.started_at,
                'duration': session.duration
            })
        
        # Sort by time
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        recent_activity = recent_activity[:10]
        
        # Get upcoming contests
        upcoming_contests = Contest.query.filter(
            Contest.start_date > datetime.now(),
            Contest.is_active == True
        ).order_by(Contest.start_date).limit(5).all()
        
        # Get due flashcards
        due_flashcards = spaced_repetition_manager.get_due_cards_count(current_user.id)
        
        return render_template('dashboard.html',
                             user_stats=user_stats,
                             recent_activity=recent_activity,
                             upcoming_contests=upcoming_contests,
                             due_flashcards=due_flashcards)
    
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html')

@dashboard_bp.route('/coding')
@login_required
def coding():
    """Coding progress and platform sync"""
    try:
        # Get platform stats
        platform_stats = {}
        for ps in current_user.platform_stats:
            platform_stats[ps.platform] = {
                'total_problems': ps.total_problems,
                'easy_solved': ps.easy_solved,
                'medium_solved': ps.medium_solved,
                'hard_solved': ps.hard_solved,
                'contest_rating': ps.contest_rating,
                'streak': ps.streak,
                'last_updated': ps.last_updated
            }
        
        # Get daily coding hours for chart
        daily_hours = DailyCodingHours.query.filter_by(user_id=current_user.id)\
            .order_by(DailyCodingHours.date.desc()).limit(30).all()
        
        chart_data = {
            'labels': [str(h.date) for h in reversed(daily_hours)],
            'data': [h.hours for h in reversed(daily_hours)]
        }
        
        return render_template('coding.html',
                             platform_stats=platform_stats,
                             chart_data=chart_data)
    
    except Exception as e:
        logger.error(f"Coding page error: {e}")
        flash('Error loading coding page', 'error')
        return render_template('coding.html')

@dashboard_bp.route('/sync_platform', methods=['POST'])
@login_required
def sync_platform():
    """Sync platform data"""
    try:
        platform = request.form.get('platform')
        username = request.form.get('username')
        
        if not platform or not username:
            flash('Platform and username are required', 'error')
            return redirect(url_for('dashboard.coding'))
        
        # Scrape platform data
        result = coding_tracker.scrape_user_stats(platform, username)
        
        if 'error' in result:
            flash(f'Error syncing {platform}: {result["error"]}', 'error')
            return redirect(url_for('dashboard.coding'))
        
        # Update or create platform stats
        existing_stat = PlatformStats.query.filter_by(
            user_id=current_user.id,
            platform=platform
        ).first()
        
        if existing_stat:
            existing_stat.total_problems = result.get('total_problems', 0)
            existing_stat.easy_solved = result.get('easy_solved', 0)
            existing_stat.medium_solved = result.get('medium_solved', 0)
            existing_stat.hard_solved = result.get('hard_solved', 0)
            existing_stat.contest_rating = result.get('contest_rating', 0)
            existing_stat.streak = result.get('streak', 0)
            existing_stat.last_updated = datetime.now()
        else:
            new_stat = PlatformStats(
                user_id=current_user.id,
                platform=platform,
                total_problems=result.get('total_problems', 0),
                easy_solved=result.get('easy_solved', 0),
                medium_solved=result.get('medium_solved', 0),
                hard_solved=result.get('hard_solved', 0),
                contest_rating=result.get('contest_rating', 0),
                streak=result.get('streak', 0)
            )
            db.session.add(new_stat)
        
        db.session.commit()
        
        # Send notification
        notification_service.create_notification(
            template_key="profile_sync_complete",
            user_id=current_user.id,
            context={"platform": platform.title()}
        )
        
        flash(f'{platform.title()} profile synced successfully!', 'success')
        return redirect(url_for('dashboard.coding'))
    
    except Exception as e:
        logger.error(f"Platform sync error: {e}")
        flash('Error syncing platform data', 'error')
        return redirect(url_for('dashboard.coding'))

# =============================================================================
# AI TUTORING ROUTES
# =============================================================================

@ai_bp.route('/tutor')
@login_required
def ai_tutor():
    """AI tutor interface"""
    return render_template('ai_tutor.html')

@ai_bp.route('/start_session', methods=['POST'])
@login_required
def start_tutor_session():
    """Start a new AI tutoring session"""
    try:
        topic = request.json.get('topic')
        difficulty = request.json.get('difficulty', 'beginner')
        
        session = ai_tutor.start_session(
            user_id=current_user.id,
            topic=topic,
            difficulty_level=difficulty
        )
        
        return jsonify({
            'session_id': session.session_id,
            'welcome_message': session.conversation_history[0].content if session.conversation_history else ""
        })
    
    except Exception as e:
        logger.error(f"Start tutor session error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/send_message', methods=['POST'])
@login_required
def send_tutor_message():
    """Send message to AI tutor"""
    try:
        session_id = request.json.get('session_id')
        message = request.json.get('message')
        
        if not session_id or not message:
            return jsonify({'error': 'Session ID and message are required'}), 400
        
        response = ai_tutor.send_message(session_id, message)
        
        if 'error' in response:
            return jsonify({'error': response['error']}), 400
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Send tutor message error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/get_recommendation', methods=['POST'])
@login_required
def get_recommendation():
    """Get AI study recommendations"""
    try:
        recommendation_type = request.json.get('type', 'study_plan')
        
        if recommendation_type == 'study_plan':
            user_goals = request.json.get('goals', '')
            skill_level = request.json.get('skill_level', 'beginner')
            
            recommendation = ai_provider.generate_study_plan(user_goals, skill_level)
            
        elif recommendation_type == 'problems':
            # Get user stats for problem recommendations
            user_stats = {}
            for ps in current_user.platform_stats:
                user_stats[ps.platform] = {
                    'total_problems': ps.total_problems,
                    'easy_solved': ps.easy_solved,
                    'medium_solved': ps.medium_solved,
                    'hard_solved': ps.hard_solved
                }
            
            weak_areas = request.json.get('weak_areas', [])
            recommendation = ai_provider.generate_problem_recommendation(user_stats, weak_areas)
            
        else:
            return jsonify({'error': 'Invalid recommendation type'}), 400
        
        # Save recommendation
        if 'error' not in recommendation:
            ai_rec = AIRecommendation(
                user_id=current_user.id,
                recommendation_type=recommendation_type,
                content=json.dumps(recommendation),
                extra_data=request.json
            )
            db.session.add(ai_rec)
            db.session.commit()
        
        return jsonify(recommendation)
    
    except Exception as e:
        logger.error(f"Get recommendation error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/generate_flashcards', methods=['POST'])
@login_required
def generate_flashcards():
    """Generate AI flashcards"""
    try:
        topic = request.json.get('topic')
        difficulty = request.json.get('difficulty', 'medium')
        count = request.json.get('count', 5)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        flashcards = ai_provider.generate_flashcards(topic, difficulty)
        flashcards = flashcards[:count]  # Limit to requested count
        
        # Save flashcards to database
        saved_flashcards = []
        for flashcard_data in flashcards:
            flashcard = Flashcard(
                user_id=current_user.id,
                topic=topic,
                question=flashcard_data.get('question', ''),
                answer=flashcard_data.get('answer', ''),
                category=flashcard_data.get('category', ''),
                difficulty=flashcard_data.get('difficulty', difficulty),
                is_ai_generated=True
            )
            db.session.add(flashcard)
            saved_flashcards.append({
                'id': flashcard.id,
                'question': flashcard.question,
                'answer': flashcard.answer,
                'category': flashcard.category,
                'difficulty': flashcard.difficulty
            })
        
        db.session.commit()
        
        return jsonify({
            'flashcards': saved_flashcards,
            'count': len(saved_flashcards)
        })
    
    except Exception as e:
        logger.error(f"Generate flashcards error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# CONTEST ROUTES
# =============================================================================

@contest_bp.route('/')
@login_required
def contests():
    """Contest list (student view)"""
    try:
        contests = Contest.query.filter(
            Contest.is_active == True
        ).order_by(Contest.start_date).all()
        
        return render_template('contests_student.html', contests=contests)
    
    except Exception as e:
        logger.error(f"Contests page error: {e}")
        flash('Error loading contests', 'error')
        return render_template('contests_student.html', contests=[])

@contest_bp.route('/admin')
@login_required
def contests_admin():
    """Admin contest management"""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        contests = Contest.query.order_by(desc(Contest.created_at)).all()
        return render_template('contests_admin.html', contests=contests)
    
    except Exception as e:
        logger.error(f"Admin contests page error: {e}")
        flash('Error loading admin contests', 'error')
        return render_template('contests_admin.html', contests=[])

@contest_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_contest():
    """Create new contest (admin only)"""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        try:
            # Create contest
            contest = Contest(
                title=request.form.get('title'),
                description=request.form.get('description'),
                start_date=datetime.fromisoformat(request.form.get('start_date')),
                duration_minutes=int(request.form.get('duration_minutes')),
                created_by=current_user.id
            )
            
            db.session.add(contest)
            db.session.flush()  # Get contest ID
            
            # Add problems
            problems_data = json.loads(request.form.get('problems', '[]'))
            for problem_data in problems_data:
                problem = ContestProblem(
                    contest_id=contest.id,
                    title=problem_data['title'],
                    description=problem_data['description'],
                    constraints=problem_data.get('constraints', ''),
                    examples=problem_data.get('examples', []),
                    points=problem_data.get('points', 100),
                    time_limit=problem_data.get('time_limit', 1),
                    memory_limit=problem_data.get('memory_limit', 256)
                )
                
                db.session.add(problem)
                db.session.flush()  # Get problem ID
                
                # Add test cases
                test_cases_data = problem_data.get('test_cases', [])
                for test_case_data in test_cases_data:
                    test_case = ContestTestCase(
                        problem_id=problem.id,
                        input_data=test_case_data['input'],
                        expected_output=test_case_data['expected_output'],
                        is_sample=test_case_data.get('is_sample', False)
                    )
                    db.session.add(test_case)
            
            db.session.commit()
            
            # Send notifications to all students
            all_students = User.query.filter_by(role='student').all()
            notification_service.create_bulk_notifications(
                template_key="contest_created",
                user_ids=[s.id for s in all_students],
                context={"contest_title": contest.title},
                contest_id=contest.id
            )
            
            flash('Contest created successfully!', 'success')
            return redirect(url_for('contest.contests_admin'))
        
        except Exception as e:
            logger.error(f"Create contest error: {e}")
            flash('Error creating contest', 'error')
    
    return render_template('create_contest.html')

@contest_bp.route('/<int:contest_id>/participate')
@login_required
def participate_contest(contest_id):
    """Participate in contest"""
    try:
        contest = Contest.query.get_or_404(contest_id)
        
        # Check if user is already participating
        participant = ContestParticipant.query.filter_by(
            contest_id=contest_id,
            user_id=current_user.id
        ).first()
        
        if not participant:
            # Add user as participant
            participant = ContestParticipant(
                contest_id=contest_id,
                user_id=current_user.id
            )
            db.session.add(participant)
            db.session.commit()
        
        # Get contest problems
        problems = ContestProblem.query.filter_by(contest_id=contest_id).all()
        
        return render_template('contest_participate.html',
                             contest=contest,
                             problems=problems,
                             participant=participant)
    
    except Exception as e:
        logger.error(f"Participate contest error: {e}")
        flash('Error joining contest', 'error')
        return redirect(url_for('contest.contests'))

@contest_bp.route('/<int:contest_id>/problem/<int:problem_id>')
@login_required
def contest_problem(contest_id, problem_id):
    """Individual contest problem"""
    try:
        contest = Contest.query.get_or_404(contest_id)
        problem = ContestProblem.query.filter_by(
            contest_id=contest_id,
            id=problem_id
        ).first_or_404()
        
        # Get sample test cases
        sample_test_cases = ContestTestCase.query.filter_by(
            problem_id=problem.id,
            is_sample=True
        ).all()
        
        return render_template('contest_problem.html',
                             contest=contest,
                             problem=problem,
                             sample_test_cases=sample_test_cases)
    
    except Exception as e:
        logger.error(f"Contest problem error: {e}")
        flash('Error loading contest problem', 'error')
        return redirect(url_for('contest.participate_contest', contest_id=contest_id))

@contest_bp.route('/<int:contest_id>/submit', methods=['POST'])
@login_required
def submit_code(contest_id):
    """Submit code for contest problem"""
    try:
        contest = Contest.query.get_or_404(contest_id)
        problem_id = request.json.get('problem_id')
        code = request.json.get('code')
        language = request.json.get('language')
        
        if not all([problem_id, code, language]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get test cases
        test_cases = ContestTestCase.query.filter_by(problem_id=problem_id).all()
        
        if not test_cases:
            return jsonify({'error': 'No test cases found'}), 400
        
        # Prepare test cases for execution
        execution_test_cases = []
        for tc in test_cases:
            execution_test_cases.append({
                'input': tc.input_data,
                'expected_output': tc.expected_output
            })
        
        # Execute code
        execution_result = code_executor.execute_code(code, language, execution_test_cases)
        
        # Create submission record
        submission = ContestSubmission(
            contest_id=contest_id,
            problem_id=problem_id,
            user_id=current_user.id,
            code=code,
            language=language,
            status='completed',
            score=execution_result.get('score', 0),
            execution_time=execution_result.get('execution_time', 0),
            memory_used=execution_result.get('memory_used', 0)
        )
        
        db.session.add(submission)
        db.session.flush()  # Get submission ID
        
        # Record test results
        for i, result in enumerate(execution_result.get('results', [])):
            test_case = test_cases[i]
            test_result = ContestTestResult(
                submission_id=submission.id,
                test_case_id=test_case.id,
                status='passed' if result['status'] == 'passed' else 'failed',
                actual_output=result.get('actual_output', ''),
                error_message=result.get('error'),
                execution_time=result.get('execution_time', 0),
                memory_used=result.get('memory_used', 0)
            )
            db.session.add(test_result)
        
        # Update participant score
        participant = ContestParticipant.query.filter_by(
            contest_id=contest_id,
            user_id=current_user.id
        ).first()
        
        if participant:
            participant.total_score += execution_result.get('score', 0)
            if execution_result.get('score', 0) > 0:
                participant.problems_solved += 1
            participant.last_submission = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'score': execution_result.get('score', 0),
            'results': execution_result.get('results', []),
            'submission_id': submission.id
        })
    
    except Exception as e:
        logger.error(f"Submit code error: {e}")
        return jsonify({'error': str(e)}), 500

@contest_bp.route('/<int:contest_id>/leaderboard')
@login_required
def contest_leaderboard(contest_id):
    """Contest leaderboard"""
    try:
        contest = Contest.query.get_or_404(contest_id)
        
        # Get participants with scores
        participants = ContestParticipant.query.filter_by(contest_id=contest_id)\
            .order_by(desc(ContestParticipant.total_score)).all()
        
        # Assign ranks
        for i, participant in enumerate(participants):
            participant.rank = i + 1
        
        db.session.commit()
        
        return render_template('contest_leaderboard.html',
                             contest=contest,
                             participants=participants)
    
    except Exception as e:
        logger.error(f"Contest leaderboard error: {e}")
        flash('Error loading leaderboard', 'error')
        return redirect(url_for('contest.participate_contest', contest_id=contest_id))

# =============================================================================
# FORUM ROUTES
# =============================================================================

@forum_bp.route('/')
@login_required
def doubts():
    """Forum main page"""
    try:
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        # Build query
        query = ForumPost.query
        
        if category:
            query = query.filter(ForumPost.category == category)
        
        if search:
            query = query.filter(
                ForumPost.title.contains(search) |
                ForumPost.content.contains(search)
            )
        
        # Paginate results
        posts = query.order_by(desc(ForumPost.created_at))\
            .paginate(page=page, per_page=10, error_out=False)
        
        # Get categories for filter
        categories = db.session.query(ForumPost.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('doubts.html',
                             posts=posts,
                             categories=categories,
                             current_category=category,
                             current_search=search)
    
    except Exception as e:
        logger.error(f"Forum page error: {e}")
        flash('Error loading forum', 'error')
        return render_template('doubts.html', posts=None, categories=[])

@forum_bp.route('/question/<int:question_id>')
@login_required
def doubt_detail(question_id):
    """Individual question page"""
    try:
        post = ForumPost.query.get_or_404(question_id)
        
        # Increment view count
        post.views += 1
        db.session.commit()
        
        # Get answers
        answers = ForumAnswer.query.filter_by(post_id=question_id)\
            .order_by(desc(ForumAnswer.votes), ForumAnswer.created_at).all()
        
        # Get discussions
        discussions = QuestionDiscussion.query.filter_by(post_id=question_id)\
            .order_by(QuestionDiscussion.created_at).all()
        
        return render_template('doubt_detail.html',
                             post=post,
                             answers=answers,
                             discussions=discussions)
    
    except Exception as e:
        logger.error(f"Question detail error: {e}")
        flash('Error loading question', 'error')
        return redirect(url_for('forum.doubts'))

@forum_bp.route('/post_question', methods=['POST'])
@login_required
def post_doubt():
    """Post a new question"""
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        category = request.form.get('category')
        tags = request.form.get('tags', '')
        study_group_id = request.form.get('study_group_id')
        
        if not title or not content:
            flash('Title and content are required', 'error')
            return redirect(url_for('forum.doubts'))
        
        # Create post
        post = ForumPost(
            title=title,
            content=content,
            author_id=current_user.id,
            category=category,
            tags=tags,
            study_group_id=int(study_group_id) if study_group_id else None,
            ai_answer_deadline=datetime.now() + timedelta(hours=24)
        )
        
        db.session.add(post)
        db.session.commit()
        
        # Send notification to study group members if applicable
        if study_group_id:
            study_group = StudyGroup.query.get(study_group_id)
            if study_group:
                member_ids = [m.user_id for m in study_group.members]
                notification_service.create_bulk_notifications(
                    template_key="study_group_question",
                    user_ids=member_ids,
                    context={"group_name": study_group.name, "question_title": title},
                    forum_post_id=post.id,
                    study_group_id=int(study_group_id)
                )
        
        flash('Question posted successfully!', 'success')
        return redirect(url_for('forum.doubt_detail', question_id=post.id))
    
    except Exception as e:
        logger.error(f"Post question error: {e}")
        flash('Error posting question', 'error')
        return redirect(url_for('forum.doubts'))

@forum_bp.route('/answer_question', methods=['POST'])
@login_required
def answer_doubt():
    """Answer a question"""
    try:
        post_id = request.form.get('post_id')
        content = request.form.get('content')
        
        if not post_id or not content:
            flash('Missing required fields', 'error')
            return redirect(url_for('forum.doubts'))
        
        # Create answer
        answer = ForumAnswer(
            post_id=int(post_id),
            content=content,
            author_id=current_user.id,
            is_ai_generated=False,
            is_anonymous=True
        )
        
        db.session.add(answer)
        db.session.commit()
        
        # Notify question author
        post = ForumPost.query.get(post_id)
        if post and post.author_id != current_user.id:
            notification_service.create_notification(
                template_key="forum_answer_received",
                user_id=post.author_id,
                context={"question_title": post.title},
                forum_post_id=int(post_id)
            )
        
        flash('Answer posted successfully!', 'success')
        return redirect(url_for('forum.doubt_detail', question_id=post_id))
    
    except Exception as e:
        logger.error(f"Answer question error: {e}")
        flash('Error posting answer', 'error')
        return redirect(url_for('forum.doubts'))

@forum_bp.route('/vote_post', methods=['POST'])
@login_required
def vote_post():
    """Vote on a forum post"""
    try:
        post_id = request.json.get('post_id')
        vote_type = request.json.get('vote_type')  # 'upvote' or 'downvote'
        
        if not post_id or vote_type not in ['upvote', 'downvote']:
            return jsonify({'error': 'Invalid request'}), 400
        
        # Check if user already voted
        existing_vote = ForumPostVote.query.filter_by(
            post_id=post_id,
            user_id=current_user.id
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                # Remove vote
                db.session.delete(existing_vote)
                vote_change = -1 if vote_type == 'upvote' else 1
            else:
                # Change vote
                existing_vote.vote_type = vote_type
                vote_change = 2 if vote_type == 'upvote' else -2
        else:
            # New vote
            vote = ForumPostVote(
                post_id=post_id,
                user_id=current_user.id,
                vote_type=vote_type
            )
            db.session.add(vote)
            vote_change = 1 if vote_type == 'upvote' else -1
        
        # Update post vote count
        post = ForumPost.query.get(post_id)
        if post:
            post.votes += vote_change
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_vote_count': post.votes if post else 0
        })
    
    except Exception as e:
        logger.error(f"Vote post error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# STUDY GROUP ROUTES
# =============================================================================

@study_bp.route('/groups')
@login_required
def study_groups():
    """Study groups page"""
    try:
        # Get user's groups
        user_groups = StudyGroup.query.join(StudyGroupMember)\
            .filter(StudyGroupMember.user_id == current_user.id).all()
        
        # Get other available groups
        available_groups = StudyGroup.query.filter_by(is_active=True)\
            .filter(~StudyGroup.id.in_([g.id for g in user_groups]))\
            .limit(10).all()
        
        return render_template('study_groups.html',
                             user_groups=user_groups,
                             available_groups=available_groups)
    
    except Exception as e:
        logger.error(f"Study groups page error: {e}")
        flash('Error loading study groups', 'error')
        return render_template('study_groups.html', user_groups=[], available_groups=[])

@study_bp.route('/groups/create', methods=['POST'])
@login_required
def create_study_group():
    """Create a new study group"""
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        topic = request.form.get('topic')
        skill_level = request.form.get('skill_level')
        max_members = int(request.form.get('max_members', 10))
        
        if not name:
            flash('Group name is required', 'error')
            return redirect(url_for('study.study_groups'))
        
        # Create study group
        group = StudyGroup(
            name=name,
            description=description,
            topic=topic,
            skill_level=skill_level,
            max_members=max_members,
            created_by=current_user.id
        )
        
        db.session.add(group)
        db.session.flush()  # Get group ID
        
        # Add creator as moderator
        member = StudyGroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role='moderator'
        )
        db.session.add(member)
        db.session.commit()
        
        flash('Study group created successfully!', 'success')
        return redirect(url_for('study.study_groups'))
    
    except Exception as e:
        logger.error(f"Create study group error: {e}")
        flash('Error creating study group', 'error')
        return redirect(url_for('study.study_groups'))

@study_bp.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a study group"""
    try:
        group = StudyGroup.query.get_or_404(group_id)
        
        # Check if group is full
        current_members = len(group.members)
        if current_members >= group.max_members:
            flash('Study group is full', 'error')
            return redirect(url_for('study.study_groups'))
        
        # Check if user is already a member
        existing_member = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if existing_member:
            flash('You are already a member of this group', 'error')
            return redirect(url_for('study.study_groups'))
        
        # Add user as member
        member = StudyGroupMember(
            group_id=group_id,
            user_id=current_user.id,
            role='member'
        )
        
        db.session.add(member)
        db.session.commit()
        
        # Send notification
        notification_service.create_notification(
            template_key="study_group_joined",
            user_id=current_user.id,
            context={"group_name": group.name},
            study_group_id=group_id
        )
        
        flash('Successfully joined the study group!', 'success')
        return redirect(url_for('study.study_groups'))
    
    except Exception as e:
        logger.error(f"Join group error: {e}")
        flash('Error joining study group', 'error')
        return redirect(url_for('study.study_groups'))

@study_bp.route('/groups/<int:group_id>/chat')
@login_required
def group_chat(group_id):
    """Study group chat"""
    try:
        group = StudyGroup.query.get_or_404(group_id)
        
        # Check if user is a member
        member = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if not member:
            flash('You are not a member of this group', 'error')
            return redirect(url_for('study.study_groups'))
        
        # Get chat messages
        messages = GroupChatMessage.query.filter_by(group_id=group_id)\
            .order_by(GroupChatMessage.created_at).limit(50).all()
        
        return render_template('group_chat.html',
                             group=group,
                             messages=messages,
                             user_role=member.role)
    
    except Exception as e:
        logger.error(f"Group chat error: {e}")
        flash('Error loading group chat', 'error')
        return redirect(url_for('study.study_groups'))

@study_bp.route('/groups/<int:group_id>/send_message', methods=['POST'])
@login_required
def send_group_message(group_id):
    """Send message to study group"""
    try:
        group = StudyGroup.query.get_or_404(group_id)
        
        # Check if user is a member
        member = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id
        ).first()
        
        if not member:
            return jsonify({'error': 'Not a member of this group'}), 403
        
        message_text = request.json.get('message')
        if not message_text:
            return jsonify({'error': 'Message is required'}), 400
        
        # Create message
        message = GroupChatMessage(
            group_id=group_id,
            user_id=current_user.id,
            message=message_text,
            message_type='text'
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Send notifications to other members
        other_members = StudyGroupMember.query.filter(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id != current_user.id
        ).all()
        
        for member_obj in other_members:
            notification_service.create_notification(
                template_key="study_group_message",
                user_id=member_obj.user_id,
                context={
                    "group_name": group.name,
                    "sender_name": current_user.username
                },
                study_group_id=group_id
            )
        
        return jsonify({
            'success': True,
            'message_id': message.id,
            'timestamp': message.created_at.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Send group message error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# LEARNING SYSTEM ROUTES
# =============================================================================

@study_bp.route('/revision')
@login_required
def revision():
    """Spaced repetition dashboard"""
    try:
        # Get user statistics
        stats = spaced_repetition_manager.get_user_statistics(current_user.id)
        
        # Get due cards count
        due_count = spaced_repetition_manager.get_due_cards_count(current_user.id)
        
        # Get recent flashcards
        recent_flashcards = Flashcard.query.filter_by(user_id=current_user.id)\
            .order_by(desc(Flashcard.last_reviewed)).limit(10).all()
        
        return render_template('revision.html',
                             stats=stats,
                             due_count=due_count,
                             recent_flashcards=recent_flashcards)
    
    except Exception as e:
        logger.error(f"Revision page error: {e}")
        flash('Error loading revision page', 'error')
        return render_template('revision.html', stats={}, due_count=0, recent_flashcards=[])

@study_bp.route('/flashcards')
@login_required
def edit_flashcards():
    """Flashcard management"""
    try:
        page = request.args.get('page', 1, type=int)
        category = request.args.get('category', '')
        
        # Build query
        query = Flashcard.query.filter_by(user_id=current_user.id)
        
        if category:
            query = query.filter_by(category=category)
        
        # Paginate results
        flashcards = query.order_by(desc(Flashcard.created_at))\
            .paginate(page=page, per_page=20, error_out=False)
        
        # Get categories
        categories = db.session.query(Flashcard.category).filter_by(user_id=current_user.id).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        
        return render_template('edit_flashcards.html',
                             flashcards=flashcards,
                             categories=categories,
                             current_category=category)
    
    except Exception as e:
        logger.error(f"Edit flashcards error: {e}")
        flash('Error loading flashcards', 'error')
        return render_template('edit_flashcards.html', flashcards=None, categories=[])

@study_bp.route('/flashcards/review')
@login_required
def review_flashcards():
    """Flashcard review session"""
    try:
        # Start review session
        session_data = spaced_repetition_manager.start_review_session(
            user_id=current_user.id,
            category=request.args.get('category'),
            max_cards=20
        )
        
        if 'error' in session_data:
            flash(session_data['error'], 'error')
            return redirect(url_for('study.revision'))
        
        return render_template('review_flashcards.html', session=session_data)
    
    except Exception as e:
        logger.error(f"Review flashcards error: {e}")
        flash('Error starting review session', 'error')
        return redirect(url_for('study.revision'))

@study_bp.route('/flashcards/review_card', methods=['POST'])
@login_required
def review_card():
    """Review a flashcard"""
    try:
        session_id = request.json.get('session_id')
        quality = request.json.get('quality', 2)  # Default to 'good'
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        result = spaced_repetition_manager.review_card(session_id, quality)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Review card error: {e}")
        return jsonify({'error': str(e)}), 500

@study_bp.route('/flashcards/create', methods=['POST'])
@login_required
def create_flashcard():
    """Create a new flashcard"""
    try:
        topic = request.form.get('topic')
        question = request.form.get('question')
        answer = request.form.get('answer')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty', 'medium')
        
        if not all([topic, question, answer]):
            flash('Topic, question, and answer are required', 'error')
            return redirect(url_for('study.edit_flashcards'))
        
        # Create flashcard
        flashcard = Flashcard(
            user_id=current_user.id,
            topic=topic,
            question=question,
            answer=answer,
            category=category,
            difficulty=difficulty,
            is_ai_generated=False
        )
        
        db.session.add(flashcard)
        db.session.commit()
        
        flash('Flashcard created successfully!', 'success')
        return redirect(url_for('study.edit_flashcards'))
    
    except Exception as e:
        logger.error(f"Create flashcard error: {e}")
        flash('Error creating flashcard', 'error')
        return redirect(url_for('study.edit_flashcards'))

# =============================================================================
# USER MANAGEMENT ROUTES
# =============================================================================

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        try:
            # Update profile information
            current_user.first_name = request.form.get('first_name')
            current_user.last_name = request.form.get('last_name')
            current_user.bio = request.form.get('bio')
            current_user.learning_goals = request.form.get('learning_goals')
            current_user.target_companies = request.form.get('target_companies')
            current_user.preferred_schedule = request.form.get('preferred_schedule')
            
            # Update platform usernames
            current_user.leetcode_username = request.form.get('leetcode_username')
            current_user.geeksforgeeks_profile = request.form.get('geeksforgeeks_profile')
            current_user.hackerrank_username = request.form.get('hackerrank_username')
            current_user.github_username = request.form.get('github_username')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.profile'))
        
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            flash('Error updating profile', 'error')
    
    return render_template('profile.html')

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    """Notification center"""
    try:
        page = request.args.get('page', 1, type=int)
        
        # Get user notifications
        notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(desc(Notification.created_at))\
            .paginate(page=page, per_page=20, error_out=False)
        
        return render_template('notifications.html', notifications=notifications)
    
    except Exception as e:
        logger.error(f"Notifications page error: {e}")
        flash('Error loading notifications', 'error')
        return render_template('notifications.html', notifications=None)

@dashboard_bp.route('/mark_notification_read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark notification as read"""
    try:
        notification_id = request.json.get('notification_id')
        
        if not notification_id:
            return jsonify({'error': 'Notification ID required'}), 400
        
        success = notification_service.mark_notification_read(notification_id, current_user.id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Notification not found'}), 404
    
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        success = notification_service.mark_all_notifications_read(current_user.id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to mark notifications as read'}), 500
    
    except Exception as e:
        logger.error(f"Mark all notifications read error: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ADMIN ROUTES
# =============================================================================

@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        # Get system statistics
        stats = {
            'total_users': User.query.count(),
            'total_contests': Contest.query.count(),
            'total_forum_posts': ForumPost.query.count(),
            'total_study_groups': StudyGroup.query.count(),
            'total_flashcards': Flashcard.query.count()
        }
        
        # Get notification statistics
        notification_stats = notification_service.get_notification_statistics()
        
        return render_template('admin_dashboard.html',
                             stats=stats,
                             notification_stats=notification_stats)
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'error')
        return render_template('admin_dashboard.html', stats={}, notification_stats={})

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# =============================================================================
# UTILITY ROUTES
# =============================================================================

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

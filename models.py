from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User Management - Main user table"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student/admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    learning_goals = db.Column(db.Text)
    target_companies = db.Column(db.Text)
    preferred_schedule = db.Column(db.String(100))
    
    # Platform usernames
    leetcode_username = db.Column(db.String(100))
    geeksforgeeks_profile = db.Column(db.String(200))
    hackerrank_username = db.Column(db.String(100))
    github_username = db.Column(db.String(100))
    
    # Relationships
    platform_stats = db.relationship('PlatformStats', backref='user', lazy=True, cascade='all, delete-orphan')
    daily_coding_hours = db.relationship('DailyCodingHours', backref='user', lazy=True, cascade='all, delete-orphan')
    problems_solved = db.relationship('ProblemsSolved', backref='user', lazy=True, cascade='all, delete-orphan')
    flashcards = db.relationship('Flashcard', backref='user', lazy=True, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')
    ai_recommendations = db.relationship('AIRecommendation', backref='user', lazy=True, cascade='all, delete-orphan')
    study_groups_created = db.relationship('StudyGroup', backref='creator', lazy=True, foreign_keys='StudyGroup.created_by')
    study_group_members = db.relationship('StudyGroupMember', backref='user', lazy=True, cascade='all, delete-orphan')
    group_chat_messages = db.relationship('GroupChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True, cascade='all, delete-orphan')
    forum_answers = db.relationship('ForumAnswer', backref='author', lazy=True, cascade='all, delete-orphan')
    forum_post_votes = db.relationship('ForumPostVote', backref='user', lazy=True, cascade='all, delete-orphan')
    forum_answer_votes = db.relationship('ForumAnswerVote', backref='user', lazy=True, cascade='all, delete-orphan')
    question_discussions = db.relationship('QuestionDiscussion', backref='user', lazy=True, cascade='all, delete-orphan')
    contests_created = db.relationship('Contest', backref='creator', lazy=True, foreign_keys='Contest.created_by')
    contest_submissions = db.relationship('ContestSubmission', backref='user', lazy=True, cascade='all, delete-orphan')
    contest_participants = db.relationship('ContestParticipant', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class PlatformStats(db.Model):
    """Platform Statistics - Tracks user progress across coding platforms"""
    __tablename__ = 'platform_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # leetcode, geeksforgeeks, hackerrank, github
    total_problems = db.Column(db.Integer, default=0)
    basic_solved = db.Column(db.Integer, default=0)
    easy_solved = db.Column(db.Integer, default=0)
    medium_solved = db.Column(db.Integer, default=0)
    hard_solved = db.Column(db.Integer, default=0)
    contest_rating = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'platform', name='_user_platform_uc'),)

class DailyCodingHours(db.Model):
    """Daily Coding Hours - Tracks daily coding time"""
    __tablename__ = 'daily_coding_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

class Problem(db.Model):
    """Problems - Coding problems from various platforms"""
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Medium, Hard
    category = db.Column(db.String(100))
    url = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    problems_solved = db.relationship('ProblemsSolved', backref='problem', lazy=True, cascade='all, delete-orphan')

class ProblemsSolved(db.Model):
    """Problems Solved - User's solved problems with details"""
    __tablename__ = 'problems_solved'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_taken = db.Column(db.Integer)  # in minutes
    approach_notes = db.Column(db.Text)
    time_complexity = db.Column(db.String(100))
    space_complexity = db.Column(db.String(100))
    personal_rating = db.Column(db.Integer)  # 1-5 scale
    review_notes = db.Column(db.Text)

class Flashcard(db.Model):
    """Flashcards - Spaced repetition learning cards"""
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Spaced repetition fields (SM-2 algorithm)
    last_reviewed = db.Column(db.DateTime)
    next_review = db.Column(db.DateTime)
    repetition_count = db.Column(db.Integer, default=0)
    review_count = db.Column(db.Integer, default=0)
    ease_factor = db.Column(db.Float, default=2.5)
    interval = db.Column(db.Integer, default=1)  # in days
    is_ai_generated = db.Column(db.Boolean, default=False)

class StudySession(db.Model):
    """Study Sessions - Learning session tracking"""
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(50))  # coding, revision, contest
    duration = db.Column(db.Integer)  # in minutes
    topics_covered = db.Column(db.Text)
    problems_solved = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class AIRecommendation(db.Model):
    """AI Recommendations - AI-generated study suggestions"""
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recommendation_type = db.Column(db.String(50))  # study_plan, problem, flashcard
    content = db.Column(db.Text, nullable=False)
    extra_data = db.Column(db.JSON)  # Additional structured data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_applied = db.Column(db.Boolean, default=False)

class StudyGroup(db.Model):
    """Study Groups - Collaborative learning groups"""
    __tablename__ = 'study_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    topic = db.Column(db.String(100))
    skill_level = db.Column(db.String(20), nullable=False)  # Beginner/Intermediate/Advanced
    max_members = db.Column(db.Integer, default=10)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    members = db.relationship('StudyGroupMember', backref='group', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('GroupChatMessage', backref='group', lazy=True, cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='study_group', lazy=True, cascade='all, delete-orphan')

class StudyGroupMember(db.Model):
    """Study Group Members - Group membership management"""
    __tablename__ = 'study_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='member')  # member/moderator
    
    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)

class GroupChatMessage(db.Model):
    """Group Chat Messages - Real-time group communication"""
    __tablename__ = 'group_chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text/file/image
    file_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)

class ForumPost(db.Model):
    """Forum Posts - Anonymous question posting"""
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    study_group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=True)
    category = db.Column(db.String(100))
    tags = db.Column(db.String(500))  # comma-separated tags
    votes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_solved = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=True)  # Always True as per spec
    ai_answer_deadline = db.Column(db.DateTime)  # 24 hours after creation
    
    # Relationships
    answers = db.relationship('ForumAnswer', backref='post', lazy=True, cascade='all, delete-orphan')
    post_votes = db.relationship('ForumPostVote', backref='post', lazy=True, cascade='all, delete-orphan')
    discussions = db.relationship('QuestionDiscussion', backref='post', lazy=True, cascade='all, delete-orphan')

class ForumAnswer(db.Model):
    """Forum Answers - Responses to forum posts"""
    __tablename__ = 'forum_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for AI answers
    votes = db.Column(db.Integer, default=0)
    is_accepted = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    answer_votes = db.relationship('ForumAnswerVote', backref='answer', lazy=True, cascade='all, delete-orphan')

class ForumPostVote(db.Model):
    """Forum Post Votes - Voting on forum posts"""
    __tablename__ = 'forum_post_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.String(20), nullable=False)  # upvote/downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='_post_user_vote_uc'),)

class ForumAnswerVote(db.Model):
    """Forum Answer Votes - Voting on forum answers"""
    __tablename__ = 'forum_answer_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('forum_answers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vote_type = db.Column(db.String(20), nullable=False)  # upvote/downvote
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('answer_id', 'user_id', name='_answer_user_vote_uc'),)

class QuestionDiscussion(db.Model):
    """Question Discussions - Follow-up discussions on forum posts"""
    __tablename__ = 'question_discussions'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=True)

class Contest(db.Model):
    """Contests - Coding contest management"""
    __tablename__ = 'contests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    problems = db.relationship('ContestProblem', backref='contest', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('ContestSubmission', backref='contest', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('ContestParticipant', backref='contest', lazy=True, cascade='all, delete-orphan')

class ContestProblem(db.Model):
    """Contest Problems - Problems within contests"""
    __tablename__ = 'contest_problems'
    
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    constraints = db.Column(db.Text)
    examples = db.Column(db.JSON)  # Array of input/output examples
    points = db.Column(db.Integer, default=100)
    time_limit = db.Column(db.Integer, default=1)  # seconds
    memory_limit = db.Column(db.Integer, default=256)  # MB
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_cases = db.relationship('ContestTestCase', backref='problem', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('ContestSubmission', backref='problem', lazy=True, cascade='all, delete-orphan')

class ContestTestCase(db.Model):
    """Contest Test Cases - Test cases for contest problems"""
    __tablename__ = 'contest_test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('contest_problems.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_sample = db.Column(db.Boolean, default=False)  # Visible to users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_results = db.relationship('ContestTestResult', backref='test_case', lazy=True, cascade='all, delete-orphan')

class ContestSubmission(db.Model):
    """Contest Submissions - User code submissions in contests"""
    __tablename__ = 'contest_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('contest_problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False)  # python/java/cpp/c
    status = db.Column(db.String(30), default='pending')  # pending/running/accepted/wrong_answer/runtime_error/time_limit_exceeded
    score = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float)  # seconds
    memory_used = db.Column(db.Float)  # MB
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_results = db.relationship('ContestTestResult', backref='submission', lazy=True, cascade='all, delete-orphan')

class ContestTestResult(db.Model):
    """Contest Test Results - Results of test case execution"""
    __tablename__ = 'contest_test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('contest_submissions.id'), nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('contest_test_cases.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # passed/failed/error
    actual_output = db.Column(db.Text)
    error_message = db.Column(db.Text)
    execution_time = db.Column(db.Float)
    memory_used = db.Column(db.Float)

class ContestParticipant(db.Model):
    """Contest Participants - Users participating in contests"""
    __tablename__ = 'contest_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_score = db.Column(db.Integer, default=0)
    problems_solved = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    last_submission = db.Column(db.DateTime)
    is_submitted = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('contest_id', 'user_id', name='_contest_user_uc'),)

class Notification(db.Model):
    """Notifications - System notifications for users"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # info/success/warning/error
    category = db.Column(db.String(50), nullable=False)  # contest/forum/study_group/system
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional foreign keys for context
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=True)
    forum_post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=True)
    study_group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=True)

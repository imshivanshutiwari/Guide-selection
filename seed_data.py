"""
Seed Data for Guide Selection Project.
Creates demo users (1 admin, 5 guides, 20 students) with realistic data.
Run: python seed_data.py
"""

import os
import sys
import random
from datetime import datetime, timezone, timedelta

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Student, Guide, Preference, Notification
import bcrypt


def hash_pw(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


RESEARCH_AREAS = [
    'Machine Learning', 'Web Development', 'Cybersecurity', 'Data Science',
    'IoT', 'Cloud Computing', 'Blockchain', 'Computer Vision',
    'NLP', 'Robotics', 'Networks', 'Database Systems'
]

GUIDE_DATA = [
    {
        'name': 'Dr. Rajesh Sharma',
        'email': 'dr.sharma@college.edu',
        'areas': ['Machine Learning', 'Data Science', 'NLP'],
        'capacity': 5,
        'designation': 'Professor',
        'bio': 'Expert in deep learning and natural language processing with 15+ years of experience.',
        'color': '#6C63FF'
    },
    {
        'name': 'Dr. Priya Patel',
        'email': 'dr.patel@college.edu',
        'areas': ['Computer Vision', 'Machine Learning', 'Robotics'],
        'capacity': 4,
        'designation': 'Associate Professor',
        'bio': 'Research focus on autonomous systems and visual perception.',
        'color': '#FF6584'
    },
    {
        'name': 'Dr. Amit Verma',
        'email': 'dr.verma@college.edu',
        'areas': ['Cybersecurity', 'Networks', 'Cloud Computing'],
        'capacity': 5,
        'designation': 'Associate Professor',
        'bio': 'Specializes in network security, penetration testing, and cloud infrastructure.',
        'color': '#43E97B'
    },
    {
        'name': 'Dr. Sneha Gupta',
        'email': 'dr.gupta@college.edu',
        'areas': ['Web Development', 'Database Systems', 'Cloud Computing'],
        'capacity': 4,
        'designation': 'Assistant Professor',
        'bio': 'Full-stack development enthusiast with expertise in scalable web architectures.',
        'color': '#00C9FF'
    },
    {
        'name': 'Dr. Vikram Singh',
        'email': 'dr.singh@college.edu',
        'areas': ['Blockchain', 'IoT', 'Data Science'],
        'capacity': 4,
        'designation': 'Assistant Professor',
        'bio': 'Working on decentralized systems and IoT-based smart solutions.',
        'color': '#F7971E'
    }
]

STUDENT_NAMES = [
    'Rahul Kumar', 'Ananya Mishra', 'Arjun Reddy', 'Priya Singh',
    'Vikash Yadav', 'Sneha Joshi', 'Rohan Mehta', 'Kavya Nair',
    'Aditya Chauhan', 'Ishita Sharma', 'Nikhil Agarwal', 'Riya Kapoor',
    'Saurabh Pandey', 'Megha Tiwari', 'Kunal Shah', 'Pooja Desai',
    'Harsh Vardhan', 'Aarti Bhatia', 'Deepak Jain', 'Simran Kaur'
]

COLORS = ['#6C63FF', '#FF6584', '#43E97B', '#00C9FF', '#F7971E', '#FC5C7D']


def seed():
    with app.app_context():
        # Drop and recreate
        db.drop_all()
        db.create_all()
        print("[DB] Database reset.")

        # ─── Admin ───────────────────────────────────
        admin_user = User(
            name='Admin User',
            email='admin@college.edu',
            password_hash=hash_pw('admin123'),
            role='admin',
            department='Computer Science',
            avatar_color='#FC5C7D'
        )
        db.session.add(admin_user)

        # ─── Guides ─────────────────────────────────
        guide_objects = []
        for gd in GUIDE_DATA:
            user = User(
                name=gd['name'],
                email=gd['email'],
                password_hash=hash_pw('guide123'),
                role='guide',
                department='Computer Science',
                avatar_color=gd['color']
            )
            db.session.add(user)
            db.session.flush()

            guide = Guide(
                user_id=user.id,
                capacity=gd['capacity'],
                current_load=0,
                bio=gd['bio'],
                designation=gd['designation']
            )
            guide.research_areas = gd['areas']
            db.session.add(guide)
            db.session.flush()
            guide_objects.append(guide)

            # Welcome notification
            notif = Notification(
                user_id=user.id, type='info', title='Welcome!',
                message=f'Welcome to GuideSelect, {gd["name"]}! Update your profile to attract students.'
            )
            db.session.add(notif)

        print(f"[GUIDES] Created {len(guide_objects)} guides.")

        # ─── Students ───────────────────────────────
        student_objects = []
        for i, name in enumerate(STUDENT_NAMES):
            email = name.lower().replace(' ', '.') + '@student.edu'
            if i == 0:
                email = 'rahul@student.edu'  # Easy login for demo

            cgpa = round(random.uniform(6.0, 9.8), 2)
            interests = random.sample(RESEARCH_AREAS, k=random.randint(2, 4))

            user = User(
                name=name,
                email=email,
                password_hash=hash_pw('student123'),
                role='student',
                department='Computer Science',
                avatar_color=random.choice(COLORS),
                created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
            )
            db.session.add(user)
            db.session.flush()

            student = Student(
                user_id=user.id,
                cgpa=cgpa,
                enrollment_number=f'CS2023{100+i}'
            )
            student.area_of_interest = interests
            db.session.add(student)
            db.session.flush()
            student_objects.append(student)

            # Welcome notification
            notif = Notification(
                user_id=user.id, type='success', title='Welcome!',
                message=f'Welcome {name}! Submit your guide preferences to get started.'
            )
            db.session.add(notif)

        print(f"[STUDENTS] Created {len(student_objects)} students.")

        # ─── Preferences (for 15 students) ──────────
        pref_count = 0
        for student in student_objects[:15]:
            # Pick 3 random guides for preferences
            chosen = random.sample(guide_objects, k=3)
            pref = Preference(
                student_id=student.id,
                choice_1_id=chosen[0].id,
                choice_2_id=chosen[1].id,
                choice_3_id=chosen[2].id,
                submitted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 10))
            )
            db.session.add(pref)
            pref_count += 1

        print(f"[PREFS] Created {pref_count} preference submissions.")

        # Admin notification
        admin_notif = Notification(
            user_id=admin_user.id, type='info', title='System Ready',
            message=f'System initialized with {len(student_objects)} students and {len(guide_objects)} guides. '
                    f'{pref_count} preferences submitted. Ready to run matching!'
        )
        db.session.add(admin_notif)

        db.session.commit()
        print("[OK] Seeding complete!")
        print("\n-- Demo Login Credentials --")
        print("Admin:   admin@college.edu / admin123")
        print("Guide:   dr.sharma@college.edu / guide123")
        print("Student: rahul@student.edu / student123")
        print("\nRun the app with: python app.py")


if __name__ == '__main__':
    seed()

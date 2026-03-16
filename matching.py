"""
Guide Selection Matching Algorithm.
Implements a 3-phase allocation engine:
  Phase 1: Preference-Based Greedy
  Phase 2: Gale-Shapley Stable Matching
  Phase 3: Fallback Pool for Admin
"""

from datetime import datetime, timezone


def run_matching(db, Student, Guide, Preference, Allocation, Notification, AuditLog):
    """
    Execute the full 3-phase matching algorithm.
    Returns a summary dict with statistics.
    """
    # Clear previous allocations
    Allocation.query.delete()
    # Reset guide loads
    for guide in Guide.query.all():
        guide.current_load = 0
    db.session.commit()

    stats = {
        'phase1_matched': 0,
        'phase2_matched': 0,
        'unmatched': 0,
        'total_students': 0,
        'details': []
    }

    # Get all students who have submitted preferences
    students_with_prefs = Student.query.join(Preference).all()
    stats['total_students'] = len(students_with_prefs)

    # ─── Phase 1: Preference-Based Greedy ────────────────────────
    # Sort students by priority score (CGPA + early submission bonus) descending
    students_with_prefs.sort(key=lambda s: s.priority_score, reverse=True)

    allocated_student_ids = set()

    for student in students_with_prefs:
        pref = student.preference
        if not pref:
            continue

        choices = [
            (pref.choice_1_id, 1),
            (pref.choice_2_id, 2),
            (pref.choice_3_id, 3),
        ]

        matched = False
        for guide_id, rank in choices:
            if guide_id is None:
                continue
            guide = db.session.get(Guide, guide_id)
            if guide and not guide.is_full:
                # Allocate!
                alloc = Allocation(
                    student_id=student.id,
                    guide_id=guide.id,
                    status='allocated',
                    method='greedy',
                    preference_rank=rank,
                    allocated_at=datetime.now(timezone.utc)
                )
                db.session.add(alloc)
                guide.current_load += 1
                allocated_student_ids.add(student.id)
                stats['phase1_matched'] += 1
                stats['details'].append({
                    'student': student.user.name,
                    'guide': guide.user.name,
                    'phase': 1,
                    'rank': rank,
                    'method': 'greedy'
                })
                matched = True
                break

    db.session.commit()

    # ─── Phase 2: Gale-Shapley Stable Matching ───────────────────
    # Collect unmatched students
    unmatched_students = [s for s in students_with_prefs if s.id not in allocated_student_ids]

    if unmatched_students:
        gale_shapley_results = _gale_shapley(unmatched_students, Guide.query.all(), db)

        for student_id, guide_id in gale_shapley_results.items():
            student = db.session.get(Student, student_id)
            guide = db.session.get(Guide, guide_id)
            if student and guide and not guide.is_full:
                # Determine which preference rank this was
                pref = student.preference
                rank = 0
                if pref:
                    if pref.choice_1_id == guide_id:
                        rank = 1
                    elif pref.choice_2_id == guide_id:
                        rank = 2
                    elif pref.choice_3_id == guide_id:
                        rank = 3

                alloc = Allocation(
                    student_id=student.id,
                    guide_id=guide.id,
                    status='allocated',
                    method='gale-shapley',
                    preference_rank=rank,
                    allocated_at=datetime.now(timezone.utc)
                )
                db.session.add(alloc)
                guide.current_load += 1
                allocated_student_ids.add(student.id)
                stats['phase2_matched'] += 1
                stats['details'].append({
                    'student': student.user.name,
                    'guide': guide.user.name,
                    'phase': 2,
                    'rank': rank,
                    'method': 'gale-shapley'
                })

        db.session.commit()

    # ─── Phase 3: Fallback Pool ──────────────────────────────────
    still_unmatched = [s for s in students_with_prefs if s.id not in allocated_student_ids]
    stats['unmatched'] = len(still_unmatched)

    for student in still_unmatched:
        stats['details'].append({
            'student': student.user.name,
            'guide': 'Unmatched (Fallback Pool)',
            'phase': 3,
            'rank': 0,
            'method': 'fallback'
        })

    # Create notifications
    for student in students_with_prefs:
        alloc = Allocation.query.filter_by(student_id=student.id).first()
        if alloc:
            guide = db.session.get(Guide, alloc.guide_id)
            notif = Notification(
                user_id=student.user_id,
                type='success',
                title='Guide Allocated!',
                message=f'You have been allocated to {guide.user.name} (Choice #{alloc.preference_rank}).'
                        if alloc.preference_rank > 0
                        else f'You have been allocated to {guide.user.name} via stable matching.'
            )
            db.session.add(notif)

            # Notify guide too
            guide_notif = Notification(
                user_id=guide.user_id,
                type='info',
                title='New Student Allocated',
                message=f'{student.user.name} (CGPA: {student.cgpa}) has been allocated to you.'
            )
            db.session.add(guide_notif)
        else:
            notif = Notification(
                user_id=student.user_id,
                type='warning',
                title='Allocation Pending',
                message='You are in the fallback pool. Admin will manually assign your guide.'
            )
            db.session.add(notif)

    # Audit log
    audit = AuditLog(
        actor_id=None,
        action='matching_algorithm_run',
        target='all_students',
        details=f'Phase 1: {stats["phase1_matched"]}, Phase 2: {stats["phase2_matched"]}, Unmatched: {stats["unmatched"]}'
    )
    db.session.add(audit)
    db.session.commit()

    return stats


def _gale_shapley(unmatched_students, all_guides, db):
    """
    Run the Gale-Shapley algorithm for stable matching.
    Students propose to guides. Guides accept/reject based on applicant score.

    Returns: dict of {student_id: guide_id} matchings
    """
    # Build student preference lists
    student_prefs = {}  # student_id -> [guide_id, ...]
    for student in unmatched_students:
        pref = student.preference
        if pref:
            student_prefs[student.id] = [g for g in pref.choices if g is not None]
        else:
            student_prefs[student.id] = []

    # Build guide preference rankings (based on applicant score)
    guide_rankings = {}  # guide_id -> {student_id: score}
    available_guides = {g.id: g for g in all_guides if not g.is_full}

    for guide in available_guides.values():
        guide_rankings[guide.id] = {}
        for student in unmatched_students:
            guide_rankings[guide.id][student.id] = guide.applicant_score(student)

    # Gale-Shapley algorithm
    # Each student proposes to guides in order; guides tentatively accept the best
    free_students = list(student_prefs.keys())
    proposal_index = {sid: 0 for sid in free_students}  # next guide to propose to
    current_match = {}  # guide_id -> student_id (tentative)
    student_match = {}  # student_id -> guide_id (final)

    max_iterations = len(free_students) * 10  # safety limit
    iteration = 0

    while free_students and iteration < max_iterations:
        iteration += 1
        student_id = free_students[0]
        prefs = student_prefs.get(student_id, [])
        idx = proposal_index.get(student_id, 0)

        if idx >= len(prefs):
            # Exhausted all preferences
            free_students.pop(0)
            continue

        guide_id = prefs[idx]
        proposal_index[student_id] = idx + 1

        if guide_id not in available_guides:
            continue

        guide = available_guides[guide_id]

        if guide_id not in current_match:
            # Guide is free, tentatively accept
            current_match[guide_id] = student_id
            student_match[student_id] = guide_id
            free_students.pop(0)
        else:
            # Guide already matched — compare
            current_student_id = current_match[guide_id]
            current_score = guide_rankings.get(guide_id, {}).get(current_student_id, 0)
            new_score = guide_rankings.get(guide_id, {}).get(student_id, 0)

            if new_score > current_score:
                # Replace: new student is better
                current_match[guide_id] = student_id
                student_match[student_id] = guide_id
                # Old student becomes free again
                if current_student_id in student_match:
                    del student_match[current_student_id]
                free_students.pop(0)
                free_students.append(current_student_id)
            else:
                # Rejected, student stays free and tries next preference
                pass  # Will loop again with next preference

    return student_match

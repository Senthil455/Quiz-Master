from flask import Response
from io import BytesIO
import openpyxl
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from collections import defaultdict

import psycopg2



app = Flask(__name__)
app.secret_key = "your_secret_key"

TEACHER_SUPERKEY="1"
STUDENT_DOMAIN = "@student.annauniv.edu"
TEACHER_DOMAIN = "@faculty.annauniv.edu"

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="quizdb",
        user="postgres",
        password="GANGSTER_GANESH"
    )

@app.route('/', methods=['GET', 'POST'])
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE email=%s AND passwordhash=%s', (email, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]

            if user[4] == 'student':
                return redirect(url_for('student_dashboard'))

            elif user[4] == 'teacher':
                # approved column can be None (pending), False (rejected), True (approved)
                if user[6] is None:
                    flash("Teacher account status pending. Please wait for admin approval.", "info")
                    return render_template('login.html', form_data=request.form)
                elif user[6] is False:
                    flash("Teacher account rejected by admin.", "error")
                    return render_template('login.html', form_data=request.form)
                elif user[6] is True:
                    return redirect(url_for('teacher_dashboard'))

            else:  # For admin users and others
                return redirect(url_for('admin_dashboard'))

        else:
            flash("Invalid email or password.", "error")
            return render_template('login.html', form_data=request.form)

    # GET request rendering login page with empty form
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        classy = request.form.get('class')
        teacher_key = request.form.get('teacher_key', '')

        # Basic input validations
        if not username or not email or not password or not role or not classy:
            flash("Please fill out all the required fields.", "error")
            return render_template('register.html', form_data=request.form)
        if role == "admin":
            flash("Online admin registration is not allowed. Please contact an existing admin.", "error")
            return render_template('register.html', form_data=request.form)
        if role == "teacher":
            if not email.endswith(TEACHER_DOMAIN):
                flash(f"Teachers must register using a {TEACHER_DOMAIN} email.", "error")
                return render_template('register.html', form_data=request.form)
            if teacher_key != TEACHER_SUPERKEY:
                flash("Invalid teacher registration code.", "error")
                return render_template('register.html', form_data=request.form)
        if role == "student":
            if not email.endswith(STUDENT_DOMAIN):
                flash(f"Students must register using a {STUDENT_DOMAIN} email.", "error")
                return render_template('register.html', form_data=request.form)

        conn = get_db_connection()
        cur = conn.cursor()

        # Check duplicate email
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            # If user is a rejected teacher, reset approval to pending with new password
            if existing_user[4] == 'teacher' and existing_user[6] == False:
                cur.execute("UPDATE users SET approved = NULL, passwordhash = %s WHERE email = %s", (password, email))
                conn.commit()
                cur.close()
                conn.close()
                flash("Your previous rejection was reset, please wait for admin approval.", "info")
                return redirect(url_for('login'))
            else:
                cur.close()
                conn.close()
                flash("Email already registered. Please login or use another email.", "error")
                return render_template('register.html', form_data=request.form)


        if role == 'teacher':
            approved = None  # Pending approval by default for teachers
        else:
            approved = True  # Auto-approved for others (students/admin)


        # Insert user
        cur.execute(
            'INSERT INTO users (name, email, passwordhash, role, class, approved) VALUES (%s, %s, %s, %s, %s, %s)',
            (username, email, password, role, classy, approved)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Registered successfully! Please login.", "success")
        return redirect(url_for('login'))

    # On GET, show page with no pre-filled data
    return render_template('register.html')

@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Handle enrollment request FIRST (POST)
    if request.method == 'POST':
        class_to_enroll = request.form.get('class_to_enroll')

        # Find status of the latest enrollment request for this class
        cur.execute('''
            SELECT approved FROM enrollments 
            WHERE studentid=%s AND class=%s 
            ORDER BY requested_at DESC LIMIT 1
        ''', (user_id, class_to_enroll))
        latest = cur.fetchone()

        if latest:
            if latest[0] is None:
                flash(f"You already have a pending enrollment request for '{class_to_enroll}'.", "warning")
            elif latest[0] is True:
                flash(f"You are already enrolled in '{class_to_enroll}'.", "info")
            else:  # latest[0] == False (rejected), allow to reapply
                cur.execute('''
                    INSERT INTO enrollments (studentid, class, approved, requested_at) 
                    VALUES (%s, %s, NULL, NOW())
                ''', (user_id, class_to_enroll))
                conn.commit()
                flash(f"Enrollment request reapplied for '{class_to_enroll}'.", "success")
        else:
            cur.execute('''
                INSERT INTO enrollments (studentid, class, approved, requested_at)
                VALUES (%s, %s, NULL, NOW())
            ''', (user_id, class_to_enroll))
            conn.commit()
            flash(f"Enrollment request for '{class_to_enroll}' submitted!", "success")

        cur.close()
        conn.close()
        return redirect(url_for('student_dashboard'))

    # GET REQUEST - Fetch all data

    # Get all available classes
    cur.execute("""
        SELECT tc.class, tc.subject, u.name AS teacher_name
        FROM teacher_classes tc
        JOIN users u ON tc.teacherid = u.userid
    """)
    available_classes = cur.fetchall()

    # Get student info
    cur.execute('SELECT name, email, role FROM users WHERE userid=%s', (user_id,))
    student = cur.fetchone()

    # Get all classes student is enrolled in (for filtering quizzes)
    cur.execute('SELECT class FROM enrollments WHERE studentid=%s AND approved=TRUE', (user_id,))
    student_classes = [row[0] for row in cur.fetchall()]

    # Get all requests for this student (approved, pending, rejected)
    cur.execute('SELECT class, approved, requested_at FROM enrollments WHERE studentid=%s ORDER BY requested_at DESC', (user_id,))
    rows = cur.fetchall()
    
    # Get recent attempts with id, title, score
    cur.execute('''
        SELECT q.title, a.score, a.attemptid FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE a.studentid=%s AND a.score IS NOT NULL
        ORDER BY a.endtime DESC LIMIT 5
    ''', (user_id,))
    recent_results = cur.fetchall()

    # Get attempt IDs which already have feedback submitted by this student
    cur.execute('''
        SELECT attemptid FROM feedback WHERE studentid = %s
    ''', (user_id,))
    feedback_attempt_rows = cur.fetchall()
    feedback_attempt_ids = {row[0] for row in feedback_attempt_rows}

    # Latest status per class
    status_by_class = defaultdict(list)
    for cls, approved, req_time in rows:
       status_by_class[cls].append((req_time, approved))

    pending_enrollment_classes = []
    rejected_enrollment_classes = []

    for cls, statlist in status_by_class.items():
      # sort by request time DESC so latest first
      statlist.sort(reverse=True)
      latest_approved = statlist[0][1]
      if latest_approved is None:
        pending_enrollment_classes.append(cls)
      elif latest_approved is False:
        rejected_enrollment_classes.append(cls)
    # else skip (approved classes aren't shown)
        # don't show approved classes in registration cards

    # Get enrolled classes with details for "My Classes" section
    cur.execute("""
        SELECT DISTINCT e.class, tc.subject
        FROM enrollments e
        LEFT JOIN teacher_classes tc ON e.class = tc.class
        WHERE e.studentid=%s AND e.approved=TRUE
        ORDER BY e.class
    """, (user_id,))
    enrolled_classes = cur.fetchall()
    enrollment_dict = {cls: True for cls, _ in enrolled_classes}

    # Completed quizzes
    cur.execute('SELECT COUNT(*) FROM attempts WHERE studentid=%s AND score IS NOT NULL', (user_id,))
    completed_quizzes = cur.fetchone()[0]

    # Average score
    cur.execute('SELECT AVG(score) FROM attempts WHERE studentid=%s AND score IS NOT NULL', (user_id,))
    avg_score = cur.fetchone()[0] or 0

    # Pending quizzes
    if student_classes:
        format_strings = ','.join(['%s'] * len(student_classes))
        cur.execute(f'''
            SELECT COUNT(*) FROM quizzes AS q
            WHERE q.class IN ({format_strings})
            AND q.isdraft = FALSE
            AND q.quizid NOT IN (
                SELECT quizid FROM attempts WHERE studentid=%s AND score IS NOT NULL
            )
        ''', (*student_classes, user_id))
        pending_quizzes = cur.fetchone()[0]
    else:
        pending_quizzes = 0

    # Best score
    cur.execute('SELECT MAX(score) FROM attempts WHERE studentid=%s AND score IS NOT NULL', (user_id,))
    best_score = cur.fetchone()[0] or 0

    # Upcoming quizzes
    upcoming_quizzes = []
    if student_classes:
        cur.execute(f'''
            SELECT quizid, title, availablefrom, availableto, class FROM quizzes
            WHERE class IN ({format_strings})
            AND isdraft = FALSE
            AND quizid NOT IN (
                SELECT quizid FROM attempts WHERE studentid=%s AND score IS NOT NULL
            )
            ORDER BY availablefrom ASC
        ''', (*student_classes, user_id))
        upcoming_quizzes = cur.fetchall()

    # Recent results
    cur.execute('''
       SELECT q.title, a.score, a.attemptid FROM attempts a
       JOIN quizzes q ON a.quizid = q.quizid
       WHERE a.studentid=%s AND a.score IS NOT NULL
       ORDER BY a.endtime DESC LIMIT 5
    ''', (user_id,))
    recent_results = cur.fetchall()


    cur.close()
    conn.close()

    return render_template(
        'student_dashboard.html',
        name=student[0],
        email=student[1],
        role=student[2],
        available_classes=available_classes,
        student_classes=student_classes,
        enrolled_classes=enrolled_classes,
        completed_quizzes=completed_quizzes,
        avg_score=avg_score,
        pending_quizzes=pending_quizzes,
        best_score=best_score,
        upcoming_quizzes=upcoming_quizzes,
        recent_results=recent_results,
        enrollment_dict=enrollment_dict,
        rejected_enrollment_classes=rejected_enrollment_classes,
        feedback_attempt_ids=feedback_attempt_ids,
        pending_enrollment_classes=pending_enrollment_classes
    )

@app.route('/teacher_dashboard')
def teacher_dashboard():
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get teacher details with class
    cur.execute('SELECT name, email, role, class FROM users WHERE userid=%s', (user_id,))
    teacher = cur.fetchone()

    # Extract teacher info - handle if class is missing
    teacher_name = teacher[0]
    teacher_email = teacher[1]
    teacher_role = teacher[2]
    classy = teacher[3] if len(teacher) > 3 and teacher[3] else "Not Assigned"

    # Get teacher's managed classes and subjects
    cur.execute('SELECT class, subject FROM teacher_classes WHERE teacherid=%s', (user_id,))
    managed_classes = cur.fetchall()

    # Extract class list for queries
    managed_class_list = [cls[0] for cls in managed_classes]

    # Total quizzes created by teacher
    cur.execute('SELECT COUNT(*) FROM quizzes WHERE createdby=%s', (user_id,))
    total_quizzes = cur.fetchone()[0]

    # Active quizzes (not draft and available now)
    cur.execute("""
        SELECT COUNT(*) FROM quizzes 
        WHERE createdby=%s AND isdraft=FALSE AND availableto >= NOW()
    """, (user_id,))
    active_quizzes = cur.fetchone()[0]
    cur.execute("""
        SELECT quizid, title FROM quizzes WHERE createdby = %s
    """, (user_id,))
    quiz_ids_titles = cur.fetchall()  # [(quizid, title), ...]

    # Initialize grouped results
    grouped_attempts = {title: [] for _, title in quiz_ids_titles}

    # Fetch all attempts for quizzes created by this teacher
    cur.execute("""
        SELECT q.quizid, q.title, u.name, u.email, a.score, a.endtime 
        FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        JOIN users u ON a.studentid = u.userid
        WHERE q.createdby = %s AND a.score IS NOT NULL
        ORDER BY q.title, a.endtime DESC
    """, (user_id,))

    for quizid, title, student_name, student_email, score, endtime in cur.fetchall():
        grouped_attempts[title].append({
            "student_name": student_name,
            "student_email": student_email,
            "score": score,
            "endtime": endtime
        })

    # Total students in teacher's classes
    if managed_class_list:
        cur.execute("""
            SELECT COUNT(*) FROM users 
            WHERE class = ANY(%s) AND role='student'
        """, (managed_class_list,))
        total_students = cur.fetchone()[0]
    else:
        total_students = 0

    # Average score across all student attempts in teacher's quizzes
    cur.execute("""
        SELECT AVG(a.score) 
        FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE q.createdby = %s AND a.score IS NOT NULL
    """, (user_id,))
    avg_score = cur.fetchone()[0] or 0
    # Assuming user_id is teacher's ID
    '''cur.execute("""
        SELECT f.feedbackid, f.feedback, f.comments, f.createdat,
               u.name AS student_name, q.title AS quiz_title
        FROM feedback f
        JOIN users u ON f.studentid = u.userid
        JOIN attempts a ON f.attemptid = a.attemptid
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE f.teacherid = %s
        ORDER BY f.createdat DESC
    """, (user_id,))
    feedbacks = cur.fetchall() '''
    # Fetch feedback tuples
    cur.execute("""
        SELECT f.feedbackid, f.feedback, f.comments, f.createdat,
               u.name AS student_name, q.title AS quiz_title
        FROM feedback f
        JOIN users u ON f.studentid = u.userid
        JOIN attempts a ON f.attemptid = a.attemptid
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE f.teacherid = %s
        ORDER BY f.createdat DESC
    """, (user_id,))
    feedback_rows = cur.fetchall()

    # Convert tuples to dicts to ease templating with attribute access
    feedbacks = []
    for row in feedback_rows:
        feedbacks.append({
            'feedbackid': row[0],
            'feedback': row[1],
            'comments': row[2],
            'createdat': row[3],
            'student_name': row[4],
            'quiz_title': row[5],
        })
    # List of quizzes created (with explicit column selection)
    cur.execute("""
        SELECT quizid, title, description, availablefrom, availableto, 
               attemptlimit, isdraft, class 
        FROM quizzes 
        WHERE createdby=%s 
        ORDER BY availablefrom DESC
    """, (user_id,))
    quiz_list = cur.fetchall()
    quiz_list = sorted(quiz_list, key=lambda q: q[0], reverse=True)


    # Recent student attempts (latest 5)
    cur.execute("""
        SELECT u.name, q.title, a.score, a.endtime
        FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        JOIN users u ON a.studentid = u.userid
        WHERE q.createdby = %s AND a.score IS NOT NULL
        ORDER BY a.endtime DESC 
        LIMIT 5
    """, (user_id,))
    recent_attempts = cur.fetchall()
    # Before closing the cursor in your route
    if managed_class_list:
        cur.execute("""
            SELECT COUNT(*) FROM enrollments
            WHERE approved IS NULL AND class = ANY(%s)
        """, (managed_class_list,))
        num_pending_enrollments = cur.fetchone()[0]


    else:
        num_pending_enrollments = 0

    cur.close()
    conn.close()

    return render_template(
        'teacher_dashboard.html',
        name=teacher_name,
        email=teacher_email,
        role=teacher_role,
        classy=classy,
        managed_classes=managed_classes,
        total_quizzes=total_quizzes,
        active_quizzes=active_quizzes,
        total_students=total_students,
        avg_score=round(avg_score, 2),
        quiz_list=quiz_list,
        num_pending_enrollments=num_pending_enrollments,
        grouped_attempts=grouped_attempts,
        feedbacks=feedbacks,
        recent_attempts=recent_attempts
    )


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != "admin":
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get admin details
    cur.execute('SELECT name, email FROM users WHERE userid=%s', (user_id,))
    admin_row = cur.fetchone()
    name = admin_row[0]
    email = admin_row[1]

    # Handle form POST actions: approve, reject, deactivate, export
    if request.method == 'POST':
        if 'approveteacher' in request.form:
            try:
                teacher_id = int(request.form.get('approveteacher'))
                cur.execute("UPDATE users SET approved = TRUE WHERE userid = %s", (teacher_id,))
                conn.commit()
                flash("Teacher approved successfully.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Could not approve teacher: {str(e)}", "error")

        elif 'rejectteacher' in request.form:
            try:
                teacher_id = int(request.form.get('rejectteacher'))
                cur.execute("UPDATE users SET approved = FALSE WHERE userid = %s", (teacher_id,))
                conn.commit()
                flash("Teacher rejected and deactivated.", "warning")
            except Exception as e:
                conn.rollback()
                flash(f"Could not reject teacher: {str(e)}", "error")

        elif 'deactivateuser' in request.form:
            try:
                user_id_to_deactivate = int(request.form.get('deactivateuser'))
                cur.execute("UPDATE users SET approved = FALSE WHERE userid = %s", (user_id_to_deactivate,))
                conn.commit()
                flash("User deactivated successfully.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Could not deactivate user: {str(e)}", "error")

        elif 'export_report' in request.form:
            cur.execute("SELECT * FROM quizzes")
            quizzes = cur.fetchall()
            # Add CSV export logic here as needed
            flash("Quiz report exported.", "success")

    # Retrieve users excluding rejected for main user management list
    cur.execute("SELECT userid, name, email, role, approved FROM users WHERE approved IS NULL OR approved = TRUE ORDER BY role, name")
    users = cur.fetchall()
    users = [dict(id=u[0], name=u[1], email=u[2], role=u[3], approved=u[4]) for u in users]

    # Retrieve rejected teachers separately
    cur.execute("SELECT userid, name, email, role FROM users WHERE role='teacher' AND approved = FALSE ORDER BY name")
    rejected_teachers = cur.fetchall()
    rejected_teachers = [dict(id=rt[0], name=rt[1], email=rt[2], role=rt[3]) for rt in rejected_teachers]

    # System-wide stats
    cur.execute("SELECT COUNT(*) FROM quizzes")
    quizzes_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT class) FROM users WHERE class IS NOT NULL")
    classes_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attempts WHERE endtime > (CURRENT_DATE - INTERVAL '7 days')")
    attempts_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template('admin_dashboard.html',
                           users=users,
                           rejected_teachers=rejected_teachers,
                           name=name,
                           email=email,
                           quizzes=quizzes_count,
                           classes=classes_count,
                           attempts=attempts_count)
       

@app.route('/export_quizzes', methods=['POST'])
def export_quizzes():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != "admin":
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT q.quizid, q.title, q.description, q.class, q.availablefrom, q.availableto, u.name AS teacher
        FROM quizzes q
        LEFT JOIN users u ON q.createdby = u.userid
    """)
    quizzes = cur.fetchall()
    cur.close()
    conn.close()

    # Create an Excel workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Quizzes"

    # Write header
    ws.append(['Quiz ID', 'Title', 'Description', 'Class', 'Available From', 'Available To', 'Teacher'])

    # Write data
    for row in quizzes:
        ws.append(row)

    # Prepare Excel file in memory
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=quiz_report.xlsx"}
    )

@app.route('/request_enrollment', methods=['POST'])
def request_enrollment():
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != 'student':
        return redirect(url_for('login'))

    requested_class = request.form.get('class_to_enroll').strip()

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if enrollment request already sent
    cur.execute(
        "SELECT * FROM enrollments WHERE studentid=%s AND class=%s AND approved=FALSE",
        (user_id, requested_class)
    )
    exists = cur.fetchone()
    if exists:
        flash("You already have a pending enrollment request for this class.", "warning")
    else:
        cur.execute(
            "INSERT INTO enrollments (studentid, class, approved) VALUES (%s, %s, FALSE)",
            (user_id, requested_class)
        )
        conn.commit()
        flash(f"Enrollment request submitted for class {requested_class}.", "success")

    cur.close()
    conn.close()
    return redirect(url_for('student_dashboard'))


@app.route('/pending_enrollments', methods=['GET', 'POST'])
def pending_enrollments():
    """
    Handles displaying pending enrollment requests for classes managed by the teacher,
    and processing 'approve' or 'reject' actions.
    """
    user_id = session.get('user_id')
    role = session.get('role')
    
    # 1. Authorization Check
    if not user_id or role != 'teacher':
        flash("You must be logged in as a teacher to view this page.", "error")
        return redirect(url_for('login'))

    conn = None
    cur = None
    requests = [] # Initialize requests list for safety

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all classes this teacher manages
        cur.execute("SELECT class FROM teacher_classes WHERE teacherid = %s", (user_id,))
        classes = [row[0] for row in cur.fetchall()]

        # Redirect if no assigned classes
        if not classes:
            flash("You are not assigned to any classes.", "error")
            # The finally block will handle closing the connection/cursor
            return redirect(url_for('teacher_dashboard'))

        if request.method == 'POST':
            # Input validation for POST request
            enrollment_id_str = request.form.get('enrollment_id')
            action = request.form.get('action')

            if not enrollment_id_str or not action:
                flash("Invalid request. Missing enrollment ID or action.", "error")
                return redirect(url_for('pending_enrollments'))

            try:
                enrollment_id = int(enrollment_id_str)
            except ValueError:
                flash("Invalid enrollment ID format.", "error")
                return redirect(url_for('pending_enrollments'))

            # Check if the enrollment request is for one of the teacher's classes before proceeding
            # This is a critical security check to prevent one teacher approving enrollments for another's class.
            cur.execute("""
                SELECT 1 
                FROM enrollments e
                JOIN teacher_classes tc ON e.class = tc.class
                WHERE e.enrollmentid = %s AND tc.teacherid = %s
            """, (enrollment_id, user_id))
            
            if not cur.fetchone():
                flash("Enrollment request not found or does not belong to your class.", "error")
                return redirect(url_for('pending_enrollments'))
            
            if action == 'approve':
                cur.execute("UPDATE enrollments SET approved = TRUE WHERE enrollmentid = %s", (enrollment_id,))
                conn.commit()
                flash("Enrollment approved.", "success")
            elif action == 'reject':
                cur.execute("UPDATE enrollments SET approved = FALSE WHERE enrollmentid = %s", (enrollment_id,))
                conn.commit()
                flash("Enrollment rejected.", "warning")

            else:
                flash("Invalid action specified.", "error")

            # After POST, redirect to avoid form resubmission
            # The finally block will close the connection
            return redirect(url_for('pending_enrollments'))

        # GET request: Fetch pending enrollments only for classes this teacher manages
        # We use classes = ANY(%s) which is a standard PostgreSQL array check syntax 
        # when passing a Python list of strings (`classes`) to psycopg2.
        if classes:
            cur.execute("""
                SELECT e.enrollmentid, u.userid, u.name, u.email, e.class
                FROM enrollments e
                JOIN users u ON e.studentid = u.userid
                WHERE e.class = ANY(%s) AND e.approved IS NULL
            """, (classes,))

             # 'classes' is the list of class names
            requests = cur.fetchall()
        
        # Return the template with the pending requests
        return render_template('pending_enrollments.html', requests=requests, classes=classes)

    except psycopg2.Error as e:
        # Catch and handle database exceptions
        print(f"Database Error in pending_enrollments: {e}")
        flash("An unexpected database error occurred. Please try again.", "error")
        return redirect(url_for('teacher_dashboard'))
        
    finally:
        # 4. Ensure cleanup: Close the cursor and connection, even if an error occurred.
        if cur:
            cur.close()
        if conn:
            conn.close()

# ... (rest of your app.py content)


@app.route('/create_class', methods=['GET', 'POST'])
def create_class():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or role != 'teacher':
        return redirect(url_for('login'))

    if request.method == 'POST':
        class_name = request.form.get('class_name').strip()
        subject = request.form.get('subject').strip()

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if the class name already exists
        cur.execute("SELECT * FROM teacher_classes WHERE class = %s", (class_name,))
        if cur.fetchone():
            flash(f"Class '{class_name}' already exists. Please choose a different name.", "error")
            cur.close()
            conn.close()
            return render_template('create_class.html')
        else:
            # DO NOT include "id" in this insert
            cur.execute(
                "INSERT INTO teacher_classes (teacherid, class, subject) VALUES (%s, %s, %s)",
                (user_id, class_name, subject)
            )
            conn.commit()
            flash(f"Class '{class_name}' created successfully!", "success")
            cur.close()
            conn.close()
            return redirect(url_for('teacher_dashboard'))

    return render_template('create_class.html')




@app.route('/manage_questions/<int:quiz_id>', methods=['GET', 'POST'])
def manage_questions(quiz_id):
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or role != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch quiz details
    cur.execute("""
        SELECT quizid, createdby, title, description, difficulty,
               availablefrom, availableto, attemptlimit, isdraft, class
        FROM quizzes 
        WHERE quizid=%s AND createdby=%s
    """, (quiz_id, user_id))
    quiz = cur.fetchone()

    if not quiz:
        flash("Quiz not found or you don't have permission.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('teacher_dashboard'))

    availableto = quiz[6]
    quiz_ended = availableto is not None and datetime.now() > availableto

    if request.method == 'POST':
        if quiz_ended:
            flash("Cannot add questions after the quiz end date.", "error")
            cur.close()
            conn.close()
            return redirect(url_for('manage_questions', quiz_id=quiz_id))

        # Add question logic...
        question_text = request.form.get('question_text')
        option_a = request.form.get('option_a')
        option_b = request.form.get('option_b')
        option_c = request.form.get('option_c')
        option_d = request.form.get('option_d')
        correct_option = request.form.get('correct_option')
        difficulty = request.form.get('difficulty')

        cur.execute("""
            INSERT INTO questions (quizid, questiontext, optiona, optionb, optionc, optiond, correctoption, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, difficulty))
        conn.commit()
        flash("Question added successfully!", "success")
        cur.close()
        conn.close()
        return redirect(url_for('manage_questions', quiz_id=quiz_id))

    # Fetch all questions for this quiz
    cur.execute("SELECT * FROM questions WHERE quizid=%s ORDER BY questionid", (quiz_id,))
    questions = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('questions.html', quiz=quiz, questions=questions, quiz_id=quiz_id, quiz_ended=quiz_ended)

@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get quiz_id before deleting
    cur.execute("SELECT quizid FROM questions WHERE questionid=%s", (question_id,))
    result = cur.fetchone()

    if result:
        quiz_id = result[0]
        cur.execute("DELETE FROM questions WHERE questionid=%s", (question_id,))
        conn.commit()
        flash("Question deleted successfully!", "success")

    cur.close()
    conn.close()
    return redirect(url_for('manage_questions', quiz_id=quiz_id))


@app.route('/attempt_quiz/<int:quiz_id>')
def attempt_quiz(quiz_id):
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or role != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get quiz details - SELECT specific columns in known order
    cur.execute("""
        SELECT quizid, createdby, title, description, difficulty, 
               availablefrom, availableto, attemptlimit, isdraft, class 
        FROM quizzes 
        WHERE quizid=%s
    """, (quiz_id,))
    quiz = cur.fetchone()

    if not quiz:
        flash("Quiz not found.", "error")
        return redirect(url_for('student_dashboard'))

    # Now indices are:
    # 0=quizid, 1=createdby, 2=title, 3=description, 4=difficulty,
    # 5=availablefrom, 6=availableto, 7=attemptlimit, 8=isdraft, 9=class

    # Check if student is enrolled in this class
    cur.execute("SELECT 1 FROM enrollments WHERE studentid=%s AND class=%s AND approved=TRUE",
                (user_id, quiz[9]))  # quiz[9] is class
    if not cur.fetchone():
        flash("You are not enrolled in this class.", "error")
        return redirect(url_for('student_dashboard'))

    # Check number of attempts
    cur.execute("SELECT COUNT(*) FROM attempts WHERE quizid=%s AND studentid=%s", (quiz_id, user_id))
    attempt_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template('attempt_quiz.html', quiz=quiz, attempt_count=attempt_count, quiz_id=quiz_id)

    # Check number of attempts


    cur.close()
    conn.close()

    # Pass quiz tuple and other data to template
    return render_template('attempt_quiz.html', quiz=quiz, attempt_count=attempt_count, quiz_id=quiz_id)


@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Create new attempt
    cur.execute("""
        INSERT INTO attempts (quizid, studentid, attemptno, starttime)
        VALUES (%s, %s, (SELECT COALESCE(MAX(attemptno), 0) + 1 FROM attempts WHERE quizid=%s AND studentid=%s), NOW())
        RETURNING attemptid
    """, (quiz_id, user_id, quiz_id, user_id))
    attempt_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    # Redirect to take_quiz page with attempt_id
    return redirect(url_for('take_quiz', attempt_id=attempt_id))


@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or role != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get teacher's classes
    cur.execute("SELECT class, subject FROM teacher_classes WHERE teacherid=%s", (user_id,))
    teacher_classes = cur.fetchall()

    if request.method == 'POST':
        title = request.form.get('title').strip()
        description = request.form.get('description').strip()
        class_name = request.form.get('class')
        difficulty = request.form.get('difficulty')
        available_from = request.form.get('available_from')
        available_to = request.form.get('available_to')
        attempt_limit = request.form.get('attempt_limit')
        is_draft = request.form.get('is_draft') == 'on'

        # --- ADD THIS BLOCK for date validation ---
        if available_from and available_to:
            dt_from = datetime.fromisoformat(available_from)
            dt_to = datetime.fromisoformat(available_to)
            if dt_to < dt_from:
                flash("Available To date must be after Available From date.", "error")
                cur.close()
                conn.close()
                return render_template(
                    'create_quiz.html',
                    teacher_classes=teacher_classes,
                    form_data={
                        "title": title,
                        "description": description,
                        "class_name": class_name,
                        "difficulty": difficulty,
                        "available_from": available_from,
                        "available_to": available_to,
                        "attempt_limit": attempt_limit,
                        "is_draft": is_draft,
                    }
                )

        # Insert quiz into database
        cur.execute("""
               INSERT INTO quizzes (createdby, title, description, difficulty, availablefrom, availableto, attemptlimit, isdraft, class)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING quizid
           """, (user_id, title, description, difficulty, available_from, available_to, attempt_limit, is_draft,
                 class_name))

        quiz_id = cur.fetchone()[0]
        conn.commit()

        flash(f"Quiz '{title}' created successfully!", "success")
        cur.close()
        conn.close()

        # Redirect to manage questions for this quiz
        return redirect(url_for('manage_questions', quiz_id=quiz_id))

    cur.close()
    conn.close()
    return render_template('create_quiz.html', teacher_classes=teacher_classes)
    

@app.route('/take_quiz/<int:attempt_id>', methods=['GET', 'POST'])
def take_quiz(attempt_id):
    user_id = session.get('user_id')
    if not user_id or session.get('role') != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Get attempt details
    cur.execute("SELECT quizid, studentid FROM attempts WHERE attemptid=%s", (attempt_id,))
    attempt = cur.fetchone()

    if not attempt or attempt[1] != user_id:
        flash("Invalid attempt.", "error")
        return redirect(url_for('student_dashboard'))

    quiz_id = attempt[0]

    # Get quiz details
    cur.execute("SELECT title, description FROM quizzes WHERE quizid=%s", (quiz_id,))
    quiz = cur.fetchone()

    # Get all questions for this quiz
    cur.execute("""
        SELECT questionid, questiontext, optiona, optionb, optionc, optiond 
        FROM questions 
        WHERE quizid=%s 
        ORDER BY questionid
    """, (quiz_id,))
    questions = cur.fetchall()

    if request.method == 'POST':
        correct_count = 0
        total_questions = len(questions)

        for question in questions:
            question_id = question[0]
            selected_answer = request.form.get(f'question_{question_id}')

            # Get correct answer
            cur.execute("SELECT correctoption FROM questions WHERE questionid=%s", (question_id,))
            correct_answer = cur.fetchone()[0]

            iscorrect = selected_answer == correct_answer
            if iscorrect:
                correct_count += 1

            # Insert response record
            cur.execute("""
                INSERT INTO responses (attemptid, questionid, selectedoption, iscorrect, submittedat)
                VALUES (%s, %s, %s, %s, NOW())
            """, (attempt_id, question_id, selected_answer, iscorrect))

        # Calculate score percentage
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0

        # Update attempt with score and end time
        cur.execute("""
            UPDATE attempts 
            SET score=%s, endtime=NOW() 
            WHERE attemptid=%s
        """, (score, attempt_id))

        # Update leaderboard logic begins here

        # Get quiz class
        cur.execute("SELECT class FROM quizzes WHERE quizid=%s", (quiz_id,))
        quiz_class = cur.fetchone()[0]

        # Check existing leaderboard entry
        cur.execute("""
            SELECT leaderboardid, totalscore FROM leaderboard
            WHERE studentid = %s AND class = %s
        """, (user_id, quiz_class))
        existing_entry = cur.fetchone()

        if existing_entry:
            leaderboardid, old_score = existing_entry
            if score > old_score:
                cur.execute("""
                    UPDATE leaderboard SET totalscore = %s WHERE leaderboardid = %s
                """, (score, leaderboardid))
        else:
            cur.execute("""
                INSERT INTO leaderboard (quizid, studentid, totalscore, class)
                VALUES (%s, %s, %s, %s)
            """, (quiz_id, user_id, score, quiz_class))

        # Recalculate ranks
        cur.execute("""
            SELECT leaderboardid FROM leaderboard WHERE class = %s ORDER BY totalscore DESC
        """, (quiz_class,))
        rows = cur.fetchall()
        for idx, row in enumerate(rows, start=1):
            cur.execute("UPDATE leaderboard SET rank = %s WHERE leaderboardid = %s", (idx, row[0]))

        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()

        flash(f"Quiz submitted! Your score: {score:.2f}%", "success")
        return redirect(url_for('student_dashboard'))

    cur.close()
    conn.close()

    return render_template('take_quiz.html', quiz=quiz, questions=questions, attempt_id=attempt_id)


@app.route('/publish_quiz/<int:quiz_id>')
def publish_quiz(quiz_id):
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or role != 'teacher':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Update quiz to make it live (isdraft = False)
    cur.execute("UPDATE quizzes SET isdraft = FALSE WHERE quizid = %s AND createdby = %s",
                (quiz_id, user_id))
    conn.commit()

    cur.close()
    conn.close()

    flash("Quiz published successfully! It is now visible to students.", "success")
    return redirect(url_for('teacher_dashboard'))


@app.route('/leaderboard/<class_name>')
def leaderboard(class_name):
    user_id = session.get('user_id')
    role = session.get('role')

    # Check if user is logged in
    if not user_id or not role:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Authorization check
    authorized = False

    if role == 'teacher':
        # Check if teacher manages this class
        cur.execute("SELECT 1 FROM teacher_classes WHERE teacherid = %s AND class = %s", (user_id, class_name))


        if cur.fetchone():
            authorized = True

    elif role == 'student':
        # Check if student is enrolled in this class
        cur.execute("SELECT 1 FROM enrollments WHERE studentid = %s AND class = %s AND approved = TRUE",
                    (user_id, class_name))
        if cur.fetchone():
            authorized = True

    # If not authorized, redirect to appropriate dashboard
    if not authorized:
        cur.close()
        conn.close()
        flash("You are not authorized to view this leaderboard.", "error")
        if role == 'teacher':
            return redirect(url_for('teacherdashboard'))
        elif role == 'student':
            return redirect(url_for('studentdashboard'))
        else:
            return redirect(url_for('login'))

    # Fetch leaderboard entries from leaderboard table
    cur.execute("""
        SELECT u.name, l.totalscore, l.rank
        FROM leaderboard l
        JOIN users u ON l.studentid = u.userid
        WHERE l.class = %s
        ORDER BY l.rank ASC NULLS LAST, l.totalscore DESC NULLS LAST
    """, (class_name,))
    leaderboard_data = cur.fetchall()

    if role == 'teacher':
        dashboard_url = url_for('teacher_dashboard')
    elif role == 'student':
        dashboard_url = url_for('student_dashboard')
    else:
        dashboard_url = url_for('login')
        
    cur.close()
    conn.close()

    return render_template('leaderboard.html', class_name=class_name, leaderboard=leaderboard_data, dashboard_url=dashboard_url)


@app.route('/list_responses')
def list_responses():
    userid = session.get('user_id')
    role = session.get('role')

    if not userid:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if role == 'student':
        # Show student's own quiz attempts
        cur.execute("""
            SELECT a.attemptid, q.title, a.score, a.starttime, a.endtime
            FROM attempts a
            JOIN quizzes q ON a.quizid = q.quizid
            WHERE a.studentid = %s
            ORDER BY a.starttime DESC
        """, (userid,))
        attempts = cur.fetchall()

    elif role == 'teacher':
        # Show attempts made on quizzes created by this teacher
        cur.execute("""
            SELECT a.attemptid, q.title, a.score, a.starttime, a.endtime, u.name as student_name
            FROM attempts a
            JOIN quizzes q ON a.quizid = q.quizid
            JOIN users u ON a.studentid = u.userid
            WHERE q.createdby = %s
            ORDER BY a.starttime DESC
        """, (userid,))
        attempts = cur.fetchall()
    else:
        attempts = []

    cur.close()
    conn.close()

    return render_template('list_responses.html', attempts=attempts, role=role)


@app.route('/view_responses/<int:attemptid>')
def view_responses(attemptid):
    userid = session.get('user_id')
    role = session.get('role')

    if not userid:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.studentid, q.title, a.score, a.starttime, a.endtime
        FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE a.attemptid = %s
    """, (attemptid,))
    attempt = cur.fetchone()

    if not attempt:
        flash("Attempt not found.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('list_responses'))

    studentid = attempt[0]

    # Access control
    if role == 'student' and studentid != userid:
        flash("You are not authorized to view this attempt.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('list_responses'))

    if role == 'teacher':
        cur.execute("""
            SELECT q.createdby FROM attempts a
            JOIN quizzes q ON a.quizid = q.quizid
            WHERE a.attemptid = %s
        """, (attemptid,))
        owner = cur.fetchone()
        if not owner or owner[0] != userid:
            flash("You are not authorized to view this attempt.", "error")
            cur.close()
            conn.close()
            return redirect(url_for('list_responses'))

    cur.execute("""
        SELECT r.questionid, q.questiontext, r.selectedoption, r.iscorrect, q.correctoption
        FROM responses r
        JOIN questions q ON r.questionid = q.questionid
        WHERE r.attemptid = %s
        ORDER BY r.questionid
    """, (attemptid,))
    responses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('view_responses.html', attempt=attempt, responses=responses)

@app.route('/feedback/<int:attempt_id>', methods=['GET'])
def feedback(attempt_id):
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Validate that the attempt belongs to the logged in student
    cur.execute("SELECT studentid FROM attempts WHERE attemptid=%s", (attempt_id,))
    attempt = cur.fetchone()
    if not attempt or attempt[0] != user_id:
        cur.close()
        conn.close()
        flash("Invalid attempt for feedback.", "error")
        return redirect(url_for('student_dashboard'))

    # Check if feedback already submitted
    cur.execute("SELECT 1 FROM feedback WHERE attemptid=%s AND studentid=%s", (attempt_id, user_id))
    feedback_exists = cur.fetchone()
    cur.close()
    conn.close()

    if feedback_exists:
        flash("You have already submitted feedback for this quiz attempt.", "info")
        return redirect(url_for('student_dashboard'))

    return render_template('feedback.html', attempt_id=attempt_id)

@app.route('/submit_attempt/<int:quizid>', methods=['POST'])
def submit_attempt(quizid):
    userid = session.get('user_id')
    if not userid or session.get('role') != 'student':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Create new attempt
    cur.execute("""
        INSERT INTO attempts (quizid, studentid, attemptno, starttime)
        VALUES (%s, %s, COALESCE((SELECT MAX(attemptno) FROM attempts WHERE quizid=%s AND studentid=%s), 0) + 1, NOW())
        RETURNING attemptid
    """, (quizid, userid, quizid, userid))
    attemptid = cur.fetchone()[0]

    total_score = 0
    total_questions = 0

    # Fetch all questions for this quiz to check answers
    cur.execute("SELECT questionid, correctoption FROM questions WHERE quizid = %s", (quizid,))
    questions = cur.fetchall()

    for q in questions:
        questionid = q[0]
        correctoption = q[1]
        selectedoption = request.form.get(f'question_{questionid}')

        if not selectedoption:
            continue

        iscorrect = (selectedoption == correctoption)

        if iscorrect:
            total_score += 1

        total_questions += 1

        # Insert response
        cur.execute("""
            INSERT INTO responses (attemptid, questionid, selectedoption, iscorrect, submittedat)
            VALUES (%s, %s, %s, %s, NOW())
        """, (attemptid, questionid, selectedoption, iscorrect))

    # Calculate percentage score
    score_value = (total_score / total_questions) * 100 if total_questions else 0

    # Update attempt with score and end time
    cur.execute("""
        UPDATE attempts SET score = %s, endtime = NOW() WHERE attemptid = %s
    """, (score_value, attemptid))

    # Get class of the quiz
    cur.execute("SELECT class FROM quizzes WHERE quizid = %s", (quizid,))
    quiz_class = cur.fetchone()[0]

    # Update leaderboard table
    cur.execute("""
        SELECT leaderboardid, totalscore FROM leaderboard
        WHERE studentid = %s AND class = %s
    """, (userid, quiz_class))
    existing_entry = cur.fetchone()

    if existing_entry:
        leaderboardid, old_score = existing_entry
        if score_value > old_score:
            cur.execute("""
                UPDATE leaderboard SET totalscore = %s WHERE leaderboardid = %s
            """, (score_value, leaderboardid))
    else:
        cur.execute("""
            INSERT INTO leaderboard (quizid, studentid, totalscore, class)
            VALUES (%s, %s, %s, %s)
        """, (quizid, userid, score_value, quiz_class))

    conn.commit()

    # Recalculate ranks
    cur.execute("""
        SELECT leaderboardid FROM leaderboard WHERE class = %s ORDER BY totalscore DESC
    """, (quiz_class,))
    rows = cur.fetchall()
    for idx, row in enumerate(rows, start=1):
        cur.execute("UPDATE leaderboard SET rank = %s WHERE leaderboardid = %s", (idx, row[0]))
    conn.commit()

    cur.close()
    conn.close()

    flash(f"Quiz submitted! Your score is {score_value:.2f}. Please provide your feedback.", "success")
    return redirect(url_for('feedback', attempt_id=attemptid))

@app.route('/submit_feedback/<int:attempt_id>', methods=['POST'])
def submit_feedback(attempt_id):
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id or role != 'student':
        return redirect(url_for('login'))
    
    feedback_text = request.form.get('feedback')
    comments_text = request.form.get('comments')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Validate attempt and get teacherid
    cur.execute("""
        SELECT a.studentid, q.createdby FROM attempts a
        JOIN quizzes q ON a.quizid = q.quizid
        WHERE a.attemptid = %s
    """, (attempt_id,))
    row = cur.fetchone()
    
    if not row or row[0] != user_id:
        flash("Invalid attempt for feedback submission.", "error")
        cur.close()
        conn.close()
        return redirect(url_for('student_dashboard'))
    
    teacher_id = row[1]
    
    # Insert feedback record
    cur.execute("""
        INSERT INTO feedback (attemptid, teacherid, studentid, feedback, comments, createdat)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (attempt_id, teacher_id, user_id, feedback_text, comments_text))
    
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Thank you for your feedback!", "success")
    return redirect(url_for('student_dashboard'))


@app.route('/empty')
def empty():
    return "<h1>Signed in. Dashboard placeholder.</h1>"

@app.route('/logout')
def logout():
    print("Logging out user:", session.get('user_id'))
    session.clear()
    print("Session after clearing:", dict(session))
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

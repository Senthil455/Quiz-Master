-- Seed data for QuizMaster
-- Run with psql or via a Python script if psql isn't available.

-- USERS
INSERT INTO users (userid, name, email, passwordhash, role, class, approved) VALUES
  (1, 'Admin User', 'admin@admin.com', 'adminpass', 'admin', NULL, TRUE),
  (2, 'Teacher One', 'teacher1@faculty.annauniv.edu', 'teacherpass', 'teacher', 'CS101', TRUE),
  (3, 'Student One', 'student1@student.annauniv.edu', 'studentpass', 'student', 'CS101', TRUE),
  (4, 'Student Two', 'student2@student.annauniv.edu', 'studentpass2', 'student', 'CS101', TRUE),
  (5, 'Teacher Two', 'teacher2@faculty.annauniv.edu', 'teacherpass2', 'teacher', 'MATH101', TRUE);

-- TEACHER_CLASSES
INSERT INTO teacher_classes (teacherid, class, subject) VALUES
  (2, 'CS101', 'Computer Science 101'),
  (5, 'MATH101', 'Mathematics 101');

-- QUIZZES
INSERT INTO quizzes (quizid, createdby, title, description, difficulty, availablefrom, availableto, attemptlimit, isdraft, class) VALUES
  (1, 2, 'Intro CS Quiz', 'Basic concepts of CS', 'Easy', NOW() - INTERVAL '1 day', NOW() + INTERVAL '14 days', 3, FALSE, 'CS101'),
  (2, 5, 'Basic Math Quiz', 'Arithmetic and algebra', 'Medium', NOW() - INTERVAL '2 days', NOW() + INTERVAL '10 days', 2, FALSE, 'MATH101');

-- QUESTIONS
INSERT INTO questions (questionid, quizid, questiontext, optiona, optionb, optionc, optiond, correctoption, difficulty) VALUES
  (1, 1, 'What is 2 + 2?', '3', '4', '5', '6', 'B', 'Easy'),
  (2, 1, 'Which of these is a programming language?', 'HTML', 'CSS', 'Python', 'Photoshop', 'C', 'Easy'),
  (3, 2, 'What is 7 * 6?', '42', '36', '48', '40', 'A', 'Easy'),
  (4, 2, 'Solve for x: 2x + 3 = 7', '1', '2', '3', '4', 'B', 'Easy');

-- ENROLLMENTS
INSERT INTO enrollments (enrollmentid, studentid, class, approved, requested_at) VALUES
  (1, 3, 'CS101', TRUE, NOW() - INTERVAL '10 days'),
  (2, 4, 'CS101', TRUE, NOW() - INTERVAL '9 days');

-- ATTEMPTS
INSERT INTO attempts (attemptid, quizid, studentid, attemptno, starttime, score, endtime) VALUES
  (1, 1, 3, 1, NOW() - INTERVAL '20 minutes', 100, NOW() - INTERVAL '10 minutes'),
  (2, 1, 4, 1, NOW() - INTERVAL '15 minutes', 50, NOW() - INTERVAL '5 minutes');

-- RESPONSES
INSERT INTO responses (attemptid, questionid, selectedoption, iscorrect, submittedat) VALUES
  (1, 1, 'B', TRUE, NOW() - INTERVAL '19 minutes'),
  (1, 2, 'C', TRUE, NOW() - INTERVAL '18 minutes'),
  (2, 1, 'A', FALSE, NOW() - INTERVAL '14 minutes'),
  (2, 2, 'C', TRUE, NOW() - INTERVAL '13 minutes');

-- LEADERBOARD
INSERT INTO leaderboard (leaderboardid, quizid, studentid, totalscore, class, rank) VALUES
  (1, 1, 3, 100, 'CS101', 1),
  (2, 1, 4, 50, 'CS101', 2);

-- FEEDBACK
INSERT INTO feedback (feedbackid, attemptid, teacherid, studentid, feedback, comments, createdat) VALUES
  (1, 1, 2, 3, 'Good attempt', 'Well done, keep practicing!', NOW() - INTERVAL '9 minutes');

-- Optional: If your tables use sequences named in the usual PostgreSQL convention, update them to the next free value.
-- Adjust sequence names if your schema uses different names.
SELECT setval('users_userid_seq', (SELECT MAX(userid) FROM users));
SELECT setval('quizzes_quizid_seq', (SELECT MAX(quizid) FROM quizzes));
SELECT setval('questions_questionid_seq', (SELECT MAX(questionid) FROM questions));
SELECT setval('enrollments_enrollmentid_seq', (SELECT MAX(enrollmentid) FROM enrollments));
SELECT setval('attempts_attemptid_seq', (SELECT MAX(attemptid) FROM attempts));
SELECT setval('leaderboard_leaderboardid_seq', (SELECT MAX(leaderboardid) FROM leaderboard));
SELECT setval('feedback_feedbackid_seq', (SELECT MAX(feedbackid) FROM feedback));

-- End of seed file

-- QuizMaster Database Schema
-- Run this before running seed_data.sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    userid SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    passwordhash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    class VARCHAR(50),
    approved BOOLEAN DEFAULT NULL
);

-- Teacher Classes table
CREATE TABLE IF NOT EXISTS teacher_classes (
    id SERIAL PRIMARY KEY,
    teacherid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    class VARCHAR(50) NOT NULL,
    subject VARCHAR(100) NOT NULL
);

-- Quizzes table
CREATE TABLE IF NOT EXISTS quizzes (
    quizid SERIAL PRIMARY KEY,
    createdby INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(20),
    availablefrom TIMESTAMP,
    availableto TIMESTAMP,
    attemptlimit INTEGER DEFAULT 1,
    isdraft BOOLEAN DEFAULT TRUE,
    class VARCHAR(50) NOT NULL
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    questionid SERIAL PRIMARY KEY,
    quizid INTEGER NOT NULL REFERENCES quizzes(quizid) ON DELETE CASCADE,
    questiontext TEXT NOT NULL,
    optiona VARCHAR(255),
    optionb VARCHAR(255),
    optionc VARCHAR(255),
    optiond VARCHAR(255),
    correctoption VARCHAR(1) NOT NULL,
    difficulty VARCHAR(20)
);

-- Enrollments table
CREATE TABLE IF NOT EXISTS enrollments (
    enrollmentid SERIAL PRIMARY KEY,
    studentid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    class VARCHAR(50) NOT NULL,
    approved BOOLEAN DEFAULT NULL,
    requested_at TIMESTAMP DEFAULT NOW()
);

-- Attempts table
CREATE TABLE IF NOT EXISTS attempts (
    attemptid SERIAL PRIMARY KEY,
    quizid INTEGER NOT NULL REFERENCES quizzes(quizid) ON DELETE CASCADE,
    studentid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    attemptno INTEGER,
    starttime TIMESTAMP DEFAULT NOW(),
    score NUMERIC(5,2),
    endtime TIMESTAMP
);

-- Responses table
CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    attemptid INTEGER NOT NULL REFERENCES attempts(attemptid) ON DELETE CASCADE,
    questionid INTEGER NOT NULL REFERENCES questions(questionid) ON DELETE CASCADE,
    selectedoption VARCHAR(1),
    iscorrect BOOLEAN,
    submittedat TIMESTAMP DEFAULT NOW()
);

-- Leaderboard table
CREATE TABLE IF NOT EXISTS leaderboard (
    leaderboardid SERIAL PRIMARY KEY,
    quizid INTEGER NOT NULL REFERENCES quizzes(quizid) ON DELETE CASCADE,
    studentid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    totalscore NUMERIC(5,2),
    class VARCHAR(50),
    rank INTEGER
);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    feedbackid SERIAL PRIMARY KEY,
    attemptid INTEGER NOT NULL REFERENCES attempts(attemptid) ON DELETE CASCADE,
    teacherid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    studentid INTEGER NOT NULL REFERENCES users(userid) ON DELETE CASCADE,
    feedback TEXT,
    comments TEXT,
    createdat TIMESTAMP DEFAULT NOW()
);

-- End of schema

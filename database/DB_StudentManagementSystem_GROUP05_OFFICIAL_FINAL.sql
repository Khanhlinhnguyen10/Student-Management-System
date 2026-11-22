/*
===============================================================================
STUDENT MANAGEMENT SYSTEM - GROUP 05
COMPLETE SQL SERVER DATABASE - DOMAIN DATA + AUTH SESSIONS + ACADEMIC GPA
===============================================================================
Basis: Requirement Specification & Design Document_Group05 (2).docx
   - Chapter 1: Authentication, Academic Management and Grade Management
   - Chapter 3: DFD 1.0 and DFD 4.0
   - Chapter 4: Log In, Log Out, Manage Gradebook, View Transcript
   - Chapter 5: Class Diagram
   - Chapter 6: Data Model

The 15 business-domain tables keep their official names, columns, PKs and FKs.
Two technical/support tables make existing requirements implementable:
   dbo.UserSessions: server-side session state and 15-minute inactivity timeout.
   dbo.GradeScales: approved course-grade-to-GPA mappings, maintained as data.

Notes about grading policy:
   - The demo letter-grade bands include B+, C+, D+ and F+ to remain compatible
     with the project's grade examples. They are a TEAM ADOPTED policy for this
     project, informed by a historical university publication; do not claim they
     are the university's currently binding grade policy without confirmation.
   - Grade weights are percentage points totaling 100.00, matching original data.
   - Credits are the weights of GPA; draft grades never contribute.
   - A repeated course contributes its latest finalized attempt to CGPA.
   - Courses not belonging to the student's major curriculum are excluded from GPA.
   - Semester GPA and CGPA are stored in dbo.SemesterResults as the official model.
   - Rounding: finalScore and GPA to 2 decimal places, SQL ROUND / HALF_UP.

OFFICIAL GROUP 05 DEMONSTRATION DATABASE — SINGLE DEPLOYMENT FILE
Contains the approved data model, support tables, academic and concurrency
procedures, original baseline rows, expanded 3-role academic data, login hashes,
and read-only verification queries. Works with SSMS/sqlcmd (GO batch separator).

In a clean development database: execute the WHOLE file once (F5).
On an already-seeded Group 05 database: it adds or migrates demo rows without
removing existing academic records. Back up the database before execution.

The 26 additional logins are: admin01-02, student01-16, lecturer01-08.
Test passwords follow: Admin01112026 / Student01112026 / Lecturer01112026
(and the matching two-digit account number, e.g. student16 / Student16112026).
The six original baseline accounts remain with their original IDs, passwords,
role relations and academic records, but their USERNAMES are moved to base_*
to avoid collisions with these 26 new logins.

EXAMPLE CREDENTIALS ARE PUBLIC TEST FIXTURES: never use in production.
Do not pass this script as a single pyodbc cursor.execute() call.
===============================================================================
*/
SET NOCOUNT ON;
GO

-- Create the application database only when it does not exist.
IF DB_ID(N'StudentManagementSystem') IS NULL
    CREATE DATABASE StudentManagementSystem;
GO
USE StudentManagementSystem;
GO

-- ============================================================================
-- SECTION A. BUSINESS DATA MODEL (15 official domain tables)
-- ============================================================================

-- 1. Users
IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users (
        userId VARCHAR(12) NOT NULL,
        username VARCHAR(50) NOT NULL,
        passwordHash VARCHAR(255) NOT NULL,
        isLocked BIT NOT NULL,
        citizenId VARCHAR(12) NOT NULL,
        fullName NVARCHAR(100) NOT NULL,
        dateOfBirth DATE NULL,
        email VARCHAR(100) NULL,
        phoneNumber VARCHAR(15) NULL,
        gender NVARCHAR(10) NULL,
        CONSTRAINT PK_Users PRIMARY KEY (userId)
    );
END;
GO


-- 2. Faculties
IF OBJECT_ID(N'dbo.Faculties', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Faculties (
        facultyId VARCHAR(10) NOT NULL,
        facultyCode VARCHAR(10) NOT NULL,
        facultyName NVARCHAR(100) NOT NULL,
        email VARCHAR(100) NULL,
        phoneNumber VARCHAR(15) NULL,
        CONSTRAINT PK_Faculties PRIMARY KEY (facultyId)
    );
END;
GO


-- 3. Majors
IF OBJECT_ID(N'dbo.Majors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Majors (
        majorId VARCHAR(10) NOT NULL,
        facultyId VARCHAR(10) NOT NULL,
        majorName NVARCHAR(100) NOT NULL,
        majorCode VARCHAR(10) NOT NULL,
        CONSTRAINT PK_Majors PRIMARY KEY (majorId),
        CONSTRAINT UQ_Majors_majorCode UNIQUE (majorCode),
        CONSTRAINT FK_Majors_Faculties
            FOREIGN KEY (facultyId) REFERENCES dbo.Faculties(facultyId)
    );
END;
GO


-- 4. Administrators
IF OBJECT_ID(N'dbo.Administrators', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Administrators (
        adminId VARCHAR(10) NOT NULL,
        userId VARCHAR(12) NOT NULL,
        CONSTRAINT PK_Administrators PRIMARY KEY (adminId),
        CONSTRAINT UQ_Administrators_userId UNIQUE (userId),
        CONSTRAINT FK_Administrators_Users
            FOREIGN KEY (userId) REFERENCES dbo.Users(userId)
    );
END;
GO


-- 5. Students
IF OBJECT_ID(N'dbo.Students', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Students (
        studentId VARCHAR(10) NOT NULL,
        userId VARCHAR(12) NOT NULL,
        majorId VARCHAR(10) NOT NULL,
        academicStatus NVARCHAR(30) NOT NULL,
        CONSTRAINT PK_Students PRIMARY KEY (studentId),
        CONSTRAINT UQ_Students_userId UNIQUE (userId),
        CONSTRAINT FK_Students_Users
            FOREIGN KEY (userId) REFERENCES dbo.Users(userId),
        CONSTRAINT FK_Students_Majors
            FOREIGN KEY (majorId) REFERENCES dbo.Majors(majorId)
    );
END;
GO


-- 6. Lecturers
IF OBJECT_ID(N'dbo.Lecturers', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Lecturers (
        lecturerId VARCHAR(10) NOT NULL,
        userId VARCHAR(12) NOT NULL,
        facultyId VARCHAR(10) NOT NULL,
        CONSTRAINT PK_Lecturers PRIMARY KEY (lecturerId),
        CONSTRAINT UQ_Lecturers_userId UNIQUE (userId),
        CONSTRAINT FK_Lecturers_Users
            FOREIGN KEY (userId) REFERENCES dbo.Users(userId),
        CONSTRAINT FK_Lecturers_Faculties
            FOREIGN KEY (facultyId) REFERENCES dbo.Faculties(facultyId)
    );
END;
GO


-- 7. Semesters
IF OBJECT_ID(N'dbo.Semesters', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Semesters (
        semesterId VARCHAR(10) NOT NULL,
        semesterName NVARCHAR(50) NOT NULL,
        endDate DATE NOT NULL,
        startDate DATE NOT NULL,
        academicYear VARCHAR(9) NOT NULL,
        CONSTRAINT PK_Semesters PRIMARY KEY (semesterId),
        CONSTRAINT UQ_Semesters_semesterName UNIQUE (semesterName)
    );
END;
GO


-- 8. Courses
IF OBJECT_ID(N'dbo.Courses', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Courses (
        courseId VARCHAR(10) NOT NULL,
        facultyId VARCHAR(10) NOT NULL,
        courseCode VARCHAR(10) NOT NULL,
        courseName NVARCHAR(100) NOT NULL,
        credits TINYINT NOT NULL,
        midtermWeight DECIMAL(4,2) NOT NULL,
        assignmentWeight DECIMAL(4,2) NOT NULL,
        attendanceWeight DECIMAL(4,2) NOT NULL,
        finalExamWeight DECIMAL(4,2) NOT NULL,
        CONSTRAINT PK_Courses PRIMARY KEY (courseId),
        CONSTRAINT UQ_Courses_courseCode UNIQUE (courseCode),
        CONSTRAINT CK_Courses_credits CHECK (credits > 0),
        CONSTRAINT FK_Courses_Faculties
            FOREIGN KEY (facultyId) REFERENCES dbo.Faculties(facultyId)
    );
END;
GO


-- 9. Curriculum
IF OBJECT_ID(N'dbo.Curriculum', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Curriculum (
        curriculumId VARCHAR(10) NOT NULL,
        majorId VARCHAR(10) NOT NULL,
        curriculumName NVARCHAR(100) NOT NULL,
        academicYear VARCHAR(9) NOT NULL,
        CONSTRAINT PK_Curriculum PRIMARY KEY (curriculumId),
        CONSTRAINT FK_Curriculum_Majors
            FOREIGN KEY (majorId) REFERENCES dbo.Majors(majorId)
    );
END;
GO

-- 10. Curriculum Courses
IF OBJECT_ID(N'dbo.CurriculumCourses', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CurriculumCourses (
        curriculumId VARCHAR(10) NOT NULL,
        courseId VARCHAR(10) NOT NULL,
        courseType VARCHAR(20) NOT NULL,
        CONSTRAINT PK_CurriculumCourses PRIMARY KEY (curriculumId, courseId),
        CONSTRAINT FK_CurriculumCourses_Curriculum
            FOREIGN KEY (curriculumId) REFERENCES dbo.Curriculum(curriculumId),
        CONSTRAINT FK_CurriculumCourses_Courses
            FOREIGN KEY (courseId) REFERENCES dbo.Courses(courseId)
    );
END;
GO


-- 11. Course Prerequisites
IF OBJECT_ID(N'dbo.CoursePrerequisites', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CoursePrerequisites (
        courseId VARCHAR(10) NOT NULL,
        prerequisiteId VARCHAR(10) NOT NULL,
        CONSTRAINT PK_CoursePrerequisites PRIMARY KEY (courseId, prerequisiteId),
        CONSTRAINT FK_CoursePrerequisites_Course
            FOREIGN KEY (courseId) REFERENCES dbo.Courses(courseId),
        CONSTRAINT FK_CoursePrerequisites_Prerequisite
            FOREIGN KEY (prerequisiteId) REFERENCES dbo.Courses(courseId)
    );
END;
GO


-- 12. Class Sections
IF OBJECT_ID(N'dbo.ClassSections', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ClassSections (
        classSectionId VARCHAR(10) NOT NULL,
        lecturerId VARCHAR(10) NULL,
        courseId VARCHAR(10) NOT NULL,
        semesterId VARCHAR(10) NOT NULL,
        classCode VARCHAR(20) NOT NULL,
        maxCapacity INT NOT NULL,
        currentEnrollment INT NOT NULL,
        room VARCHAR(30) NULL,
        dayOfWeek TINYINT NULL,
        startTime TIME NULL,
        endTime TIME NULL,
        CONSTRAINT PK_ClassSections PRIMARY KEY (classSectionId),
        CONSTRAINT FK_ClassSections_Lecturers
            FOREIGN KEY (lecturerId) REFERENCES dbo.Lecturers(lecturerId),
        CONSTRAINT FK_ClassSections_Courses
            FOREIGN KEY (courseId) REFERENCES dbo.Courses(courseId),
        CONSTRAINT FK_ClassSections_Semesters
            FOREIGN KEY (semesterId) REFERENCES dbo.Semesters(semesterId)
    );
END;
GO


-- 13. Enrollments
IF OBJECT_ID(N'dbo.Enrollments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Enrollments (
        enrollmentId VARCHAR(10) NOT NULL,
        studentId VARCHAR(10) NOT NULL,
        classSectionId VARCHAR(10) NOT NULL,
        enrollmentDate DATE NOT NULL,
        CONSTRAINT PK_Enrollments PRIMARY KEY (enrollmentId),
        CONSTRAINT FK_Enrollments_Students
            FOREIGN KEY (studentId) REFERENCES dbo.Students(studentId),
        CONSTRAINT FK_Enrollments_ClassSections
            FOREIGN KEY (classSectionId) REFERENCES dbo.ClassSections(classSectionId)
    );
END;
GO


-- 14. GradeBooks
IF OBJECT_ID(N'dbo.GradeBooks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GradeBooks (
        gradebookId VARCHAR(10) NOT NULL,
        enrollmentId VARCHAR(10) NOT NULL,
        midtermMark DECIMAL(4,2) NULL,
        assignmentMark DECIMAL(4,2) NULL,
        attendanceMark DECIMAL(4,2) NULL,
        finalExamMark DECIMAL(4,2) NULL,
        finalScore DECIMAL(4,2) NULL,
        letterGrade VARCHAR(2) NULL,
        isFinalized BIT NULL
            CONSTRAINT DF_GradeBooks_isFinalized DEFAULT (0),
        CONSTRAINT PK_GradeBooks PRIMARY KEY (gradebookId),
        CONSTRAINT UQ_GradeBooks_enrollmentId UNIQUE (enrollmentId),
        CONSTRAINT FK_GradeBooks_Enrollments
            FOREIGN KEY (enrollmentId) REFERENCES dbo.Enrollments(enrollmentId)
    );
END;
GO


-- 15. SemesterResults
IF OBJECT_ID(N'dbo.SemesterResults', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SemesterResults (
        studentId VARCHAR(10) NOT NULL,
        semesterId VARCHAR(10) NOT NULL,
        semesterGPA DECIMAL(4,2) NULL,
        cumulativeGPA DECIMAL(4,2) NULL,
        CONSTRAINT PK_SemesterResults PRIMARY KEY (studentId, semesterId),
        CONSTRAINT FK_SemesterResults_Students
            FOREIGN KEY (studentId) REFERENCES dbo.Students(studentId),
        CONSTRAINT FK_SemesterResults_Semesters
            FOREIGN KEY (semesterId) REFERENCES dbo.Semesters(semesterId)
    );
END;
GO



-- ============================================================================
-- SECTION B. SUPPORT DATA REQUIRED BY EXISTING USE CASES
-- ============================================================================

-- UserSessions records a server-side authentication session. The application
-- generates a cryptographically random secret and stores only its SHA-256 hash
-- (64 lowercase hexadecimal characters) here. Raw tokens must never be in SQL.
-- All times are UTC; session validity is determined from expiresAt and revokedAt.
IF OBJECT_ID(N'dbo.UserSessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.UserSessions (
        sessionId UNIQUEIDENTIFIER NOT NULL
            CONSTRAINT DF_UserSessions_sessionId DEFAULT NEWID(),
        userId VARCHAR(12) NOT NULL,
        tokenHash CHAR(64) COLLATE Latin1_General_100_BIN2 NOT NULL,
        createdAt DATETIME2(3) NOT NULL
            CONSTRAINT DF_UserSessions_createdAt DEFAULT SYSUTCDATETIME(),
        lastActivityAt DATETIME2(3) NOT NULL
            CONSTRAINT DF_UserSessions_lastActivityAt DEFAULT SYSUTCDATETIME(),
        expiresAt DATETIME2(3) NOT NULL,
        revokedAt DATETIME2(3) NULL,
        CONSTRAINT PK_UserSessions PRIMARY KEY (sessionId),
        CONSTRAINT UQ_UserSessions_tokenHash UNIQUE (tokenHash),
        CONSTRAINT FK_UserSessions_Users FOREIGN KEY (userId)
            REFERENCES dbo.Users(userId) ON DELETE CASCADE,
        CONSTRAINT CK_UserSessions_times CHECK (
            createdAt <= lastActivityAt
            AND expiresAt = DATEADD(MINUTE, 15, lastActivityAt)
        ),
        CONSTRAINT CK_UserSessions_hash CHECK (
            tokenHash NOT LIKE '%[^0-9a-f]%' COLLATE Latin1_General_100_BIN2
        )
    );
END;
GO

-- GradeScales is a lookup table for the letter grade and 4.00-scale point.
-- The mapping is editable by a DATABASE MIGRATION, not by Student or Lecturer.
-- The min/max bounds are inclusive and expressed to 2 decimals.
IF OBJECT_ID(N'dbo.GradeScales', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GradeScales (
        letterGrade VARCHAR(2) NOT NULL,
        minScore DECIMAL(4,2) NOT NULL,
        maxScore DECIMAL(4,2) NOT NULL,
        gradePoint DECIMAL(3,2) NOT NULL,
        isPassing BIT NOT NULL,
        CONSTRAINT PK_GradeScales PRIMARY KEY (letterGrade),
        CONSTRAINT UQ_GradeScales_minScore UNIQUE (minScore),
        CONSTRAINT CK_GradeScales_interval CHECK (
            minScore >= 0 AND maxScore <= 10 AND minScore <= maxScore
        ),
        CONSTRAINT CK_GradeScales_point CHECK (gradePoint BETWEEN 0 AND 4)
    );
END;
GO

-- Indexes for frequently used active-session and academic lookups.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID(N'dbo.UserSessions')
               AND name=N'IX_UserSessions_user_expiry')
    CREATE INDEX IX_UserSessions_user_expiry ON dbo.UserSessions(userId, expiresAt);
GO

-- ============================================================================
-- SECTION C. LETTER-GRADE POLICY USED BY THE PROJECT
-- ============================================================================
-- The 2026 national regulation allows institutions to define more letter bands.
-- These A/B+/B/C+/C/D+/D/F+/F bands come from a university-published historical
-- conversion table, adopted here as a project policy for reproducible testing.
-- Verify the currently applicable school policy before presenting official GPAs.
-- The project data includes B+ and A grades, supported by this extended scale.
-- The grades F/F+ are not passing; F+ still carries 0.50 toward the GPA.
-- Sources: 56/2026/TT-BGDDT, Articles 12-13 (grade and credit-GPA framework);
-- UTH published historical grading conversion table (extended letter bands).
BEGIN TRY
    BEGIN TRANSACTION;
    INSERT INTO dbo.GradeScales (letterGrade, minScore, maxScore, gradePoint, isPassing)
    SELECT src.letterGrade, src.minScore, src.maxScore, src.gradePoint, src.isPassing
    FROM (VALUES
        ('F',  0.00, 1.99, 0.00, 0),
        ('F+', 2.00, 3.99, 0.50, 0),
        ('D',  4.00, 4.99, 1.00, 1),
        ('D+', 5.00, 5.49, 1.50, 1),
        ('C',  5.50, 5.99, 2.00, 1),
        ('C+', 6.00, 6.99, 2.50, 1),
        ('B',  7.00, 7.99, 3.00, 1),
        ('B+', 8.00, 8.49, 3.50, 1),
        ('A',  8.50, 10.00, 4.00, 1)
    ) AS src (letterGrade, minScore, maxScore, gradePoint, isPassing)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.GradeScales AS existing
        WHERE existing.letterGrade = src.letterGrade
    );
    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

-- Existing mappings cannot silently overlap or leave gaps on the hundredth grid.
-- Validate complete coverage of the 1001 possible rounded scores from 0 to 10.
IF EXISTS (
    SELECT 1
    FROM (
        SELECT TOP (1001) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
        FROM sys.all_objects AS a CROSS JOIN sys.all_objects AS b
    ) AS numbers
    OUTER APPLY (
        SELECT COUNT(*) AS nMatch
        FROM dbo.GradeScales AS g
        WHERE CONVERT(DECIMAL(4,2), numbers.n / 100.0)
              BETWEEN g.minScore AND g.maxScore
    ) AS mapped
    WHERE mapped.nMatch <> 1
)
    THROW 51001, 'GradeScales has gaps or overlapping score intervals.', 1;
GO


-- ============================================================================
-- SECTION D. DATA INTEGRITY RULES AND PERFORMANCE INDEXES
-- ============================================================================

SET XACT_ABORT ON;
GO
BEGIN TRY
    BEGIN TRANSACTION;

    -- Login and Create Account must not have ambiguous identities.
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id = OBJECT_ID(N'dbo.Users') AND name=N'UX_Users_username')
        CREATE UNIQUE INDEX UX_Users_username ON dbo.Users(username);

    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id = OBJECT_ID(N'dbo.Users') AND name=N'UX_Users_citizenId')
        CREATE UNIQUE INDEX UX_Users_citizenId ON dbo.Users(citizenId);

    -- Explicit Unique Faculty Code/Class Code rules in UC Create.
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id = OBJECT_ID(N'dbo.Faculties') AND name=N'UX_Faculties_facultyCode')
        CREATE UNIQUE INDEX UX_Faculties_facultyCode ON dbo.Faculties(facultyCode);

    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id = OBJECT_ID(N'dbo.ClassSections') AND name=N'UX_ClassSections_classCode')
        CREATE UNIQUE INDEX UX_ClassSections_classCode ON dbo.ClassSections(classCode);

    -- Same student cannot be enrolled twice in one section.
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id = OBJECT_ID(N'dbo.Enrollments') AND name=N'UX_Enrollments_student_section')
        CREATE UNIQUE INDEX UX_Enrollments_student_section
        ON dbo.Enrollments(studentId, classSectionId);

    -- UC Create/Configure Semester: end date must follow start date.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.Semesters') AND name=N'CK_Semesters_date_order')
        ALTER TABLE dbo.Semesters WITH CHECK ADD CONSTRAINT CK_Semesters_date_order
        CHECK (endDate > startDate);

    -- Grading weights use percentage points: 20.00+20.00+10.00+50.00 = 100.00.
    -- NOTE: a single weight of 100.00 does NOT fit DECIMAL(4,2) in the official model.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.Courses') AND name=N'CK_Courses_weight_total_100')
        ALTER TABLE dbo.Courses WITH CHECK ADD CONSTRAINT CK_Courses_weight_total_100
        CHECK (midtermWeight >= 0 AND assignmentWeight >= 0
           AND attendanceWeight >= 0 AND finalExamWeight >= 0
           AND midtermWeight + assignmentWeight + attendanceWeight
               + finalExamWeight = 100.00);

    -- Capacity is strictly positive; enrollment stays within capacity.
    -- The equality between currentEnrollment and COUNT(Enrollments) needs
    -- an atomic enrollment transaction in Python Service/Repository.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.ClassSections') AND name=N'CK_ClassSections_capacity')
        ALTER TABLE dbo.ClassSections WITH CHECK ADD CONSTRAINT CK_ClassSections_capacity
        CHECK (maxCapacity > 0 AND currentEnrollment BETWEEN 0 AND maxCapacity);

    -- Prevent clearly invalid within-day start/end time ordering.
    -- Do NOT enforce schedule field NOT NULL here: final diagram permits NULL,
    -- while Create Class Section Validator will enforce mandatory schedule.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.ClassSections') AND name=N'CK_ClassSections_time_order')
        ALTER TABLE dbo.ClassSections WITH CHECK ADD CONSTRAINT CK_ClassSections_time_order
        CHECK (startTime IS NULL OR endTime IS NULL OR startTime < endTime);

    -- Grade Management: marks and final score all 0..10, inclusive.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.GradeBooks') AND name=N'CK_GradeBooks_marks_0_10')
        ALTER TABLE dbo.GradeBooks WITH CHECK ADD CONSTRAINT CK_GradeBooks_marks_0_10
        CHECK ((midtermMark IS NULL OR midtermMark BETWEEN 0 AND 10)
           AND (assignmentMark IS NULL OR assignmentMark BETWEEN 0 AND 10)
           AND (attendanceMark IS NULL OR attendanceMark BETWEEN 0 AND 10)
           AND (finalExamMark IS NULL OR finalExamMark BETWEEN 0 AND 10)
           AND (finalScore IS NULL OR finalScore BETWEEN 0 AND 10));

    -- The final UML/business rule requires finalized results to be complete.
    -- isFinalized defaults FALSE; SQL NULL must not masquerade as a third status.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.GradeBooks') AND name=N'CK_GradeBooks_finalized_complete')
        ALTER TABLE dbo.GradeBooks WITH CHECK ADD CONSTRAINT CK_GradeBooks_finalized_complete
        CHECK (isFinalized IS NOT NULL AND (
            isFinalized = 0 OR (
                midtermMark IS NOT NULL
                AND assignmentMark IS NOT NULL
                AND attendanceMark IS NOT NULL
                AND finalExamMark IS NOT NULL
                AND finalScore IS NOT NULL
                AND NULLIF(LTRIM(RTRIM(letterGrade)), '') IS NOT NULL
            )
        ));

    -- Direct prerequisite self-reference is forbidden by the
    -- course prerequisite meaning; indirect cycles checked in AcademicService.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.CoursePrerequisites') AND name=N'CK_CoursePrerequisites_no_self')
        ALTER TABLE dbo.CoursePrerequisites WITH CHECK ADD CONSTRAINT CK_CoursePrerequisites_no_self
        CHECK (courseId <> prerequisiteId);

    -- The final Student Dashboard explicitly displays GPA /4.00.
    -- This CHECK bounds stored GPA, but does NOT invent letter-grade mappings.
    IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE
                   parent_object_id=OBJECT_ID(N'dbo.SemesterResults') AND name=N'CK_SemesterResults_gpa_0_4')
        ALTER TABLE dbo.SemesterResults WITH CHECK ADD CONSTRAINT CK_SemesterResults_gpa_0_4
        CHECK ((semesterGPA IS NULL OR semesterGPA BETWEEN 0 AND 4)
           AND (cumulativeGPA IS NULL OR cumulativeGPA BETWEEN 0 AND 4));

    -- Each non-NULL letter grade must exist in the centralized grading policy.
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys
                   WHERE parent_object_id=OBJECT_ID(N'dbo.GradeBooks')
                     AND name=N'FK_GradeBooks_GradeScales')
        ALTER TABLE dbo.GradeBooks WITH CHECK ADD CONSTRAINT FK_GradeBooks_GradeScales
        FOREIGN KEY (letterGrade) REFERENCES dbo.GradeScales(letterGrade);

    -- Regular NON-UNIQUE FK indexes; query-performance only, NO new domain data.
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Majors') AND name=N'IX_Majors_facultyId')
        CREATE INDEX IX_Majors_facultyId ON dbo.Majors(facultyId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Students') AND name=N'IX_Students_majorId')
        CREATE INDEX IX_Students_majorId ON dbo.Students(majorId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Lecturers') AND name=N'IX_Lecturers_facultyId')
        CREATE INDEX IX_Lecturers_facultyId ON dbo.Lecturers(facultyId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Courses') AND name=N'IX_Courses_facultyId')
        CREATE INDEX IX_Courses_facultyId ON dbo.Courses(facultyId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Curriculum') AND name=N'IX_Curriculum_majorId')
        CREATE INDEX IX_Curriculum_majorId ON dbo.Curriculum(majorId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.CurriculumCourses') AND name=N'IX_CurriculumCourses_courseId')
        CREATE INDEX IX_CurriculumCourses_courseId ON dbo.CurriculumCourses(courseId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.CoursePrerequisites') AND name=N'IX_CoursePrerequisites_prerequisiteId')
        CREATE INDEX IX_CoursePrerequisites_prerequisiteId ON dbo.CoursePrerequisites(prerequisiteId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.ClassSections') AND name=N'IX_ClassSections_course_semester')
        CREATE INDEX IX_ClassSections_course_semester ON dbo.ClassSections(courseId, semesterId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.ClassSections') AND name=N'IX_ClassSections_lecturer_semester')
        CREATE INDEX IX_ClassSections_lecturer_semester ON dbo.ClassSections(lecturerId, semesterId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.Enrollments') AND name=N'IX_Enrollments_classSectionId')
        CREATE INDEX IX_Enrollments_classSectionId ON dbo.Enrollments(classSectionId);
    IF NOT EXISTS (SELECT 1 FROM sys.indexes
                   WHERE object_id=OBJECT_ID(N'dbo.SemesterResults') AND name=N'IX_SemesterResults_semesterId')
        CREATE INDEX IX_SemesterResults_semesterId ON dbo.SemesterResults(semesterId);

    COMMIT TRANSACTION;
    PRINT 'PASS: Schema constraints and indexes are ready.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    PRINT 'SCHEMA HARDENING FAILED: investigate duplicate data or violated CHECK; nothing committed in this stage.';
    THROW;
END CATCH;
GO



-- ============================================================================
-- SECTION E. SESSION LIFECYCLE (LOG IN, ACTIVITY, LOG OUT)
-- ============================================================================
-- Authentication Service in Flask must validate the password hash and selected
-- role BEFORE it calls usp_CreateUserSession. Only the Flask DB account may call
-- these routines; they should never be exposed as unauthenticated HTTP endpoints.

CREATE OR ALTER PROCEDURE dbo.usp_CreateUserSession
    @UserId VARCHAR(12),
    @TokenHash CHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(3) = SYSUTCDATETIME();
    DECLARE @RoleCount INT;

    IF @TokenHash LIKE '%[^0-9a-f]%' COLLATE Latin1_General_100_BIN2
        THROW 51002, 'Invalid hexadecimal session token hash.', 1;

    SELECT @RoleCount =
        (CASE WHEN a.userId IS NULL THEN 0 ELSE 1 END)
      + (CASE WHEN s.userId IS NULL THEN 0 ELSE 1 END)
      + (CASE WHEN l.userId IS NULL THEN 0 ELSE 1 END)
    FROM dbo.Users AS u
    LEFT JOIN dbo.Administrators AS a ON a.userId = u.userId
    LEFT JOIN dbo.Students AS s ON s.userId = u.userId
    LEFT JOIN dbo.Lecturers AS l ON l.userId = u.userId
    WHERE u.userId = @UserId AND u.isLocked = 0;

    IF @RoleCount IS NULL OR @RoleCount <> 1
        THROW 51003, 'Account is locked, absent, or role assignment is invalid.', 1;

    INSERT INTO dbo.UserSessions
        (userId, tokenHash, createdAt, lastActivityAt, expiresAt)
    VALUES
        (@UserId, @TokenHash, @Now, @Now, DATEADD(MINUTE, 15, @Now));

    SELECT sessionId, userId, expiresAt
    FROM dbo.UserSessions WHERE tokenHash = @TokenHash;
END;
GO

-- An expired session is revoked; a valid one slides forward by 15 minutes.
-- All update statements are atomic, and no raw bearer token is stored in SQL.
CREATE OR ALTER PROCEDURE dbo.usp_TouchUserSession
    @TokenHash CHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(3) = SYSUTCDATETIME();

    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE dbo.UserSessions
           SET revokedAt = @Now
         WHERE tokenHash = @TokenHash
           AND revokedAt IS NULL AND expiresAt <= @Now;

        DECLARE @Verified TABLE (userId VARCHAR(12), expiresAt DATETIME2(3));
        UPDATE sess
           SET lastActivityAt = @Now,
               expiresAt = DATEADD(MINUTE, 15, @Now)
           OUTPUT inserted.userId, inserted.expiresAt
             INTO @Verified(userId, expiresAt)
        FROM dbo.UserSessions AS sess
        JOIN dbo.Users AS u ON u.userId = sess.userId
        WHERE sess.tokenHash = @TokenHash
          AND sess.revokedAt IS NULL AND sess.expiresAt > @Now
          AND u.isLocked = 0;

        COMMIT TRANSACTION;
        SELECT userId, expiresAt FROM @Verified;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- Return 1 on an active-session invalidation, 0 if already revoked/absent.
-- Flask confirms logout only AFTER this database update is committed.
CREATE OR ALTER PROCEDURE dbo.usp_RevokeUserSession
    @TokenHash CHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @Now DATETIME2(3) = SYSUTCDATETIME();
    DECLARE @Affected INT;

    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE dbo.UserSessions
           SET revokedAt = @Now
         WHERE tokenHash = @TokenHash AND revokedAt IS NULL;
        SET @Affected = @@ROWCOUNT;
        COMMIT TRANSACTION;
        SELECT @Affected AS invalidatedSessions;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- ============================================================================
-- SECTION F. COURSE-GRADE AND GPA BUSINESS OPERATIONS
-- ============================================================================
-- GPA policy: compute from finalized marks only, using course credits as weights.
-- Restrict academic courses to CurriculumCourses for the student's major.
-- For repeated courses, keep the latest FINALIZED attempt in CGPA; each term's
-- GPA reflects its own finalized attempts. Updating a prior term recomputes all
-- later cumulative GPA results for the same student.
-- This routine is called in the SAME TRANSACTION as finalized-grade updates.

CREATE OR ALTER PROCEDURE dbo.usp_RecalculateStudentGPA
    @StudentId VARCHAR(10),
    @ReturnRows BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @LockResult INT;

    BEGIN TRY
        BEGIN TRANSACTION;
        IF NOT EXISTS (SELECT 1 FROM dbo.Students WHERE studentId=@StudentId)
            THROW 51011, 'Student ID does not exist.', 1;

        -- Serialize concurrent grade/GPA changes of the same student.
        DECLARE @LockName NVARCHAR(255) = N'GPA:' + @StudentId;
        EXEC @LockResult = sys.sp_getapplock
            @Resource = @LockName,
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = 10000;
        IF @LockResult < 0
            THROW 51012, 'Cannot obtain student GPA calculation lock.', 1;

        -- Detect results that cannot be converted using exactly one scale band.
        IF EXISTS (
            SELECT 1
            FROM dbo.Enrollments AS e
            JOIN dbo.ClassSections AS cs ON cs.classSectionId = e.classSectionId
            JOIN dbo.GradeBooks AS gb ON gb.enrollmentId = e.enrollmentId
            JOIN dbo.Students AS st ON st.studentId = e.studentId
            OUTER APPLY (
                SELECT COUNT(*) AS nMatch, MAX(gs.letterGrade) AS expectedLetter
                FROM dbo.GradeScales AS gs
                WHERE gb.finalScore BETWEEN gs.minScore AND gs.maxScore
            ) AS mapped
            WHERE e.studentId = @StudentId AND gb.isFinalized = 1
              AND EXISTS (
                SELECT 1 FROM dbo.Curriculum AS cu
                JOIN dbo.CurriculumCourses AS cc ON cc.curriculumId = cu.curriculumId
                WHERE cu.majorId=st.majorId AND cc.courseId=cs.courseId
              )
              AND (mapped.nMatch <> 1 OR gb.letterGrade <> mapped.expectedLetter
                   OR gb.finalScore IS NULL OR gb.letterGrade IS NULL)
        )
            THROW 51013, 'Finalized letter grade is inconsistent with GradeScales.', 1;

        CREATE TABLE #ApprovedGrades (
            courseId VARCHAR(10) NOT NULL,
            semesterId VARCHAR(10) NOT NULL,
            semesterStart DATE NOT NULL,
            enrollmentDate DATE NOT NULL,
            enrollmentId VARCHAR(10) NOT NULL,
            credits INT NOT NULL,
            gradePoint DECIMAL(3,2) NOT NULL
        );

        INSERT INTO #ApprovedGrades
            (courseId, semesterId, semesterStart, enrollmentDate,
             enrollmentId, credits, gradePoint)
        SELECT cr.courseId, sem.semesterId, sem.startDate, e.enrollmentDate,
               e.enrollmentId, cr.credits, gs.gradePoint
        FROM dbo.Enrollments AS e
        JOIN dbo.ClassSections AS cs ON cs.classSectionId = e.classSectionId
        JOIN dbo.Semesters AS sem ON sem.semesterId = cs.semesterId
        JOIN dbo.Courses AS cr ON cr.courseId = cs.courseId
        JOIN dbo.GradeBooks AS gb ON gb.enrollmentId = e.enrollmentId
        JOIN dbo.GradeScales AS gs ON gb.finalScore BETWEEN gs.minScore AND gs.maxScore
        JOIN dbo.Students AS st ON st.studentId = e.studentId
        WHERE e.studentId = @StudentId AND gb.isFinalized = 1
          AND EXISTS (
            SELECT 1 FROM dbo.Curriculum AS cu
            JOIN dbo.CurriculumCourses AS cc ON cc.curriculumId = cu.curriculumId
            WHERE cu.majorId=st.majorId AND cc.courseId=cr.courseId
          );

        -- Count only the latest attempt for a course within the same semester.
        SELECT courseId, semesterId, semesterStart, enrollmentDate,
               enrollmentId, credits, gradePoint
        INTO #TermGrades
        FROM (
            SELECT g.*,
                   ROW_NUMBER() OVER (
                       PARTITION BY semesterId, courseId
                       ORDER BY enrollmentDate DESC, enrollmentId DESC
                   ) AS seq
            FROM #ApprovedGrades AS g
        ) AS t WHERE t.seq=1;

        SELECT g.semesterId, MAX(g.semesterStart) AS semesterStart,
               CAST(ROUND(
                   SUM(CAST(g.gradePoint AS DECIMAL(12,4)) * g.credits)
                   / NULLIF(SUM(CAST(g.credits AS DECIMAL(12,4))),0), 2
               ) AS DECIMAL(4,2)) AS semesterGPA
        INTO #TermGpas
        FROM #TermGrades AS g
        GROUP BY g.semesterId;

        -- For every target semester, rank all finalized course attempts up to
        -- that semester. A retaken course contributes only its latest attempt.
        SELECT tg.semesterId AS targetSemesterId, tg.semesterGPA,
               g.courseId, g.credits, g.gradePoint,
               ROW_NUMBER() OVER (
                   PARTITION BY tg.semesterId, g.courseId
                   ORDER BY g.semesterStart DESC, g.enrollmentDate DESC,
                            g.semesterId DESC, g.enrollmentId DESC
               ) AS attemptRank
        INTO #CumulativeCandidates
        FROM #TermGpas AS tg
        JOIN #TermGrades AS g
          ON g.semesterStart < tg.semesterStart
          OR (g.semesterStart=tg.semesterStart
              AND g.semesterId<=tg.semesterId);

        SELECT targetSemesterId AS semesterId,
               MAX(semesterGPA) AS semesterGPA,
               CAST(ROUND(
                   SUM(CAST(gradePoint AS DECIMAL(12,4)) * credits)
                   / NULLIF(SUM(CAST(credits AS DECIMAL(12,4))),0), 2
               ) AS DECIMAL(4,2)) AS cumulativeGPA
        INTO #CalculatedResults
        FROM #CumulativeCandidates
        WHERE attemptRank=1
        GROUP BY targetSemesterId;

        -- Update/insert the official (studentId, semesterId) composite-key rows.
        UPDATE sr
           SET semesterGPA=calc.semesterGPA,
               cumulativeGPA=calc.cumulativeGPA
        FROM dbo.SemesterResults AS sr
        JOIN #CalculatedResults AS calc ON calc.semesterId=sr.semesterId
        WHERE sr.studentId=@StudentId;

        INSERT INTO dbo.SemesterResults
            (studentId, semesterId, semesterGPA, cumulativeGPA)
        SELECT @StudentId, calc.semesterId, calc.semesterGPA, calc.cumulativeGPA
        FROM #CalculatedResults AS calc
        WHERE NOT EXISTS (
            SELECT 1 FROM dbo.SemesterResults AS sr WITH (UPDLOCK, HOLDLOCK)
            WHERE sr.studentId=@StudentId AND sr.semesterId=calc.semesterId
        );

        -- Derived results with no finalized grade are no longer valid.
        DELETE FROM dbo.SemesterResults
        WHERE studentId=@StudentId
          AND NOT EXISTS (
              SELECT 1 FROM #CalculatedResults AS calc
              WHERE calc.semesterId=dbo.SemesterResults.semesterId
          );

        COMMIT TRANSACTION;
        IF @ReturnRows = 1
            SELECT studentId, semesterId, semesterGPA, cumulativeGPA
            FROM dbo.SemesterResults WHERE studentId=@StudentId
            ORDER BY semesterId;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- Lecturer finalization is an atomic operation: authentication + assignment,
-- complete marks, weighted result, letter-grade mapping and GPA recalculation.
-- Grade component editing is handled by Flask GradeService before this final step.
CREATE OR ALTER PROCEDURE dbo.usp_FinalizeGradeBook
    @GradebookId VARCHAR(10),
    @TokenHash CHAR(64)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Now DATETIME2(3)=SYSUTCDATETIME();
    DECLARE @LecturerId VARCHAR(10);
    DECLARE @StudentId VARCHAR(10);
    DECLARE @Mid DECIMAL(4,2), @Assignment DECIMAL(4,2),
            @Attendance DECIMAL(4,2), @Exam DECIMAL(4,2);
    DECLARE @Wmid DECIMAL(4,2), @Wassign DECIMAL(4,2),
            @Watt DECIMAL(4,2), @Wexam DECIMAL(4,2);
    DECLARE @Final DECIMAL(4,2), @Letter VARCHAR(2), @MatchCount INT;
    DECLARE @LockResult INT, @SessionsTouched INT;

    BEGIN TRY
        BEGIN TRANSACTION;
        SELECT @LecturerId=l.lecturerId
        FROM dbo.UserSessions AS sess WITH (UPDLOCK, HOLDLOCK)
        JOIN dbo.Users AS u ON u.userId=sess.userId
        JOIN dbo.Lecturers AS l ON l.userId=u.userId
        WHERE sess.tokenHash=@TokenHash
          AND sess.revokedAt IS NULL AND sess.expiresAt>@Now
          AND u.isLocked=0
          AND NOT EXISTS (SELECT 1 FROM dbo.Administrators AS a WHERE a.userId=u.userId)
          AND NOT EXISTS (SELECT 1 FROM dbo.Students AS st WHERE st.userId=u.userId);

        IF @LecturerId IS NULL
            THROW 51020, 'Active assigned Lecturer session is required.', 1;

        SELECT @StudentId=e.studentId,
               @Mid=gb.midtermMark, @Assignment=gb.assignmentMark,
               @Attendance=gb.attendanceMark, @Exam=gb.finalExamMark,
               @Wmid=cr.midtermWeight, @Wassign=cr.assignmentWeight,
               @Watt=cr.attendanceWeight, @Wexam=cr.finalExamWeight
        FROM dbo.GradeBooks AS gb WITH (UPDLOCK, HOLDLOCK)
        JOIN dbo.Enrollments AS e ON e.enrollmentId=gb.enrollmentId
        JOIN dbo.ClassSections AS cs ON cs.classSectionId=e.classSectionId
        JOIN dbo.Courses AS cr ON cr.courseId=cs.courseId
        WHERE gb.gradebookId=@GradebookId AND cs.lecturerId=@LecturerId;

        IF @StudentId IS NULL
            THROW 51021, 'Gradebook is absent or this lecturer is not assigned.', 1;
        IF @Mid IS NULL OR @Assignment IS NULL OR @Attendance IS NULL OR @Exam IS NULL
            THROW 51022, 'All four component marks are required before finalization.', 1;

        DECLARE @LockName NVARCHAR(255) = N'GPA:' + @StudentId;
        EXEC @LockResult=sys.sp_getapplock
            @Resource=@LockName,
            @LockMode='Exclusive', @LockOwner='Transaction', @LockTimeout=10000;
        IF @LockResult < 0
            THROW 51023, 'Cannot lock student GPA update.', 1;

        SET @Final = CAST(ROUND(
             (CAST(@Mid AS DECIMAL(12,4))*@Wmid
             +CAST(@Assignment AS DECIMAL(12,4))*@Wassign
             +CAST(@Attendance AS DECIMAL(12,4))*@Watt
             +CAST(@Exam AS DECIMAL(12,4))*@Wexam) / 100.00, 2
        ) AS DECIMAL(4,2));

        SELECT @MatchCount=COUNT(*), @Letter=MAX(letterGrade)
        FROM dbo.GradeScales
        WHERE @Final BETWEEN minScore AND maxScore;
        IF @MatchCount <> 1
            THROW 51024, 'Grade-scale mapping is missing or ambiguous.', 1;

        UPDATE dbo.GradeBooks
           SET finalScore=@Final, letterGrade=@Letter, isFinalized=1
        WHERE gradebookId=@GradebookId;

        -- The nested procedure uses the same SQL transaction; its failure rolls
        -- back the grade finalization as well as any partially calculated GPA.
        EXEC dbo.usp_RecalculateStudentGPA
            @StudentId=@StudentId, @ReturnRows=0;

        UPDATE dbo.UserSessions
           SET lastActivityAt=@Now, expiresAt=DATEADD(MINUTE,15,@Now)
        WHERE tokenHash=@TokenHash AND revokedAt IS NULL AND expiresAt>@Now;
        SET @SessionsTouched=@@ROWCOUNT;
        IF @SessionsTouched<>1
            THROW 51025, 'Session expired during grade finalization.', 1;

        COMMIT TRANSACTION;
        SELECT gradebookId, finalScore, letterGrade, isFinalized
        FROM dbo.GradeBooks WHERE gradebookId=@GradebookId;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO


-- ============================================================================
-- SECTION G. RE-RUNNABLE DEVELOPMENT DATA
-- ============================================================================
-- Set @SeedDemoData=0 in a production or shared university database.
-- Password hashes are for synthetic TEST accounts only; the actual test
-- password is managed out-of-band by the development team.
-- Existing records are never overwritten by the development-data section.
SET XACT_ABORT ON;
GO
DECLARE @SeedDemoData BIT = 1;
IF @SeedDemoData = 1
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;
        DECLARE @NewExampleGradeData BIT = 0;
        IF NOT EXISTS (
            SELECT 1 FROM dbo.GradeBooks WHERE gradebookId='GRB0000001'
        ) SET @NewExampleGradeData = 1;

    -- Demo data: Users (inserts only when PK is absent).
-- Synthetic credentials use Werkzeug-compatible PBKDF2 hashes; no live passwords are stored here.
    INSERT INTO dbo.Users (userId, username, passwordHash, isLocked, citizenId, fullName, dateOfBirth, email, phoneNumber, gender)
    SELECT src.userId, src.username, src.passwordHash, src.isLocked, src.citizenId, src.fullName, src.dateOfBirth, src.email, src.phoneNumber, src.gender
    FROM (VALUES
    ('USR000000001', 'admin01',
     'pbkdf2:sha256:600000$df9e7787bee0f5959c6071d6$47f5e7a4f9810537254bfb5642ed70f52d46d3145c7b3df16ea236ef2bf57739',
     0, '079000000001', N'Nguyen Van Minh', '1985-01-15',
     'admin01@example.test', '0900000001', 'Male'),

    ('USR000000002', 'student01',
     'pbkdf2:sha256:600000$50ae06afa3c809666f0ea075$7ba28032ab12fdaa42cf7595b3c4fd3ec533e0aa8ed9730a36e21ee21e68be09',
     0, '079000000002', N'Tran Minh Anh', '2005-03-12',
     'student01@example.test', '0900000002', 'Female'),

    ('USR000000003', 'student02',
     'pbkdf2:sha256:600000$5c791efe463bcb66b8708cd2$dbbe233fd30aa69b961cec42086974186ac6f1560658e63f0c1fe7177fda3070',
     0, '079000000003', N'Le Quoc Bao', '2005-07-21',
     'student02@example.test', '0900000003', 'Male'),

    ('USR000000004', 'student03',
     'pbkdf2:sha256:600000$692c563fb5e6ab6726b782b2$1054cc983e17f2447edc307ef2e31383f07e07dfd96e65247300344c6b6dc5cf',
     0, '079000000004', N'Pham Thu Ha', '2005-11-08',
     'student03@example.test', '0900000004', 'Female'),

    ('USR000000005', 'lecturer01',
     'pbkdf2:sha256:600000$84e786255baa5edf18a0e7f6$47d9aaa1f891e0fb0b37d6165da06689c7df3dd6e82277b2f2e38d77cc940e32',
     0, '079000000005', N'Nguyen Thi Lan', '1980-06-18',
     'lecturer01@example.test', '0900000005', 'Female'),

    ('USR000000006', 'lecturer02',
     'pbkdf2:sha256:600000$b1182fb4b5ce949c7a33d8c3$b1da58c0ed666fee3cb304a2b438e629f6366f784a53606c3eefa541fe7a6aab',
     0, '079000000006', N'Tran Hoang Nam', '1978-09-25',
     'lecturer02@example.test', '0900000006', 'Male')
    ) AS src (userId, username, passwordHash, isLocked, citizenId, fullName, dateOfBirth, email, phoneNumber, gender)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Users AS tgt WHERE tgt.userId=src.userId
    );

    -- Demo data: Faculties (inserts only when PK is absent).
    INSERT INTO dbo.Faculties (facultyId, facultyCode, facultyName, email, phoneNumber)
    SELECT src.facultyId, src.facultyCode, src.facultyName, src.email, src.phoneNumber
    FROM (VALUES
    ('FAC0000001', 'CNTT', N'Information Technology',
     'it@example.test', '0280000001'),

    ('FAC0000002', 'QTKD', N'Business Administration',
     'business@example.test', '0280000002')
    ) AS src (facultyId, facultyCode, facultyName, email, phoneNumber)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Faculties AS tgt WHERE tgt.facultyId=src.facultyId
    );

    -- Demo data: Administrators (inserts only when PK is absent).
    INSERT INTO dbo.Administrators (adminId, userId)
    SELECT src.adminId, src.userId
    FROM (VALUES
    ('ADM0000001', 'USR000000001')
    ) AS src (adminId, userId)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Administrators AS tgt WHERE tgt.adminId=src.adminId
    );

    -- Demo data: Majors (inserts only when PK is absent).
    INSERT INTO dbo.Majors (majorId, facultyId, majorName, majorCode)
    SELECT src.majorId, src.facultyId, src.majorName, src.majorCode
    FROM (VALUES
    ('MJR0000001', 'FAC0000001',
     N'Management Information Systems', 'MIS'),

    ('MJR0000002', 'FAC0000002',
     N'Business Administration', 'BA')
    ) AS src (majorId, facultyId, majorName, majorCode)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Majors AS tgt WHERE tgt.majorId=src.majorId
    );

    -- Demo data: Semesters (inserts only when PK is absent).
    INSERT INTO dbo.Semesters (semesterId, semesterName, endDate, startDate, academicYear)
    SELECT src.semesterId, src.semesterName, src.endDate, src.startDate, src.academicYear
    FROM (VALUES
    ('SEM0000001', N'Semester 1',
     '2026-01-15', '2025-09-01', '2025-2026'),
    ('SEM0000002', N'Semester 2',
     '2026-06-15', '2026-02-01', '2025-2026')
    ) AS src (semesterId, semesterName, endDate, startDate, academicYear)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Semesters AS tgt WHERE tgt.semesterId=src.semesterId
    );

    -- Demo data: Students (inserts only when PK is absent).
    INSERT INTO dbo.Students (studentId, userId, majorId, academicStatus)
    SELECT src.studentId, src.userId, src.majorId, src.academicStatus
    FROM (VALUES
    ('STU0000001', 'USR000000002', 'MJR0000001', N'Active'),
    ('STU0000002', 'USR000000003', 'MJR0000001', N'Active'),
    ('STU0000003', 'USR000000004', 'MJR0000002', N'Active')
    ) AS src (studentId, userId, majorId, academicStatus)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Students AS tgt WHERE tgt.studentId=src.studentId
    );

    -- Demo data: Lecturers (inserts only when PK is absent).
    INSERT INTO dbo.Lecturers (lecturerId, userId, facultyId)
    SELECT src.lecturerId, src.userId, src.facultyId
    FROM (VALUES
    ('LEC0000001', 'USR000000005', 'FAC0000001'),
    ('LEC0000002', 'USR000000006', 'FAC0000002')
    ) AS src (lecturerId, userId, facultyId)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Lecturers AS tgt WHERE tgt.lecturerId=src.lecturerId
    );

    -- Demo data: Courses (inserts only when PK is absent).
    INSERT INTO dbo.Courses (courseId, facultyId, courseCode, courseName, credits, midtermWeight, assignmentWeight, attendanceWeight, finalExamWeight)
    SELECT src.courseId, src.facultyId, src.courseCode, src.courseName, src.credits, src.midtermWeight, src.assignmentWeight, src.attendanceWeight, src.finalExamWeight
    FROM (VALUES
    ('CRS0000001', 'FAC0000001', 'DBI101',
     N'Database Systems', 3, 20.00, 20.00, 10.00, 50.00),

    ('CRS0000002', 'FAC0000001', 'PRG102',
     N'Python Programming', 3, 20.00, 20.00, 10.00, 50.00),

    ('CRS0000003', 'FAC0000002', 'MGT103',
     N'Principles of Management', 3, 20.00, 20.00, 10.00, 50.00)
    ) AS src (courseId, facultyId, courseCode, courseName, credits, midtermWeight, assignmentWeight, attendanceWeight, finalExamWeight)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Courses AS tgt WHERE tgt.courseId=src.courseId
    );

    -- Demo data: Curriculum (inserts only when PK is absent).
    -- Curriculum demo for a second major, used only for integration testing.
    -- Academic office must approve the actual curriculum for real students.
    INSERT INTO dbo.Curriculum (curriculumId, majorId, curriculumName, academicYear)
    SELECT src.curriculumId, src.majorId, src.curriculumName, src.academicYear
    FROM (VALUES
    ('CUR0000001', 'MJR0000001',
     N'MIS Curriculum 2025', '2025-2026'),
    ('CUR0000002', 'MJR0000002',
     N'Business Administration Curriculum 2025', '2025-2026')
    ) AS src (curriculumId, majorId, curriculumName, academicYear)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Curriculum AS tgt WHERE tgt.curriculumId=src.curriculumId
    );

    -- Demo data: CurriculumCourses (inserts only when PK is absent).
    -- CurriculumCourse links allow GPA filtering to the study plan of each major.
    -- Demo relationships are not an official university course catalog.
    INSERT INTO dbo.CurriculumCourses (curriculumId, courseId, courseType)
    SELECT src.curriculumId, src.courseId, src.courseType
    FROM (VALUES
    ('CUR0000001', 'CRS0000001', 'Required'),
    ('CUR0000001', 'CRS0000002', 'Required'),
    ('CUR0000001', 'CRS0000003', 'Elective'),
    ('CUR0000002', 'CRS0000003', 'Required'),
    ('CUR0000002', 'CRS0000001', 'Elective')
    ) AS src (curriculumId, courseId, courseType)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.CurriculumCourses AS tgt WHERE tgt.curriculumId=src.curriculumId AND tgt.courseId=src.courseId
    );

    -- Demo data: CoursePrerequisites (inserts only when PK is absent).
    INSERT INTO dbo.CoursePrerequisites (courseId, prerequisiteId)
    SELECT src.courseId, src.prerequisiteId
    FROM (VALUES
    ('CRS0000002', 'CRS0000001'),
    ('CRS0000003', 'CRS0000002')
    ) AS src (courseId, prerequisiteId)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.CoursePrerequisites AS tgt WHERE tgt.courseId=src.courseId AND tgt.prerequisiteId=src.prerequisiteId
    );

    -- Demo data: ClassSections (inserts only when PK is absent).
    INSERT INTO dbo.ClassSections (classSectionId, lecturerId, courseId, semesterId, classCode, maxCapacity, currentEnrollment, room, dayOfWeek, startTime, endTime)
    SELECT src.classSectionId, src.lecturerId, src.courseId, src.semesterId, src.classCode, src.maxCapacity, src.currentEnrollment, src.room, src.dayOfWeek, src.startTime, src.endTime
    FROM (VALUES
    ('CLS0000001', 'LEC0000001', 'CRS0000001',
     'SEM0000001', 'DBI101.01', 40, 3, 'A.101',
     2, '07:00', '09:30'),

    ('CLS0000002', 'LEC0000001', 'CRS0000002',
     'SEM0000001', 'PRG102.01', 35, 2, 'A.202',
     3, '09:45', '12:15'),

    ('CLS0000003', 'LEC0000002', 'CRS0000003',
     'SEM0000001', 'MGT103.01', 40, 1, 'B.303',
     4, '13:00', '15:30'),
    ('CLS0000004', 'LEC0000001', 'CRS0000001',
     'SEM0000002', 'DBI101.02', 40, 1, 'A.101',
     2, '07:00', '09:30')
    ) AS src (classSectionId, lecturerId, courseId, semesterId, classCode, maxCapacity, currentEnrollment, room, dayOfWeek, startTime, endTime)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.ClassSections AS tgt WHERE tgt.classSectionId=src.classSectionId
    );

    -- Demo data: Enrollments (inserts only when PK is absent).
    INSERT INTO dbo.Enrollments (enrollmentId, studentId, classSectionId, enrollmentDate)
    SELECT src.enrollmentId, src.studentId, src.classSectionId, src.enrollmentDate
    FROM (VALUES
    ('ENR0000001', 'STU0000001', 'CLS0000001', '2025-08-20'),
    ('ENR0000002', 'STU0000002', 'CLS0000001', '2025-08-20'),
    ('ENR0000003', 'STU0000003', 'CLS0000001', '2025-08-21'),
    ('ENR0000004', 'STU0000001', 'CLS0000002', '2025-08-21'),
    ('ENR0000005', 'STU0000002', 'CLS0000002', '2025-08-21'),
    ('ENR0000006', 'STU0000001', 'CLS0000003', '2025-08-22'),
    ('ENR0000007', 'STU0000001', 'CLS0000004', '2026-01-20')
    ) AS src (enrollmentId, studentId, classSectionId, enrollmentDate)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.Enrollments AS tgt WHERE tgt.enrollmentId=src.enrollmentId
    );

    -- Demo data: GradeBooks (inserts only when PK is absent).
    -- One gradebook is left as a draft to test finalized-grade access rules.
    -- Letter grades are consistent with the configured illustrative academic grading scale.
    INSERT INTO dbo.GradeBooks (gradebookId, enrollmentId, midtermMark, assignmentMark, attendanceMark, finalExamMark, finalScore, letterGrade, isFinalized)
    SELECT src.gradebookId, src.enrollmentId, src.midtermMark, src.assignmentMark, src.attendanceMark, src.finalExamMark, src.finalScore, src.letterGrade, src.isFinalized
    FROM (VALUES
    ('GRB0000001', 'ENR0000001', 8.00, 8.50, 9.00, 8.50, 8.45, 'B+', 1),
    ('GRB0000002', 'ENR0000002', 7.50, 8.00, 8.50, 8.00, 7.95, 'B', 1),
    ('GRB0000003', 'ENR0000003', 9.00, 9.00, 9.50, 9.00, 9.05, 'A', 1),
    ('GRB0000004', 'ENR0000004', 8.50, 9.00, 9.00, 8.50, 8.65, 'A', 1),
    ('GRB0000005', 'ENR0000005', 7.00, 7.50, 8.00, 7.50, 7.45, 'B', 1),
    ('GRB0000006', 'ENR0000006', 8.00, NULL, NULL, NULL, NULL, NULL, 0),
    ('GRB0000007', 'ENR0000007', 9.00, 8.50, 9.50, 9.00, 8.95, 'A', 1)
    ) AS src (gradebookId, enrollmentId, midtermMark, assignmentMark, attendanceMark, finalExamMark, finalScore, letterGrade, isFinalized)
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.GradeBooks AS tgt WHERE tgt.gradebookId=src.gradebookId
    );



        -- Recalculate only on the first insertion of the synthetic gradebook set.
        -- This avoids rewriting GPA on repeated deployments to an existing DB.
        IF @NewExampleGradeData = 1
        BEGIN
            EXEC dbo.usp_RecalculateStudentGPA @StudentId='STU0000001';
            EXEC dbo.usp_RecalculateStudentGPA @StudentId='STU0000002';
            EXEC dbo.usp_RecalculateStudentGPA @StudentId='STU0000003';
        END;

        COMMIT TRANSACTION;
        PRINT 'Development sample data ready.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO


-- ============================================================================
-- SECTION H. DATABASE SELF-CHECKS (READ ONLY)
-- ============================================================================
-- Expected in a fresh demonstration database: 17 tables (15 domain + 2 support).
SELECT DB_NAME() AS DatabaseName;
SELECT COUNT(*) AS TableCount FROM sys.tables WHERE schema_id=SCHEMA_ID(N'dbo');
SELECT name AS TableName FROM sys.tables WHERE schema_id=SCHEMA_ID(N'dbo') ORDER BY name;

-- Ensure every CHECK constraint is enabled and trusted by SQL Server.
SELECT OBJECT_NAME(parent_object_id) AS TableName, name AS CheckName,
       is_disabled, is_not_trusted
FROM sys.check_constraints
WHERE OBJECT_SCHEMA_NAME(parent_object_id)=N'dbo'
ORDER BY TableName, CheckName;

-- All sessions are INVALID if expired, revoked or user locked, even if the
-- physical session row is retained for diagnostics and later cleanup.
SELECT COUNT(*) AS ActiveSessions
FROM dbo.UserSessions AS sess JOIN dbo.Users AS u ON u.userId=sess.userId
WHERE sess.revokedAt IS NULL AND sess.expiresAt>SYSUTCDATETIME()
      AND u.isLocked=0;

SELECT letterGrade, minScore, maxScore, gradePoint, isPassing
FROM dbo.GradeScales ORDER BY minScore;

-- GPA values are produced from finalized and curriculum-eligible results.
SELECT studentId, semesterId, semesterGPA, cumulativeGPA
FROM dbo.SemesterResults ORDER BY studentId, semesterId;

-- Invalid or mismatched finalized grade labels should return NO ROWS.
SELECT gb.gradebookId, gb.finalScore, gb.letterGrade,
       gs.letterGrade AS ExpectedLetter
FROM dbo.GradeBooks AS gb
OUTER APPLY (
    SELECT MAX(g.letterGrade) AS letterGrade, COUNT(*) AS Matches
    FROM dbo.GradeScales AS g
    WHERE gb.finalScore BETWEEN g.minScore AND g.maxScore
) AS gs
WHERE gb.isFinalized=1 AND (
    gs.Matches <> 1 OR gb.letterGrade<>gs.letterGrade
    OR gb.letterGrade IS NULL OR gb.finalScore IS NULL
);

-- Every class's cached enrollment count should match the real enrollment rows.
SELECT cs.classSectionId, cs.currentEnrollment, COUNT(e.enrollmentId) AS ActualCount
FROM dbo.ClassSections AS cs
LEFT JOIN dbo.Enrollments AS e ON e.classSectionId=cs.classSectionId
GROUP BY cs.classSectionId,cs.currentEnrollment
HAVING cs.currentEnrollment<>COUNT(e.enrollmentId);

-- Detect users with no role or accidentally assigned to multiple role tables.
SELECT u.userId, u.username,
       (CASE WHEN ad.userId IS NULL THEN 0 ELSE 1 END
        + CASE WHEN st.userId IS NULL THEN 0 ELSE 1 END
        + CASE WHEN le.userId IS NULL THEN 0 ELSE 1 END) AS RoleCount
FROM dbo.Users AS u
LEFT JOIN dbo.Administrators AS ad ON ad.userId=u.userId
LEFT JOIN dbo.Students AS st ON st.userId=u.userId
LEFT JOIN dbo.Lecturers AS le ON le.userId=u.userId
WHERE (CASE WHEN ad.userId IS NULL THEN 0 ELSE 1 END
        + CASE WHEN st.userId IS NULL THEN 0 ELSE 1 END
        + CASE WHEN le.userId IS NULL THEN 0 ELSE 1 END) <> 1;

-- Every major should have a curriculum for Student View Curriculum.
SELECT majorId, majorName FROM dbo.Majors AS m
WHERE NOT EXISTS (SELECT 1 FROM dbo.Curriculum AS c WHERE c.majorId=m.majorId);

-- Final scores should match the course's configured weighted components.
SELECT gb.gradebookId, gb.finalScore,
       CAST(ROUND((CAST(gb.midtermMark AS DECIMAL(12,4))*cr.midtermWeight
                   +CAST(gb.assignmentMark AS DECIMAL(12,4))*cr.assignmentWeight
                   +CAST(gb.attendanceMark AS DECIMAL(12,4))*cr.attendanceWeight
                   +CAST(gb.finalExamMark AS DECIMAL(12,4))*cr.finalExamWeight)
                  / 100.00, 2) AS DECIMAL(4,2)) AS ExpectedFinalScore
FROM dbo.GradeBooks AS gb
JOIN dbo.Enrollments AS e ON e.enrollmentId=gb.enrollmentId
JOIN dbo.ClassSections AS cs ON cs.classSectionId=e.classSectionId
JOIN dbo.Courses AS cr ON cr.courseId=cs.courseId
WHERE gb.isFinalized=1 AND (
    gb.finalScore IS NULL OR gb.finalScore <>
    CAST(ROUND((CAST(gb.midtermMark AS DECIMAL(12,4))*cr.midtermWeight
                +CAST(gb.assignmentMark AS DECIMAL(12,4))*cr.assignmentWeight
                +CAST(gb.attendanceMark AS DECIMAL(12,4))*cr.attendanceWeight
                +CAST(gb.finalExamMark AS DECIMAL(12,4))*cr.finalExamWeight)
               /100.00, 2) AS DECIMAL(4,2))
);

-- IMPORTANT: the database stores and computes GPA. Flask still must enforce:
-- password verification, role/access checks, field validation, and API security.
-- Student Transcript APIs must filter by the authenticated student's userId
-- and isFinalized=1; unrestricted SELECTs are for SSMS development only.


-- ============================================================================
-- SECTION I. TRANSACTION CONCURRENCY PROTECTION (DEPLOYMENT SOURCE)
-- This section documents the installed stored procedure.
-- Do not rerun all earlier sections against the live database merely to deploy it.
-- ============================================================================
/*
  DEPLOYMENT ADD-ONLY - Student Management System Group 05
  Run this file on the EXISTING StudentManagementSystem database.
  Adds/redeploys one grade-draft concurrency procedure. No demo transactions,
  no UPDATE/INSERT/DELETE against business data and no table changes.
  Must still update Flask Gradebook repository to invoke it before protection
  is effective for draft edits. This does NOT affect Change Password.
*/
IF DB_ID(N'StudentManagementSystem') IS NULL
    THROW 51200, 'StudentManagementSystem database does not exist.', 1;
GO
USE StudentManagementSystem;
GO
IF OBJECT_ID(N'dbo.GradeBooks', N'U') IS NULL
   OR OBJECT_ID(N'dbo.UserSessions', N'U') IS NULL
   OR OBJECT_ID(N'dbo.Lecturers', N'U') IS NULL
   OR OBJECT_ID(N'dbo.Enrollments', N'U') IS NULL
   OR OBJECT_ID(N'dbo.ClassSections', N'U') IS NULL
    THROW 51201, 'Missing required existing table; deployment aborted.', 1;
GO
CREATE OR ALTER PROCEDURE dbo.usp_UpdateDraftGradeComponentsSafely
    @GradebookId VARCHAR(10),
    @TokenHash CHAR(64),
    @ExpectedMidterm DECIMAL(4,2) = NULL,
    @ExpectedAssignment DECIMAL(4,2) = NULL,
    @ExpectedAttendance DECIMAL(4,2) = NULL,
    @ExpectedFinalExam DECIMAL(4,2) = NULL,
    @NewMidterm DECIMAL(4,2) = NULL,
    @NewAssignment DECIMAL(4,2) = NULL,
    @NewAttendance DECIMAL(4,2) = NULL,
    @NewFinalExam DECIMAL(4,2) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Now DATETIME2(3) = SYSUTCDATETIME();
    DECLARE @LecturerId VARCHAR(10);
    DECLARE @StoredMidterm DECIMAL(4,2);
    DECLARE @StoredAssignment DECIMAL(4,2);
    DECLARE @StoredAttendance DECIMAL(4,2);
    DECLARE @StoredFinalExam DECIMAL(4,2);
    DECLARE @Finalized BIT;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Same identity and role checks as finalization; NEVER trust a role
        -- or lecturer ID provided by the browser.
        SELECT @LecturerId = l.lecturerId
        FROM dbo.UserSessions AS sess WITH (UPDLOCK, HOLDLOCK)
        JOIN dbo.Users AS u ON u.userId = sess.userId
        JOIN dbo.Lecturers AS l ON l.userId = u.userId
        WHERE sess.tokenHash = @TokenHash
          AND sess.revokedAt IS NULL
          AND sess.expiresAt > @Now
          AND u.isLocked = 0
          AND NOT EXISTS (
              SELECT 1 FROM dbo.Administrators AS a WHERE a.userId=u.userId
          )
          AND NOT EXISTS (
              SELECT 1 FROM dbo.Students AS s WHERE s.userId=u.userId
          );

        IF @LecturerId IS NULL
            THROW 51140, 'Active Lecturer session is required.', 1;

        -- Take an update lock BEFORE comparing existing marks to the editor's
        -- originally loaded values. Hold until the transaction commits.
        SELECT
            @StoredMidterm = gb.midtermMark,
            @StoredAssignment = gb.assignmentMark,
            @StoredAttendance = gb.attendanceMark,
            @StoredFinalExam = gb.finalExamMark,
            @Finalized = gb.isFinalized
        FROM dbo.GradeBooks AS gb WITH (UPDLOCK, HOLDLOCK)
        JOIN dbo.Enrollments AS e ON e.enrollmentId = gb.enrollmentId
        JOIN dbo.ClassSections AS cs ON cs.classSectionId = e.classSectionId
        WHERE gb.gradebookId = @GradebookId
          AND cs.lecturerId = @LecturerId;

        IF @@ROWCOUNT <> 1
            THROW 51141, 'Gradebook not found or not assigned to Lecturer.', 1;

        IF @Finalized IS NULL OR @Finalized <> 0
            THROW 51143, 'Finalized gradebooks cannot be edited.', 1;

        IF (@NewMidterm IS NOT NULL AND (@NewMidterm < 0 OR @NewMidterm > 10))
           OR (@NewAssignment IS NOT NULL AND (@NewAssignment < 0 OR @NewAssignment > 10))
           OR (@NewAttendance IS NOT NULL AND (@NewAttendance < 0 OR @NewAttendance > 10))
           OR (@NewFinalExam IS NOT NULL AND (@NewFinalExam < 0 OR @NewFinalExam > 10))
            THROW 51144, 'Marks must be in the range 0.00 to 10.00.', 1;

        -- EXCEPT compares complete tuples and treats two NULLs as equal.
        -- If another user committed a different grade since this page loaded,
        -- reject the stale write rather than silently losing that update.
        IF EXISTS (
            SELECT @ExpectedMidterm, @ExpectedAssignment,
                   @ExpectedAttendance, @ExpectedFinalExam
            EXCEPT
            SELECT @StoredMidterm, @StoredAssignment,
                   @StoredAttendance, @StoredFinalExam
        )
            THROW 51142, 'Concurrent edit detected. Reload current grades.', 1;

        UPDATE dbo.GradeBooks
        SET midtermMark = @NewMidterm,
            assignmentMark = @NewAssignment,
            attendanceMark = @NewAttendance,
            finalExamMark = @NewFinalExam
        WHERE gradebookId = @GradebookId AND isFinalized = 0;

        IF @@ROWCOUNT <> 1
            THROW 51145, 'Gradebook changed before update.', 1;

        -- A successful grade update must not refresh an expired or revoked
        -- session. The row is locked from authentication to the final update.
        UPDATE dbo.UserSessions
        SET lastActivityAt = @Now,
            expiresAt = DATEADD(MINUTE, 15, @Now)
        WHERE tokenHash = @TokenHash
          AND revokedAt IS NULL
          AND expiresAt > @Now;

        IF @@ROWCOUNT <> 1
            THROW 51146, 'Session expired during grade update.', 1;

        COMMIT TRANSACTION;

        SELECT gradebookId, midtermMark, assignmentMark,
               attendanceMark, finalExamMark, isFinalized
        FROM dbo.GradeBooks
        WHERE gradebookId = @GradebookId;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

SELECT DB_NAME() AS DatabaseName,
       OBJECT_ID(N'dbo.usp_UpdateDraftGradeComponentsSafely', N'P') AS ProcedureObjectId;
GO


/* ============================================================================
   SECTION I. FULL-SYSTEM SYNTHETIC DEMO DATA — 3 ROLES
   ============================================================================
   Integrated directly with the database schema, original demonstration data,
   GPA calculations and concurrency-protection procedures above.
   This section resolves login-name collisions with baseline accounts, and
   migrates previously committed demo_ accounts without altering their IDs.
   This section adds synthetic accounts, faculties, courses, class sections, gradebooks,
   enrollments and derived GPAs without replacing original rows or schema.

   RUN THIS ONE FILE IN SSMS (F5), NOT as one pyodbc cursor.execute():
   1) BACK UP StudentManagementSystem / test on a DEVELOPMENT COPY.
   2) The OFFICIAL file has @ApplySeed=1 and saves the new demo rows.
   3) The read-only verification at the end prints counts and concurrency target.
   4) For a preview-only run, change @ApplySeed=0, but this affects only the
      expanded demo data, not original schema and baseline seed above.

   IMPORTANT: The ORIGINAL SQL ABOVE has @SeedDemoData=1 and commits its own
   original six users / academic rows independently of @ApplySeed.
   @ApplySeed=0 rolls back ONLY the expanded-demo-data section.
   Do not run this script on a live/production school database.

   Original concurrency-protection stored procedures are unchanged.
   Concurrency target GRB0000006 is NOT updated or deleted by this section.
============================================================================ */

/*
STUDENT MANAGEMENT SYSTEM - GROUP 05
ADDITIVE, RE-RUNNABLE FULL-SYSTEM DEMO DATA (SQL SERVER)

Source: DB_StudentManagementSystem_FINAL(1).sql (15 domain tables + 2 support tables)
Run in SSMS against a BACKED-UP DEVELOPMENT COPY, never production.
NO DROP / ALTER TABLE / UPDATE of original sample accounts or original gradebooks.
The concurrency target GRB0000006 is explicitly left untouched.

Account login examples (synthetic DEVELOPMENT accounts only):
    Administrator: admin01 / Admin01112026
    Student:       student01 / Student01112026
    Lecturer:      lecturer01 / Lecturer01112026
Other accounts use matching two-digit numbers (01-02 / 01-16 / 01-08).
Demo passwords are predictable and must never be used for real users.
Passwords are stored as Werkzeug-compatible PBKDF2-SHA256 600,000 hashes.
These publicly known demo accounts are NOT suitable for production.

The OFFICIAL submission defaults @ApplySeed=1 and commits demo data.
Set @ApplySeed=0 only when previewing the expanded section on a test copy;
original database setup and original sample rows have already committed.
Re-running after successful seed preserves existing academic demo records.

IMPORTANT: UserSessions is created only by real login; no fake session tokens.
GradeScales already exists in SQL FINAL and is NOT edited.
SemesterResults are recalculated using dbo.usp_RecalculateStudentGPA.
*/

USE StudentManagementSystem;
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET LOCK_TIMEOUT 15000;
GO

DECLARE @ApplySeed BIT = 1; -- OFFICIAL DEFAULT: 1 = COMMIT, 0 = preview / ROLLBACK

IF DB_NAME() <> N'StudentManagementSystem'
    THROW 52000, 'Stop: you are in the wrong database.', 1;
IF OBJECT_ID(N'dbo.GradeBooks',N'U') IS NULL
   OR OBJECT_ID(N'dbo.Users',N'U') IS NULL
   OR OBJECT_ID(N'dbo.CurriculumCourses',N'U') IS NULL
   OR OBJECT_ID(N'dbo.GradeScales',N'U') IS NULL
    THROW 52001, 'Stop: deploy the approved SQL FINAL schema first.', 1;
IF OBJECT_ID(N'dbo.usp_RecalculateStudentGPA',N'P') IS NULL
    THROW 52002, 'Stop: SQL FINAL GPA procedure is missing.', 1;

-- Clean a leftover local temp table when re-running in the SAME SSMS connection.
-- This does not touch any permanent table or original rows.
IF OBJECT_ID(N'tempdb..#DemoEnrollmentPlan', N'U') IS NOT NULL
    DROP TABLE #DemoEnrollmentPlan;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Prevent multiple deployments of this demo script from racing each other.
    DECLARE @SeedLock INT;
    EXEC @SeedLock = sys.sp_getapplock
        @Resource=N'SMS_G05_FULL_DEMO_SEED_V1',
        @LockMode='Exclusive',
        @LockOwner='Transaction',
        @LockTimeout=15000;
    IF @SeedLock < 0 THROW 52003, 'Cannot acquire demo seed lock.', 1;

    -- ================================================================
    -- A. USERS: 2 Administrator + 16 Student + 8 Lecturer
    -- ================================================================
    DECLARE @SeedUsers TABLE (
        userId VARCHAR(12) PRIMARY KEY,
        username VARCHAR(50), passwordHash VARCHAR(255), isLocked BIT,
        citizenId VARCHAR(12), fullName NVARCHAR(100), dateOfBirth DATE,
        email VARCHAR(100), phoneNumber VARCHAR(15), gender NVARCHAR(10)
    );
    INSERT INTO @SeedUsers VALUES
        ('USR000009001', 'admin01', 'pbkdf2:sha256:600000$690a92fc5fbc3dc59d4eb7d2$dea59d299b679983b0bfa4a3d370fb36906f6fc727dac25fa3a361289f5b73a3', 0, '999026009001', N'Nguyen Hai Dang', '1981-02-02', 'demo_admin01@g05-demo.invalid', '0999909001', 'Male'),
        ('USR000009002', 'admin02', 'pbkdf2:sha256:600000$cd70f3fefd8942f53f07b9b7$6b8c6f2a781271985e7846ef32f43eae48a5a4e8f54ec97fe55fedb689377a4a', 0, '999026009002', N'Tran Thi Minh Chau', '1982-03-03', 'demo_admin02@g05-demo.invalid', '0999909002', 'Female'),
        ('USR000009003', 'student01', 'pbkdf2:sha256:600000$d7fa9250f9df0fcfb6e0def4$9900ff17a7b842ff4bb0e3eef75bb93ff4d90fc0a5ea894130e32eb141601541', 0, '999026009003', N'Pham Gia Huy', '2004-02-02', 'demo_student01@g05-demo.invalid', '0999909003', 'Male'),
        ('USR000009004', 'student02', 'pbkdf2:sha256:600000$dfacb25370df29c1cf2b6061$ec2aca2c36d09ac4a0685bcd97cb2ad9f9fef5ea95b79e6c22389cc5c966fa99', 0, '999026009004', N'Le Ngoc Anh', '2005-03-03', 'demo_student02@g05-demo.invalid', '0999909004', 'Female'),
        ('USR000009005', 'student03', 'pbkdf2:sha256:600000$b1acee56cfe42415e73420df$dcbdf58fceefae734eccd34b76d76ff4a7350e02161d810697c302cb04352374', 0, '999026009005', N'Do Minh Khang', '2006-04-04', 'demo_student03@g05-demo.invalid', '0999909005', 'Male'),
        ('USR000009006', 'student04', 'pbkdf2:sha256:600000$855537699d3c235fbc0f3c82$0a48bc10453cd46edd4bc91d7b7c59e8a5712217dd39fcb063a7a2bdf4838a8b', 0, '999026009006', N'Vo Thanh Thao', '2003-05-05', 'demo_student04@g05-demo.invalid', '0999909006', 'Female'),
        ('USR000009007', 'student05', 'pbkdf2:sha256:600000$c1fc7662d0ea86218314b80b$aed984bc5b41aec045c014c0d35b4ca28e6790cc3a019f9ece2f1b6b40e94c9b', 0, '999026009007', N'Bui Tuan Kiet', '2004-06-06', 'demo_student05@g05-demo.invalid', '0999909007', 'Male'),
        ('USR000009008', 'student06', 'pbkdf2:sha256:600000$194d725404f957dff4c3ba0e$08ca15df8fa7c1e1752294345465f08f53dd7c1115a9989dff460e301419bf75', 1, '999026009008', N'Hoang My Linh', '2005-07-07', 'demo_student06@g05-demo.invalid', '0999909008', 'Female'),
        ('USR000009009', 'student07', 'pbkdf2:sha256:600000$74b5280be2fe4a8364fba228$4ecca438549005b72c03072b9c602c724e4c1a7f3ac9946c79dacf35c6b5f380', 0, '999026009009', N'Tran Anh Tuan', '2006-08-08', 'demo_student07@g05-demo.invalid', '0999909009', 'Male'),
        ('USR000009010', 'student08', 'pbkdf2:sha256:600000$cc47f79f7d38b193affd022a$15cb735059a77911c82b47d3753298e167289c3dd4b15aeedf22e93f8e0b7510', 0, '999026009010', N'Nguyen Thu Ha', '2003-09-09', 'demo_student08@g05-demo.invalid', '0999909010', 'Female'),
        ('USR000009011', 'student09', 'pbkdf2:sha256:600000$61ea863c633139768e85fb84$a4d1a6da8a9887c1e8c27b0f81c8f5f2b70d818885c20f4d122bbd14461438d4', 0, '999026009011', N'Phan Minh Quan', '2004-10-10', 'demo_student09@g05-demo.invalid', '0999909011', 'Male'),
        ('USR000009012', 'student10', 'pbkdf2:sha256:600000$38996f74825aad2e0e2c51f7$7b06902770fdc1a965b9a86c1c5e3b4ac78491cddec1915b9b736bc9fd622bdc', 0, '999026009012', N'Mai Ngoc Lan', '2005-11-11', 'demo_student10@g05-demo.invalid', '0999909012', 'Female'),
        ('USR000009013', 'student11', 'pbkdf2:sha256:600000$bda84f89a65d0f741c9f0b7f$b91810026ebe568771722597e55ecc5bab96d69e184c093b2e4111ba65c86714', 0, '999026009013', N'Dang Minh Quan', '2006-12-12', 'demo_student11@g05-demo.invalid', '0999909013', 'Male'),
        ('USR000009014', 'student12', 'pbkdf2:sha256:600000$b190502deb2afc8c190d4959$318980fe685ae78c2ec90fd88a351e4807c167b4735d808cc25e21412d17d7b1', 0, '999026009014', N'Nguyen Thu Trang', '2003-01-13', 'demo_student12@g05-demo.invalid', '0999909014', 'Female'),
        ('USR000009015', 'student13', 'pbkdf2:sha256:600000$ec90beb15ec9b327992aa25e$27bc0c1ae4dff5fdbb77ee76decd6da21f0cae7d0502088db91adcfa9db7b6dc', 0, '999026009015', N'Le Duy Bao', '2004-02-14', 'demo_student13@g05-demo.invalid', '0999909015', 'Male'),
        ('USR000009016', 'student14', 'pbkdf2:sha256:600000$643b7f555ae8f170ff05467f$459b9b72cda3dc106f3c6cf4f9139585908d221c678fa72127df3c830b01943c', 0, '999026009016', N'Trinh Thanh Vy', '2005-03-15', 'demo_student14@g05-demo.invalid', '0999909016', 'Female'),
        ('USR000009017', 'student15', 'pbkdf2:sha256:600000$6c5b6883a7edcdad36860458$f2fea81b1a9479c4c9cf59f33e80b21a37d6306fdb41e7c37ad2f942ff4521b2', 0, '999026009017', N'Vo Minh Phuc', '2006-04-16', 'demo_student15@g05-demo.invalid', '0999909017', 'Male'),
        ('USR000009018', 'student16', 'pbkdf2:sha256:600000$20e9c5e305fbaf2b651bb285$d93e594d50ce8c079bd760c69bc60e175b4493c4e15fd2e644ecf0b92cd499d6', 0, '999026009018', N'Duong Minh Ngoc', '2003-05-17', 'demo_student16@g05-demo.invalid', '0999909018', 'Female'),
        ('USR000009019', 'lecturer01', 'pbkdf2:sha256:600000$7f808a7f0b04fc4a25e87b57$59c2550b0b3c26ecccaa87a0102189db64e8abe31c0dd0054ca91fb6a62e2493', 0, '999026009019', N'Nguyen Thanh Binh', '1981-02-02', 'demo_lecturer01@g05-demo.invalid', '0999909019', 'Male'),
        ('USR000009020', 'lecturer02', 'pbkdf2:sha256:600000$0ce8c6c58e93084f6e4e5702$618f2e7d27b0d2aa57ca39f7ff486bde43e122d6daed962a948d071d94f4bd78', 0, '999026009020', N'Pham Thi Quynh Nhu', '1982-03-03', 'demo_lecturer02@g05-demo.invalid', '0999909020', 'Female'),
        ('USR000009021', 'lecturer03', 'pbkdf2:sha256:600000$27d589572d4b842dca35c4fc$f4e352b3e95476c4f5648206533e2a41756aadb07591ffbf77db99f02b2f362d', 0, '999026009021', N'Le Duc Thinh', '1983-04-04', 'demo_lecturer03@g05-demo.invalid', '0999909021', 'Male'),
        ('USR000009022', 'lecturer04', 'pbkdf2:sha256:600000$68c968df91e371f2bfe585e7$0e827f5e576739794bb964b381e2f45ab415e8c1f36aee4ef2667f380b197510', 0, '999026009022', N'Dang Hoai Thu', '1984-05-05', 'demo_lecturer04@g05-demo.invalid', '0999909022', 'Female'),
        ('USR000009023', 'lecturer05', 'pbkdf2:sha256:600000$b5aad52a693859d31d80e66d$203ba04bca8bf2a57cf5f338f06e9e4fca7b8264397a7999db8e97a4be77523d', 0, '999026009023', N'Vo Ngoc Minh', '1985-06-06', 'demo_lecturer05@g05-demo.invalid', '0999909023', 'Male'),
        ('USR000009024', 'lecturer06', 'pbkdf2:sha256:600000$7538ffb31bea6bd6169947b5$ed85861e5672a91662a53ac13612e010d02807a941ddda5063f0b4abf29140f2', 0, '999026009024', N'Tran Thu Hien', '1986-07-07', 'demo_lecturer06@g05-demo.invalid', '0999909024', 'Female'),
        ('USR000009025', 'lecturer07', 'pbkdf2:sha256:600000$c52fde9e698a4dca1b5e7891$e2ccb205df34305e78f66a3864e7de9549f6e5c2f6a486393ac03c64ac5a5568', 0, '999026009025', N'Bui Khac Tien', '1987-08-08', 'demo_lecturer07@g05-demo.invalid', '0999909025', 'Male'),
        ('USR000009026', 'lecturer08', 'pbkdf2:sha256:600000$17f759e9a120beb0182df5d1$f9c5b90fa4c1a3319b7906fb48ce4abd55c99594783332701747f027fed74e30', 0, '999026009026', N'Ngo My Dung', '1988-09-09', 'demo_lecturer08@g05-demo.invalid', '0999909026', 'Female');

    -- ================================================================
    -- LOGIN NAMESPACE MIGRATION (six original baseline accounts)
    -- The original source shipped admin01, student01-03, lecturer01-02.
    -- Reserve these clean usernames for the 26 expanded demo accounts.
    -- Keep all original IDs, roles, passwords, grades and related rows.
    -- Re-execution is safe: 'base_' usernames are left unchanged.
    -- ================================================================
    DECLARE @BaseAccounts TABLE (
        userId VARCHAR(12) PRIMARY KEY,
        citizenId VARCHAR(12) NOT NULL,
        oldUsername VARCHAR(50) NOT NULL,
        newUsername VARCHAR(50) NOT NULL
    );
    INSERT INTO @BaseAccounts (userId, citizenId, oldUsername, newUsername)
    VALUES
        ('USR000000001','079000000001','admin01','base_admin01'),
        ('USR000000002','079000000002','student01','base_student01'),
        ('USR000000003','079000000003','student02','base_student02'),
        ('USR000000004','079000000004','student03','base_student03'),
        ('USR000000005','079000000005','lecturer01','base_lecturer01'),
        ('USR000000006','079000000006','lecturer02','base_lecturer02');

    -- Never rename an unexpected account that happens to reuse a login.
    IF EXISTS (
        SELECT 1
        FROM @BaseAccounts b
        JOIN dbo.Users u ON u.username=b.oldUsername
        WHERE u.userId<>b.userId
          AND NOT EXISTS (
              SELECT 1 FROM @SeedUsers su
              WHERE su.userId=u.userId AND su.username=u.username
          )
    ) THROW 52010, 'Baseline username belongs to an unexpected account.', 1;

    IF EXISTS (
        SELECT 1
        FROM @BaseAccounts b
        JOIN dbo.Users u ON u.userId=b.userId
        WHERE u.username=b.oldUsername
          AND u.citizenId<>b.citizenId
    ) THROW 52011, 'Baseline identity check failed; no usernames changed.', 1;

    IF EXISTS (
        SELECT 1
        FROM @BaseAccounts b
        JOIN dbo.Users u ON u.username=b.newUsername
        WHERE u.userId<>b.userId
    ) THROW 52012, 'A reserved base_ username is already owned by another account.', 1;

    DECLARE @RenamedBase TABLE(userId VARCHAR(12) PRIMARY KEY);
    UPDATE u
       SET username=b.newUsername
       OUTPUT inserted.userId INTO @RenamedBase(userId)
    FROM dbo.Users u
    INNER JOIN @BaseAccounts b ON b.userId=u.userId
    WHERE u.username=b.oldUsername
      AND u.citizenId=b.citizenId;

    -- A prior authenticated baseline session cannot silently retain an
    -- account whose login identity has been changed by deployment.
    UPDATE sess
       SET revokedAt=SYSUTCDATETIME()
    FROM dbo.UserSessions sess
    JOIN @RenamedBase r ON r.userId=sess.userId
    WHERE sess.revokedAt IS NULL;

    -- The six baseline accounts now have base_* usernames. New demo logins
    -- admin01/student01/lecturer01 can be inserted without UNIQUE collisions.

    -- Stop if any reserved demo user ID belongs to another identity.
    -- Permit migrating already committed old demo_ usernames to the new convention.
    IF EXISTS (
        SELECT 1 FROM @SeedUsers src
        JOIN dbo.Users u ON u.userId = src.userId
        WHERE u.citizenId <> src.citizenId
           OR u.username NOT IN (src.username, CONCAT('demo_', src.username))
    ) THROW 52004, 'Demo user ID is already owned by another identity.', 1;

    -- Stop if an unrelated account already uses a requested new login.
    IF EXISTS (
        SELECT 1 FROM @SeedUsers src
        JOIN dbo.Users u ON u.username = src.username
        WHERE u.userId <> src.userId
    ) THROW 52009, 'Requested demo username already belongs to another user.', 1;

    -- Migrate old demo_ names ONLY. Do not reset passwords for accounts
    -- that were already migrated (they may have changed passwords later).
    DECLARE @RenamedDemoUsers TABLE (userId VARCHAR(12) PRIMARY KEY);
    UPDATE u
       SET username = src.username,
           passwordHash = src.passwordHash
       OUTPUT inserted.userId INTO @RenamedDemoUsers(userId)
    FROM dbo.Users u
    INNER JOIN @SeedUsers src ON src.userId = u.userId
    WHERE u.username = CONCAT('demo_', src.username)
      AND u.citizenId = src.citizenId;

    -- Invalidate pre-existing sessions for renamed accounts.
    UPDATE sess
       SET revokedAt = SYSUTCDATETIME()
    FROM dbo.UserSessions sess
    JOIN @RenamedDemoUsers ren ON ren.userId = sess.userId
    WHERE sess.revokedAt IS NULL;

    INSERT INTO dbo.Users
        (userId,username,passwordHash,isLocked,citizenId,fullName,dateOfBirth,email,phoneNumber,gender)
    SELECT src.userId,src.username,src.passwordHash,src.isLocked,src.citizenId,
           src.fullName,src.dateOfBirth,src.email,src.phoneNumber,src.gender
    FROM @SeedUsers src
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Users u WHERE u.userId=src.userId);
    -- B. FACULTIES / MAJORS
    INSERT INTO dbo.Faculties(facultyId,facultyCode,facultyName,email,phoneNumber)
    SELECT v.facultyId,v.facultyCode,v.facultyName,v.email,v.phoneNumber
    FROM (VALUES
        ('FAC0000901', 'MATH', N'Applied Mathematics', 'mathematics@g05-demo.invalid', '0280000901'),
        ('FAC0000902', 'LANG', N'Foreign Languages', 'languages@g05-demo.invalid', '0280000902')
    ) v(facultyId,facultyCode,facultyName,email,phoneNumber)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Faculties f WHERE f.facultyId=v.facultyId);

    INSERT INTO dbo.Majors(majorId,facultyId,majorName,majorCode)
    SELECT v.majorId,v.facultyId,v.majorName,v.majorCode
    FROM (VALUES
        ('MJR0000901', 'FAC0000901', N'Data Science', 'DS'),
        ('MJR0000902', 'FAC0000902', N'English Studies', 'ENG')
    ) v(majorId,facultyId,majorName,majorCode)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Majors m WHERE m.majorId=v.majorId);
    -- C. ALL THREE ROLES, each account mapped to exactly one role.
    INSERT INTO dbo.Administrators(adminId,userId)
    SELECT v.adminId,v.userId
    FROM (VALUES
        ('ADM0000901', 'USR000009001'),
        ('ADM0000902', 'USR000009002')
    ) v(adminId,userId)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Administrators x WHERE x.adminId=v.adminId);

    DECLARE @SeedStudents TABLE (
        studentId VARCHAR(10) PRIMARY KEY,
        userId VARCHAR(12), majorId VARCHAR(10),
        facultyId VARCHAR(10), academicStatus NVARCHAR(30)
    );
    INSERT INTO @SeedStudents VALUES
        ('STU0000901', 'USR000009003', 'MJR0000001', 'FAC0000001', N'Active'),
        ('STU0000902', 'USR000009004', 'MJR0000001', 'FAC0000001', N'Active'),
        ('STU0000903', 'USR000009005', 'MJR0000001', 'FAC0000001', N'Active'),
        ('STU0000904', 'USR000009006', 'MJR0000001', 'FAC0000001', N'Active'),
        ('STU0000905', 'USR000009007', 'MJR0000001', 'FAC0000001', N'On Leave'),
        ('STU0000906', 'USR000009008', 'MJR0000001', 'FAC0000001', N'Active'),
        ('STU0000907', 'USR000009009', 'MJR0000002', 'FAC0000002', N'Active'),
        ('STU0000908', 'USR000009010', 'MJR0000002', 'FAC0000002', N'Active'),
        ('STU0000909', 'USR000009011', 'MJR0000002', 'FAC0000002', N'Active'),
        ('STU0000910', 'USR000009012', 'MJR0000002', 'FAC0000002', N'Suspended'),
        ('STU0000911', 'USR000009013', 'MJR0000901', 'FAC0000901', N'Active'),
        ('STU0000912', 'USR000009014', 'MJR0000901', 'FAC0000901', N'Active'),
        ('STU0000913', 'USR000009015', 'MJR0000901', 'FAC0000901', N'Active'),
        ('STU0000914', 'USR000009016', 'MJR0000902', 'FAC0000902', N'Active'),
        ('STU0000915', 'USR000009017', 'MJR0000902', 'FAC0000902', N'Active'),
        ('STU0000916', 'USR000009018', 'MJR0000902', 'FAC0000902', N'Graduated');
    INSERT INTO dbo.Students(studentId,userId,majorId,academicStatus)
    SELECT v.studentId,v.userId,v.majorId,v.academicStatus
    FROM @SeedStudents v
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Students x WHERE x.studentId=v.studentId);

    DECLARE @SeedLecturers TABLE (
        lecturerId VARCHAR(10) PRIMARY KEY,
        userId VARCHAR(12), facultyId VARCHAR(10)
    );
    INSERT INTO @SeedLecturers VALUES
        ('LEC0000901', 'USR000009019', 'FAC0000001'),
        ('LEC0000902', 'USR000009020', 'FAC0000001'),
        ('LEC0000903', 'USR000009021', 'FAC0000001'),
        ('LEC0000904', 'USR000009022', 'FAC0000002'),
        ('LEC0000905', 'USR000009023', 'FAC0000002'),
        ('LEC0000906', 'USR000009024', 'FAC0000002'),
        ('LEC0000907', 'USR000009025', 'FAC0000901'),
        ('LEC0000908', 'USR000009026', 'FAC0000902');
    INSERT INTO dbo.Lecturers(lecturerId,userId,facultyId)
    SELECT v.lecturerId,v.userId,v.facultyId
    FROM @SeedLecturers v
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Lecturers x WHERE x.lecturerId=v.lecturerId);
    -- D. THREE ADDITIONAL SEMESTERS (plus use original two).
    INSERT INTO dbo.Semesters(semesterId,semesterName,endDate,startDate,academicYear)
    SELECT v.semesterId,v.semesterName,v.endDate,v.startDate,v.academicYear
    FROM (VALUES
        ('SEM0000900', N'2024-2025 Semester 2', '2025-06-20', '2025-02-03', '2024-2025'),
        ('SEM0000901', N'2026-2027 Semester 1', '2027-01-20', '2026-09-01', '2026-2027'),
        ('SEM0000902', N'2026-2027 Semester 2', '2027-06-20', '2027-02-01', '2026-2027')
    ) v(semesterId,semesterName,endDate,startDate,academicYear)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Semesters s WHERE s.semesterId=v.semesterId);
    -- E. THIRTEEN NEW COURSES WITH DIFFERENT WEIGHT PROFILES.
    INSERT INTO dbo.Courses
      (courseId,facultyId,courseCode,courseName,credits,
       midtermWeight,assignmentWeight,attendanceWeight,finalExamWeight)
    SELECT v.courseId,v.facultyId,v.courseCode,v.courseName,v.credits,
           v.midtermWeight,v.assignmentWeight,v.attendanceWeight,v.finalExamWeight
    FROM (VALUES
        ('CRS0000901', 'FAC0000001', 'WEB201', N'Web Application Development', 3, 20, 20, 10, 50),
        ('CRS0000902', 'FAC0000001', 'NET202', N'Computer Networks', 3, 15, 25, 10, 50),
        ('CRS0000903', 'FAC0000001', 'DBA203', N'Database Administration', 3, 30, 10, 10, 50),
        ('CRS0000904', 'FAC0000001', 'SEC204', N'Information Security', 3, 20, 20, 10, 50),
        ('CRS0000905', 'FAC0000002', 'MKT201', N'Principles of Marketing', 3, 20, 20, 10, 50),
        ('CRS0000906', 'FAC0000002', 'FIN202', N'Corporate Finance', 3, 25, 15, 10, 50),
        ('CRS0000907', 'FAC0000002', 'ACC203', N'Financial Accounting', 3, 20, 20, 10, 50),
        ('CRS0000908', 'FAC0000901', 'MAT201', N'Linear Algebra', 3, 15, 25, 10, 50),
        ('CRS0000909', 'FAC0000901', 'STA202', N'Probability and Statistics', 3, 20, 20, 10, 50),
        ('CRS0000910', 'FAC0000902', 'ENG201', N'Academic English', 2, 20, 20, 10, 50),
        ('CRS0000911', 'FAC0000902', 'ENG202', N'Business English', 2, 20, 20, 10, 50),
        ('CRS0000912', 'FAC0000001', 'CAP205', N'IT Capstone Project', 4, 20, 20, 10, 50),
        ('CRS0000913', 'FAC0000002', 'BUS301', N'Strategic Management', 3, 20, 20, 10, 50)
    ) v(courseId,facultyId,courseCode,courseName,credits,
        midtermWeight,assignmentWeight,attendanceWeight,finalExamWeight)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Courses c WHERE c.courseId=v.courseId);
    -- F. CURRICULUM / CURRICULUM COURSES / PREREQUISITES.
    INSERT INTO dbo.Curriculum(curriculumId,majorId,curriculumName,academicYear)
    SELECT v.curriculumId,v.majorId,v.curriculumName,v.academicYear
    FROM (VALUES
        ('CUR0000901', 'MJR0000901', N'Data Science - Academic Plan 2025', '2025-2026'),
        ('CUR0000902', 'MJR0000902', N'English Studies - Academic Plan 2025', '2025-2026')
    ) v(curriculumId,majorId,curriculumName,academicYear)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Curriculum c WHERE c.curriculumId=v.curriculumId);

    INSERT INTO dbo.CurriculumCourses(curriculumId,courseId,courseType)
    SELECT v.curriculumId,v.courseId,v.courseType
    FROM (VALUES
        ('CUR0000001', 'CRS0000901', 'Required'),
        ('CUR0000001', 'CRS0000902', 'Required'),
        ('CUR0000001', 'CRS0000903', 'Required'),
        ('CUR0000001', 'CRS0000904', 'Required'),
        ('CUR0000001', 'CRS0000908', 'Elective'),
        ('CUR0000001', 'CRS0000912', 'Elective'),
        ('CUR0000002', 'CRS0000905', 'Required'),
        ('CUR0000002', 'CRS0000906', 'Required'),
        ('CUR0000002', 'CRS0000907', 'Required'),
        ('CUR0000002', 'CRS0000910', 'Elective'),
        ('CUR0000002', 'CRS0000913', 'Elective'),
        ('CUR0000901', 'CRS0000908', 'Required'),
        ('CUR0000901', 'CRS0000909', 'Required'),
        ('CUR0000901', 'CRS0000901', 'Elective'),
        ('CUR0000902', 'CRS0000910', 'Required'),
        ('CUR0000902', 'CRS0000911', 'Required'),
        ('CUR0000902', 'CRS0000905', 'Elective')
    ) v(curriculumId,courseId,courseType)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.CurriculumCourses x
        WHERE x.curriculumId=v.curriculumId AND x.courseId=v.courseId);

    -- Prerequisites are on ADVANCED courses with no seeded enrollments.
    INSERT INTO dbo.CoursePrerequisites(courseId,prerequisiteId)
    SELECT v.courseId,v.prerequisiteId
    FROM (VALUES
        ('CRS0000912', 'CRS0000903'),
        ('CRS0000912', 'CRS0000902'),
        ('CRS0000913', 'CRS0000905'),
        ('CRS0000913', 'CRS0000906')
    ) v(courseId,prerequisiteId)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.CoursePrerequisites x
        WHERE x.courseId=v.courseId AND x.prerequisiteId=v.prerequisiteId);
    -- G. CLASS SECTIONS: past, current, future, assigned & unassigned.
    -- The new NULL lecturer sections provide safe scheduling-conflict scenarios.
    DECLARE @SeedSections TABLE (
       classSectionId VARCHAR(10) PRIMARY KEY,
       courseId VARCHAR(10), semesterId VARCHAR(10),
       classCode VARCHAR(20), lecturerId VARCHAR(10) NULL,
       maxCapacity INT, currentEnrollment INT,
       room VARCHAR(30), dayOfWeek TINYINT,
       startTime TIME, endTime TIME, facultyId VARCHAR(10)
    );
    INSERT INTO @SeedSections VALUES
        ('CLS0000901', 'CRS0000901', 'SEM0000900', 'WEB201.00', 'LEC0000901', 36, 0, 'D.A101', 2, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000902', 'CRS0000905', 'SEM0000900', 'MKT201.00', 'LEC0000904', 36, 0, 'D.B201', 3, '07:00', '09:30', 'FAC0000002'),
        ('CLS0000903', 'CRS0000908', 'SEM0000900', 'MAT201.00', 'LEC0000907', 32, 0, 'D.C301', 4, '07:00', '09:30', 'FAC0000901'),
        ('CLS0000904', 'CRS0000910', 'SEM0000900', 'ENG201.00', 'LEC0000908', 32, 0, 'D.D401', 5, '07:00', '09:30', 'FAC0000902'),
        ('CLS0000905', 'CRS0000901', 'SEM0000001', 'WEB201.01', 'LEC0000901', 36, 0, 'D.A101', 2, '09:45', '12:15', 'FAC0000001'),
        ('CLS0000906', 'CRS0000902', 'SEM0000001', 'NET202.01', 'LEC0000902', 36, 0, 'D.A102', 3, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000907', 'CRS0000905', 'SEM0000001', 'MKT201.01', 'LEC0000904', 36, 0, 'D.B201', 2, '13:00', '15:30', 'FAC0000002'),
        ('CLS0000908', 'CRS0000906', 'SEM0000001', 'FIN202.01', 'LEC0000905', 36, 0, 'D.B202', 4, '09:45', '12:15', 'FAC0000002'),
        ('CLS0000909', 'CRS0000908', 'SEM0000001', 'MAT201.01', 'LEC0000907', 32, 0, 'D.C301', 5, '07:00', '09:30', 'FAC0000901'),
        ('CLS0000910', 'CRS0000910', 'SEM0000001', 'ENG201.01', 'LEC0000908', 32, 0, 'D.D401', 6, '07:00', '09:30', 'FAC0000902'),
        ('CLS0000911', 'CRS0000901', 'SEM0000002', 'WEB201.02', 'LEC0000901', 36, 0, 'D.A101', 2, '09:45', '12:15', 'FAC0000001'),
        ('CLS0000912', 'CRS0000904', 'SEM0000002', 'SEC204.01', 'LEC0000903', 36, 0, 'D.A103', 4, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000913', 'CRS0000905', 'SEM0000002', 'MKT201.02', 'LEC0000904', 36, 0, 'D.B201', 3, '13:00', '15:30', 'FAC0000002'),
        ('CLS0000914', 'CRS0000907', 'SEM0000002', 'ACC203.01', 'LEC0000906', 36, 0, 'D.B203', 5, '07:00', '09:30', 'FAC0000002'),
        ('CLS0000915', 'CRS0000909', 'SEM0000002', 'STA202.01', 'LEC0000907', 32, 0, 'D.C301', 3, '07:00', '09:30', 'FAC0000901'),
        ('CLS0000916', 'CRS0000911', 'SEM0000002', 'ENG202.01', 'LEC0000908', 32, 0, 'D.D401', 4, '07:00', '09:30', 'FAC0000902'),
        ('CLS0000917', 'CRS0000903', 'SEM0000901', 'DBA203.01', 'LEC0000901', 36, 0, 'D.A101', 2, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000918', 'CRS0000901', 'SEM0000901', 'WEB201.03', 'LEC0000902', 36, 0, 'D.A102', 3, '09:45', '12:15', 'FAC0000001'),
        ('CLS0000919', 'CRS0000904', 'SEM0000901', 'SEC204.02', 'LEC0000903', 36, 0, 'D.A103', 4, '09:45', '12:15', 'FAC0000001'),
        ('CLS0000920', 'CRS0000902', 'SEM0000901', 'NET202.02', NULL, 36, 0, 'D.A104', 2, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000921', 'CRS0000905', 'SEM0000901', 'MKT201.03', 'LEC0000904', 36, 0, 'D.B201', 2, '07:00', '09:30', 'FAC0000002'),
        ('CLS0000922', 'CRS0000906', 'SEM0000901', 'FIN202.02', 'LEC0000905', 36, 0, 'D.B202', 3, '09:45', '12:15', 'FAC0000002'),
        ('CLS0000923', 'CRS0000907', 'SEM0000901', 'ACC203.02', 'LEC0000906', 36, 0, 'D.B203', 5, '13:00', '15:30', 'FAC0000002'),
        ('CLS0000924', 'CRS0000906', 'SEM0000901', 'FIN202.03', NULL, 36, 0, 'D.B204', 3, '10:30', '12:15', 'FAC0000002'),
        ('CLS0000925', 'CRS0000908', 'SEM0000901', 'MAT201.02', 'LEC0000907', 32, 0, 'D.C301', 4, '09:45', '12:15', 'FAC0000901'),
        ('CLS0000926', 'CRS0000909', 'SEM0000901', 'STA202.02', NULL, 32, 0, 'D.C302', 4, '09:45', '12:15', 'FAC0000901'),
        ('CLS0000927', 'CRS0000910', 'SEM0000901', 'ENG201.02', 'LEC0000908', 32, 0, 'D.D401', 5, '09:45', '12:15', 'FAC0000902'),
        ('CLS0000928', 'CRS0000911', 'SEM0000901', 'ENG202.02', NULL, 32, 0, 'D.D402', 5, '09:45', '12:15', 'FAC0000902'),
        ('CLS0000929', 'CRS0000902', 'SEM0000902', 'NET202.03', 'LEC0000902', 36, 0, 'D.A102', 3, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000930', 'CRS0000903', 'SEM0000902', 'DBA203.02', NULL, 36, 0, 'D.A101', 2, '07:00', '09:30', 'FAC0000001'),
        ('CLS0000931', 'CRS0000905', 'SEM0000902', 'MKT201.04', 'LEC0000905', 36, 0, 'D.B201', 4, '09:45', '12:15', 'FAC0000002'),
        ('CLS0000932', 'CRS0000906', 'SEM0000902', 'FIN202.04', NULL, 36, 0, 'D.B202', 4, '09:45', '12:15', 'FAC0000002'),
        ('CLS0000933', 'CRS0000908', 'SEM0000902', 'MAT201.03', 'LEC0000907', 32, 0, 'D.C301', 2, '07:00', '09:30', 'FAC0000901'),
        ('CLS0000934', 'CRS0000910', 'SEM0000902', 'ENG201.03', 'LEC0000908', 32, 0, 'D.D401', 3, '07:00', '09:30', 'FAC0000902');

    IF EXISTS (
        SELECT 1 FROM @SeedSections src
        JOIN dbo.ClassSections cs ON cs.classSectionId=src.classSectionId
        WHERE cs.classCode<>src.classCode OR cs.courseId<>src.courseId
           OR cs.semesterId<>src.semesterId
    ) THROW 52005, 'Demo section ID already represents another section.', 1;

    INSERT INTO dbo.ClassSections
      (classSectionId,lecturerId,courseId,semesterId,classCode,maxCapacity,
       currentEnrollment,room,dayOfWeek,startTime,endTime)
    SELECT src.classSectionId,src.lecturerId,src.courseId,src.semesterId,
           src.classCode,src.maxCapacity,0,src.room,src.dayOfWeek,src.startTime,src.endTime
    FROM @SeedSections src
    WHERE NOT EXISTS (SELECT 1 FROM dbo.ClassSections cs
        WHERE cs.classSectionId=src.classSectionId);
    -- H. ENROLLMENTS: generate STABLE synthetic IDs from a fixed plan.
    -- Students are enrolled only in sections of their MAJOR'S FACULTY,
    -- and only in courses included in that major's curriculum.
    -- Inactive students have historical enrollments but no new classes.
    -- Unassigned sections remain empty and ready for Assign Lecturer tests.
    CREATE TABLE #DemoEnrollmentPlan (
        enrollmentId VARCHAR(10) NOT NULL PRIMARY KEY,
        gradebookId VARCHAR(10) NOT NULL UNIQUE,
        studentId VARCHAR(10) NOT NULL,
        classSectionId VARCHAR(10) NOT NULL,
        enrollmentDate DATE NOT NULL,
        semesterStart DATE NOT NULL
    );

    ;WITH Eligible AS (
        SELECT st.studentId, sec.classSectionId, sem.startDate,
               ROW_NUMBER() OVER (ORDER BY st.studentId, sec.classSectionId) AS rn
        FROM @SeedStudents AS st
        JOIN @SeedSections AS sec ON sec.facultyId=st.facultyId
        JOIN dbo.Semesters AS sem ON sem.semesterId=sec.semesterId
        WHERE sec.lecturerId IS NOT NULL
          AND (st.academicStatus=N'Active' OR sem.startDate<'2026-08-01')
          AND EXISTS (
              SELECT 1 FROM dbo.Curriculum cu
              JOIN dbo.CurriculumCourses cc ON cc.curriculumId=cu.curriculumId
              WHERE cu.majorId=st.majorId AND cc.courseId=sec.courseId
          )
    )
    INSERT INTO #DemoEnrollmentPlan
      (enrollmentId,gradebookId,studentId,classSectionId,enrollmentDate,semesterStart)
    SELECT 'ENR'+RIGHT('0000000'+CONVERT(VARCHAR(7),900+rn),7),
           'GRB'+RIGHT('0000000'+CONVERT(VARCHAR(7),900+rn),7),
           studentId,classSectionId,DATEADD(DAY,-14,startDate),startDate
    FROM Eligible;

    IF EXISTS (
        SELECT 1 FROM #DemoEnrollmentPlan p
        JOIN dbo.Enrollments en ON en.enrollmentId=p.enrollmentId
        WHERE en.studentId<>p.studentId OR en.classSectionId<>p.classSectionId
    ) THROW 52006, 'Demo enrollment ID already belongs to another student/section.', 1;

    INSERT INTO dbo.Enrollments(enrollmentId,studentId,classSectionId,enrollmentDate)
    SELECT p.enrollmentId,p.studentId,p.classSectionId,p.enrollmentDate
    FROM #DemoEnrollmentPlan p
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Enrollments e WHERE e.enrollmentId=p.enrollmentId);

    -- Capacity counts must match the actual enrollment records, including
    -- registrations made later through the UI. Never update original sections.
    UPDATE cs SET currentEnrollment=actual.cnt
    FROM dbo.ClassSections cs
    JOIN @SeedSections src ON src.classSectionId=cs.classSectionId
    CROSS APPLY (
        SELECT COUNT(*) AS cnt FROM dbo.Enrollments en
        WHERE en.classSectionId=cs.classSectionId
    ) actual
    WHERE cs.currentEnrollment<>actual.cnt;
    -- I. GRADEBOOKS: completed historical vs. draft current/future.
    -- Deterministic marks produce A/B/C/D/F bands; finalScore is calculated
    -- from each course's exact percentage weights, then mapped via GradeScales.
    -- The special original GRB0000006 is intentionally NOT referenced.
    IF EXISTS (
       SELECT 1 FROM #DemoEnrollmentPlan p
       JOIN dbo.GradeBooks gb ON gb.gradebookId=p.gradebookId
       WHERE gb.enrollmentId<>p.enrollmentId
    ) THROW 52007, 'Demo gradebook ID already belongs to another enrollment.', 1;

    INSERT INTO dbo.GradeBooks
      (gradebookId,enrollmentId,midtermMark,assignmentMark,attendanceMark,
       finalExamMark,finalScore,letterGrade,isFinalized)
    SELECT p.gradebookId,p.enrollmentId,
       CASE WHEN p.semesterStart<'2026-08-01' OR
                 (p.semesterStart<'2027-01-01' AND nr.n%2=0)
            THEN marks.midterm ELSE NULL END AS midtermMark,
       CASE WHEN p.semesterStart<'2026-08-01' THEN marks.assignment ELSE NULL END,
       CASE WHEN p.semesterStart<'2026-08-01' THEN marks.attendance ELSE NULL END,
       CASE WHEN p.semesterStart<'2026-08-01' THEN marks.finalexam ELSE NULL END,
       CASE WHEN p.semesterStart<'2026-08-01' THEN finalcalc.finalScore ELSE NULL END,
       CASE WHEN p.semesterStart<'2026-08-01' THEN gs.letterGrade ELSE NULL END,
       CASE WHEN p.semesterStart<'2026-08-01' THEN 1 ELSE 0 END
    FROM #DemoEnrollmentPlan p
    JOIN dbo.ClassSections cs ON cs.classSectionId=p.classSectionId
    JOIN dbo.Courses cr ON cr.courseId=cs.courseId
    CROSS APPLY (
      SELECT n=(CONVERT(INT,RIGHT(p.studentId,2))*7
               +CONVERT(INT,RIGHT(p.classSectionId,2))*3)%10
    ) AS nr
    CROSS APPLY (
      SELECT base=CONVERT(DECIMAL(4,2),CASE nr.n
          WHEN 0 THEN 0.50 WHEN 1 THEN 2.20 WHEN 2 THEN 3.70
          WHEN 3 THEN 4.80 WHEN 4 THEN 5.30 WHEN 5 THEN 6.20
          WHEN 6 THEN 7.40 WHEN 7 THEN 8.10 WHEN 8 THEN 9.20
          ELSE 9.80 END)
    ) AS b
    CROSS APPLY (
      SELECT midterm=b.base,
          assignment=CONVERT(DECIMAL(4,2),CASE WHEN b.base>9.50
                                   THEN 9.50 ELSE b.base+0.50 END),
          attendance=CONVERT(DECIMAL(4,2),9.00),
          finalexam=CONVERT(DECIMAL(4,2),CASE WHEN b.base<4.00
                                   THEN b.base+0.75 ELSE b.base-0.25 END)
    ) AS marks
    CROSS APPLY (
      SELECT finalScore=CAST(ROUND(
          (marks.midterm*cr.midtermWeight
           +marks.assignment*cr.assignmentWeight
           +marks.attendance*cr.attendanceWeight
           +marks.finalexam*cr.finalExamWeight)/100.00,2
          ) AS DECIMAL(4,2))
    ) AS finalcalc
    LEFT JOIN dbo.GradeScales gs
      ON finalcalc.finalScore BETWEEN gs.minScore AND gs.maxScore
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.GradeBooks gb WHERE gb.gradebookId=p.gradebookId
    );

    IF EXISTS (
      SELECT 1 FROM #DemoEnrollmentPlan p
      LEFT JOIN dbo.GradeBooks gb ON gb.gradebookId=p.gradebookId
      WHERE gb.gradebookId IS NULL OR gb.enrollmentId<>p.enrollmentId
    ) THROW 52008, 'Some demo enrollments have no matching gradebook.', 1;

    -- J. SEMESTER RESULTS: compute GPA via EXISTING official stored proc.
    -- Calling this on NEW seeded students only leaves original STU000000x alone.
    DECLARE @StudentForGPA VARCHAR(10);
    DECLARE DemoGpaCursor CURSOR LOCAL FAST_FORWARD FOR
        SELECT studentId FROM @SeedStudents ORDER BY studentId;
    OPEN DemoGpaCursor;
    FETCH NEXT FROM DemoGpaCursor INTO @StudentForGPA;
    WHILE @@FETCH_STATUS=0
    BEGIN
        EXEC dbo.usp_RecalculateStudentGPA
            @StudentId=@StudentForGPA, @ReturnRows=0;
        FETCH NEXT FROM DemoGpaCursor INTO @StudentForGPA;
    END;
    CLOSE DemoGpaCursor;
    DEALLOCATE DemoGpaCursor;

    -- ================================================================
    -- N. FINAL VALIDATIONS (only new rows; original 6 demo accounts untouched)
    -- ================================================================
    IF EXISTS (
        SELECT 1 FROM dbo.ClassSections AS cs
        LEFT JOIN dbo.Enrollments AS en ON en.classSectionId=cs.classSectionId
        WHERE cs.classSectionId IN (SELECT classSectionId FROM @SeedSections)
        GROUP BY cs.classSectionId, cs.currentEnrollment, cs.maxCapacity
        HAVING cs.currentEnrollment<>COUNT(en.enrollmentId)
            OR COUNT(en.enrollmentId)>cs.maxCapacity
    ) THROW 52050, 'Invalid demo class enrollment counts.', 1;

    IF EXISTS (
        SELECT 1 FROM dbo.GradeBooks AS gb
        JOIN dbo.Enrollments AS en ON en.enrollmentId=gb.enrollmentId
        JOIN dbo.ClassSections AS cs ON cs.classSectionId=en.classSectionId
        JOIN dbo.Courses AS c ON c.courseId=cs.courseId
        WHERE gb.gradebookId IN (SELECT gradebookId FROM #DemoEnrollmentPlan)
            AND gb.isFinalized=1
            AND (gb.finalScore<>CAST(ROUND(
                (gb.midtermMark*c.midtermWeight + gb.assignmentMark*c.assignmentWeight
                 + gb.attendanceMark*c.attendanceWeight + gb.finalExamMark*c.finalExamWeight)/100.00,2
                ) AS DECIMAL(4,2))
                OR NOT EXISTS (
                    SELECT 1 FROM dbo.GradeScales gs
                    WHERE gs.letterGrade=gb.letterGrade
                      AND gb.finalScore BETWEEN gs.minScore AND gs.maxScore
                ))
    ) THROW 52051, 'A finalized demo grade is inconsistent.', 1;

    IF EXISTS (
        SELECT 1 FROM dbo.ClassSections a
        JOIN dbo.ClassSections b
          ON b.semesterId=a.semesterId
         AND b.lecturerId=a.lecturerId
         AND b.dayOfWeek=a.dayOfWeek
         AND b.classSectionId<>a.classSectionId
         AND b.startTime<a.endTime
         AND b.endTime>a.startTime
        WHERE a.classSectionId IN (SELECT classSectionId FROM @SeedSections)
          AND a.lecturerId IS NOT NULL
    ) THROW 52052, 'Demo lecturer teaching schedules conflict.', 1;

    IF EXISTS (
        SELECT 1 FROM dbo.Users AS u
        WHERE u.userId IN (SELECT userId FROM @SeedUsers)
          AND (SELECT COUNT(*) FROM dbo.Administrators a WHERE a.userId=u.userId)
            +(SELECT COUNT(*) FROM dbo.Students s WHERE s.userId=u.userId)
            +(SELECT COUNT(*) FROM dbo.Lecturers l WHERE l.userId=u.userId)<>1
    ) THROW 52053, 'Invalid demo user role assignment.', 1;

    PRINT '=================== DEMO ROW COUNTS ===================';
    SELECT 'Users' AS TableName, COUNT(*) AS DemoRows FROM dbo.Users
        WHERE userId IN (SELECT userId FROM @SeedUsers)
    UNION ALL SELECT 'Administrators', COUNT(*) FROM dbo.Administrators
        WHERE adminId IN ('ADM0000901','ADM0000902')
    UNION ALL SELECT 'Students', COUNT(*) FROM dbo.Students
        WHERE studentId IN (SELECT studentId FROM @SeedStudents)
    UNION ALL SELECT 'Lecturers', COUNT(*) FROM dbo.Lecturers
        WHERE lecturerId IN (SELECT lecturerId FROM @SeedLecturers)
    UNION ALL SELECT 'ClassSections', COUNT(*) FROM dbo.ClassSections
        WHERE classSectionId IN (SELECT classSectionId FROM @SeedSections)
    UNION ALL SELECT 'Enrollments', COUNT(*) FROM dbo.Enrollments
        WHERE enrollmentId IN (SELECT enrollmentId FROM #DemoEnrollmentPlan)
    UNION ALL SELECT 'GradeBooks', COUNT(*) FROM dbo.GradeBooks
        WHERE gradebookId IN (SELECT gradebookId FROM #DemoEnrollmentPlan)
    UNION ALL SELECT 'SemesterResults', COUNT(*) FROM dbo.SemesterResults
        WHERE studentId IN (SELECT studentId FROM @SeedStudents);

    SELECT cs.classCode, cs.semesterId, cs.lecturerId,
           cs.dayOfWeek, cs.startTime, cs.endTime
    FROM dbo.ClassSections cs
    WHERE cs.classSectionId IN (SELECT classSectionId FROM @SeedSections)
      AND cs.lecturerId IS NULL
    ORDER BY cs.semesterId, cs.classCode;

    -- The temporary planning table is no longer needed after verification.
    -- Drop it before committing so re-execution in this same SSMS tab succeeds.
    IF OBJECT_ID(N'tempdb..#DemoEnrollmentPlan', N'U') IS NOT NULL
        DROP TABLE #DemoEnrollmentPlan;

    IF @ApplySeed=1
    BEGIN
        COMMIT TRANSACTION;
        PRINT 'SUCCESS: OFFICIAL GROUP 05 DEMO DATA COMMITTED.';
    END
    ELSE
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT 'DRY RUN PASSED: all new data rolled back. Set @ApplySeed=1 to save.';
    END;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO


/* ============================================================================
   SECTION J. READ-ONLY POST-RUN VERIFICATION
   ============================================================================
   Queries display the committed data when @ApplySeed=1 (default).
   They are read-only; they do not alter any database records.
   Nothing below inserts, updates or deletes rows.
============================================================================ */

/*
STUDENT MANAGEMENT SYSTEM - GROUP 05
VERIFY ADDITIVE FULL-DEMO SEED (READ-ONLY)
Runs automatically after SECTION I in this single official SQL file.
Does not INSERT, UPDATE, DELETE or alter the schema.
*/
USE StudentManagementSystem;
GO
SET NOCOUNT ON;

-- 1. Physical table counts (15 domain + 2 support).
SELECT 'Users' AS TableName, COUNT_BIG(*) AS Records FROM dbo.Users
UNION ALL SELECT 'Faculties', COUNT_BIG(*) FROM dbo.Faculties
UNION ALL SELECT 'Majors', COUNT_BIG(*) FROM dbo.Majors
UNION ALL SELECT 'Administrators', COUNT_BIG(*) FROM dbo.Administrators
UNION ALL SELECT 'Students', COUNT_BIG(*) FROM dbo.Students
UNION ALL SELECT 'Lecturers', COUNT_BIG(*) FROM dbo.Lecturers
UNION ALL SELECT 'Semesters', COUNT_BIG(*) FROM dbo.Semesters
UNION ALL SELECT 'Courses', COUNT_BIG(*) FROM dbo.Courses
UNION ALL SELECT 'Curriculum', COUNT_BIG(*) FROM dbo.Curriculum
UNION ALL SELECT 'CurriculumCourses', COUNT_BIG(*) FROM dbo.CurriculumCourses
UNION ALL SELECT 'CoursePrerequisites', COUNT_BIG(*) FROM dbo.CoursePrerequisites
UNION ALL SELECT 'ClassSections', COUNT_BIG(*) FROM dbo.ClassSections
UNION ALL SELECT 'Enrollments', COUNT_BIG(*) FROM dbo.Enrollments
UNION ALL SELECT 'GradeBooks', COUNT_BIG(*) FROM dbo.GradeBooks
UNION ALL SELECT 'SemesterResults', COUNT_BIG(*) FROM dbo.SemesterResults
UNION ALL SELECT 'UserSessions', COUNT_BIG(*) FROM dbo.UserSessions
UNION ALL SELECT 'GradeScales', COUNT_BIG(*) FROM dbo.GradeScales
ORDER BY TableName;

-- 2. Every new synthetic login, role, and status.
SELECT u.username, u.fullName, u.isLocked,
       CASE WHEN a.userId IS NOT NULL THEN 'Administrator'
            WHEN s.userId IS NOT NULL THEN 'Student'
            WHEN l.userId IS NOT NULL THEN 'Lecturer'
            ELSE 'MISSING ROLE' END AS RoleName,
       s.academicStatus, s.studentId, l.lecturerId
FROM dbo.Users u
LEFT JOIN dbo.Administrators a ON a.userId=u.userId
LEFT JOIN dbo.Students s ON s.userId=u.userId
LEFT JOIN dbo.Lecturers l ON l.userId=u.userId
WHERE u.userId BETWEEN 'USR000009001' AND 'USR000009026'
ORDER BY u.username;

-- 3. Demo sections requiring assignment.
SELECT sem.semesterName, cs.classCode, c.courseName,
       f.facultyName AS courseFaculty, cs.dayOfWeek, cs.startTime,
       cs.endTime, cs.room
FROM dbo.ClassSections cs
JOIN dbo.Courses c ON c.courseId=cs.courseId
JOIN dbo.Faculties f ON f.facultyId=c.facultyId
JOIN dbo.Semesters sem ON sem.semesterId=cs.semesterId
WHERE cs.classSectionId BETWEEN 'CLS0000901' AND 'CLS0000934'
  AND cs.lecturerId IS NULL
ORDER BY sem.startDate, cs.classCode;

-- 4. Finalized vs draft gradebooks from the new test cohort.
SELECT gb.isFinalized, gs.letterGrade,
       COUNT(*) AS Gradebooks
FROM dbo.GradeBooks gb
LEFT JOIN dbo.GradeScales gs ON gs.letterGrade=gb.letterGrade
WHERE gb.gradebookId BETWEEN 'GRB0000901' AND 'GRB0001999'
GROUP BY gb.isFinalized, gs.letterGrade
ORDER BY gb.isFinalized DESC, gs.letterGrade;

-- 5. New students' GPA records.
SELECT sr.studentId, s.semesterName,
       sr.semesterGPA, sr.cumulativeGPA
FROM dbo.SemesterResults sr
JOIN dbo.Semesters s ON s.semesterId=sr.semesterId
WHERE sr.studentId BETWEEN 'STU0000901' AND 'STU0000916'
ORDER BY sr.studentId, s.startDate;

-- 6. Error checks: zero rows is expected for the new sections.
SELECT cs.classCode, cs.currentEnrollment,
       COUNT(e.enrollmentId) AS ActualEnrollments
FROM dbo.ClassSections cs
LEFT JOIN dbo.Enrollments e ON e.classSectionId=cs.classSectionId
WHERE cs.classSectionId BETWEEN 'CLS0000901' AND 'CLS0000934'
GROUP BY cs.classCode, cs.currentEnrollment
HAVING cs.currentEnrollment<>COUNT(e.enrollmentId);

-- 7. Gradebook used by the existing concurrency demonstrations.
-- It must be left untouched by the NEW seed.
SELECT gradebookId,enrollmentId,midtermMark,assignmentMark,
       attendanceMark,finalExamMark,finalScore,letterGrade,isFinalized
FROM dbo.GradeBooks
WHERE gradebookId='GRB0000006';

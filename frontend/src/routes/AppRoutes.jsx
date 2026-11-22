
import {
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";

import { ROUTES } from "../config/routes";

// =========================================
// AUTHENTICATION
// =========================================

import AuthLayout from "../layouts/AuthLayout";
import LoginPage from "../features/auth/pages/LoginPage";
import RecoverPasswordPage from "../features/auth/pages/RecoverPasswordPage";

import {
  AuthProvider,
  useAuth,
} from "../features/auth/context/AuthContext";

import NotFoundPage from "../pages/errors/NotFoundPage";

// =========================================
// ADMINISTRATOR
// =========================================

import AdminLayout from "../features/admin/layouts/AdminLayout";
import AdminDashboardPage from "../features/admin/pages/AdminDashboardPage";
import AdminStudentsPage from "../features/admin/pages/AdminStudentsPage";
import AdminCreateAccountPage from "../features/admin/pages/AdminCreateAccountPage";
import AdminLecturersPage from "../features/admin/pages/AdminLecturersPage";
import AdminAssignLecturerPage from "../features/admin/pages/AdminAssignLecturerPage";
import AdminSemestersPage from "../features/admin/pages/AdminSemestersPage";
import AdminFacultiesPage from "../features/admin/pages/AdminFacultiesPage";
import AdminCoursesPage from "../features/admin/pages/AdminCoursesPage";

// =========================================
// USE CASES 35-39 - CLASS SECTION MANAGEMENT
// =========================================

import AdminClassSectionsPage from "../features/admin/pages/AdminClassSectionsPage";

// =========================================
// STUDENT
// =========================================

import StudentLayout from "../features/student/layouts/StudentLayout";
import StudentDashboardPage from "../features/student/pages/StudentDashboardPage";
import StudentProfilePage from "../features/student/pages/StudentProfilePage";
import StudentCurriculumPage from "../features/student/pages/StudentCurriculumPage";
import StudentTranscriptPage from "../features/student/pages/StudentTranscriptPage";
import StudentChangePasswordPage from "../features/student/pages/StudentChangePasswordPage";

// =========================================
// LECTURER
// =========================================

import LecturerLayout from "../features/lecturer/layouts/LecturerLayout";
import LecturerDashboardPage from "../features/lecturer/pages/LecturerDashboardPage";
import LecturerGradebookPage from "../features/lecturer/pages/LecturerGradebookPage";
import LecturerProfilePage from "../features/lecturer/pages/LecturerProfilePage";
import LecturerChangePasswordPage from "../features/lecturer/pages/LecturerChangePasswordPage";

// =========================================
// ROLE DESTINATIONS
// =========================================

const ROLE_PATHS = {
  Administrator: ROUTES.ADMIN,
  Student: ROUTES.STUDENT,
  Lecturer: ROUTES.LECTURER,
};

function destinationFor(user) {
  return ROLE_PATHS[user?.role] || ROUTES.LOGIN;
}

// =========================================
// LOGIN ROUTE
// =========================================

function LoginRoute() {
  const { user } = useAuth();

  return user ? (
    <Navigate
      to={destinationFor(user)}
      replace
    />
  ) : (
    <LoginPage />
  );
}

// =========================================
// PROTECTED ROLE ROUTE
// =========================================

function ProtectedRoleRoute({ requiredRole }) {
  const { user } = useAuth();

  if (!user) {
    return (
      <Navigate
        to={ROUTES.LOGIN}
        replace
      />
    );
  }

  if (user.role !== requiredRole) {
    return (
      <Navigate
        to={destinationFor(user)}
        replace
      />
    );
  }

  return <Outlet />;
}

// =========================================
// APPLICATION ROUTES
// =========================================

function ApplicationRoutes() {
  const { user, checking } = useAuth();

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center text-[#71849A]">
        Checking your session...
      </div>
    );
  }

  return (
    <Routes>
      {/* HOME */}
      <Route
        path={ROUTES.HOME}
        element={
          <Navigate
            to={destinationFor(user)}
            replace
          />
        }
      />

      {/* AUTHENTICATION */}
      <Route element={<AuthLayout />}>
        <Route
          path={ROUTES.LOGIN}
          element={<LoginRoute />}
        />

        <Route
          path={ROUTES.RECOVER_PASSWORD}
          element={<RecoverPasswordPage />}
        />
      </Route>

      {/* ADMINISTRATOR */}
      <Route
        element={
          <ProtectedRoleRoute
            requiredRole="Administrator"
          />
        }
      >
        <Route
          path={ROUTES.ADMIN}
          element={<AdminLayout />}
        >
          <Route
            index
            element={<AdminDashboardPage />}
          />

          <Route
            path="students"
            element={<AdminStudentsPage />}
          />

          <Route
            path="createaccount"
            element={<AdminCreateAccountPage />}
          />

          <Route
            path="lecturers"
            element={<AdminLecturersPage />}
          />

          <Route
            path="assignlecturer"
            element={<AdminAssignLecturerPage />}
          />

          <Route
            path="semesters"
            element={<AdminSemestersPage />}
          />

          <Route
            path="faculties"
            element={<AdminFacultiesPage />}
          />

          {/* USE CASES 30-34 - COURSE MANAGEMENT */}
          <Route
            path="courses"
            element={<AdminCoursesPage />}
          />

          {/* USE CASES 35-39 - CLASS SECTION MANAGEMENT */}
          <Route
            path="class-sections"
            element={<AdminClassSectionsPage />}
          />
        </Route>
      </Route>

      {/* STUDENT */}
      <Route
        element={
          <ProtectedRoleRoute
            requiredRole="Student"
          />
        }
      >
        <Route
          path={ROUTES.STUDENT}
          element={<StudentLayout />}
        >
          <Route
            index
            element={<StudentDashboardPage />}
          />

          <Route
            path="profile"
            element={<StudentProfilePage />}
          />

          <Route
            path="curriculum"
            element={<StudentCurriculumPage />}
          />

          <Route
            path="transcript"
            element={<StudentTranscriptPage />}
          />

          <Route
            path="change-password"
            element={<StudentChangePasswordPage />}
          />
        </Route>
      </Route>

      {/* LECTURER */}
      <Route
        element={
          <ProtectedRoleRoute
            requiredRole="Lecturer"
          />
        }
      >
        <Route
          path={ROUTES.LECTURER}
          element={<LecturerLayout />}
        >
          <Route
            index
            element={<LecturerDashboardPage />}
          />

          <Route
            path="profile"
            element={<LecturerProfilePage />}
          />

          <Route
            path="gradebook"
            element={<LecturerGradebookPage />}
          />

          <Route
            path="change-password"
            element={<LecturerChangePasswordPage />}
          />
        </Route>
      </Route>

      {/* NOT FOUND */}
      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}

// =========================================
// ROOT APP ROUTES
// =========================================

export default function AppRoutes() {
  return (
    <AuthProvider>
      <ApplicationRoutes />
    </AuthProvider>
  );
}

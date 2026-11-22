
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  ArrowRight,
  BookOpen,
  FileText,
  GraduationCap,
  UserRound,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";

import {
  fetchStudentCurriculum,
  fetchStudentTranscript,
} from "../api/studentApi";

// =============================================
// ACADEMIC MODULES
// =============================================

const MODULES = [
  {
    title: "Profile",
    description: "Personal information",
    to: "/student/profile",
    Icon: UserRound,
    color: "bg-[#E5F0FC] text-[#476FA9]",
  },
  {
    title: "Curriculum",
    description: "Courses and credits",
    to: "/student/curriculum",
    Icon: BookOpen,
    color: "bg-[#E5F5EF] text-[#397C6B]",
  },
  {
    title: "Transcript",
    description: "Grades and GPA",
    to: "/student/transcript",
    Icon: FileText,
    color: "bg-[#ECE7FA] text-[#75649C]",
  },
];

// =============================================
// HELPERS
// =============================================

function completedCredits(courses) {
  const counted = new Set();

  return courses.reduce((total, course) => {
    if (
      course.status !== "Completed" ||
      counted.has(course.courseId)
    ) {
      return total;
    }

    counted.add(course.courseId);

    const credits = Number(course.credits);

    return total + (
      Number.isFinite(credits) && credits > 0
        ? credits
        : 0
    );
  }, 0);
}

function formatGPA(value) {
  if (value === null || value === undefined) {
    return "—";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toFixed(2)
    : "—";
}

// =============================================
// COMPACT SUMMARY CARD
// =============================================

function SummaryCard({
  title,
  value,
  note,
  Icon,
  color,
}) {
  return (
    <div className="rounded-2xl border border-[#DCE9F7] bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-[#365D91]">
            {title}
          </h3>

          <p className="mt-1 text-[11px] text-[#8295AA]">
            {note}
          </p>
        </div>

        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${color}`}
        >
          <Icon size={20} aria-hidden="true" />
        </div>
      </div>

      <p
        aria-live="polite"
        className="mt-3 text-3xl font-bold leading-none text-[#365D91]"
      >
        {value}
      </p>
    </div>
  );
}

// =============================================
// COMPACT MODULE CARD
// =============================================

function ModuleCard({ title, description, to, Icon, color }) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-3 rounded-2xl border border-[#DCE9F7] bg-white p-4 shadow-sm transition hover:border-[#9DBFE6] hover:bg-[#F8FBFF]"
    >
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${color}`}
      >
        <Icon size={21} aria-hidden="true" />
      </div>

      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-bold text-[#365D91]">
          {title}
        </h3>

        <p className="mt-0.5 text-xs text-[#8295AA]">
          {description}
        </p>

        <span className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-[#476FA9]">
          View {title}
          <ArrowRight size={13} aria-hidden="true" />
        </span>
      </div>
    </Link>
  );
}

// =============================================
// STUDENT DASHBOARD
// =============================================

export default function StudentDashboardPage() {
  const { user } = useAuth();

  const [gpa, setGpa] = useState({
    status: "loading",
    value: null,
  });

  const [credits, setCredits] = useState({
    status: "loading",
    value: null,
  });

  useEffect(() => {
    const controller = new AbortController();

    async function loadSummary() {
      const [transcriptResult, curriculumResult] =
        await Promise.allSettled([
          fetchStudentTranscript({
            signal: controller.signal,
          }),
          fetchStudentCurriculum({
            signal: controller.signal,
          }),
        ]);

      if (controller.signal.aborted) return;

      if (transcriptResult.status === "fulfilled") {
        setGpa({
          status: "ready",
          value:
            transcriptResult.value.latestCumulativeGPA ?? null,
        });
      } else {
        setGpa({
          status: "error",
          value: null,
        });
      }

      if (curriculumResult.status === "fulfilled") {
        setCredits({
          status: "ready",
          value: completedCredits(
            curriculumResult.value.courses
          ),
        });
      } else {
        setCredits({
          status: "error",
          value: null,
        });
      }
    }

    loadSummary();

    return () => controller.abort();
  }, []);

  const gpaValue =
    gpa.status === "loading"
      ? "..."
      : formatGPA(gpa.value);

  const creditsValue =
    credits.status === "loading"
      ? "..."
      : credits.status === "ready"
        ? credits.value
        : "—";

  const gpaNote =
    gpa.status === "loading"
      ? "Loading GPA..."
      : gpa.status === "error"
        ? "Unable to load GPA"
        : gpa.value === null
          ? "No GPA recorded yet"
          : "Cumulative GPA / 4.00";

  const creditsNote =
    credits.status === "loading"
      ? "Loading credits..."
      : credits.status === "error"
        ? "Unable to load credits"
        : "Earned from completed courses";

  return (
    <div className="min-w-0 space-y-4 pb-3">

      {/* SHORT WELCOME BANNER */}

      <section className="flex items-center justify-between gap-4 rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E5F1FD] to-[#F4F0FC] px-5 py-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#7398C4]">
            Academia Student Portal
          </p>

          <h2 className="mt-1 text-lg font-bold text-[#365D91]">
            Your Academic Journey
          </h2>

          <p className="mt-1 text-xs text-[#6885A6]">
            Welcome, {user?.fullName || user?.username || "Student"}.
            Access your academic information below.
          </p>
        </div>

        <div className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/80 text-[#729FD6] sm:flex">
          <GraduationCap size={26} aria-hidden="true" />
        </div>
      </section>

      {/* ACADEMIC SUMMARY */}

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-base font-bold text-[#365D91]">
            Academic Summary
          </h2>

          <span className="text-[11px] text-[#8295AA]">
            Finalized results
          </span>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <SummaryCard
            title="Cumulative GPA"
            value={gpaValue}
            note={gpaNote}
            Icon={GraduationCap}
            color="bg-[#E5F0FC] text-[#476FA9]"
          />

          <SummaryCard
            title="Completed Credits"
            value={creditsValue}
            note={creditsNote}
            Icon={BookOpen}
            color="bg-[#E5F5EF] text-[#397C6B]"
          />
        </div>
      </section>

      {/* ACADEMIC MODULES */}

      <section>
        <h2 className="mb-2 text-base font-bold text-[#365D91]">
          Academic Information
        </h2>

        <div className="grid gap-3 md:grid-cols-3">
          {MODULES.map((module) => (
            <ModuleCard
              key={module.title}
              {...module}
            />
          ))}
        </div>
      </section>

      {/* FOOTNOTE */}

      <p className="text-[11px] text-[#8295AA]">
        GPA and earned credits use finalized academic results.
      </p>
    </div>
  );
}

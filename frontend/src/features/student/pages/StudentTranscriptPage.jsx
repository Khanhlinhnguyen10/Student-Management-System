
import { useEffect, useState } from "react";

import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  FileText,
  GraduationCap,
  RefreshCw,
} from "lucide-react";

import { fetchStudentTranscript } from "../api/studentApi";

// =============================================
// HELPERS
// =============================================

function formatScore(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  return Number.isFinite(number)
    ? number.toFixed(2)
    : "—";
}

function StatCard({ label, value, Icon, color }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#E2ECF7] bg-white/90 p-3">
      <div
        className={`hidden h-9 w-9 shrink-0 items-center justify-center rounded-lg sm:flex ${color}`}
      >
        <Icon size={18} aria-hidden="true" />
      </div>

      <div>
        <p className="text-[11px] text-[#8295AA]">
          {label}
        </p>

        <p className="mt-0.5 text-xl font-bold text-[#365D91]">
          {value}
        </p>
      </div>
    </div>
  );
}

function ScoreCell({ value, strong = false }) {
  return (
    <td
      className={`px-2 py-2.5 text-center ${
        strong
          ? "font-bold text-[#365D91]"
          : "text-[#607892]"
      }`}
    >
      {formatScore(value)}
    </td>
  );
}

// =============================================
// COMPACT SEMESTER TABLE
// =============================================

function SemesterSection({ semester }) {
  const courses = Array.isArray(semester.courses)
    ? semester.courses
    : [];

  return (
    <section className="overflow-hidden rounded-2xl border border-[#DCE9F7] bg-white shadow-sm">

      {/* COMPACT SEMESTER HEADER */}

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E7EFF8] bg-[#F8FBFF] px-4 py-3">
        <div>
          <h2 className="text-base font-bold text-[#365D91]">
            {semester.semesterName || "Semester"}
          </h2>

          <p className="mt-0.5 text-[11px] text-[#8295AA]">
            Academic Year: {semester.academicYear || "—"}
            {"  ·  "}
            {courses.length} finalized result(s)
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <div className="rounded-lg bg-[#E5F0FC] px-3 py-1.5">
            <p className="text-[10px] text-[#7190B3]">
              Semester GPA
            </p>

            <p className="text-sm font-bold text-[#365D91]">
              {formatScore(semester.semesterGPA)}
            </p>
          </div>

          <div className="rounded-lg bg-[#E5F5EF] px-3 py-1.5">
            <p className="text-[10px] text-[#659C88]">
              Cumulative GPA
            </p>

            <p className="text-sm font-bold text-[#397C6B]">
              {formatScore(semester.cumulativeGPA)}
            </p>
          </div>
        </div>
      </div>

      {/* GRADE TABLE */}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1000px] text-left text-xs">

          <thead className="bg-[#EBF3FD] text-[#426794]">
            <tr>
              <th className="px-3 py-3">Course</th>
              <th className="px-3 py-3">Course Name</th>
              <th className="px-2 py-3">Class</th>
              <th className="px-2 py-3 text-center">Credits</th>
              <th className="px-2 py-3 text-center">Attendance</th>
              <th className="px-2 py-3 text-center">Assignment</th>
              <th className="px-2 py-3 text-center">Midterm</th>
              <th className="px-2 py-3 text-center">Final Exam</th>
              <th className="px-2 py-3 text-center">Final Score</th>
              <th className="px-2 py-3 text-center">Letter</th>
              <th className="px-2 py-3 text-center">Point</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#EDF2F8]">
            {courses.map((course, index) => (
              <tr
                key={`${semester.semesterId}-${course.courseId}-${course.classCode}-${index}`}
                className="hover:bg-[#F8FBFF]"
              >
                <td className="px-3 py-2.5 font-bold text-[#476FA9]">
                  {course.courseCode}
                </td>

                <td className="px-3 py-2.5 font-medium text-[#365D91]">
                  {course.courseName}
                </td>

                <td className="px-2 py-2.5 text-[#607892]">
                  {course.classCode || "—"}
                </td>

                <td className="px-2 py-2.5 text-center text-[#607892]">
                  {course.credits}
                </td>

                <ScoreCell value={course.attendanceMark} />
                <ScoreCell value={course.assignmentMark} />
                <ScoreCell value={course.midtermMark} />
                <ScoreCell value={course.finalExamMark} />
                <ScoreCell value={course.finalScore} strong />

                <td className="px-2 py-2.5 text-center">
                  <span className="inline-flex rounded-full bg-[#E5F5EF] px-2.5 py-1 text-[11px] font-bold text-[#397C6B]">
                    {course.letterGrade || "—"}
                  </span>
                </td>

                <ScoreCell value={course.gradePoint} />
              </tr>
            ))}
          </tbody>

        </table>
      </div>
    </section>
  );
}

// =============================================
// STUDENT TRANSCRIPT PAGE
// =============================================

export default function StudentTranscriptPage() {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadTranscript() {
      setLoading(true);
      setError("");

      try {
        const result = await fetchStudentTranscript({
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setTranscript(result);
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        setTranscript(null);
        setError(
          err.message || "Unable to load transcript."
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadTranscript();

    return () => controller.abort();
  }, [reloadKey]);

  const semesters = Array.isArray(transcript?.semesters)
    ? transcript.semesters
    : [];

  return (
    <div className="min-w-0 space-y-3 pb-2">

      {/* COMPACT PAGE HEADER */}

      <section>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6389B7]">
          Student / Academic Information
        </p>

        <h1 className="mt-1 text-2xl font-bold text-[#365D91]">
          My Academic Transcript
        </h1>

        <p className="mt-1 text-xs text-[#71849A]">
          Finalized grades and academic performance by semester.
        </p>
      </section>

      {/* LOADING */}

      {loading && (
        <div
          role="status"
          className="aca-panel flex items-center gap-2 p-5 text-sm text-[#71849A]"
        >
          <RefreshCw
            size={18}
            className="animate-spin"
            aria-hidden="true"
          />
          Loading transcript...
        </div>
      )}

      {/* ERROR */}

      {!loading && error && (
        <section
          className="aca-panel p-5"
          role="alert"
        >
          <div className="flex items-center gap-2 text-sm text-[#B9384A]">
            <AlertCircle size={18} />
            {error}
          </div>

          <button
            type="button"
            onClick={() => setReloadKey((n) => n + 1)}
            className="mt-3 rounded-lg bg-[#E5F0FC] px-4 py-2 text-sm font-semibold text-[#476FA9]"
          >
            Try Again
          </button>
        </section>
      )}

      {/* TRANSCRIPT DATA */}

      {!loading && !error && transcript && (
        <>
          {/* COMPACT SUMMARY */}

          <section className="grid grid-cols-3 gap-2 rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E8F3FD] to-[#F4F0FC] p-3">
            <StatCard
              label="Finalized Results"
              value={transcript.totalFinalizedResults ?? 0}
              Icon={CheckCircle2}
              color="bg-[#E5F5EF] text-[#397C6B]"
            />

            <StatCard
              label="Academic Semesters"
              value={semesters.length}
              Icon={BookOpen}
              color="bg-[#E5F0FC] text-[#476FA9]"
            />

            <StatCard
              label="Cumulative GPA"
              value={formatScore(transcript.latestCumulativeGPA)}
              Icon={GraduationCap}
              color="bg-[#ECE7FA] text-[#75649C]"
            />
          </section>

          {/* EMPTY STATE */}

          {semesters.length === 0 && (
            <section className="aca-panel p-7 text-center">
              <FileText
                size={32}
                className="mx-auto text-[#8EAED2]"
              />

              <h2 className="mt-3 text-base font-bold text-[#365D91]">
                No finalized results available
              </h2>

              <p className="mt-1 text-xs text-[#8295AA]">
                Your transcript will appear when grades are finalized.
              </p>
            </section>
          )}

          {/* SEMESTERS APPEAR IMMEDIATELY BELOW SUMMARY */}

          {semesters.map((semester) => (
            <SemesterSection
              key={semester.semesterId}
              semester={semester}
            />
          ))}

          {/* SHORT FOOTNOTE */}

          <p className="px-1 text-[11px] leading-5 text-[#8295AA]">
            Only finalized grades are displayed.
            GPA values come from academic records;
            unavailable values appear as —.
          </p>
        </>
      )}
    </div>
  );
}

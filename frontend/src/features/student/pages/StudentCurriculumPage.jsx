
import { useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Clock3,
  GraduationCap,
  RefreshCw,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";
import { fetchStudentCurriculum } from "../api/studentApi";

// =============================================
// COMPACT STAT CARD
// =============================================

function StatCard({ label, value, Icon, color }) {
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-xl border border-[#E2ECF7] bg-white/85 p-3">
      <div className={`hidden h-9 w-9 shrink-0 items-center justify-center rounded-lg sm:flex ${color}`}>
        <Icon size={18} aria-hidden="true" />
      </div>

      <div className="min-w-0">
        <p className="text-[11px] text-[#8295AA]">
          {label}
        </p>
        <p className="text-xl font-bold text-[#365D91]">
          {value}
        </p>
      </div>
    </div>
  );
}

// =============================================
// COURSE BADGES
// =============================================

function TypeBadge({ type }) {
  const required = type?.toLowerCase() === "required";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold ${
        required
          ? "bg-[#E5F0FC] text-[#476FA9]"
          : "bg-[#EEE8FA] text-[#75649C]"
      }`}
    >
      {type || "—"}
    </span>
  );
}

function StatusBadge({ status }) {
  const completed = status === "Completed";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap ${
        completed
          ? "bg-[#DDF3EA] text-[#28785F]"
          : "bg-[#FFF0E3] text-[#A36B3D]"
      }`}
    >
      {completed ? (
        <CheckCircle2 size={13} aria-hidden="true" />
      ) : (
        <Clock3 size={13} aria-hidden="true" />
      )}
      {completed ? "Completed" : "Not Completed"}
    </span>
  );
}

// =============================================
// CURRICULUM PAGE
// =============================================

export default function StudentCurriculumPage() {
  const { refreshUser } = useAuth();

  const [curriculum, setCurriculum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCurriculum() {
      setLoading(true);
      setError("");

      try {
        const result = await fetchStudentCurriculum({
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setCurriculum(result);
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        setCurriculum(null);
        setError(
          err.message || "Unable to load curriculum."
        );

        if (err.status === 401) {
          void refreshUser();
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadCurriculum();

    return () => controller.abort();
  }, [reloadKey, refreshUser]);

  const courses = Array.isArray(curriculum?.courses)
    ? curriculum.courses
    : [];

  const completedCourses = courses.filter(
    (course) => course.status === "Completed"
  ).length;

  const totalCredits = courses.reduce(
    (total, course) => {
      const credits = Number(course.credits);
      return total + (
        Number.isFinite(credits) ? credits : 0
      );
    },
    0
  );

  return (
    <div className="min-w-0 space-y-3 pb-2">

      {/* COMPACT HEADING */}

      <section>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6389B7]">
          Student / Academic Information
        </p>

        <h1 className="mt-1 text-2xl font-bold text-[#365D91]">
          My Curriculum
        </h1>

        <p className="mt-1 text-xs text-[#71849A]">
          Courses, credits, prerequisites and completion status.
        </p>
      </section>

      {/* LOADING */}

      {loading && (
        <div
          className="aca-panel flex items-center gap-2 p-5 text-sm text-[#71849A]"
          role="status"
        >
          <RefreshCw
            size={18}
            className="animate-spin"
            aria-hidden="true"
          />
          Loading curriculum...
        </div>
      )}

      {/* ERROR */}

      {!loading && error && (
        <section className="aca-panel p-5" role="alert">
          <div className="flex items-center gap-2 text-sm text-[#B9384A]">
            <AlertCircle size={18} aria-hidden="true" />
            {error}
          </div>

          <button
            type="button"
            className="mt-3 rounded-lg bg-[#E5F0FC] px-4 py-2 text-sm font-semibold text-[#476FA9]"
            onClick={() => setReloadKey((n) => n + 1)}
          >
            Try Again
          </button>
        </section>
      )}

      {!loading && !error && curriculum && (
        <>
          {/* PROGRAM + SUMMARY IN ONE PANEL */}

          <section className="rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E8F3FD] to-[#F4F0FC] p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">

              <div className="flex min-w-0 items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/80 text-[#476FA9]">
                  <GraduationCap size={21} aria-hidden="true" />
                </div>

                <div className="min-w-0">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[#7797BB]">
                    Academic Program
                  </p>

                  <h2 className="mt-1 text-base font-bold text-[#365D91]">
                    {curriculum.curriculumName || "Curriculum"}
                  </h2>

                  <p className="mt-1 text-xs text-[#68819D]">
                    {curriculum.majorName || "Major unavailable"}
                  </p>

                  <p className="mt-0.5 text-xs text-[#68819D]">
                    Academic Year: {curriculum.academicYear || "—"}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 lg:w-[465px] lg:shrink-0">
                <StatCard
                  label="Courses"
                  value={courses.length}
                  Icon={BookOpen}
                  color="bg-[#E5F0FC] text-[#476FA9]"
                />

                <StatCard
                  label="Completed"
                  value={completedCourses}
                  Icon={CheckCircle2}
                  color="bg-[#E5F5EF] text-[#397C6B]"
                />

                <StatCard
                  label="Total Credits"
                  value={totalCredits}
                  Icon={GraduationCap}
                  color="bg-[#ECE7FA] text-[#75649C]"
                />
              </div>
            </div>
          </section>

          {/* COURSE TABLE - MOVED UP */}

          <section className="overflow-hidden rounded-2xl border border-[#DCE9F7] bg-white shadow-sm">

            <div className="flex items-center justify-between gap-3 border-b border-[#E7EFF8] px-4 py-3">
              <div>
                <h2 className="text-base font-bold text-[#365D91]">
                  Curriculum Courses
                </h2>
                <p className="mt-0.5 text-[11px] text-[#8295AA]">
                  Required and elective courses
                </p>
              </div>

              <span className="rounded-full bg-[#DDF3EA] px-3 py-1 text-xs font-semibold text-[#397C6B]">
                {courses.length} courses
              </span>
            </div>

            {courses.length === 0 ? (
              <p className="p-5 text-sm text-[#71849A]">
                No courses assigned to this curriculum.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px] text-left text-xs">
                  <thead className="bg-[#EBF3FD] text-[#426794]">
                    <tr>
                      <th className="px-3 py-3">Course Code</th>
                      <th className="px-3 py-3">Course Name</th>
                      <th className="px-3 py-3 text-center">Credits</th>
                      <th className="px-3 py-3">Type</th>
                      <th className="px-3 py-3">Prerequisites</th>
                      <th className="px-3 py-3">Status</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-[#EDF2F8]">
                    {courses.map((course) => (
                      <tr
                        key={course.courseId}
                        className="hover:bg-[#F8FBFF]"
                      >
                        <td className="px-3 py-3 font-bold text-[#476FA9]">
                          {course.courseCode}
                        </td>

                        <td className="px-3 py-3 font-medium text-[#365D91]">
                          {course.courseName}
                        </td>

                        <td className="px-3 py-3 text-center text-[#607892]">
                          {course.credits}
                        </td>

                        <td className="px-3 py-3">
                          <TypeBadge type={course.courseType} />
                        </td>

                        <td className="px-3 py-3 text-[#68819D]">
                          {Array.isArray(course.prerequisites) &&
                          course.prerequisites.length > 0 ? (
                            <div className="space-y-1">
                              {course.prerequisites.map((item) => (
                                <div key={item.courseId}>
                                  <span className="font-semibold">
                                    {item.courseCode}
                                  </span>
                                  {item.courseName
                                    ? ` - ${item.courseName}`
                                    : ""}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-[#9BAABD]">
                              None
                            </span>
                          )}
                        </td>

                        <td className="px-3 py-3">
                          <StatusBadge status={course.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* SMALL EXPLANATION */}

          <p className="px-1 text-[11px] leading-5 text-[#8295AA]">
            Completed means a finalized passing result exists.
            Total Credits represents curriculum credits, not earned credits.
          </p>
        </>
      )}
    </div>
  );
}

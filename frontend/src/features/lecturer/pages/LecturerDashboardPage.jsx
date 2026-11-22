
import { useEffect, useState } from "react";

import {
  AlertCircle,
  BookOpen,
  CalendarDays,
  GraduationCap,
  RefreshCw,
  Users,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";
import { fetchAssignedSections } from "../api/lecturerApi";


function StatCard({ title, value, Icon, color }) {
  return (
    <div
      className={[
        "flex min-h-[65px] items-center gap-3",
        "rounded-xl border border-[#DCE9F7]",
        "bg-white px-3.5 py-2",
        "shadow-[0_1px_3px_rgba(60,104,154,0.05)]",
      ].join(" ")}
    >
      <div
        className={[
          "flex h-9 w-9 shrink-0",
          "items-center justify-center",
          "rounded-[10px]",
          color,
        ].join(" ")}
      >
        <Icon size={18} aria-hidden="true" />
      </div>

      <div className="min-w-0">
        <p className="text-[11px] text-[#8295AA]">
          {title}
        </p>

        <p className="mt-0.5 text-[21px] font-bold leading-6 text-[#365D91]">
          {value}
        </p>
      </div>
    </div>
  );
}


export default function LecturerDashboardPage() {
  const { user } = useAuth();

  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadSections() {
      setLoading(true);
      setError("");

      try {
        const data = await fetchAssignedSections({
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setSections(data);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setSections([]);

          setError(
            err.status === 401
              ? "Session expired. Please log in again."
              : err.message || "Unable to load classes."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadSections();

    return () => controller.abort();
  }, [reloadKey]);

  const enrollmentCount = sections.reduce(
    (sum, section) =>
      sum + Number(section.studentCount || 0),
    0
  );

  const courseCount = new Set(
    sections.map((section) => section.courseId)
  ).size;

  return (
    <div className="min-w-0 space-y-2.5 pb-1">

      {/* COMPACT DASHBOARD HEADER */}
      <section
        className={[
          "rounded-xl border border-[#DCE9F7]",
          "bg-gradient-to-r",
          "from-[#E5F1FD] to-[#F4F0FC]",
          "px-4 py-2.5",
        ].join(" ")}
      >
        <div className="flex items-center gap-3">

          <div
            className={[
              "hidden h-9 w-9 shrink-0",
              "items-center justify-center",
              "rounded-[10px]",
              "bg-white/85 text-[#476FA9]",
              "sm:flex",
            ].join(" ")}
          >
            <GraduationCap
              size={21}
              aria-hidden="true"
            />
          </div>

          <div className="min-w-0">
            <p
              className={[
                "text-[9px] font-bold uppercase",
                "tracking-[0.15em] text-[#7398C4]",
              ].join(" ")}
            >
              Lecturer / Academic Overview
            </p>

            <h1
              className={[
                "mt-0.5 text-[20px] font-bold",
                "leading-6 text-[#365D91]",
              ].join(" ")}
            >
              Lecturer Dashboard
            </h1>

            <p className="mt-0.5 text-[11px] text-[#6885A6]">
              Welcome, {user?.fullName || "Lecturer"}.
              {" "}Manage your assigned class sections.
            </p>
          </div>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <div
          role="alert"
          className={[
            "rounded-lg border border-[#F5CDD2]",
            "bg-[#FFF1F2] px-3 py-2",
            "text-xs text-[#AE4757]",
          ].join(" ")}
        >
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>

          <button
            type="button"
            onClick={() =>
              setReloadKey((n) => n + 1)
            }
            className="mt-2 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold"
          >
            Try Again
          </button>
        </div>
      )}

      {/* SUMMARY */}
      <section className="grid gap-2 md:grid-cols-3">

        <StatCard
          title="Assigned Classes"
          value={
            loading ? "..." : error ? "—" : sections.length
          }
          Icon={BookOpen}
          color="bg-[#E5F0FC] text-[#476FA9]"
        />

        <StatCard
          title="Enrollment Records"
          value={
            loading ? "..." : error ? "—" : enrollmentCount
          }
          Icon={Users}
          color="bg-[#E5F5EF] text-[#397C6B]"
        />

        <StatCard
          title="Courses Taught"
          value={
            loading ? "..." : error ? "—" : courseCount
          }
          Icon={GraduationCap}
          color="bg-[#ECE7FA] text-[#75649C]"
        />
      </section>

      {/* ASSIGNED CLASSES */}
      <section
        className={[
          "overflow-hidden rounded-xl",
          "border border-[#DCE9F7]",
          "bg-white shadow-sm",
        ].join(" ")}
      >
        <div
          className={[
            "flex items-center justify-between gap-3",
            "border-b border-[#E7EFF8]",
            "px-4 py-2.5",
          ].join(" ")}
        >
          <div className="min-w-0">
            <h2 className="text-[14px] font-bold text-[#365D91]">
              My Assigned Classes
            </h2>

            <p className="mt-0.5 text-[10px] text-[#8295AA]">
              Class sections assigned to your account
            </p>
          </div>

          <span
            className={[
              "shrink-0 rounded-full",
              "bg-[#DDF3EA] px-2.5 py-1",
              "text-[11px] font-semibold text-[#397C6B]",
            ].join(" ")}
          >
            {loading
              ? "Loading"
              : `${sections.length} classes`}
          </span>
        </div>

        {loading ? (
          <div
            role="status"
            className="flex items-center gap-2 p-4 text-xs text-[#71849A]"
          >
            <RefreshCw
              size={16}
              className="animate-spin"
              aria-hidden="true"
            />
            Loading assigned classes...
          </div>
        ) : !error && sections.length === 0 ? (
          <p className="p-4 text-xs text-[#71849A]">
            No assigned class sections found.
          </p>
        ) : !error ? (
          <div
            className="overflow-auto"
            style={{
              maxHeight: "min(46dvh, 400px)",
            }}
          >
            <table className="w-full min-w-[710px] text-left text-[11px]">

              <thead className="sticky top-0 z-10 bg-[#EBF3FD] text-[#426794]">
                <tr>
                  <th className="px-3 py-2">
                    Class Code
                  </th>

                  <th className="px-3 py-2">
                    Course
                  </th>

                  <th className="px-3 py-2">
                    Semester
                  </th>

                  <th className="px-3 py-2 text-center">
                    Credits
                  </th>

                  <th className="px-3 py-2 text-center">
                    Students
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-[#EDF2F8]">
                {sections.map((section) => (
                  <tr
                    key={section.classSectionId}
                    className="hover:bg-[#F8FBFF]"
                  >
                    <td className="px-3 py-2 font-bold text-[#476FA9]">
                      {section.classCode}
                    </td>

                    <td className="px-3 py-2">
                      <p className="font-semibold text-[#365D91]">
                        {section.courseName}
                      </p>

                      <p className="text-[10px] text-[#8295AA]">
                        {section.courseCode}
                      </p>
                    </td>

                    <td className="px-3 py-2 text-[#607892]">
                      <span className="inline-flex items-center gap-1">
                        <CalendarDays
                          size={12}
                          aria-hidden="true"
                        />
                        {section.semesterName}
                      </span>

                      <p className="text-[10px] text-[#8295AA]">
                        {section.academicYear}
                      </p>
                    </td>

                    <td className="px-3 py-2 text-center text-[#607892]">
                      {section.credits}
                    </td>

                    <td className="px-3 py-2 text-center">
                      <span
                        className={[
                          "inline-flex rounded-full",
                          "bg-[#E5F5EF] px-2.5 py-0.5",
                          "font-semibold text-[#397C6B]",
                        ].join(" ")}
                      >
                        {section.studentCount}
                        /{section.maxCapacity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {/* DATA DEFINITION */}
      <p className="px-1 text-[10px] text-[#8295AA]">
        Enrollment Records counts class registrations,
        not necessarily unique students.
      </p>
    </div>
  );
}

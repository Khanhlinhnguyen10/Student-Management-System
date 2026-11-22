
import { useEffect, useMemo, useState } from "react";

import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Eye,
  LockKeyhole,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  createAdminCourse,
  deleteAdminCourse,
  fetchAdminCourse,
  fetchAdminCourses,
  updateAdminCourse,
} from "../api/adminCoursesApi";

import {
  fetchAdminFaculties,
} from "../api/adminFacultiesApi";

// =========================================
// CONSTANTS
// =========================================

const EMPTY_FORM = {
  facultyId: "",
  courseCode: "",
  courseName: "",
  credits: "3",
  midtermWeight: "20",
  assignmentWeight: "20",
  attendanceWeight: "10",
  finalExamWeight: "50",
  prerequisiteIds: [],
};

const WEIGHT_FIELDS = [
  ["midtermWeight", "Midterm"],
  ["assignmentWeight", "Assignment"],
  ["attendanceWeight", "Attendance"],
  ["finalExamWeight", "Final Exam"],
];

const INPUT_STYLE =
  "mt-1.5 w-full rounded-xl border border-[#D4E3F4] " +
  "bg-white px-3.5 py-2.5 text-sm text-[#385B82] " +
  "outline-none focus:border-[#82B0E3] " +
  "focus:ring-2 focus:ring-[#E1EFFC] " +
  "disabled:cursor-not-allowed disabled:bg-[#F2F5FA]";

const PRIMARY_BUTTON =
  "inline-flex items-center justify-center gap-2 " +
  "rounded-xl bg-[#476FA9] px-4 py-2.5 " +
  "text-sm font-semibold text-white transition " +
  "hover:bg-[#3E6498] disabled:cursor-not-allowed " +
  "disabled:opacity-50";

const SECONDARY_BUTTON =
  "inline-flex items-center justify-center gap-2 " +
  "rounded-xl bg-[#E8F2FC] px-4 py-2.5 " +
  "text-sm font-semibold text-[#476FA9] " +
  "hover:bg-[#DCEBFA] disabled:opacity-50";

// =========================================
// HELPERS
// =========================================

function hasAcademicLinks(course) {
  return (
    Number(course.classSectionCount || 0) > 0 ||
    Number(course.curriculumCount || 0) > 0 ||
    Number(course.dependentCourseCount || 0) > 0
  );
}

function safeText(value) {
  return value == null || value === ""
    ? "-"
    : String(value);
}

function toForm(course) {
  return {
    facultyId: course.facultyId,
    courseCode: course.courseCode,
    courseName: course.courseName,
    credits: String(course.credits),
    midtermWeight: String(course.midtermWeight),
    assignmentWeight: String(course.assignmentWeight),
    attendanceWeight: String(course.attendanceWeight),
    finalExamWeight: String(course.finalExamWeight),
    prerequisiteIds: [
      ...(course.prerequisiteIds || []),
    ],
  };
}

function parseWeight(value, label) {
  const raw = String(value ?? "").trim();

  if (!/^\d+(?:\.\d{1,2})?$/.test(raw)) {
    throw new Error(
      `${label} must have at most 2 decimal places.`
    );
  }

  const number = Number(raw);

  if (
    !Number.isFinite(number) ||
    number < 0 ||
    number > 100
  ) {
    throw new Error(
      `${label} must be between 0 and 100.`
    );
  }

  return number;
}

function buildPayload(form, isCreate) {
  const credits = Number(form.credits);

  if (
    !Number.isInteger(credits) ||
    credits < 1 ||
    credits > 255
  ) {
    throw new Error(
      "Credits must be an integer from 1 to 255."
    );
  }

  const weights = {};

  for (const [key, label] of WEIGHT_FIELDS) {
    weights[key] = parseWeight(form[key], label);
  }

  const totalCents = Math.round(
    Object.values(weights).reduce(
      (total, value) =>
        total + Math.round(value * 100),
      0
    )
  );

  if (totalCents !== 10000) {
    throw new Error(
      "The four grading weights must total 100%."
    );
  }

  if (!form.facultyId) {
    throw new Error(
      "Please select a Managing Faculty."
    );
  }

  const payload = {
    facultyId: form.facultyId,
    courseName: form.courseName.trim(),
    credits,
    ...weights,
    prerequisiteIds: [
      ...form.prerequisiteIds,
    ],
  };

  if (isCreate) {
    payload.courseCode = form.courseCode
      .trim()
      .toUpperCase();
  }

  return payload;
}

function DetailItem({ label, value }) {
  return (
    <div className="rounded-xl bg-[#F5F9FF] p-3">
      <p className="text-[11px] font-semibold text-[#829AB5]">
        {label}
      </p>
      <p className="mt-1 break-words text-sm font-semibold text-[#42668C]">
        {safeText(value)}
      </p>
    </div>
  );
}

// =========================================
// MAIN PAGE
// =========================================

export default function AdminCoursesPage() {
  const [courses, setCourses] = useState([]);
  const [faculties, setFaculties] = useState([]);

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formMode, setFormMode] = useState(null);
  const [editingId, setEditingId] = useState("");
  const [form, setForm] = useState({
    ...EMPTY_FORM,
  });

  const [viewing, setViewing] = useState(null);

  // =========================================
  // LOAD COURSES AND FACULTIES
  // =========================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const [courseRecords, facultyRecords] =
          await Promise.all([
            fetchAdminCourses({
              signal: controller.signal,
            }),
            fetchAdminFaculties({
              signal: controller.signal,
            }),
          ]);

        if (controller.signal.aborted) return;

        setCourses(courseRecords);
        setFaculties(facultyRecords);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err.message ||
              "Unable to load Course Management."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => controller.abort();
  }, [refreshKey]);

  // =========================================
  // SEARCH
  // =========================================

  const filtered = useMemo(() => {
    const keyword = search
      .trim()
      .toLowerCase();

    if (!keyword) return courses;

    return courses.filter((course) =>
      [
        course.courseId,
        course.courseCode,
        course.courseName,
        course.facultyName,
        course.facultyCode,
      ].some((value) =>
        String(value ?? "")
          .toLowerCase()
          .includes(keyword)
      )
    );
  }, [courses, search]);

  // =========================================
  // PREPARE CREATE FORM
  // =========================================

  function openCreate() {
    if (busy) return;

    setFormMode("create");
    setEditingId("");
    setViewing(null);
    setForm({
      ...EMPTY_FORM,
      prerequisiteIds: [],
    });

    setError("");
    setSuccess("");
  }

  // =========================================
  // OPEN COURSE DETAILS
  // =========================================

  async function openView(course) {
    if (busy) return;

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const record = await fetchAdminCourse(
        course.courseId
      );

      setViewing(record);
      setFormMode(null);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load course details."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // PREPARE EDIT FORM
  // =========================================

  async function openEdit(course) {
    if (busy) return;

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const record = await fetchAdminCourse(
        course.courseId
      );

      setForm(toForm(record));
      setEditingId(record.courseId);
      setFormMode("edit");
      setViewing(null);
    } catch (err) {
      setError(
        err.message ||
          "Unable to load course for editing."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // CHANGE INPUT
  // =========================================

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  // =========================================
  // TOGGLE PREREQUISITE
  // =========================================

  function togglePrerequisite(courseId) {
    setForm((current) => {
      const selected = new Set(
        current.prerequisiteIds
      );

      if (selected.has(courseId)) {
        selected.delete(courseId);
      } else {
        selected.add(courseId);
      }

      return {
        ...current,
        prerequisiteIds: [...selected],
      };
    });
  }

  // =========================================
  // CANCEL EDIT
  // =========================================

  function closeForm() {
    if (busy) return;

    setFormMode(null);
    setEditingId("");
    setForm({
      ...EMPTY_FORM,
      prerequisiteIds: [],
    });
  }

  // =========================================
  // SAVE COURSE
  // =========================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (busy || !formMode) return;

    setError("");
    setSuccess("");

    const isCreate = formMode === "create";

    let payload;

    try {
      payload = buildPayload(form, isCreate);
    } catch (err) {
      setError(err.message);
      return;
    }

    setBusy(true);

    try {
      const response = isCreate
        ? await createAdminCourse(payload)
        : await updateAdminCourse(
            editingId,
            payload
          );

      setSuccess(
        response.message ||
          "Course saved successfully."
      );

      setFormMode(null);
      setEditingId("");
      setForm({
        ...EMPTY_FORM,
        prerequisiteIds: [],
      });

      setRefreshKey((number) => number + 1);
    } catch (err) {
      setError(
        err.message ||
          "Unable to save course."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // DELETE COURSE
  // =========================================

  async function handleDelete(course) {
    if (busy) return;

    setError("");
    setSuccess("");

    if (hasAcademicLinks(course)) {
      setError(
        "Cannot delete a course linked to class " +
          "sections, curriculum records or " +
          "dependent courses."
      );
      return;
    }

    const confirmed = window.confirm(
      `Delete ${course.courseCode} - ` +
        `${course.courseName}?\n\n` +
        "This action cannot be undone."
    );

    if (!confirmed) return;

    setBusy(true);

    try {
      const response = await deleteAdminCourse(
        course.courseId
      );

      setSuccess(
        response.message ||
          "Course deleted successfully."
      );

      if (viewing?.courseId === course.courseId) {
        setViewing(null);
      }

      setRefreshKey((number) => number + 1);
    } catch (err) {
      setError(
        err.message ||
          "Unable to delete course."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // RENDER
  // =========================================

  return (
    <div className="min-w-0 space-y-4 pb-6">
      {/* HEADER */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E5F1FD] to-[#F4F0FC] p-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-[#476FA9] shadow-sm">
            <BookOpen size={21} />
          </div>

          <div>
            <h1 className="text-xl font-bold text-[#365D91]">
              Course Management
            </h1>
            <p className="mt-1 text-xs text-[#718DA9]">
              Manage courses, grading weights and prerequisites.
            </p>
          </div>
        </div>

        <button
          type="button"
          disabled={busy || loading}
          onClick={openCreate}
          className={PRIMARY_BUTTON}
        >
          <Plus size={17} />
          Create Course
        </button>
      </section>

      {/* ERROR */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-[#F2D1D1] bg-[#FFF7F6] px-4 py-3 text-sm text-[#A64A4A]"
        >
          <AlertCircle
            size={17}
            className="shrink-0"
          />
          {error}
        </div>
      )}

      {/* SUCCESS */}
      {success && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-xl border border-[#CEE9DC] bg-[#F0FAF5] px-4 py-3 text-sm text-[#387966]"
        >
          <CheckCircle2 size={17} />
          {success}
        </div>
      )}

      {/* COURSE TABLE */}
      <section className="rounded-2xl border border-[#DFEAF6] bg-white p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full max-w-sm">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7B98B7]"
            />

            <input
              type="search"
              placeholder="Search course code, name or faculty"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              className="w-full rounded-xl border border-[#D4E3F4] bg-[#F9FBFF] py-2.5 pl-9 pr-3 text-sm text-[#365D91] outline-none focus:border-[#82B0E3]"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="whitespace-nowrap text-xs text-[#8197B0]">
              {filtered.length} course(s)
            </span>

            <button
              type="button"
              disabled={loading || busy}
              className={SECONDARY_BUTTON}
              onClick={() => {
                setError("");
                setRefreshKey((n) => n + 1);
              }}
            >
              <RefreshCw
                size={15}
                className={
                  loading ? "animate-spin" : ""
                }
              />
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1020px] text-left text-xs">
            <thead className="bg-[#EAF3FD] text-[#446B98]">
              <tr>
                <th className="rounded-l-lg px-3 py-3">
                  Course
                </th>
                <th className="px-3 py-3">
                  Faculty
                </th>
                <th className="px-3 py-3 text-center">
                  Credits
                </th>
                <th className="px-3 py-3">
                  Grade Weights
                </th>
                <th className="px-3 py-3">
                  Prerequisites
                </th>
                <th className="px-3 py-3">
                  Linked Records
                </th>
                <th className="rounded-r-lg px-3 py-3 text-center">
                  Action
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#EDF3FA]">
              {!loading && filtered.map((course) => (
                <tr
                  key={course.courseId}
                  className="hover:bg-[#F8FBFF]"
                >
                  {/* COURSE */}
                  <td className="px-3 py-3">
                    <p className="font-bold text-[#365D91]">
                      {course.courseCode} - {course.courseName}
                    </p>

                    <p className="mt-1 text-[10px] text-[#91A6BC]">
                      {course.courseId}
                    </p>
                  </td>

                  {/* FACULTY */}
                  <td className="px-3 py-3 text-[#607E9D]">
                    {course.facultyName}
                  </td>

                  {/* CREDITS */}
                  <td className="px-3 py-3 text-center font-bold text-[#476FA9]">
                    {course.credits}
                  </td>

                  {/* WEIGHTS */}
                  <td className="px-3 py-3 text-[11px] text-[#6783A3]">
                    <div>
                      Midterm: {course.midtermWeight}%
                    </div>
                    <div>
                      Assignment: {course.assignmentWeight}%
                    </div>
                    <div>
                      Attendance: {course.attendanceWeight}%
                    </div>
                    <div>
                      Final Exam: {course.finalExamWeight}%
                    </div>
                  </td>

                  {/* PREREQUISITES */}
                  <td className="px-3 py-3 text-[#607E9D]">
                    {course.prerequisites?.length
                      ? course.prerequisites
                          .map((item) => item.courseCode)
                          .join(", ")
                      : "None"}
                  </td>

                  {/* REFERENCES */}
                  <td className="px-3 py-3 text-[11px] text-[#6783A3]">
                    <div>
                      {course.classSectionCount} class section(s)
                    </div>
                    <div>
                      {course.curriculumCount} curriculum link(s)
                    </div>
                    <div>
                      {course.dependentCourseCount} dependent course(s)
                    </div>
                  </td>

                  {/* ACTION */}
                  <td className="px-3 py-3">
                    <div className="flex justify-center gap-1.5">
                      <button
                        type="button"
                        disabled={busy}
                        title="View Course"
                        aria-label={`View ${course.courseCode}`}
                        onClick={() => openView(course)}
                        className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                      >
                        <Eye size={15} />
                      </button>

                      <button
                        type="button"
                        disabled={busy}
                        title="Update Course"
                        aria-label={`Edit ${course.courseCode}`}
                        onClick={() => openEdit(course)}
                        className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                      >
                        <Pencil size={15} />
                      </button>

                      <button
                        type="button"
                        disabled={
                          busy ||
                          hasAcademicLinks(course)
                        }
                        title={
                          hasAcademicLinks(course)
                            ? "Course has linked academic records"
                            : "Delete Course"
                        }
                        aria-label={`Delete ${course.courseCode}`}
                        onClick={() =>
                          handleDelete(course)
                        }
                        className="rounded-lg bg-[#FFF1EE] p-2 text-[#B96657] hover:bg-[#FFE2DD] disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {hasAcademicLinks(course) ? (
                          <LockKeyhole size={15} />
                        ) : (
                          <Trash2 size={15} />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {loading && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-3 py-8 text-center text-[#8197B0]"
                  >
                    Loading courses...
                  </td>
                </tr>
              )}

              {!loading && filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-3 py-8 text-center text-[#8197B0]"
                  >
                    No courses found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* VIEW DETAILS */}
      {viewing && !formMode && (
        <section className="rounded-2xl border border-[#DCE9F7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold text-[#365D91]">
              Course Details
            </h2>

            <button
              type="button"
              onClick={() => setViewing(null)}
              aria-label="Close Course Details"
              className="text-[#7891AD]"
            >
              <X size={18} />
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <DetailItem
              label="Course ID"
              value={viewing.courseId}
            />
            <DetailItem
              label="Course Code"
              value={viewing.courseCode}
            />
            <DetailItem
              label="Course Name"
              value={viewing.courseName}
            />
            <DetailItem
              label="Credits"
              value={viewing.credits}
            />
            <DetailItem
              label="Managing Faculty"
              value={viewing.facultyName}
            />
            <DetailItem
              label="Prerequisites"
              value={
                viewing.prerequisites?.length
                  ? viewing.prerequisites
                      .map((p) => p.courseCode)
                      .join(", ")
                  : "None"
              }
            />

            {WEIGHT_FIELDS.map(([key, label]) => (
              <DetailItem
                key={key}
                label={`${label} Weight`}
                value={`${viewing[key]}%`}
              />
            ))}
          </div>
        </section>
      )}

      {/* CREATE / UPDATE FORM */}
      {formMode && (
        <section className="rounded-2xl border border-[#DCE9F7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#365D91]">
                {formMode === "create"
                  ? "Create Course"
                  : "Update Course"}
              </h2>

              {formMode === "edit" && (
                <p className="mt-1 text-xs text-[#8AA1B8]">
                  {editingId}
                </p>
              )}
            </div>

            <button
              type="button"
              disabled={busy}
              onClick={closeForm}
              aria-label="Close Course Form"
              className="text-[#7891AD] disabled:opacity-50"
            >
              <X size={19} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              {/* CODE */}
              <label className="text-xs font-semibold text-[#466C98]">
                Course Code *
                <input
                  required
                  maxLength={10}
                  pattern="[A-Za-z0-9]{1,10}"
                  disabled={
                    busy ||
                    formMode === "edit"
                  }
                  value={form.courseCode}
                  placeholder="TEST301"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "courseCode",
                      event.target.value.toUpperCase()
                    )
                  }
                />
                {formMode === "edit" && (
                  <span className="mt-1 block text-[10px] font-normal text-[#8BA1B7]">
                    Course Code cannot be changed.
                  </span>
                )}
              </label>

              {/* NAME */}
              <label className="text-xs font-semibold text-[#466C98]">
                Course Name *
                <input
                  required
                  maxLength={100}
                  disabled={busy}
                  value={form.courseName}
                  placeholder="Test Course"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "courseName",
                      event.target.value
                    )
                  }
                />
              </label>

              {/* FACULTY */}
              <label className="text-xs font-semibold text-[#466C98]">
                Managing Faculty *
                <select
                  required
                  disabled={busy}
                  value={form.facultyId}
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "facultyId",
                      event.target.value
                    )
                  }
                >
                  <option value="">
                    Select Managing Faculty
                  </option>
                  {faculties.map((faculty) => (
                    <option
                      key={faculty.facultyId}
                      value={faculty.facultyId}
                    >
                      {faculty.facultyCode} - {faculty.facultyName}
                    </option>
                  ))}
                </select>
              </label>

              {/* CREDITS */}
              <label className="text-xs font-semibold text-[#466C98]">
                Credits *
                <input
                  required
                  type="number"
                  min="1"
                  max="255"
                  step="1"
                  disabled={busy}
                  value={form.credits}
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "credits",
                      event.target.value
                    )
                  }
                />
              </label>
            </div>

            {/* GRADING WEIGHTS */}
            <div className="rounded-xl border border-[#DFEAF7] bg-[#F7FAFF] p-4">
              <h3 className="text-sm font-bold text-[#365D91]">
                Grading Weights
              </h3>

              <p className="mt-1 text-xs text-[#849BB3]">
                Enter percentages. The four weights must total 100%.
              </p>

              <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {WEIGHT_FIELDS.map(([key, label]) => (
                  <label
                    key={key}
                    className="text-xs font-semibold text-[#466C98]"
                  >
                    {label} (%) *
                    <input
                      required
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      disabled={busy}
                      value={form[key]}
                      className={INPUT_STYLE}
                      onChange={(event) =>
                        updateForm(
                          key,
                          event.target.value
                        )
                      }
                    />
                  </label>
                ))}
              </div>
            </div>

            {/* PREREQUISITES */}
            <div className="rounded-xl border border-[#DFEAF7] bg-[#F7FAFF] p-4">
              <h3 className="text-sm font-bold text-[#365D91]">
                Prerequisite Courses
              </h3>

              <p className="mt-1 text-xs text-[#849BB3]">
                Optional. Select courses required before this course.
                Circular dependencies are not allowed.
              </p>

              <div className="mt-3 grid max-h-52 grid-cols-1 gap-2 overflow-y-auto rounded-xl bg-white p-3 sm:grid-cols-2 lg:grid-cols-3">
                {courses
                  .filter(
                    (item) =>
                      item.courseId !== editingId
                  )
                  .map((course) => (
                    <label
                      key={course.courseId}
                      className="flex cursor-pointer items-start gap-2 rounded-lg border border-[#E3EDF8] p-2.5 hover:bg-[#F2F8FF]"
                    >
                      <input
                        type="checkbox"
                        disabled={busy}
                        checked={form.prerequisiteIds.includes(
                          course.courseId
                        )}
                        onChange={() =>
                          togglePrerequisite(course.courseId)
                        }
                        className="mt-0.5 accent-[#476FA9]"
                      />

                      <span className="text-[11px] text-[#557393]">
                        <strong className="text-[#365D91]">
                          {course.courseCode}
                        </strong>
                        {" - "}
                        {course.courseName}
                      </span>
                    </label>
                  ))}

                {courses.length === 0 && (
                  <p className="text-xs text-[#8BA1B7]">
                    No prerequisite courses available.
                  </p>
                )}
              </div>

              <p className="mt-2 text-[11px] font-medium text-[#6384A8]">
                Selected: {form.prerequisiteIds.length} prerequisite(s)
              </p>
            </div>

            {/* ACTION BUTTONS */}
            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={busy}
                className={PRIMARY_BUTTON}
              >
                {busy ? (
                  <RefreshCw
                    size={15}
                    className="animate-spin"
                  />
                ) : (
                  <CheckCircle2 size={15} />
                )}

                {busy
                  ? "Saving..."
                  : formMode === "create"
                    ? "Create Course"
                    : "Save Changes"}
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={closeForm}
                className={SECONDARY_BUTTON}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}
    </div>
  );
}

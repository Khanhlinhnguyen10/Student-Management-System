
import { useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ClipboardList,
  Pencil,
  RefreshCw,
  Save,
  X,
  LockKeyhole,
} from "lucide-react";

import {
  fetchAssignedSections,
  fetchSectionGradebook,
  saveGradebookDraft,
  saveFinalGrade,
} from "../api/lecturerApi";

const MARK_FIELDS = [
  ["midtermMark", "Midterm"],
  ["assignmentMark", "Assignment"],
  ["attendanceMark", "Attendance"],
  ["finalExamMark", "Final Exam"],
];

function displayMark(value) {
  return value == null ? "-" : Number(value).toFixed(2);
}

function createDraft(student) {
  return Object.fromEntries(
    MARK_FIELDS.map(([field]) => [
      field,
      student[field] == null ? "" : String(student[field]),
    ])
  );
}

function validateMarks(draft, requireAll = false) {
  const marks = {};

  for (const [field, label] of MARK_FIELDS) {
    const raw = String(draft[field] ?? "").trim();

    if (raw === "") {
      if (requireAll) {
        throw new Error(
          `${label} is required to finalize grades.`
        );
      }

      marks[field] = null;
      continue;
    }

    const value = Number(raw);

    if (
      !/^\d+(?:\.\d{1,2})?$/.test(raw) ||
      !Number.isFinite(value) ||
      value < 0 ||
      value > 10
    ) {
      throw new Error(
        `${label} must be between 0 and 10 (maximum 2 decimal places).`
      );
    }

    marks[field] = value;
  }

  return marks;
}

export default function LecturerGradebookPage() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [gradebook, setGradebook] = useState(null);

  const [loadingSections, setLoadingSections] = useState(true);
  const [loadingGrades, setLoadingGrades] = useState(false);
  const [saving, setSaving] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({});

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  // Load assigned class sections
  useEffect(() => {
    const controller = new AbortController();

    async function loadSections() {
      setLoadingSections(true);
      setError("");

      try {
        const data = await fetchAssignedSections({
          signal: controller.signal,
        });

        if (controller.signal.aborted) return;

        setSections(data);

        setSectionId((current) =>
          data.some(
            (item) => item.classSectionId === current
          )
            ? current
            : (data[0]?.classSectionId ?? "")
        );
      } catch (err) {
        if (!controller.signal.aborted) {
          setSections([]);
          setError(
            err.message || "Unable to load assigned classes."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingSections(false);
        }
      }
    }

    loadSections();
    return () => controller.abort();
  }, []);

  // Load gradebook
  useEffect(() => {
    if (!sectionId) {
      setGradebook(null);
      return undefined;
    }

    const controller = new AbortController();

    async function loadGradebook() {
      setLoadingGrades(true);
      setError("");
      setGradebook(null);
      setEditingId(null);
      setDraft({});

      try {
        const data = await fetchSectionGradebook(
          sectionId,
          { signal: controller.signal }
        );

        if (!controller.signal.aborted) {
          setGradebook(data);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err.message || "Unable to load student grades."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingGrades(false);
        }
      }
    }

    loadGradebook();
    return () => controller.abort();
  }, [sectionId, refreshKey]);

  function handleEdit(student) {
    if (student.isFinalized || saving) return;

    setError("");
    setSuccess("");
    setEditingId(student.enrollmentId);
    setDraft(createDraft(student));
  }

  function handleCancel() {
    setEditingId(null);
    setDraft({});
    setError("");
  }

  async function handleSave(student, finalize = false) {
    if (
      saving ||
      editingId !== student.enrollmentId ||
      !gradebook
    ) {
      return;
    }

    setError("");
    setSuccess("");

    if (student.isFinalized) {
      setError(
        "Finalized grades cannot be edited here."
      );
      return;
    }

    let marks;

    try {
      marks = validateMarks(draft, finalize);
    } catch (err) {
      setError(err.message);
      return;
    }

    if (
      finalize &&
      !window.confirm(
        `Finalize grades for ${student.studentName}? ` +
        "This will calculate the final grade and GPA."
      )
    ) {
      return;
    }

    setSaving(true);

    try {
      if (finalize) {
        const result = await saveFinalGrade(
          gradebook.section.classSectionId,
          student.enrollmentId,
          marks
        );

        setSuccess(
          `Grades finalized for ${student.studentName}: ` +
          `${displayMark(result.finalScore)} ` +
          `(${result.letterGrade}).`
        );
      } else {
        await saveGradebookDraft(
          gradebook.section.classSectionId,
          student.enrollmentId,
          marks
        );

        setSuccess(
          `Draft grades saved for ${student.studentName}.`
        );
      }

      setEditingId(null);
      setDraft({});
      setRefreshKey((n) => n + 1);
    } catch (err) {
      setError(
        err.message || "Unable to save student grades."
      );
    } finally {
      setSaving(false);
    }
  }

  const students = gradebook?.students ?? [];
  const weights = gradebook?.section?.weights ?? {};

  const components = [
    ["Midterm", weights.midterm],
    ["Assignment", weights.assignment],
    ["Attendance", weights.attendance],
    ["Final Exam", weights.finalExam],
  ];

  const tableScrollClass =
    students.length > 6
      ? "max-h-[420px] overflow-auto"
      : "overflow-x-auto";

  return (
    <div className="min-w-0 space-y-2.5 pb-1">
      {/* PAGE HEADER */}
      <section className="flex items-center gap-3 rounded-xl border border-[#DCE9F7] bg-gradient-to-r from-[#E5F1FD] to-[#F4F0FC] px-4 py-2.5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-white/90 text-[#476FA9]">
          <ClipboardList size={19} />
        </div>

        <div className="min-w-0">
          <h1 className="text-[20px] font-bold leading-6 text-[#365D91]">
            Gradebook
          </h1>

          <p className="mt-0.5 text-[11px] text-[#6885A6]">
            Enter and update grades for assigned classes.
          </p>
        </div>
      </section>

      {/* ASSIGNED CLASS */}
      <section className="rounded-xl border border-[#DCE9F7] bg-white px-3.5 py-3 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label
            htmlFor="section-select"
            className="shrink-0 text-[11px] font-bold text-[#365D91]"
          >
            Assigned Class
          </label>

          <select
            id="section-select"
            value={sectionId}
            disabled={
              loadingSections ||
              saving ||
              editingId !== null
            }
            onChange={(event) => {
              setSectionId(event.target.value);
              setError("");
              setSuccess("");
            }}
            className="h-9 min-w-0 flex-1 rounded-lg border border-[#CFDFF1] bg-[#F8FBFF] px-3 text-[12px] text-[#365D91] outline-none focus:border-[#75A7DE] disabled:opacity-60"
          >
            {sections.length === 0 && (
              <option value="">
                No assigned classes
              </option>
            )}

            {sections.map((section) => (
              <option
                key={section.classSectionId}
                value={section.classSectionId}
              >
                {section.classCode} - {section.courseName} -{" "}
                {section.semesterName}
              </option>
            ))}
          </select>

          <button
            type="button"
            disabled={
              !sectionId ||
              saving ||
              loadingGrades ||
              editingId !== null
            }
            onClick={() => {
              setError("");
              setSuccess("");
              setRefreshKey((n) => n + 1);
            }}
            className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg bg-[#E7F1FC] px-3 text-[11px] font-semibold text-[#476FA9] transition hover:bg-[#DDEBFB] disabled:opacity-50"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </section>

      {/* ERROR */}
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[12px] text-red-700"
        >
          {error}
        </p>
      )}

      {/* SUCCESS */}
      {success && (
        <p
          role="status"
          className="flex items-center gap-2 rounded-lg bg-[#E5F5EF] px-3 py-2 text-[12px] text-[#397C6B]"
        >
          <CheckCircle2 size={15} />
          {success}
        </p>
      )}

      {/* LOADING */}
      {loadingGrades && (
        <p
          role="status"
          className="flex items-center gap-2 rounded-lg bg-white px-3 py-3 text-xs text-[#71849A]"
        >
          <RefreshCw
            size={15}
            className="animate-spin"
          />
          Loading student grades...
        </p>
      )}

      {/* GRADEBOOK */}
      {gradebook && !loadingGrades && (
        <>
          {/* CLASS SUMMARY */}
          <section className="rounded-xl border border-[#DCE9F7] bg-white px-3.5 py-3">
            <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
              <div className="flex min-w-0 items-center gap-2">
                <BookOpen
                  size={16}
                  className="shrink-0 text-[#476FA9]"
                />

                <h2 className="min-w-0 text-[13px] font-bold text-[#365D91]">
                  {gradebook.section.classCode} -{" "}
                  {gradebook.section.courseName}
                </h2>
              </div>

              <span className="shrink-0 rounded-full bg-[#E5F5EF] px-2.5 py-1 text-[10px] font-semibold text-[#397C6B]">
                {students.length} students
              </span>
            </div>

            <div className="mt-2 flex flex-wrap gap-2">
              {components.map(([label, weight]) => (
                <div
                  key={label}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#DFEAF7] bg-[#F8FBFF] px-2.5 py-1.5"
                >
                  <span className="text-[11px] text-[#8195AC]">
                    {label}
                  </span>

                  <span className="text-[12px] font-bold text-[#456C9D]">
                    {weight == null ? "-" : `${weight}%`}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* STUDENT GRADE RECORDS */}
          <section className="overflow-hidden rounded-xl border border-[#DCE9F7] bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E6EFF8] px-3.5 py-2.5">
              <h2 className="text-[13px] font-bold text-[#365D91]">
                Student Grade Records
              </h2>

              <p className="text-[10px] text-[#8195AC]">
                Save Draft allows empty marks.
                Finalize requires all four.
              </p>
            </div>

            <div className={tableScrollClass}>
              <table className="w-full min-w-[1040px] text-left text-[11px]">
                <thead className="sticky top-0 z-10 bg-[#EAF3FD] text-[#426794]">
                  <tr>
                    <th className="px-3 py-2">
                      Student
                    </th>

                    {MARK_FIELDS.map(([field, label]) => (
                      <th
                        key={field}
                        className="px-2 py-2 text-center"
                      >
                        {label}
                      </th>
                    ))}

                    <th className="px-2 py-2 text-center">
                      Final Score
                    </th>

                    <th className="px-2 py-2 text-center">
                      Letter
                    </th>

                    <th className="px-2 py-2">
                      Status
                    </th>

                    <th className="px-3 py-2 text-center">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-[#EDF2F8]">
                  {students.map((student) => {
                    const isEditing =
                      editingId === student.enrollmentId;

                    return (
                      <tr
                        key={student.enrollmentId}
                        className="hover:bg-[#F8FBFF]"
                      >
                        {/* STUDENT */}
                        <td className="px-3 py-2 align-middle">
                          <div className="flex min-h-[42px] min-w-0 flex-col justify-center gap-0.5">
                            <span className="block text-[11px] font-bold leading-[17px] text-[#476FA9]">
                              {student.studentId}
                            </span>

                            <span
                              className="block whitespace-normal break-words text-[12px] font-medium leading-[19px] text-[#607892]"
                              title={student.studentName}
                            >
                              {student.studentName}
                            </span>
                          </div>
                        </td>

                        {/* MARK INPUTS */}
                        {MARK_FIELDS.map(([field, label]) => (
                          <td
                            key={field}
                            className="px-2 py-2 text-center"
                          >
                            {isEditing ? (
                              <input
                                type="number"
                                min="0"
                                max="10"
                                step="0.01"
                                value={draft[field] ?? ""}
                                aria-label={`${label} for ${student.studentName}`}
                                disabled={saving}
                                onChange={(event) =>
                                  setDraft((current) => ({
                                    ...current,
                                    [field]: event.target.value,
                                  }))
                                }
                                className="h-8 w-[65px] rounded-lg border border-[#BAD1EE] bg-[#F8FBFF] px-1.5 text-center text-[11px] outline-none focus:border-[#538DCE]"
                              />
                            ) : (
                              <span className="text-[#607892]">
                                {displayMark(student[field])}
                              </span>
                            )}
                          </td>
                        ))}

                        {/* FINAL SCORE */}
                        <td className="px-2 py-2 text-center font-bold text-[#365D91]">
                          {displayMark(student.finalScore)}
                        </td>

                        {/* LETTER */}
                        <td className="px-2 py-2 text-center font-bold text-[#476FA9]">
                          {student.letterGrade || "-"}
                        </td>

                        {/* STATUS */}
                        <td className="px-2 py-2">
                          <span
                            className={
                              "inline-flex whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-semibold " +
                              (student.isFinalized
                                ? "bg-[#E4F4EB] text-[#397C6B]"
                                : "bg-[#FFF2DC] text-[#96702E]")
                            }
                          >
                            {student.isFinalized
                              ? "Finalized"
                              : student.gradebookId
                                ? "Draft"
                                : "Not recorded"}
                          </span>
                        </td>

                        {/* ACTIONS */}
                        <td className="px-3 py-2 text-center">
                          {isEditing ? (
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                type="button"
                                disabled={saving}
                                onClick={() =>
                                  handleSave(student, false)
                                }
                                className="inline-flex h-8 items-center gap-1 whitespace-nowrap rounded-lg bg-[#476FA9] px-2.5 font-semibold text-white hover:bg-[#3E6498] disabled:opacity-50"
                              >
                                <Save size={12} />
                                {saving
                                  ? "Saving..."
                                  : "Save Draft"}
                              </button>

                              <button
                                type="button"
                                disabled={saving}
                                onClick={() =>
                                  handleSave(student, true)
                                }
                                className="inline-flex h-8 items-center gap-1 whitespace-nowrap rounded-lg bg-[#E1F2EB] px-2.5 font-semibold text-[#2F7561] hover:bg-[#CEE8DB] disabled:opacity-50"
                              >
                                <CheckCircle2 size={12} />
                                Finalize
                              </button>

                              <button
                                type="button"
                                disabled={saving}
                                onClick={handleCancel}
                                className="inline-flex h-8 items-center gap-1 rounded-lg bg-[#EEF2F7] px-2.5 font-semibold text-[#506988] disabled:opacity-50"
                              >
                                <X size={12} />
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              type="button"
                              disabled={
                                saving ||
                                editingId !== null ||
                                Boolean(student.isFinalized)
                              }
                              onClick={() =>
                                handleEdit(student)
                              }
                              title={
                                student.isFinalized
                                  ? "Finalized grades are locked"
                                  : "Edit grades"
                              }
                              className="inline-flex h-8 items-center gap-1.5 whitespace-nowrap rounded-lg bg-[#E6F0FC] px-2.5 font-semibold text-[#365D91] hover:bg-[#D8E8FA] disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {student.isFinalized ? (
                                <LockKeyhole size={12} />
                              ) : (
                                <Pencil size={12} />
                              )}

                              {student.isFinalized
                                ? "Locked"
                                : student.gradebookId
                                  ? "Edit"
                                  : "Enter Grades"}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}

                  {/* EMPTY STATE */}
                  {students.length === 0 && (
                    <tr>
                      <td
                        colSpan={9}
                        className="p-5 text-center text-[#8195AC]"
                      >
                        No enrolled students in this class.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

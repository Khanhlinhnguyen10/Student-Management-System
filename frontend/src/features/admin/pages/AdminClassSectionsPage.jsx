
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import { useNavigate } from "react-router-dom";

import {
  AlertCircle,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Eye,
  GraduationCap,
  MapPin,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  UserRound,
  Users,
  X,
} from "lucide-react";

import {
  fetchAdminClassSections,
  fetchAdminClassSection,
  fetchClassSectionSemesters,
  fetchClassSectionCourses,
  createAdminClassSection,
  updateAdminClassSection,
  deleteAdminClassSection,
} from "../api/adminClassSectionsApi";


// ============================================================
// CONSTANTS
// ============================================================

const DAYS = [
  { value: 2, label: "Monday" },
  { value: 3, label: "Tuesday" },
  { value: 4, label: "Wednesday" },
  { value: 5, label: "Thursday" },
  { value: 6, label: "Friday" },
  { value: 7, label: "Saturday" },
  { value: 1, label: "Sunday" },
];

const EMPTY_FORM = {
  classCode: "",
  courseId: "",
  semesterId: "",
  maxCapacity: "36",
  room: "",
  dayOfWeek: "",
  startTime: "",
  endTime: "",
};

const INPUT_CLASS = [
  "w-full rounded-xl border border-slate-200",
  "bg-white px-3 py-2.5 text-sm text-slate-700",
  "outline-none transition",
  "focus:border-[#83B1E3]",
  "focus:ring-2 focus:ring-[#DCEBFC]",
  "disabled:bg-slate-100",
  "disabled:text-slate-500",
].join(" ");

const LABEL_CLASS =
  "mb-1.5 block text-xs font-semibold text-slate-600";

const PRIMARY_BUTTON = [
  "inline-flex items-center justify-center gap-2",
  "rounded-xl bg-[#476FA9] px-4 py-2.5",
  "text-sm font-semibold text-white",
  "transition hover:bg-[#385D94]",
  "disabled:cursor-not-allowed disabled:opacity-60",
].join(" ");

const SECONDARY_BUTTON = [
  "inline-flex items-center justify-center gap-2",
  "rounded-xl border border-[#D8E5F5]",
  "bg-white px-4 py-2.5",
  "text-sm font-medium text-[#476FA9]",
  "transition hover:bg-[#EFF6FF]",
  "disabled:cursor-not-allowed disabled:opacity-60",
].join(" ");


// ============================================================
// HELPERS
// ============================================================

function getErrorMessage(error, fallback) {
  return error instanceof Error
    ? error.message
    : fallback;
}

function formatTime(value) {
  if (!value) {
    return "";
  }

  return String(value).slice(0, 5);
}

function getDayLabel(day) {
  const found = DAYS.find(
    (item) => item.value === Number(day)
  );

  return found ? found.label : "Not scheduled";
}

function formatSchedule(section) {
  if (
    section.dayOfWeek == null ||
    !section.startTime ||
    !section.endTime
  ) {
    return "Not scheduled";
  }

  return [
    getDayLabel(section.dayOfWeek),
    formatTime(section.startTime),
    "-",
    formatTime(section.endTime),
  ].join(" ");
}

function getLecturerLabel(section) {
  if (!section.lecturerId) {
    return "Not assigned";
  }

  return (
    section.lecturerName ||
    section.lecturerId
  );
}

function createFormValues(
  section = null,
  selectedSemester = ""
) {
  if (!section) {
    return {
      ...EMPTY_FORM,
      semesterId: selectedSemester,
    };
  }

  return {
    classCode: section.classCode || "",
    courseId: section.courseId || "",
    semesterId: section.semesterId || "",
    maxCapacity: String(
      section.maxCapacity ?? 36
    ),
    room: section.room || "",
    dayOfWeek:
      section.dayOfWeek == null
        ? ""
        : String(section.dayOfWeek),
    startTime: formatTime(
      section.startTime
    ),
    endTime: formatTime(
      section.endTime
    ),
  };
}


// ============================================================
// SMALL UI COMPONENTS
// ============================================================

function SectionLabel({
  children,
  required = false,
}) {
  return (
    <label className={LABEL_CLASS}>
      {children}

      {required && (
        <span className="ml-1 text-red-400">
          *
        </span>
      )}
    </label>
  );
}


function StatCard({
  icon: Icon,
  label,
  value,
  tone = "blue",
}) {
  const tones = {
    blue: {
      background: "bg-[#EAF3FF]",
      foreground: "text-[#527FC0]",
    },
    mint: {
      background: "bg-[#E6F7F1]",
      foreground: "text-[#429B83]",
    },
    lavender: {
      background: "bg-[#F0EBFF]",
      foreground: "text-[#8470B9]",
    },
    peach: {
      background: "bg-[#FFF0E8]",
      foreground: "text-[#C88A62]",
    },
  };

  const selected = tones[tone] || tones.blue;

  return (
    <div
      className={[
        "rounded-2xl border border-[#E3EBF6]",
        "bg-white p-4 shadow-sm",
      ].join(" ")}
    >
      <div className="flex items-center gap-3">
        <div
          className={[
            "flex h-11 w-11 shrink-0",
            "items-center justify-center rounded-xl",
            selected.background,
            selected.foreground,
          ].join(" ")}
        >
          <Icon size={20} />
        </div>

        <div className="min-w-0">
          <p className="text-xs text-slate-500">
            {label}
          </p>

          <p className="mt-1 text-xl font-bold text-slate-800">
            {value}
          </p>
        </div>
      </div>
    </div>
  );
}


function Notice({
  type = "error",
  children,
  onDismiss,
}) {
  const success = type === "success";

  return (
    <div
      role="alert"
      className={[
        "flex items-start gap-3 rounded-xl",
        "border px-4 py-3 text-sm",
        success
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-red-200 bg-red-50 text-red-700",
      ].join(" ")}
    >
      {success ? (
        <CheckCircle2
          size={18}
          className="mt-0.5 shrink-0"
        />
      ) : (
        <AlertCircle
          size={18}
          className="mt-0.5 shrink-0"
        />
      )}

      <div className="min-w-0 flex-1">
        {children}
      </div>

      {onDismiss && (
        <button
          type="button"
          aria-label="Dismiss message"
          onClick={onDismiss}
          className="shrink-0 opacity-70 hover:opacity-100"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}


function Modal({
  title,
  description,
  onClose,
  children,
  disabled = false,
}) {
  return (
    <div
      className={[
        "fixed inset-0 z-50",
        "flex items-center justify-center",
        "bg-slate-900/40 p-4",
      ].join(" ")}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={[
          "flex max-h-[90vh] w-full max-w-3xl",
          "flex-col overflow-hidden rounded-2xl",
          "border border-[#DCE8F7]",
          "bg-white shadow-2xl",
        ].join(" ")}
      >
        <div
          className={[
            "flex items-start justify-between gap-4",
            "border-b border-[#E4EDF8]",
            "bg-[#F3F8FF] px-6 py-5",
          ].join(" ")}
        >
          <div>
            <h2 className="text-lg font-bold text-[#355C92]">
              {title}
            </h2>

            {description && (
              <p className="mt-1 text-sm text-slate-500">
                {description}
              </p>
            )}
          </div>

          <button
            type="button"
            aria-label="Close dialog"
            disabled={disabled}
            onClick={onClose}
            className={[
              "rounded-lg p-2 text-slate-500",
              "transition hover:bg-white",
              "disabled:opacity-50",
            ].join(" ")}
          >
            <X size={20} />
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {children}
        </div>
      </div>
    </div>
  );
}


function DetailItem({
  label,
  value,
}) {
  return (
    <div
      className={[
        "rounded-xl border border-[#E5EDF8]",
        "bg-[#FAFCFF] p-3",
      ].join(" ")}
    >
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 break-words text-sm font-semibold text-slate-700">
        {value ?? "-"}
      </p>
    </div>
  );
}


// ============================================================
// MAIN PAGE
// ============================================================

export default function AdminClassSectionsPage() {
  const navigate = useNavigate();

  // ----------------------------------------------------------
  // DATA STATE
  // ----------------------------------------------------------

  const [sections, setSections] = useState([]);
  const [semesters, setSemesters] = useState([]);
  const [courses, setCourses] = useState([]);

  const [
    selectedSemester,
    setSelectedSemester,
  ] = useState("");

  const [
    selectedCourse,
    setSelectedCourse,
  ] = useState("");

  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [
    optionsLoading,
    setOptionsLoading,
  ] = useState(true);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [refreshKey, setRefreshKey] = useState(0);

  // ----------------------------------------------------------
  // MODAL STATE
  // ----------------------------------------------------------

  const [modal, setModal] = useState(null);

  const [
    selectedSection,
    setSelectedSection,
  ] = useState(null);

  const [form, setForm] = useState({
    ...EMPTY_FORM,
  });

  const [saving, setSaving] = useState(false);
  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [modalError, setModalError] = useState("");

  // ----------------------------------------------------------
  // LOAD DROPDOWN DATA
  // ----------------------------------------------------------

  useEffect(() => {
    const controller = new AbortController();

    async function loadOptions() {
      try {
        setOptionsLoading(true);

        const [
          semesterRecords,
          courseRecords,
        ] = await Promise.all([
          fetchClassSectionSemesters({
            signal: controller.signal,
          }),
          fetchClassSectionCourses({
            signal: controller.signal,
          }),
        ]);

        if (controller.signal.aborted) {
          return;
        }

        setSemesters(semesterRecords);
        setCourses(courseRecords);
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }

        setError(
          getErrorMessage(
            err,
            "Unable to load Class Section options."
          )
        );
      } finally {
        if (!controller.signal.aborted) {
          setOptionsLoading(false);
        }
      }
    }

    loadOptions();

    return () => {
      controller.abort();
    };
  }, []);

  // ----------------------------------------------------------
  // LOAD CLASS SECTION LIST
  // ----------------------------------------------------------

  useEffect(() => {
    const controller = new AbortController();

    async function loadSections() {
      try {
        setLoading(true);
        setError("");

        const records =
          await fetchAdminClassSections(
            selectedSemester,
            {
              signal: controller.signal,
            }
          );

        if (controller.signal.aborted) {
          return;
        }

        setSections(records);
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }

        setSections([]);

        setError(
          getErrorMessage(
            err,
            "Unable to load Class Sections."
          )
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadSections();

    return () => {
      controller.abort();
    };
  }, [
    selectedSemester,
    refreshKey,
  ]);

  // ----------------------------------------------------------
  // FILTER CLASS SECTIONS
  // ----------------------------------------------------------

  const filteredSections = useMemo(() => {
    const keyword = search
      .trim()
      .toLowerCase();

    return sections.filter((section) => {
      const matchesCourse =
        !selectedCourse ||
        section.courseId === selectedCourse;

      const searchable = [
        section.classSectionId,
        section.classCode,
        section.courseCode,
        section.courseName,
        section.semesterName,
        section.lecturerName,
        section.room,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        !keyword ||
        searchable.includes(keyword);

      return matchesCourse && matchesSearch;
    });
  }, [
    sections,
    selectedCourse,
    search,
  ]);

  // ----------------------------------------------------------
  // STATISTICS
  // ----------------------------------------------------------

  const statistics = useMemo(() => {
    const assigned = filteredSections.filter(
      (section) => Boolean(section.lecturerId)
    ).length;

    const enrollment = filteredSections.reduce(
      (total, section) =>
        total +
        Number(section.currentEnrollment || 0),
      0
    );

    const capacity = filteredSections.reduce(
      (total, section) =>
        total +
        Number(section.maxCapacity || 0),
      0
    );

    return {
      total: filteredSections.length,
      assigned,
      enrollment,
      capacity,
    };
  }, [filteredSections]);

  // ----------------------------------------------------------
  // REFRESH LIST
  // ----------------------------------------------------------

  function refreshList() {
    setSuccess("");
    setError("");

    setRefreshKey((value) => value + 1);
  }

  // ----------------------------------------------------------
  // CLOSE MODAL
  // ----------------------------------------------------------

  function closeModal() {
    if (saving) {
      return;
    }

    setModal(null);
    setSelectedSection(null);
    setModalError("");
  }

  // ----------------------------------------------------------
  // OPEN CREATE
  // ----------------------------------------------------------

  function openCreate() {
    setSuccess("");
    setModalError("");
    setSelectedSection(null);

    setForm(
      createFormValues(
        null,
        selectedSemester ||
          semesters[0]?.semesterId ||
          ""
      )
    );

    setModal("create");
  }

  // ----------------------------------------------------------
  // OPEN VIEW
  // ----------------------------------------------------------

  async function openView(section) {
    setModal("view");
    setSelectedSection(section);
    setModalError("");
    setDetailLoading(true);

    try {
      const details =
        await fetchAdminClassSection(
          section.classSectionId
        );

      setSelectedSection(details);
    } catch (err) {
      setModalError(
        getErrorMessage(
          err,
          "Unable to load Class Section details."
        )
      );
    } finally {
      setDetailLoading(false);
    }
  }

  // ----------------------------------------------------------
  // OPEN UPDATE
  // ----------------------------------------------------------

  function openUpdate(section) {
    setSuccess("");
    setModalError("");

    setSelectedSection(section);

    setForm(
      createFormValues(section)
    );

    setModal("update");
  }

  // ----------------------------------------------------------
  // OPEN DELETE
  // ----------------------------------------------------------

  function openDelete(section) {
    setModalError("");
    setSelectedSection(section);
    setModal("delete");
  }

  // ----------------------------------------------------------
  // UPDATE FORM VALUE
  // ----------------------------------------------------------

  function changeForm(name, value) {
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    if (modalError) {
      setModalError("");
    }
  }

  // ----------------------------------------------------------
  // BUILD AND VALIDATE FORM PAYLOAD
  // ----------------------------------------------------------

  function buildPayload() {
    const capacityText =
      String(form.maxCapacity).trim();

    if (!/^[0-9]+$/.test(capacityText)) {
      throw new Error(
        "Maximum Capacity must be a positive integer."
      );
    }

    const maxCapacity =
      Number(capacityText);

    if (
      !Number.isSafeInteger(maxCapacity) ||
      maxCapacity <= 0
    ) {
      throw new Error(
        "Maximum Capacity must be a positive integer."
      );
    }

    if (
      modal === "update" &&
      selectedSection &&
      maxCapacity <
        Number(
          selectedSection.currentEnrollment || 0
        )
    ) {
      throw new Error(
        "Maximum Capacity cannot be lower than Current Enrollment."
      );
    }

    const room = form.room.trim();
    const dayOfWeek = form.dayOfWeek
      ? Number(form.dayOfWeek)
      : null;

    const startTime =
      form.startTime.trim();

    const endTime =
      form.endTime.trim();

    const hasAnySchedule = Boolean(
      room ||
      dayOfWeek ||
      startTime ||
      endTime
    );

    const hasFullSchedule = Boolean(
      room &&
      dayOfWeek &&
      startTime &&
      endTime
    );

    if (
      modal === "create" &&
      !hasFullSchedule
    ) {
      throw new Error(
        "Room, Day of Week, Start Time and End Time are required."
      );
    }

    if (
      hasAnySchedule &&
      !hasFullSchedule
    ) {
      throw new Error(
        "Room and Class Schedule must be provided together."
      );
    }

    if (
      hasFullSchedule &&
      endTime <= startTime
    ) {
      throw new Error(
        "End Time must be after Start Time."
      );
    }

    const scheduleFields = {
      maxCapacity,
      room: room || null,
      dayOfWeek,
      startTime: startTime || null,
      endTime: endTime || null,
    };

    if (modal === "update") {
      return scheduleFields;
    }

    const classCode =
      form.classCode.trim().toUpperCase();

    if (!classCode) {
      throw new Error(
        "Class Code is required."
      );
    }

    if (!form.courseId) {
      throw new Error(
        "Course is required."
      );
    }

    if (!form.semesterId) {
      throw new Error(
        "Semester is required."
      );
    }

    return {
      classCode,
      courseId: form.courseId,
      semesterId: form.semesterId,
      ...scheduleFields,
    };
  }

  // ----------------------------------------------------------
  // SUBMIT CREATE OR UPDATE
  // ----------------------------------------------------------

  async function handleSubmit(event) {
    event.preventDefault();

    if (saving) {
      return;
    }

    setModalError("");
    setSuccess("");

    try {
      const payload = buildPayload();

      setSaving(true);

      let response;

      if (modal === "create") {
        response =
          await createAdminClassSection(
            payload
          );
      } else if (
        modal === "update" &&
        selectedSection
      ) {
        response =
          await updateAdminClassSection(
            selectedSection.classSectionId,
            payload
          );
      } else {
        throw new Error(
          "Invalid Class Section operation."
        );
      }

      setModal(null);
      setSelectedSection(null);

      setSuccess(
        response.message ||
          "Class Section saved successfully."
      );

      setRefreshKey(
        (value) => value + 1
      );
    } catch (err) {
      setModalError(
        getErrorMessage(
          err,
          "Unable to save Class Section."
        )
      );
    } finally {
      setSaving(false);
    }
  }

  // ----------------------------------------------------------
  // CONFIRM DELETE
  // ----------------------------------------------------------

  async function handleDelete() {
    if (
      saving ||
      !selectedSection
    ) {
      return;
    }

    setSaving(true);
    setModalError("");
    setSuccess("");

    try {
      const response =
        await deleteAdminClassSection(
          selectedSection.classSectionId
        );

      setModal(null);
      setSelectedSection(null);

      setSuccess(
        response.message ||
          "Class Section deleted successfully."
      );

      setRefreshKey(
        (value) => value + 1
      );
    } catch (err) {
      setModalError(
        getErrorMessage(
          err,
          "Unable to delete Class Section."
        )
      );
    } finally {
      setSaving(false);
    }
  }

  // ==========================================================
  // RENDER PAGE
  // ==========================================================

  return (
    <div className="min-h-full bg-[#F7FAFF] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">

        {/* =============================================== */}
        {/* PAGE HEADER */}
        {/* =============================================== */}

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <div className="rounded-xl bg-[#E8F1FF] p-2.5 text-[#476FA9]">
                <CalendarDays size={23} />
              </div>

              <span className="text-xs font-semibold uppercase tracking-wider text-[#7395C3]">
                Administrator
              </span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-[#2F5488]">
              Class Section Management
            </h1>

            <p className="mt-2 max-w-2xl text-sm text-slate-500">
              Manage class sections, schedules,
              rooms and enrollment capacity.
              Lecturer assignments are managed separately.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={refreshList}
              className={SECONDARY_BUTTON}
            >
              <RefreshCw size={16} />
              Refresh
            </button>

            <button
              type="button"
              onClick={openCreate}
              disabled={
                optionsLoading ||
                courses.length === 0 ||
                semesters.length === 0
              }
              className={PRIMARY_BUTTON}
            >
              <Plus size={17} />
              Create Class Section
            </button>
          </div>
        </div>

        {/* =============================================== */}
        {/* ALERTS */}
        {/* =============================================== */}

        {error && (
          <Notice
            type="error"
            onDismiss={() => setError("")}
          >
            {error}
          </Notice>
        )}

        {success && (
          <Notice
            type="success"
            onDismiss={() => setSuccess("")}
          >
            {success}
          </Notice>
        )}

        {/* =============================================== */}
        {/* STATISTICS */}
        {/* =============================================== */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            icon={CalendarDays}
            label="Class Sections"
            value={statistics.total}
            tone="blue"
          />

          <StatCard
            icon={UserRound}
            label="Assigned Lecturers"
            value={statistics.assigned}
            tone="lavender"
          />

          <StatCard
            icon={Users}
            label="Current Enrollment"
            value={statistics.enrollment}
            tone="mint"
          />

          <StatCard
            icon={GraduationCap}
            label="Total Capacity"
            value={statistics.capacity}
            tone="peach"
          />
        </div>

        {/* =============================================== */}
        {/* FILTERS */}
        {/* =============================================== */}

        <div className="rounded-2xl border border-[#E3EBF6] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Search
              size={17}
              className="text-[#638EC5]"
            />

            <h2 className="text-sm font-semibold text-[#365B91]">
              Search and Filter
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">

            <div>
              <SectionLabel>
                Semester
              </SectionLabel>

              <select
                value={selectedSemester}
                onChange={(event) =>
                  setSelectedSemester(
                    event.target.value
                  )
                }
                className={INPUT_CLASS}
              >
                <option value="">
                  All Semesters
                </option>

                {semesters.map((semester) => (
                  <option
                    key={semester.semesterId}
                    value={semester.semesterId}
                  >
                    {semester.semesterName}
                    {" - "}
                    {semester.academicYear}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <SectionLabel>
                Course
              </SectionLabel>

              <select
                value={selectedCourse}
                onChange={(event) =>
                  setSelectedCourse(
                    event.target.value
                  )
                }
                className={INPUT_CLASS}
              >
                <option value="">
                  All Courses
                </option>

                {courses.map((course) => (
                  <option
                    key={course.courseId}
                    value={course.courseId}
                  >
                    {course.courseCode}
                    {" - "}
                    {course.courseName}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <SectionLabel>
                Search Class Section
              </SectionLabel>

              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-3 text-slate-400"
                />

                <input
                  type="text"
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value
                    )
                  }
                  placeholder="Class code, course, lecturer..."
                  className={`${INPUT_CLASS} pl-9`}
                />
              </div>
            </div>

          </div>
        </div>

        {/* =============================================== */}
        {/* TABLE */}
        {/* =============================================== */}

        <div className="overflow-hidden rounded-2xl border border-[#E3EBF6] bg-white shadow-sm">

          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E8EFF8] px-5 py-4">
            <div>
              <h2 className="text-base font-bold text-[#365B91]">
                Class Section List
              </h2>

              <p className="mt-1 text-xs text-slate-500">
                {filteredSections.length}
                {" "}
                section(s) found
              </p>
            </div>

            <button
              type="button"
              onClick={() =>
                navigate(
                  "/admin/assignlecturer"
                )
              }
              className={SECONDARY_BUTTON}
            >
              <UserRound size={16} />
              Assign Lecturer
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1000px] text-left text-sm">

              <thead className="bg-[#F2F7FE] text-xs font-semibold text-[#5879A6]">
                <tr>
                  <th className="px-5 py-4">
                    Class Section
                  </th>

                  <th className="px-4 py-4">
                    Course / Semester
                  </th>

                  <th className="px-4 py-4">
                    Lecturer
                  </th>

                  <th className="px-4 py-4">
                    Room / Schedule
                  </th>

                  <th className="px-4 py-4">
                    Enrollment
                  </th>

                  <th className="px-5 py-4 text-right">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-[#EDF2F9]">

                {loading ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-5 py-14 text-center text-slate-500"
                    >
                      Loading Class Sections...
                    </td>
                  </tr>
                ) : filteredSections.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-5 py-14 text-center"
                    >
                      <CalendarDays
                        size={32}
                        className="mx-auto mb-3 text-[#9CB8D9]"
                      />

                      <p className="font-medium text-slate-600">
                        No Class Sections found.
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        Try another filter or create a new section.
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredSections.map((section) => {
                    const enrolled = Number(
                      section.currentEnrollment || 0
                    );

                    const capacity = Number(
                      section.maxCapacity || 0
                    );

                    const percentage =
                      capacity > 0
                        ? Math.min(
                            100,
                            (enrolled / capacity) * 100
                          )
                        : 0;

                    const canDelete =
                      enrolled === 0;

                    return (
                      <tr
                        key={section.classSectionId}
                        className="transition hover:bg-[#FAFCFF]"
                      >
                        <td className="px-5 py-4 align-top">
                          <p className="font-semibold text-[#365B91]">
                            {section.classCode}
                          </p>

                          <p className="mt-1 text-xs text-slate-400">
                            {section.classSectionId}
                          </p>
                        </td>

                        <td className="px-4 py-4 align-top">
                          <p className="font-medium text-slate-700">
                            {section.courseCode}
                          </p>

                          <p className="mt-1 max-w-[220px] truncate text-xs text-slate-500">
                            {section.courseName}
                          </p>

                          <p className="mt-1 text-xs text-[#7895BC]">
                            {section.semesterName}
                          </p>
                        </td>

                        <td className="px-4 py-4 align-top">
                          {section.lecturerId ? (
                            <div>
                              <span
                                className={[
                                  "inline-flex items-center gap-1",
                                  "rounded-lg bg-[#E7F7F0]",
                                  "px-2 py-1 text-xs font-medium",
                                  "text-[#328469]",
                                ].join(" ")}
                              >
                                <CheckCircle2 size={12} />
                                Assigned
                              </span>

                              <p className="mt-2 text-xs text-slate-600">
                                {getLecturerLabel(section)}
                              </p>
                            </div>
                          ) : (
                            <span
                              className={[
                                "inline-flex items-center",
                                "rounded-lg bg-[#FFF3E6]",
                                "px-2 py-1 text-xs",
                                "font-medium text-[#B9854D]",
                              ].join(" ")}
                            >
                              Not assigned
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-4 align-top">
                          <p className="flex items-center gap-1 text-slate-700">
                            <MapPin size={13} />
                            {section.room || "No room"}
                          </p>

                          <p className="mt-2 flex items-start gap-1 text-xs text-slate-500">
                            <Clock3
                              size={13}
                              className="mt-0.5 shrink-0"
                            />

                            {formatSchedule(section)}
                          </p>
                        </td>

                        <td className="px-4 py-4 align-top">
                          <p className="text-sm font-semibold text-slate-700">
                            {enrolled}
                            <span className="font-normal text-slate-400">
                              {" / "}
                              {capacity}
                            </span>
                          </p>

                          <div className="mt-2 h-1.5 w-24 overflow-hidden rounded-full bg-[#E8EFF9]">
                            <div
                              className="h-full rounded-full bg-[#76A5DC]"
                              style={{
                                width: `${percentage}%`,
                              }}
                            />
                          </div>
                        </td>

                        <td className="px-5 py-4 align-top">
                          <div className="flex justify-end gap-1">

                            <button
                              type="button"
                              title="View Details"
                              aria-label={`View ${section.classCode}`}
                              onClick={() =>
                                openView(section)
                              }
                              className="rounded-lg p-2 text-[#5887C1] transition hover:bg-[#EBF3FF]"
                            >
                              <Eye size={17} />
                            </button>

                            <button
                              type="button"
                              title="Update Class Section"
                              aria-label={`Update ${section.classCode}`}
                              onClick={() =>
                                openUpdate(section)
                              }
                              className="rounded-lg p-2 text-[#5887C1] transition hover:bg-[#EBF3FF]"
                            >
                              <Pencil size={17} />
                            </button>

                            <button
                              type="button"
                              title={
                                canDelete
                                  ? "Delete Class Section"
                                  : "Cannot delete a section with enrolled students"
                              }
                              aria-label={`Delete ${section.classCode}`}
                              disabled={!canDelete}
                              onClick={() =>
                                openDelete(section)
                              }
                              className={[
                                "rounded-lg p-2",
                                "text-red-400 transition",
                                "hover:bg-red-50",
                                "disabled:cursor-not-allowed",
                                "disabled:opacity-30",
                              ].join(" ")}
                            >
                              <Trash2 size={17} />
                            </button>

                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* =============================================== */}
        {/* FOOTNOTE */}
        {/* =============================================== */}

        <div className="flex items-start gap-2 rounded-xl border border-[#DFEAF8] bg-[#EFF6FF] px-4 py-3 text-xs text-[#5C7EAA]">
          <ShieldCheck
            size={16}
            className="mt-0.5 shrink-0"
          />

          <p>
            Class Code, Course and Semester cannot be changed
            after creation. Lecturer assignments are managed
            through Assign Lecturer. Enrollment counts are
            maintained by the system.
          </p>
        </div>
      </div>

      {/* ================================================== */}
      {/* CREATE / UPDATE MODAL */}
      {/* ================================================== */}

      {(modal === "create" || modal === "update") && (
        <Modal
          title={
            modal === "create"
              ? "Create Class Section"
              : "Update Class Section"
          }
          description={
            modal === "create"
              ? "Enter the class section information."
              : "Update capacity, room and schedule only."
          }
          onClose={closeModal}
          disabled={saving}
        >
          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >

            {modalError && (
              <Notice type="error">
                {modalError}
              </Notice>
            )}

            {/* IDENTIFICATION */}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

              <div>
                <SectionLabel required>
                  Class Code
                </SectionLabel>

                <input
                  type="text"
                  maxLength={20}
                  value={form.classCode}
                  onChange={(event) =>
                    changeForm(
                      "classCode",
                      event.target.value
                    )
                  }
                  placeholder="Example: DBI101.04"
                  disabled={modal === "update"}
                  className={INPUT_CLASS}
                  required
                />
              </div>

              <div>
                <SectionLabel required>
                  Maximum Capacity
                </SectionLabel>

                <input
                  type="number"
                  min={1}
                  step={1}
                  value={form.maxCapacity}
                  onChange={(event) =>
                    changeForm(
                      "maxCapacity",
                      event.target.value
                    )
                  }
                  className={INPUT_CLASS}
                  required
                />
              </div>

              <div>
                <SectionLabel required>
                  Course
                </SectionLabel>

                <select
                  value={form.courseId}
                  onChange={(event) =>
                    changeForm(
                      "courseId",
                      event.target.value
                    )
                  }
                  disabled={modal === "update"}
                  className={INPUT_CLASS}
                  required
                >
                  <option value="">
                    Select Course
                  </option>

                  {courses.map((course) => (
                    <option
                      key={course.courseId}
                      value={course.courseId}
                    >
                      {course.courseCode}
                      {" - "}
                      {course.courseName}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <SectionLabel required>
                  Semester
                </SectionLabel>

                <select
                  value={form.semesterId}
                  onChange={(event) =>
                    changeForm(
                      "semesterId",
                      event.target.value
                    )
                  }
                  disabled={modal === "update"}
                  className={INPUT_CLASS}
                  required
                >
                  <option value="">
                    Select Semester
                  </option>

                  {semesters.map((semester) => (
                    <option
                      key={semester.semesterId}
                      value={semester.semesterId}
                    >
                      {semester.semesterName}
                      {" - "}
                      {semester.academicYear}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* SCHEDULE */}

            <div className="border-t border-[#E8EFF8] pt-5">
              <div className="mb-4 flex items-center gap-2">
                <Clock3
                  size={17}
                  className="text-[#648FC6]"
                />

                <h3 className="text-sm font-bold text-[#365B91]">
                  Room and Class Schedule
                </h3>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

                <div>
                  <SectionLabel required={modal === "create"}>
                    Room
                  </SectionLabel>

                  <input
                    type="text"
                    maxLength={30}
                    value={form.room}
                    onChange={(event) =>
                      changeForm(
                        "room",
                        event.target.value
                      )
                    }
                    placeholder="Example: D.A101"
                    className={INPUT_CLASS}
                    required={modal === "create"}
                  />
                </div>

                <div>
                  <SectionLabel required={modal === "create"}>
                    Day of Week
                  </SectionLabel>

                  <select
                    value={form.dayOfWeek}
                    onChange={(event) =>
                      changeForm(
                        "dayOfWeek",
                        event.target.value
                      )
                    }
                    className={INPUT_CLASS}
                    required={modal === "create"}
                  >
                    <option value="">
                      Select Day
                    </option>

                    {DAYS.map((day) => (
                      <option
                        key={day.value}
                        value={day.value}
                      >
                        {day.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <SectionLabel required={modal === "create"}>
                    Start Time
                  </SectionLabel>

                  <input
                    type="time"
                    value={form.startTime}
                    onChange={(event) =>
                      changeForm(
                        "startTime",
                        event.target.value
                      )
                    }
                    className={INPUT_CLASS}
                    required={modal === "create"}
                  />
                </div>

                <div>
                  <SectionLabel required={modal === "create"}>
                    End Time
                  </SectionLabel>

                  <input
                    type="time"
                    value={form.endTime}
                    onChange={(event) =>
                      changeForm(
                        "endTime",
                        event.target.value
                      )
                    }
                    className={INPUT_CLASS}
                    required={modal === "create"}
                  />
                </div>
              </div>
            </div>

            {/* BUSINESS NOTES */}

            <div className="rounded-xl border border-[#DFEAF7] bg-[#F3F8FF] p-4 text-xs text-[#5B7FAE]">
              <div className="flex items-start gap-2">
                <ShieldCheck
                  size={17}
                  className="shrink-0"
                />

                <div className="space-y-1">
                  {modal === "create" ? (
                    <>
                      <p>
                        Current Enrollment starts at 0.
                      </p>

                      <p>
                        No Lecturer is assigned during creation.
                      </p>
                    </>
                  ) : (
                    <>
                      <p>
                        Class Code, Course, Semester and Lecturer
                        remain unchanged.
                      </p>

                      <p>
                        Maximum Capacity cannot be lower than
                        Current Enrollment (
                        {selectedSection?.currentEnrollment ?? 0}
                        ).
                      </p>
                    </>
                  )}

                  <p>
                    Room and schedule conflicts are checked
                    before saving.
                  </p>
                </div>
              </div>
            </div>

            {/* FORM ACTIONS */}

            <div className="flex justify-end gap-3 border-t border-[#E8EFF8] pt-5">
              <button
                type="button"
                onClick={closeModal}
                disabled={saving}
                className={SECONDARY_BUTTON}
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={saving}
                className={PRIMARY_BUTTON}
              >
                {saving
                  ? "Saving..."
                  : modal === "create"
                    ? "Create Class Section"
                    : "Save Changes"}
              </button>
            </div>

          </form>
        </Modal>
      )}

      {/* ================================================== */}
      {/* VIEW MODAL */}
      {/* ================================================== */}

      {modal === "view" && (
        <Modal
          title="Class Section Details"
          description="View class section information and schedule."
          onClose={closeModal}
        >
          {modalError && (
            <div className="mb-4">
              <Notice type="error">
                {modalError}
              </Notice>
            </div>
          )}

          {detailLoading ? (
            <p className="py-10 text-center text-sm text-slate-500">
              Loading Class Section details...
            </p>
          ) : selectedSection ? (
            <div className="space-y-5">

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">

                <DetailItem
                  label="Class Section ID"
                  value={
                    selectedSection.classSectionId
                  }
                />

                <DetailItem
                  label="Class Code"
                  value={
                    selectedSection.classCode
                  }
                />

                <DetailItem
                  label="Course"
                  value={
                    `${selectedSection.courseCode} - ${selectedSection.courseName}`
                  }
                />

                <DetailItem
                  label="Semester"
                  value={
                    selectedSection.semesterName
                  }
                />

                <DetailItem
                  label="Assigned Lecturer"
                  value={
                    getLecturerLabel(
                      selectedSection
                    )
                  }
                />

                <DetailItem
                  label="Room"
                  value={
                    selectedSection.room ||
                    "Not assigned"
                  }
                />

                <DetailItem
                  label="Class Schedule"
                  value={
                    formatSchedule(
                      selectedSection
                    )
                  }
                />

                <DetailItem
                  label="Maximum Capacity"
                  value={
                    selectedSection.maxCapacity
                  }
                />

                <DetailItem
                  label="Current Enrollment"
                  value={
                    selectedSection.currentEnrollment
                  }
                />
              </div>

              <div className="flex flex-wrap justify-end gap-3 border-t border-[#E8EFF8] pt-5">
                <button
                  type="button"
                  onClick={closeModal}
                  className={SECONDARY_BUTTON}
                >
                  Close
                </button>

                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      "/admin/assignlecturer"
                    )
                  }
                  className={PRIMARY_BUTTON}
                >
                  <UserRound size={16} />
                  Assign Lecturer
                </button>
              </div>
            </div>
          ) : null}
        </Modal>
      )}

      {/* ================================================== */}
      {/* DELETE CONFIRMATION MODAL */}
      {/* ================================================== */}

      {modal === "delete" && selectedSection && (
        <Modal
          title="Delete Class Section"
          description="Confirm the deletion of this class section."
          onClose={closeModal}
          disabled={saving}
        >
          <div className="space-y-5">

            {modalError && (
              <Notice type="error">
                {modalError}
              </Notice>
            )}

            <div className="rounded-xl border border-red-100 bg-red-50 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle
                  size={21}
                  className="mt-0.5 shrink-0 text-red-500"
                />

                <div>
                  <p className="text-sm font-semibold text-red-700">
                    Are you sure you want to delete this Class Section?
                  </p>

                  <p className="mt-2 text-sm text-red-600">
                    Class Code:
                    {" "}
                    <strong>
                      {selectedSection.classCode}
                    </strong>
                  </p>

                  <p className="mt-1 text-xs text-red-500">
                    This action cannot be undone.
                    Sections linked to enrollment records
                    cannot be deleted.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={closeModal}
                disabled={saving}
                className={SECONDARY_BUTTON}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleDelete}
                disabled={saving}
                className={[
                  "inline-flex items-center gap-2",
                  "rounded-xl bg-red-500 px-4 py-2.5",
                  "text-sm font-semibold text-white",
                  "transition hover:bg-red-600",
                  "disabled:opacity-60",
                ].join(" ")}
              >
                <Trash2 size={16} />

                {saving
                  ? "Deleting..."
                  : "Confirm Delete"}
              </button>
            </div>
          </div>
        </Modal>
      )}

    </div>
  );
}

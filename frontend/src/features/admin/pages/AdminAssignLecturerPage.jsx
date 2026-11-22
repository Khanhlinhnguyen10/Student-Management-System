
import { useEffect, useMemo, useState } from "react";

import {
  AlertCircle,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  MapPin,
  RefreshCw,
  UserRound,
} from "lucide-react";

import {
  fetchAssignmentSemesters,
  fetchAssignmentSections,
  fetchAssignmentLecturers,
  submitLecturerAssignment,
} from "../api/adminAssignLecturerApi";

const FIELD =
  "mt-2 w-full rounded-xl border border-[#DBE7F5] bg-white px-4 py-3 " +
  "text-sm text-[#426180] outline-none transition focus:border-[#86B3E2] " +
  "focus:ring-4 focus:ring-[#DFEDFC] disabled:cursor-not-allowed disabled:bg-[#F3F6FA]";

const PANEL =
  "rounded-3xl border border-[#E1EBF7] bg-white p-5 shadow-sm md:p-6";

const DAYS = [
  "Mon", "Tue", "Wed", "Thu",
  "Fri", "Sat", "Sun",
];

const FULL_DAYS = [
  "Monday", "Tuesday", "Wednesday", "Thursday",
  "Friday", "Saturday", "Sunday",
];

const id = (value) =>
  value == null ? "" : String(value);

// ========================================
// DATE HELPERS
// ========================================

function isoDate(value) {
  const match = String(value ?? "").match(
    /^(\d{4}-\d{2}-\d{2})/
  );

  return match ? match[1] : "";
}

function fromIso(value) {
  const iso = isoDate(value);

  if (!iso) return null;

  const [year, month, day] =
    iso.split("-").map(Number);

  const date = new Date(
    Date.UTC(year, month - 1, day)
  );

  return Number.isNaN(date.getTime())
    ? null
    : date;
}

function toIso(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(value, days) {
  const date = fromIso(value);

  if (!date) return "";

  date.setUTCDate(
    date.getUTCDate() + days
  );

  return toIso(date);
}

function mondayOf(value) {
  const date = fromIso(value);

  if (!date) return "";

  const day = date.getUTCDay();

  return addDays(
    value,
    -(day === 0 ? 6 : day - 1)
  );
}

function mondayIndex(value) {
  const date = fromIso(value);

  if (!date) return -1;

  return (date.getUTCDay() + 6) % 7;
}

function dateText(value) {
  const match = isoDate(value).match(
    /^(\d{4})-(\d{2})-(\d{2})$/
  );

  if (!match) return "Date unavailable";

  const date = new Date(
    Date.UTC(
      Number(match[1]),
      Number(match[2]) - 1,
      Number(match[3])
    )
  );

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

function dayText(value) {
  const index = mondayIndex(value);

  return index < 0
    ? "Day unavailable"
    : FULL_DAYS[index];
}

function todayIso() {
  const now = new Date();

  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
  ].join("-");
}

function semesterLabel(item) {
  const name = String(
    item?.semesterName ?? ""
  ).trim();

  const year = String(
    item?.academicYear ?? ""
  ).trim();

  if (
    !year ||
    name.toLowerCase().includes(
      year.toLowerCase()
    )
  ) {
    return name || year;
  }

  return `${name} - ${year}`;
}

// ========================================
// TIMETABLE HELPERS
// ========================================

function clock(value) {
  return (
    String(value ?? "").match(
      /^(\d{1,2}:\d{2})/
    )?.[1] ?? "--:--"
  );
}

function minutes(value) {
  const match = String(value ?? "").match(
    /^(\d{1,2}):(\d{2})/
  );

  if (!match) return null;

  return (
    Number(match[1]) * 60 +
    Number(match[2])
  );
}

// SQL FINAL: Monday = 2, Tuesday = 3,
// ... Saturday = 7, Sunday = 1/8/0.

function sectionDayIndex(dayOfWeek) {
  if (
    dayOfWeek === null ||
    dayOfWeek === undefined ||
    dayOfWeek === ""
  ) {
    return -1;
  }

  const day = Number(dayOfWeek);

  if (day >= 2 && day <= 7) {
    return day - 2;
  }

  if (
    day === 1 ||
    day === 8 ||
    day === 0
  ) {
    return 6;
  }

  return -1;
}

function sectionWeekday(dayOfWeek) {
  const index = sectionDayIndex(dayOfWeek);

  return index < 0
    ? "Weekday unavailable"
    : FULL_DAYS[index];
}

function scheduled(section) {
  return (
    section?.dayOfWeek != null &&
    sectionDayIndex(
      section.dayOfWeek
    ) !== -1 &&
    minutes(section.startTime) !== null &&
    minutes(section.endTime) !== null
  );
}

function overlaps(first, second) {
  if (
    !scheduled(first) ||
    !scheduled(second)
  ) {
    return false;
  }

  return (
    sectionDayIndex(first.dayOfWeek) ===
      sectionDayIndex(second.dayOfWeek) &&
    minutes(first.startTime) <
      minutes(second.endTime) &&
    minutes(first.endTime) >
      minutes(second.startTime)
  );
}

// Each calendar date is a projected weekly
// meeting within the semester period.

function meetingOn(section, date, semester) {
  if (
    !scheduled(section) ||
    !date ||
    !semester
  ) {
    return false;
  }

  const start = isoDate(
    semester.startDate
  );

  const end = isoDate(
    semester.endDate
  );

  return Boolean(
    start &&
    end &&
    date >= start &&
    date <= end &&
    sectionDayIndex(section.dayOfWeek) ===
      mondayIndex(date)
  );
}

// ========================================
// SHARED UI COMPONENTS
// ========================================

function Notice({
  success = false,
  children,
}) {
  return (
    <div
      role={success ? "status" : "alert"}
      className={`flex gap-3 rounded-2xl border p-3 text-sm ${
        success
          ? "border-[#BCE6D7] bg-[#F0FBF6] text-[#397F67]"
          : "border-[#F1D7D2] bg-[#FFF7F5] text-[#A5605A]"
      }`}
    >
      {success ? (
        <CheckCircle2
          size={18}
          className="shrink-0"
        />
      ) : (
        <AlertCircle
          size={18}
          className="shrink-0"
        />
      )}

      <span>{children}</span>
    </div>
  );
}

function FormField({
  label,
  htmlFor,
  children,
  optional = false,
}) {
  return (
    <div>
      <label
        htmlFor={htmlFor}
        className="text-sm font-semibold text-[#5B7798]"
      >
        {label}{" "}
        {optional ? (
          <span className="text-xs font-normal text-[#91A3B7]">
            (optional)
          </span>
        ) : (
          <span className="text-rose-400">
            *
          </span>
        )}
      </label>

      {children}
    </div>
  );
}

// ========================================
// MAIN PAGE
// ========================================

export default function AdminAssignLecturerPage() {
  const [semesters, setSemesters] =
    useState([]);

  const [lecturers, setLecturers] =
    useState([]);

  const [sections, setSections] =
    useState([]);

  const [history, setHistory] =
    useState([]);

  const [semesterId, setSemesterId] =
    useState("");

  const [facultyId, setFacultyId] =
    useState("");

  const [courseCode, setCourseCode] =
    useState("");

  const [lecturerId, setLecturerId] =
    useState("");

  const [classSectionId, setClassSectionId] =
    useState("");

  const [weekdayFilter, setWeekdayFilter] =
    useState("");

  const [includeFaculty, setIncludeFaculty] =
    useState(false);

  const [showAssigned, setShowAssigned] =
    useState(false);

  const [loadingOptions, setLoadingOptions] =
    useState(true);

  const [loadingSections, setLoadingSections] =
    useState(false);

  const [loadingHistory, setLoadingHistory] =
    useState(false);

  const [historyPartial, setHistoryPartial] =
    useState(false);

  const [saving, setSaving] =
    useState(false);

  const [refreshKey, setRefreshKey] =
    useState(0);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [calendarMode, setCalendarMode] =
    useState("week");

  const [chosenDate, setChosenDate] =
    useState(todayIso());

  // ========================================
  // LOAD SEMESTERS AND LECTURERS
  // ========================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadOptions() {
      setLoadingOptions(true);
      setError("");

      try {
        const [
          semesterItems,
          lecturerItems,
        ] = await Promise.all([
          fetchAssignmentSemesters(
            controller.signal
          ),
          fetchAssignmentLecturers(
            controller.signal
          ),
        ]);

        if (controller.signal.aborted) {
          return;
        }

        setSemesters(semesterItems);
        setLecturers(lecturerItems);

        const today = todayIso();

        const current = semesterItems.find(
          (semester) =>
            isoDate(semester.startDate) &&
            isoDate(semester.endDate) &&
            isoDate(semester.startDate) <= today &&
            today <= isoDate(semester.endDate)
        );

        setSemesterId(
          id(current?.semesterId)
        );

        setChosenDate(
          current &&
          today >= isoDate(current.startDate) &&
          today <= isoDate(current.endDate)
            ? today
            : isoDate(current?.startDate) || today
        );
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err.message ||
              "Unable to load semesters or lecturers."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingOptions(false);
        }
      }
    }

    loadOptions();

    return () => controller.abort();
  }, []);

  // ========================================
  // LOAD CLASS SECTIONS
  // ========================================

  useEffect(() => {
    if (!semesterId) {
      setSections([]);
      setLoadingSections(false);

      return undefined;
    }

    const controller = new AbortController();

    async function loadSections() {
      setLoadingSections(true);

      try {
        const data =
          await fetchAssignmentSections(
            semesterId,
            controller.signal
          );

        if (!controller.signal.aborted) {
          setSections(data);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setSections([]);

          setError(
            err.message ||
              "Unable to load class sections."
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
  }, [semesterId, refreshKey]);

  // ========================================
  // LOAD TEACHING HISTORY
  // ========================================

  useEffect(() => {
    if (!semesters.length) {
      return undefined;
    }

    const controller = new AbortController();

    async function loadHistory() {
      setLoadingHistory(true);
      setHistoryPartial(false);

      try {
        const results =
          await Promise.allSettled(
            semesters.map((semester) =>
              fetchAssignmentSections(
                id(semester.semesterId),
                controller.signal
              )
            )
          );

        if (controller.signal.aborted) {
          return;
        }

        setHistory(
          results.flatMap((result) =>
            result.status === "fulfilled"
              ? result.value
              : []
          )
        );

        setHistoryPartial(
          results.some(
            (result) =>
              result.status === "rejected"
          )
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingHistory(false);
        }
      }
    }

    loadHistory();

    return () => controller.abort();
  }, [semesters, refreshKey]);

  // ========================================
  // SELECTED SEMESTER
  // ========================================

  const selectedSemester =
    semesters.find(
      (semester) =>
        id(semester.semesterId) === semesterId
    ) ?? null;

  // ========================================
  // FACULTIES
  // ========================================

  const faculties = useMemo(() => {
    const map = new Map();

    sections.forEach((section) => {
      const facultyId = id(
        section.courseFacultyId
      );

      if (
        facultyId &&
        !map.has(facultyId)
      ) {
        map.set(facultyId, {
          id: facultyId,
          name:
            section.courseFacultyName ||
            facultyId,
        });
      }
    });

    return [...map.values()].sort(
      (a, b) =>
        a.name.localeCompare(b.name)
    );
  }, [sections]);

  const selectedFaculty =
    faculties.find(
      (faculty) =>
        faculty.id === facultyId
    ) ?? null;

  // ========================================
  // COURSES BY FACULTY
  // ========================================

  const courses = useMemo(() => {
    const map = new Map();

    sections
      .filter(
        (section) =>
          id(section.courseFacultyId) ===
          facultyId
      )
      .forEach((section) => {
        const code = id(
          section.courseCode ||
          section.courseId
        );

        if (
          code &&
          !map.has(code)
        ) {
          map.set(code, {
            code,
            name:
              section.courseName ||
              code,
          });
        }
      });

    return [...map.values()].sort(
      (a, b) =>
        a.name.localeCompare(b.name)
    );
  }, [sections, facultyId]);

  const selectedCourse =
    courses.find(
      (course) =>
        course.code === courseCode
    ) ?? null;

  // ========================================
  // LECTURER TEACHING HISTORY
  // ========================================

  const knownTeacherIds = useMemo(() => {
    const taught = new Set();

    history.forEach((section) => {
      const sameCourse =
        id(
          section.courseCode ||
          section.courseId
        ) === courseCode;

      if (
        courseCode &&
        sameCourse &&
        section.lecturerId
      ) {
        taught.add(
          id(section.lecturerId)
        );
      }
    });

    return taught;
  }, [history, courseCode]);

  const availableLecturers = useMemo(() => {
    if (
      !selectedCourse ||
      !facultyId ||
      loadingHistory
    ) {
      return [];
    }

    return lecturers
      .filter(
        (lecturer) =>
          id(lecturer.facultyId) === facultyId &&
          (
            knownTeacherIds.has(
              id(lecturer.lecturerId)
            ) ||
            includeFaculty
          )
      )
      .sort((a, b) => {
        const aRank =
          knownTeacherIds.has(
            id(a.lecturerId)
          )
            ? 0
            : 1;

        const bRank =
          knownTeacherIds.has(
            id(b.lecturerId)
          )
            ? 0
            : 1;

        return (
          aRank - bRank ||
          String(a.fullName).localeCompare(
            String(b.fullName)
          )
        );
      });
  }, [
    lecturers,
    facultyId,
    selectedCourse,
    knownTeacherIds,
    includeFaculty,
    loadingHistory,
  ]);

  const selectedLecturer =
    availableLecturers.find(
      (lecturer) =>
        id(lecturer.lecturerId) === lecturerId
    ) ?? null;

  // ========================================
  // CURRENT TEACHING CLASSES
  // ========================================

  const teachingSections = useMemo(
    () =>
      sections
        .filter(
          (section) =>
            selectedLecturer &&
            id(section.lecturerId) ===
              id(selectedLecturer.lecturerId)
        )
        .sort(
          (a, b) =>
            Number(a.dayOfWeek) -
              Number(b.dayOfWeek) ||
            (minutes(a.startTime) ?? 0) -
              (minutes(b.startTime) ?? 0)
        ),
    [sections, selectedLecturer]
  );

  // ========================================
  // CLASS SECTIONS
  // ========================================

  const courseSections = sections.filter(
    (section) =>
      selectedCourse &&
      id(section.courseFacultyId) === facultyId &&
      id(
        section.courseCode ||
        section.courseId
      ) === courseCode
  );

  const validDays = [
    ...new Set(
      courseSections.map(
        (section) =>
          sectionDayIndex(
            section.dayOfWeek
          )
      )
    ),
  ]
    .filter((day) => day >= 0)
    .sort((a, b) => a - b);

  const filteredSections =
    courseSections.filter(
      (section) =>
        weekdayFilter === "" ||
        sectionDayIndex(
          section.dayOfWeek
        ) === Number(weekdayFilter)
    );

  const unassigned =
    filteredSections.filter(
      (section) =>
        !section.lecturerId
    );

  const assigned =
    filteredSections.filter(
      (section) =>
        Boolean(section.lecturerId)
    );

  const classOptions = [
    ...unassigned,
    ...(showAssigned ? assigned : []),
  ];

  const selectedSection =
    classOptions.find(
      (section) =>
        id(section.classSectionId) ===
        classSectionId
    ) ?? null;

  // ========================================
  // SCHEDULE CONFLICT CHECK
  // ========================================

  const conflicts =
    selectedSection &&
    selectedLecturer
      ? teachingSections.filter(
          (section) =>
            id(section.classSectionId) !==
              classSectionId &&
            overlaps(
              section,
              selectedSection
            )
        )
      : [];

  const unchanged = Boolean(
    selectedSection &&
    selectedLecturer &&
    id(selectedSection.lecturerId) ===
      id(selectedLecturer.lecturerId)
  );

  const canSubmit = Boolean(
    !loadingOptions &&
    !loadingSections &&
    !loadingHistory &&
    !saving &&
    selectedSemester &&
    selectedCourse &&
    selectedLecturer &&
    selectedSection &&
    scheduled(selectedSection) &&
    !unchanged &&
    conflicts.length === 0
  );

  // ========================================
  // CALENDAR DATA
  // ========================================

  const start = isoDate(
    selectedSemester?.startDate
  );

  const end = isoDate(
    selectedSemester?.endDate
  );

  const calendarReady =
    Boolean(start && end);

  const activeDate =
    calendarReady &&
    chosenDate >= start &&
    chosenDate <= end
      ? chosenDate
      : start;

  const weekStart =
    mondayOf(activeDate);

  const weekDays = Array.from(
    { length: 7 },
    (_, index) =>
      addDays(weekStart, index)
  );

  const monthDate =
    fromIso(activeDate);

  const monthStart = monthDate
    ? toIso(
        new Date(
          Date.UTC(
            monthDate.getUTCFullYear(),
            monthDate.getUTCMonth(),
            1
          )
        )
      )
    : "";

  const monthEnd = monthDate
    ? toIso(
        new Date(
          Date.UTC(
            monthDate.getUTCFullYear(),
            monthDate.getUTCMonth() + 1,
            0
          )
        )
      )
    : "";

  const monthGridStart =
    mondayOf(monthStart);

  const monthCells = monthGridStart
    ? Array.from(
        { length: 42 },
        (_, index) =>
          addDays(
            monthGridStart,
            index
          )
      )
    : [];

  const monthTitle = monthDate
    ? monthDate.toLocaleString("en-US", {
        month: "long",
        year: "numeric",
        timeZone: "UTC",
      })
    : "";

  function scheduleForDate(date) {
    return teachingSections.filter(
      (section) =>
        meetingOn(
          section,
          date,
          selectedSemester
        )
    );
  }

  const dayClasses =
    scheduleForDate(activeDate);

  const proposedOnDate = Boolean(
    selectedLecturer &&
    selectedSection &&
    !unchanged &&
    meetingOn(
      selectedSection,
      activeDate,
      selectedSemester
    )
  );

  // ========================================
  // CALENDAR NAVIGATION
  // ========================================

  function moveCalendar(step) {
    if (!calendarReady) {
      return;
    }

    if (calendarMode === "week") {
      const next = addDays(
        activeDate,
        step * 7
      );

      if (next < start) {
        setChosenDate(start);
      } else if (next > end) {
        setChosenDate(end);
      } else {
        setChosenDate(next);
      }
    } else {
      const date = fromIso(activeDate);

      const target = new Date(
        Date.UTC(
          date.getUTCFullYear(),
          date.getUTCMonth() + step,
          1
        )
      );

      const next = toIso(target);

      setChosenDate(
        next < start
          ? start
          : next > end
            ? end
            : next
      );
    }
  }

  // ========================================
  // FIELD HANDLERS
  // ========================================

  function clearMessages() {
    setError("");
    setSuccess("");
  }

  function changeSemester(next) {
    setSemesterId(next);
    setSections([]);

    setFacultyId("");
    setCourseCode("");
    setLecturerId("");
    setClassSectionId("");
    setWeekdayFilter("");

    setIncludeFaculty(false);
    setShowAssigned(false);

    clearMessages();

    const semester = semesters.find(
      (item) =>
        id(item.semesterId) === next
    );

    const today = todayIso();

    setChosenDate(
      semester &&
      isoDate(semester.startDate) <= today &&
      today <= isoDate(semester.endDate)
        ? today
        : isoDate(semester?.startDate) || today
    );
  }

  function changeFaculty(next) {
    setFacultyId(next);

    setCourseCode("");
    setLecturerId("");
    setClassSectionId("");
    setWeekdayFilter("");

    setIncludeFaculty(false);
    setShowAssigned(false);

    clearMessages();
  }

  function changeCourse(next) {
    setCourseCode(next);

    setLecturerId("");
    setClassSectionId("");
    setWeekdayFilter("");

    setIncludeFaculty(false);
    setShowAssigned(false);

    clearMessages();
  }

  function refresh() {
    setLecturerId("");
    setClassSectionId("");

    clearMessages();

    setRefreshKey(
      (value) => value + 1
    );
  }

  // ========================================
  // CONFIRM ASSIGNMENT
  // ========================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (!canSubmit) return;

    if (selectedSection.lecturerId) {
      const confirmed = window.confirm(
        `Reassign lecturer for class ${selectedSection.classCode}?\n\n` +
        `Current lecturer: ${
          selectedSection.lecturerName ||
          selectedSection.lecturerId
        }\n` +
        `New lecturer: ${
          selectedLecturer.fullName
        }\n\n` +
        "The previous assignment will be replaced."
      );

      if (!confirmed) return;
    }

    setSaving(true);
    clearMessages();

    try {
      const result =
        await submitLecturerAssignment({
          classSectionId:
            selectedSection.classSectionId,
          lecturerId:
            selectedLecturer.lecturerId,
        });

      setSuccess(
        result.message ||
          "Lecturer assigned successfully."
      );

      setShowAssigned(true);

      setRefreshKey(
        (value) => value + 1
      );
    } catch (err) {
      setError(
        err.message ||
          "Unable to assign lecturer."
      );
    } finally {
      setSaving(false);
    }
  }

  // ========================================
  // USER INTERFACE
  // ========================================

  return (
    <main className="min-h-full bg-[#F6FAFF] px-4 py-6 text-[#405C7B] md:px-8">
      <div className="mx-auto max-w-6xl space-y-5">

        {/* PAGE HEADER */}

        <header className="flex items-center justify-between gap-3">
          <div>
            <p className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#7EA0C5]">
              <GraduationCap size={15} />
              Administrator / Academic Management
            </p>

            <h1 className="text-2xl font-bold text-[#385876]">
              Assign Lecturer
            </h1>

            <p className="mt-1 text-sm text-[#8297B0]">
              Choose a faculty, course, and lecturer,
              then review the projected weekly
              or monthly schedule.
            </p>
          </div>

          <div className="rounded-2xl bg-[#E2EFFF] p-3 text-[#6698D1]">
            <BookOpen size={23} />
          </div>
        </header>

        {error && (
          <Notice>{error}</Notice>
        )}

        {success && (
          <Notice success>
            {success}
          </Notice>
        )}

        <div className="grid gap-5 lg:grid-cols-[0.93fr_1.07fr]">

          {/* LEFT: ASSIGNMENT FORM */}

          <form
            onSubmit={handleSubmit}
            className={`${PANEL} space-y-4`}
          >
            <div>
              <h2 className="text-lg font-bold text-[#43617F]">
                Assignment Details
              </h2>

              <p className="mt-1 text-xs text-[#8BA1BA]">
                Semester → Faculty → Course →
                Lecturer → Class Section
              </p>
            </div>

            {/* SEMESTER */}

            <FormField
              label="1. Semester"
              htmlFor="assign-semester"
            >
              <select
                id="assign-semester"
                className={FIELD}
                value={semesterId}
                onChange={(event) =>
                  changeSemester(
                    event.target.value
                  )
                }
                disabled={
                  loadingOptions || saving
                }
                required
              >
                <option value="">
                  Select semester
                </option>

                {semesters.map(
                  (semester) => (
                    <option
                      key={semester.semesterId}
                      value={semester.semesterId}
                    >
                      {semesterLabel(
                        semester
                      )}
                    </option>
                  )
                )}
              </select>

              {selectedSemester && (
                <p className="mt-2 text-xs text-[#7294B5]">
                  {dateText(start)}
                  {" - "}
                  {dateText(end)}
                </p>
              )}
            </FormField>

            {/* FACULTY */}

            <FormField
              label="2. Faculty"
              htmlFor="assign-faculty"
            >
              <select
                id="assign-faculty"
                className={FIELD}
                value={
                  selectedFaculty?.id || ""
                }
                onChange={(event) =>
                  changeFaculty(
                    event.target.value
                  )
                }
                disabled={
                  !semesterId ||
                  loadingSections ||
                  saving
                }
                required
              >
                <option value="">
                  Select faculty
                </option>

                {faculties.map(
                  (faculty) => (
                    <option
                      key={faculty.id}
                      value={faculty.id}
                    >
                      {faculty.name}
                    </option>
                  )
                )}
              </select>
            </FormField>

            {/* COURSE */}

            <FormField
              label="3. Course"
              htmlFor="assign-course"
            >
              <select
                id="assign-course"
                className={FIELD}
                value={
                  selectedCourse?.code || ""
                }
                onChange={(event) =>
                  changeCourse(
                    event.target.value
                  )
                }
                disabled={
                  !selectedFaculty ||
                  loadingSections ||
                  saving
                }
                required
              >
                <option value="">
                  Select course
                </option>

                {courses.map(
                  (course) => (
                    <option
                      key={course.code}
                      value={course.code}
                    >
                      {course.code}
                      {" - "}
                      {course.name}
                    </option>
                  )
                )}
              </select>
            </FormField>

            {/* LECTURER */}

            <FormField
              label="4. Lecturer"
              htmlFor="assign-lecturer"
            >
              <select
                id="assign-lecturer"
                className={FIELD}
                value={
                  selectedLecturer
                    ? lecturerId
                    : ""
                }
                onChange={(event) => {
                  setLecturerId(
                    event.target.value
                  );

                  setClassSectionId("");
                  clearMessages();
                }}
                disabled={
                  !selectedCourse ||
                  loadingHistory ||
                  saving
                }
                required
              >
                <option value="">
                  {loadingHistory
                    ? "Loading teaching history..."
                    : "Select lecturer"}
                </option>

                {availableLecturers.map(
                  (lecturer) => (
                    <option
                      key={lecturer.lecturerId}
                      value={lecturer.lecturerId}
                    >
                      {lecturer.fullName}

                      {knownTeacherIds.has(
                        id(lecturer.lecturerId)
                      )
                        ? " - Previously assigned to this course"
                        : " - Same faculty"}
                    </option>
                  )
                )}
              </select>

              {selectedCourse &&
                !loadingHistory && (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-[#7492B2]">
                      {
                        availableLecturers.filter(
                          (lecturer) =>
                            knownTeacherIds.has(
                              id(
                                lecturer.lecturerId
                              )
                            )
                        ).length
                      }{" "}
                      lecturer(s) from this faculty
                      have previously been assigned
                      to this course.
                    </p>

                    <label className="flex cursor-pointer items-start gap-2 text-xs text-[#6684A6]">
                      <input
                        type="checkbox"
                        checked={includeFaculty}
                        className="mt-0.5 accent-[#7EADE0]"
                        onChange={(event) => {
                          setIncludeFaculty(
                            event.target.checked
                          );

                          setLecturerId("");
                          setClassSectionId("");

                          clearMessages();
                        }}
                      />

                      <span>
                        Show other lecturers from
                        the same faculty
                        (for new assignments)
                      </span>
                    </label>

                    {historyPartial && (
                      <p className="text-xs text-[#B37B50]">
                        Teaching history is incomplete
                        because some semester records
                        could not be loaded.
                      </p>
                    )}
                  </div>
                )}
            </FormField>

            {/* WEEKDAY AND CLASS SECTION */}

            <div className="grid gap-3 sm:grid-cols-2">
              <FormField
                label="Filter by weekday"
                htmlFor="assign-day"
                optional
              >
                <select
                  id="assign-day"
                  className={FIELD}
                  value={weekdayFilter}
                  onChange={(event) => {
                    setWeekdayFilter(
                      event.target.value
                    );

                    setClassSectionId("");
                    clearMessages();
                  }}
                  disabled={
                    !selectedLecturer ||
                    saving
                  }
                >
                  <option value="">
                    All weekdays
                  </option>

                  {validDays.map(
                    (day) => (
                      <option
                        key={day}
                        value={day}
                      >
                        {DAYS[day]}
                      </option>
                    )
                  )}
                </select>
              </FormField>

              <FormField
                label="5. Class Section"
                htmlFor="assign-section"
              >
                <select
                  id="assign-section"
                  className={FIELD}
                  value={
                    selectedSection
                      ? classSectionId
                      : ""
                  }
                  onChange={(event) => {
                    setClassSectionId(
                      event.target.value
                    );

                    clearMessages();
                  }}
                  disabled={
                    !selectedLecturer ||
                    loadingSections ||
                    saving
                  }
                  required
                >
                  <option value="">
                    Select class section
                  </option>

                  {unassigned.map(
                    (section) => (
                      <option
                        key={section.classSectionId}
                        value={section.classSectionId}
                      >
                        {section.classCode}
                        {" · "}
                        {sectionWeekday(
                          section.dayOfWeek
                        )}
                        {" "}
                        {clock(
                          section.startTime
                        )}
                      </option>
                    )
                  )}

                  {showAssigned &&
                    assigned.map(
                      (section) => (
                        <option
                          key={
                            section.classSectionId
                          }
                          value={
                            section.classSectionId
                          }
                        >
                          {section.classCode}
                          {" · Assigned to: "}
                          {section.lecturerName ||
                            section.lecturerId}
                        </option>
                      )
                    )}
                </select>
              </FormField>
            </div>

            {/* REASSIGNMENT OPTION */}

            {selectedCourse && (
              <label className="flex cursor-pointer items-center gap-2 text-xs text-[#6885A3]">
                <input
                  type="checkbox"
                  className="accent-[#7EADE0]"
                  checked={showAssigned}
                  onChange={(event) => {
                    setShowAssigned(
                      event.target.checked
                    );

                    if (
                      !event.target.checked &&
                      selectedSection?.lecturerId
                    ) {
                      setClassSectionId("");
                    }

                    clearMessages();
                  }}
                />

                Include already assigned sections
                {" "}({assigned.length}) for
                reassignment when needed
              </label>
            )}

            {/* CLASS PREVIEW */}

            {selectedSection && (
              <div className="rounded-2xl bg-[#F3F8FF] p-3 text-xs leading-6 text-[#6785A7]">
                <b>
                  {selectedSection.classCode}
                </b>
                {" · "}
                {sectionWeekday(
                  selectedSection.dayOfWeek
                )}
                {", "}
                {clock(
                  selectedSection.startTime
                )}
                {"-"}
                {clock(
                  selectedSection.endTime
                )}

                <p>
                  Room:{" "}
                  {selectedSection.room || "TBD"}
                </p>

                <p>
                  Current lecturer:{" "}
                  {selectedSection.lecturerName ||
                    "Not assigned"}
                </p>
              </div>
            )}

            {/* SCHEDULE CONFLICT */}

            {conflicts.length > 0 && (
              <Notice>
                Schedule conflict with:{" "}
                {conflicts
                  .map(
                    (section) =>
                      `${section.classCode} (` +
                      `${sectionWeekday(
                        section.dayOfWeek
                      )}, ` +
                      `${clock(
                        section.startTime
                      )}-${clock(
                        section.endTime
                      )})`
                  )
                  .join(", ")}
                . Please choose a different
                lecturer or class section.
              </Notice>
            )}

            {/* CONFIRM ASSIGNMENT */}

{/* CONFIRM ASSIGNMENT */}

<div className="border-t border-[#EBF0F8] pt-5">
  <button
    type="submit"
    disabled={!canSubmit}
    className="
      flex w-full items-center justify-center gap-2
      rounded-xl bg-[#476FA9] px-4 py-3.5
      text-sm font-bold text-white
      shadow-[0_3px_8px_rgba(56,101,158,0.18)]
      transition-all duration-200
      hover:bg-[#3E6498]
      active:scale-[0.99]
      disabled:cursor-not-allowed
      disabled:bg-[#CBD9E9]
      disabled:shadow-none
      disabled:opacity-70
    "
  >
    {saving ? (
      <>
        <RefreshCw
          size={17}
          className="animate-spin"
        />
        Saving assignment...
      </>
    ) : unchanged ? (
      <>
        <CheckCircle2 size={17} />
        Already assigned
      </>
    ) : (
      <>
        <CheckCircle2 size={17} />
        Confirm Assignment
      </>
    )}
  </button>

  <p className="mt-2 text-center text-xs text-[#91A3B7]">
    Changes are saved only after confirmation.
    Flask checks teaching schedule conflicts
    before updating SQL Server.
  </p>
</div>



          </form>

          {/* RIGHT: LECTURER TIMETABLE */}

          <section
            className={`${PANEL} space-y-4`}
          >
            <div className="flex items-center justify-between gap-2">
              <div>
                <h2 className="text-lg font-bold text-[#43617F]">
                  Lecturer Teaching Schedule
                </h2>

                <p className="text-xs text-[#8BA1BA]">
                  Projected recurring timetable
                  during the selected semester
                </p>
              </div>

              <button
                type="button"
                onClick={refresh}
                disabled={
                  !semesterId ||
                  loadingSections ||
                  saving
                }
                title="Refresh data from SQL Server"
                className="rounded-xl border border-[#DFEAF7] p-2.5 text-[#759BC5] hover:bg-[#F0F6FF] disabled:opacity-50"
              >
                <RefreshCw
                  size={17}
                  className={
                    loadingSections
                      ? "animate-spin"
                      : ""
                  }
                />
              </button>
            </div>

            {/* SEMESTER SUMMARY */}

            {selectedSemester && (
              <div className="rounded-2xl bg-[#EDF5FF] p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-[#7D9BBE]">
                  {semesterLabel(
                    selectedSemester
                  )}
                </p>

                <p className="mt-1 text-sm text-[#52789F]">
                  {dateText(start)}
                  {" - "}
                  {dateText(end)}
                </p>

                {selectedLecturer && (
                  <p className="mt-3 flex items-center gap-2 text-sm font-bold text-[#41688D]">
                    <UserRound size={17} />
                    {selectedLecturer.fullName}
                  </p>
                )}
              </div>
            )}

            {/* TIMETABLE EMPTY STATE */}

            {!selectedLecturer ? (
              <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-[#D7E5F5] bg-[#FAFCFF] p-6 text-center text-sm text-[#819DB8]">
                <CalendarDays
                  size={33}
                  className="mb-3 text-[#94B6D8]"
                />

                Select a faculty, course, and lecturer
                to view the teaching schedule
                by date and time.
              </div>
            ) : !calendarReady ? (
              <Notice>
                Semester start and end dates are
                unavailable, so the calendar
                cannot be generated.
              </Notice>
            ) : (
              <>
                {/* CALENDAR CONTROLS */}

                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex rounded-xl bg-[#F2F7FD] p-1 text-xs font-semibold">
                    <button
                      type="button"
                      onClick={() =>
                        setCalendarMode("week")
                      }
                      className={`rounded-lg px-3 py-2 ${
                        calendarMode === "week"
                          ? "bg-white text-[#497AB0] shadow-sm"
                          : "text-[#8299B2]"
                      }`}
                    >
                      Week
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setCalendarMode("month")
                      }
                      className={`rounded-lg px-3 py-2 ${
                        calendarMode === "month"
                          ? "bg-white text-[#497AB0] shadow-sm"
                          : "text-[#8299B2]"
                      }`}
                    >
                      Month
                    </button>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-semibold text-[#55799F]">
                    <button
                      type="button"
                      onClick={() =>
                        moveCalendar(-1)
                      }
                      className="rounded-lg border border-[#DDE8F5] p-2 hover:bg-[#F4F8FF]"
                      title="Previous period"
                    >
                      <ChevronLeft size={16} />
                    </button>

                    <span className="min-w-28 text-center">
                      {calendarMode === "week"
                        ? `${dateText(
                            weekDays[0]
                          )} - ${dateText(
                            weekDays[6]
                          )}`
                        : monthTitle}
                    </span>

                    <button
                      type="button"
                      onClick={() =>
                        moveCalendar(1)
                      }
                      className="rounded-lg border border-[#DDE8F5] p-2 hover:bg-[#F4F8FF]"
                      title="Next period"
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>

                {/* WEEK VIEW */}

                {calendarMode === "week" ? (
                  <div className="grid grid-cols-7 gap-1.5">
                    {weekDays.map(
                      (date, index) => {
                        const count =
                          scheduleForDate(
                            date
                          ).length;

                        const within =
                          date >= start &&
                          date <= end;

                        return (
                          <button
                            key={date}
                            type="button"
                            disabled={!within}
                            onClick={() =>
                              setChosenDate(date)
                            }
                            className={`relative rounded-xl border px-1 py-3 text-center transition ${
                              date === activeDate
                                ? "border-[#78ACDD] bg-[#E0EFFD] text-[#346C9C]"
                                : within
                                  ? "border-[#E4EDF7] bg-[#F7FAFE] text-[#6886A7] hover:bg-[#EDF5FF]"
                                  : "border-[#F1F4F8] bg-[#FAFBFD] text-[#C0CEDD]"
                            }`}
                          >
                            <span className="block text-[10px] font-semibold">
                              {DAYS[index]}
                            </span>

                            <span className="mt-1 block text-base font-bold">
                              {
                                fromIso(
                                  date
                                ).getUTCDate()
                              }
                            </span>

                            {within &&
                              count > 0 && (
                                <span className="mx-auto mt-1 block w-fit rounded-full bg-[#B9DBF6] px-1.5 text-[10px] text-[#3975A8]">
                                  {count}
                                </span>
                              )}
                          </button>
                        );
                      }
                    )}
                  </div>
                ) : (
                  /* MONTH VIEW */

                  <div className="overflow-hidden rounded-xl border border-[#E3ECF7]">
                    <div className="grid grid-cols-7 bg-[#F2F7FE] text-center text-xs font-semibold text-[#7391B2]">
                      {DAYS.map(
                        (day) => (
                          <span
                            key={day}
                            className="py-2"
                          >
                            {day}
                          </span>
                        )
                      )}
                    </div>

                    <div className="grid grid-cols-7 gap-px bg-[#E3ECF7]">
                      {monthCells.map(
                        (date) => {
                          const inMonth =
                            date >= monthStart &&
                            date <= monthEnd;

                          const within =
                            date >= start &&
                            date <= end;

                          const count =
                            scheduleForDate(
                              date
                            ).length;

                          return (
                            <button
                              type="button"
                              key={date}
                              disabled={!within}
                              onClick={() =>
                                setChosenDate(
                                  date
                                )
                              }
                              className={`min-h-14 bg-white p-1 text-left text-xs transition ${
                                date === activeDate
                                  ? "bg-[#E1F0FD]"
                                  : within
                                    ? "hover:bg-[#F2F8FF]"
                                    : "opacity-40"
                              }`}
                            >
                              <span
                                className={
                                  inMonth
                                    ? "text-[#57789B]"
                                    : "text-[#B1C3D5]"
                                }
                              >
                                {
                                  fromIso(
                                    date
                                  ).getUTCDate()
                                }
                              </span>

                              {within &&
                                count > 0 && (
                                  <span className="mt-1 block rounded bg-[#DCEEFE] px-1 py-0.5 text-center text-[10px] text-[#477BAD]">
                                    {count}{" "}
                                    {count === 1
                                      ? "class"
                                      : "classes"}
                                  </span>
                                )}
                            </button>
                          );
                        }
                      )}
                    </div>
                  </div>
                )}

                {/* SELECTED DAY DETAILS */}

                <div className="space-y-3 border-t border-[#E8EFF8] pt-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-bold text-[#44698F]">
                      {dayText(activeDate)}
                      {", "}
                      {dateText(activeDate)}
                    </h3>

                    <span className="text-xs text-[#86A0BC]">
                      {dayClasses.length}
                      {" "}
                      {dayClasses.length === 1
                        ? "assigned class"
                        : "assigned classes"}
                    </span>
                  </div>

                  {dayClasses.length === 0 &&
                    !proposedOnDate && (
                      <p className="rounded-xl bg-[#F7FAFE] p-4 text-xs text-[#8CA3BB]">
                        No teaching classes scheduled
                        for the selected date.
                      </p>
                    )}

                  {/* SAVED CLASSES */}

                  {dayClasses.map(
                    (section) => (
                      <article
                        key={
                          section.classSectionId
                        }
                        className="rounded-2xl border border-[#E0EBF8] bg-[#FAFCFF] p-4"
                      >
                        <p className="mb-2 flex items-center gap-2 text-xs font-semibold text-[#5C8BB9]">
                          <CalendarDays size={14} />

                          {dayText(activeDate)}
                          {", "}
                          {dateText(activeDate)}
                          {" · "}
                          {clock(
                            section.startTime
                          )}
                          {"-"}
                          {clock(
                            section.endTime
                          )}
                        </p>

                        <p className="font-bold text-[#476A94]">
                          {section.courseName}

                          <span className="font-normal text-[#7998B7]">
                            {" · "}
                            {section.classCode}
                          </span>
                        </p>

                        <p className="mt-2 flex items-center gap-1 text-xs text-[#819DB8]">
                          <MapPin size={13} />

                          Room:{" "}
                          {section.room || "TBD"}
                        </p>
                      </article>
                    )
                  )}

                  {/* UNSAVED PROPOSED CLASS */}

                  {proposedOnDate && (
                    <article className="rounded-2xl border border-dashed border-[#81B5D8] bg-[#F0F9FF] p-4">
                      <p className="mb-2 text-xs font-bold text-[#397EAF]">
                        PROPOSED ASSIGNMENT
                        {" · "}
                        NOT SAVED
                      </p>

                      <p className="text-xs font-semibold text-[#5C8BB9]">
                        {dayText(activeDate)}
                        {", "}
                        {dateText(activeDate)}
                        {" · "}
                        {clock(
                          selectedSection.startTime
                        )}
                        {"-"}
                        {clock(
                          selectedSection.endTime
                        )}
                      </p>

                      <p className="mt-2 font-bold text-[#476A94]">
                        {selectedSection.courseName}
                        {" · "}
                        {selectedSection.classCode}
                      </p>

                      <p className="mt-1 text-xs text-[#819DB8]">
                        Room:{" "}
                        {selectedSection.room || "TBD"}
                      </p>
                    </article>
                  )}
                </div>

                {/* ASSIGNMENT PREVIEW */}

                {selectedSection && (
                  <div className="rounded-2xl bg-[#F3F8FF] p-3 text-xs leading-6 text-[#6B8AA9]">
                    <p>
                      <b>Proposed class:</b>{" "}
                      {selectedSection.classCode}
                      {" · "}
                      {sectionWeekday(
                        selectedSection.dayOfWeek
                      )}
                      {", "}
                      {clock(
                        selectedSection.startTime
                      )}
                      {"-"}
                      {clock(
                        selectedSection.endTime
                      )}
                    </p>

                    <p>
                      <b>Current lecturer:</b>{" "}
                      {selectedSection.lecturerName ||
                        "Not assigned"}
                    </p>
                  </div>
                )}

                {/* IMPORTANT SCHEDULE NOTE */}

                <p className="text-[11px] leading-relaxed text-[#91A7BE]">
                  Calendar dates are projected from
                  the weekly schedule and semester
                  dates in SQL Server. Holidays,
                  cancellations, make-up classes,
                  and one-off changes are not included.
                </p>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

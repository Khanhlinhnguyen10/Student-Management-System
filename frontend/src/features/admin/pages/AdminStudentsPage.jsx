
import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Pencil,
  Save,
  Trash2,
  X,
} from "lucide-react";
import {
  deleteStudent,
  fetchStudentById,
  fetchStudents,
  updateStudent,
} from "../api/adminStudentApi";
import { useAuth } from "../../auth/context/AuthContext";
import { fetchCreateAccountMajors } from "../api/adminCreateAccountApi";

const PAGE_SIZE = 10;

const EMPTY_FORM = {
  citizenId: "",
  fullName: "",
  dateOfBirth: "",
  email: "",
  gender: "",
  phoneNumber: "",
  majorId: "",
  academicStatus: "",
};

function formFromStudent(student) {
  return {
    ...Object.fromEntries(
      Object.keys(EMPTY_FORM).map((field) => [
        field,
        student[field] ?? "",
      ])
    ),
    dateOfBirth: (student.dateOfBirth ?? "").slice(0, 10),
  };
}

function validateStudent(form) {
  if (!form.citizenId.trim()) return "Citizen ID is required.";
  if (form.citizenId.trim().length > 12) {
    return "Citizen ID must not exceed 12 characters.";
  }
  if (!form.fullName.trim()) return "Full Name is required.";
  if (form.fullName.trim().length > 200) {
    return "Full Name must not exceed 200 characters.";
  }
  if (!form.majorId) return "Please select a major.";
  if (!form.academicStatus.trim()) {
    return "Academic Status is required.";
  }
  if (form.academicStatus.trim().length > 60) {
    return "Academic Status must not exceed 60 characters.";
  }
  if (
    form.email.trim() &&
    !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())
  ) {
    return "Invalid email address.";
  }
  return "";
}

function EditField({ label, name, form, onChange, required = false,
  type = "text", maxLength }) {
  return (
    <label className="block min-w-0 space-y-1.5">
      <span className="text-xs font-semibold text-[#45678F]">
        {label}{required && <span className="ml-1 text-[#BB5265]">*</span>}
      </span>
      <input
        name={name}
        type={type}
        value={form[name]}
        maxLength={maxLength}
        required={required}
        onChange={(event) => onChange(name, event.target.value)}
        className="h-10 w-full rounded-lg border border-[#CEDFF1] bg-[#F9FCFF] px-3 text-sm text-[#365D91] outline-none focus:border-[#7DA8DA] focus:ring-2 focus:ring-[#E0EEFC]"
      />
    </label>
  );
}

function SearchIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m16 16 5 5" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M2 12s3.5-6 10-6s10 6 10 6s-3.5 6-10 6S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function maskCitizenId(value) {
  if (!value) return "-";

  const text = String(value);

  if (text.length <= 6) return "••••••";

  return `${text.slice(0, 3)}••••••${text.slice(-3)}`;
}

function getInitials(name = "") {
  const words = name.trim().split(/\s+/).filter(Boolean);

  return words
    .slice(-2)
    .map((word) => word.charAt(0))
    .join("")
    .toUpperCase();
}

function StatusBadge({ status }) {
  const label = status?.trim() || "Unknown";
  const normalized = label.toLowerCase();

  const classes =
    normalized === "active"
      ? "bg-[#D7F8EE] text-[#087767]"
      : normalized === "on leave"
        ? "bg-[#EDF0FA] text-[#5D6482]"
        : "bg-[#FFF0DF] text-[#98611F]";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${classes}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

function DetailField({ label, value }) {
  return (
    <div className="border-b border-[#EEF0F8] py-3 sm:grid sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-4">
      <dt className="text-sm text-[#727B8D]">{label}</dt>

      <dd className="mt-1 break-words text-sm font-medium text-[#243653] sm:mt-0">
        {value || "-"}
      </dd>
    </div>
  );
}

export default function AdminStudentsPage() {
  const { refreshUser } = useAuth();

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [students, setStudents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selected, setSelected] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [panelMode, setPanelMode] = useState("view");
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [majors, setMajors] = useState([]);
  const [saving, setSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [mutationError, setMutationError] = useState("");
  const [mutationSuccess, setMutationSuccess] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  const detailsController = useRef(null);
  const panelRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();

    setLoading(true);
    setError("");

    fetchStudents({
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      search,
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted) return;

        setStudents(data.items || []);
        setTotal(data.total || 0);

        // Refresh the client-side view of the SQL session expiry.
        void refreshUser();
      })
      .catch((err) => {
        if (controller.signal.aborted) return;

        setStudents([]);
        setTotal(0);

        setError(
          err.status === 403
            ? "Bạn không có quyền xem danh sách sinh viên."
            : err.message || "Không thể tải dữ liệu sinh viên."
        );

        if (err.status === 401) {
          void refreshUser();
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [page, search, refreshUser, reloadKey]);

  useEffect(() => {
    return () => detailsController.current?.abort();
  }, []);

  useEffect(() => {
    if (selected) {
      panelRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [selected, panelMode]);

  function closeDetails() {
    if (saving) return;
    detailsController.current?.abort();
    setSelected(null);
    setDetailsLoading(false);
    setDetailError("");
    setPanelMode("view");
  }

  function submitSearch(event) {
    event.preventDefault();

    closeDetails();
    setPage(1);
    setSearch(searchInput.trim());
  }

  function changePage(nextPage) {
    closeDetails();
    setPage(nextPage);
  }

  async function openDetails(studentId, mode = "view") {
    if (saving || deleting) return;
    detailsController.current?.abort();

    const controller = new AbortController();
    detailsController.current = controller;

    setSelected(null);
    setPanelMode(mode);
    setDetailsLoading(true);
    setDetailError("");
    setMutationError("");
    setMutationSuccess("");

    try {
      const [response, options] = await Promise.all([
        fetchStudentById(studentId, controller.signal),
        mode === "edit"
          ? fetchCreateAccountMajors({ signal: controller.signal })
          : Promise.resolve([]),
      ]);

      if (controller.signal.aborted) return;

      setSelected(response.student);
      setForm(formFromStudent(response.student));
      setMajors(options);
      void refreshUser();
    } catch (err) {
      if (controller.signal.aborted) return;
      setDetailError(
        err.message || "Unable to load student information."
      );
      if (err.status === 401) void refreshUser();
    } finally {
      if (!controller.signal.aborted) setDetailsLoading(false);
    }
  }

  function changeForm(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setMutationError("");
  }

  async function handleSave(event) {
    event.preventDefault();
    if (!selected || panelMode !== "edit" || saving) return;

    const validationError = validateStudent(form);
    if (validationError) {
      setMutationError(validationError);
      return;
    }

    setSaving(true);
    setMutationError("");
    setMutationSuccess("");

    const optional = (value) => value.trim() || null;
    const payload = {
      citizenId: form.citizenId.trim(),
      fullName: form.fullName.trim(),
      dateOfBirth: form.dateOfBirth || null,
      email: optional(form.email),
      gender: optional(form.gender),
      phoneNumber: optional(form.phoneNumber),
      majorId: form.majorId,
      academicStatus: form.academicStatus.trim(),
    };

    try {
      const response = await updateStudent(selected.studentId, payload);
      setSelected(response.student);
      setPanelMode("view");
      setMutationSuccess("Student record updated successfully.");
      setReloadKey((current) => current + 1);
    } catch (err) {
      setMutationError(err.message || "Unable to update student record.");
      if (err.status === 401) void refreshUser();
    } finally {
      setSaving(false);
    }
  }

  function openDelete(student) {
    if (saving || deleting) return;
    detailsController.current?.abort();
    setDetailsLoading(false);
    setDeleteTarget(student);
    setDeleteError("");
    setMutationError("");
    setMutationSuccess("");
  }

  async function confirmDelete() {
    if (!deleteTarget || deleting) return;
    const targetId = deleteTarget.studentId;
    setDeleting(true);
    setDeleteError("");

    try {
      await deleteStudent(targetId);
      setDeleteTarget(null);
      if (selected?.studentId === targetId) closeDetails();
      setMutationSuccess(`Student ${targetId} deleted successfully.`);
      if (page > 1 && students.length === 1) {
        setPage((current) => current - 1);
      } else {
        setReloadKey((current) => current + 1);
      }
    } catch (err) {
      setDeleteError(err.message || "Unable to delete student record.");
      if (err.status === 401) void refreshUser();
    } finally {
      setDeleting(false);
    }
  }

  const totalPages = Math.max(
    1,
    Math.ceil(total / PAGE_SIZE)
  );

  const firstRow =
    total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

  const lastRow = Math.min(
    page * PAGE_SIZE,
    total
  );

  const firstVisiblePage = Math.max(
    1,
    Math.min(page - 2, totalPages - 4)
  );

  const visiblePages = Array.from(
    { length: Math.min(5, totalPages) },
    (_, index) => firstVisiblePage + index
  );

  return (
    <main>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-[#092B70]">
          Students
        </h1>

        <p className="mt-1 text-sm text-[#697181]">
          Manage student records.
        </p>
      </div>

      <form
        onSubmit={submitSearch}
        className="rounded-xl bg-white p-3 shadow-sm sm:p-4"
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex min-w-0 flex-1 items-center gap-2.5 rounded-lg bg-[#F7F7FD] px-3 py-2.5 text-[#8390A7]">
            <SearchIcon />

            <label htmlFor="student-search" className="sr-only">
              Tìm theo mã hoặc tên sinh viên
            </label>

            <input
              id="student-search"
              type="search"
              value={searchInput}
              onChange={(event) =>
                setSearchInput(event.target.value)
              }
              placeholder="Search student name or ID..."
              maxLength={100}
              className="min-w-0 flex-1 bg-transparent text-sm text-[#253451] outline-none placeholder:text-[#9196A5]"
            />
          </div>

          <button
            type="submit"
            className="rounded-lg bg-[#092B70] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#203E8C]"
          >
            Search
          </button>
        </div>
      </form>

      {mutationSuccess && (
        <div role="status" className="mt-4 flex items-center gap-2 rounded-lg border border-[#C9E8D8] bg-[#EFFAF4] px-4 py-3 text-sm text-[#287052]">
          <CheckCircle2 size={18} />
          {mutationSuccess}
        </div>
      )}

      <section
        aria-label="Student records"
        aria-busy={loading}
        className="mt-4 overflow-hidden rounded-xl border border-[#EEF0F7] bg-white shadow-sm"
      >
        <div className="border-b border-[#EEF0F7] px-5 py-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-bold text-[#1B2E53]">
              Student List
            </h2>

            <span className="text-xs text-[#7C8597]">
              {total} students
            </span>
          </div>
        </div>

        {error ? (
          <div
            role="alert"
            className="m-5 rounded-lg bg-red-50 p-4 text-sm text-red-700"
          >
            {error}
          </div>
        ) : loading ? (
          <p className="p-6 text-sm text-[#768197]">
            Loading student records...
          </p>
        ) : students.length === 0 ? (
          <p className="p-6 text-sm text-[#768197]">
            No student records found.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1060px] text-left text-xs">
              <thead className="bg-[#F0F2FC] text-[#4D5669]">
                <tr className="uppercase tracking-wide">
                  <th scope="col" className="px-4 py-3 font-bold">
                    Student ID
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Full Name
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Citizen ID
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Faculty
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Major
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 font-bold">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-[#EDF0F7]">
                {students.map((student) => (
                  <tr
                    key={student.studentId}
                    className="hover:bg-[#FAFBFF]"
                  >
                    <td className="whitespace-nowrap px-4 py-3.5 font-bold text-[#203E8C]">
                      {student.studentId}
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex min-w-40 items-center gap-2.5">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#DCE7FF] text-[10px] font-bold text-[#2859BD]">
                          {getInitials(student.fullName)}
                        </span>

                        <span className="font-semibold text-[#27344C]">
                          {student.fullName}
                        </span>
                      </div>
                    </td>

                    <td className="whitespace-nowrap px-4 py-3.5 font-mono text-[#697181]">
                      {maskCitizenId(student.citizenId)}
                    </td>

                    <td className="px-4 py-3.5 text-[#4F5A6D]">
                      {student.facultyName}
                    </td>

                    <td className="px-4 py-3.5 font-medium text-[#33435F]">
                      {student.majorName}
                    </td>

                    <td className="px-4 py-3.5">
                      <StatusBadge status={student.academicStatus} />
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-1.5 whitespace-nowrap">
                        <button
                          type="button"
                          disabled={saving || deleting}
                          onClick={() => openDetails(student.studentId)}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 font-semibold text-[#173D8B] hover:bg-[#EBF0FD] disabled:opacity-50"
                          aria-label={`View ${student.fullName}`}
                        >
                          <EyeIcon /> View
                        </button>
                        <button
                          type="button"
                          disabled={saving || deleting}
                          onClick={() => openDetails(student.studentId, "edit")}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 font-semibold text-[#346A9D] hover:bg-[#E5F2FE] disabled:opacity-50"
                          aria-label={`Edit ${student.fullName}`}
                        >
                          <Pencil size={14} /> Edit
                        </button>
                        <button
                          type="button"
                          disabled={saving || deleting}
                          onClick={() => openDelete(student)}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 font-semibold text-[#B13D51] hover:bg-[#FFF0F2] disabled:opacity-50"
                          aria-label={`Delete ${student.fullName}`}
                        >
                          <Trash2 size={14} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#EDF0F7] px-5 py-4">
          <p className="text-xs text-[#697181]">
            Showing {firstRow}-{lastRow} of {total} students
          </p>

          <nav
            aria-label="Student records pagination"
            className="flex flex-wrap items-center gap-1"
          >
            <button
              type="button"
              disabled={page === 1 || loading}
              onClick={() => changePage(page - 1)}
              className="rounded-md px-3 py-2 text-xs text-[#657086] hover:bg-[#F2F4FB] disabled:opacity-35"
            >
              Previous
            </button>

            {visiblePages.map((number) => (
              <button
                key={number}
                type="button"
                disabled={loading}
                onClick={() => changePage(number)}
                aria-current={
                  page === number ? "page" : undefined
                }
                className={`h-8 w-8 rounded-md text-xs font-semibold ${
                  page === number
                    ? "bg-[#092B70] text-white"
                    : "text-[#647084] hover:bg-[#F2F4FB]"
                }`}
              >
                {number}
              </button>
            ))}

            <button
              type="button"
              disabled={page === totalPages || loading}
              onClick={() => changePage(page + 1)}
              className="rounded-md px-3 py-2 text-xs text-[#657086] hover:bg-[#F2F4FB] disabled:opacity-35"
            >
              Next
            </button>
          </nav>
        </div>
      </section>

      {detailsLoading && (
        <p
          role="status"
          className="mt-5 text-sm text-[#697181]"
        >
          Loading student details...
        </p>
      )}

      {detailError && (
        <p
          role="alert"
          className="mt-5 rounded-lg bg-red-50 p-4 text-sm text-red-700"
        >
          {detailError}
        </p>
      )}

      {selected && (
        <section
          ref={panelRef}
          aria-label={panelMode === "edit" ? "Edit student" : "Student details"}
          className="mt-6 rounded-xl border border-[#EDF0F7] bg-white p-5 shadow-sm sm:p-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDF0F7] pb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#5974B0]">
                {panelMode === "edit" ? "Edit Student" : "Student Profile"}
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#092B70]">
                {selected.fullName}
              </h2>
            </div>

            <button
              type="button"
              onClick={closeDetails}
              disabled={saving}
              className="rounded-lg border border-[#DDE3EF] px-4 py-2 text-sm font-medium text-[#4E5D75] hover:bg-[#F7F8FC] disabled:opacity-50"
            >
              Close
            </button>
          </div>

          {mutationSuccess && (
            <p role="status" className="mt-4 rounded-lg bg-[#EFFAF4] p-3 text-sm text-[#287052]">
              {mutationSuccess}
            </p>
          )}
          {mutationError && (
            <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {mutationError}
            </p>
          )}

          {panelMode === "edit" ? (
            <form onSubmit={handleSave} className="mt-5 space-y-4">
              <p className="text-xs text-[#697181]">
                Student ID: <strong>{selected.studentId}</strong> (read-only).
                Faculty follows the selected Major.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                <EditField label="Citizen ID Number" name="citizenId"
                  form={form} onChange={changeForm} maxLength={12} required />
                <EditField label="Full Name" name="fullName"
                  form={form} onChange={changeForm} maxLength={200} required />
                <EditField label="Date of Birth" name="dateOfBirth"
                  type="date" form={form} onChange={changeForm} />
                <EditField label="Email" name="email" type="email"
                  form={form} onChange={changeForm} maxLength={100} />
                <EditField label="Gender" name="gender"
                  form={form} onChange={changeForm} maxLength={20} />
                <EditField label="Phone Number" name="phoneNumber" type="tel"
                  form={form} onChange={changeForm} maxLength={15} />
                <label className="block min-w-0 space-y-1.5">
                  <span className="text-xs font-semibold text-[#45678F]">
                    Major <span className="text-[#BB5265]">*</span>
                  </span>
                  <select
                    value={form.majorId}
                    required
                    onChange={(event) => changeForm("majorId", event.target.value)}
                    className="h-10 w-full rounded-lg border border-[#CEDFF1] bg-[#F9FCFF] px-3 text-sm text-[#365D91] outline-none focus:border-[#7DA8DA]"
                  >
                    <option value="">Select a major</option>
                    {form.majorId && !majors.some((m) => m.majorId === form.majorId) && (
                      <option value={form.majorId}>Current Major - {selected.majorName}</option>
                    )}
                    {majors.map((major) => (
                      <option key={major.majorId} value={major.majorId}>
                        {major.majorName} - {major.facultyName}
                      </option>
                    ))}
                  </select>
                </label>
                <EditField label="Academic Status" name="academicStatus"
                  form={form} onChange={changeForm} maxLength={60} required />
              </div>
              <div className="flex justify-end gap-2 border-t border-[#EDF0F7] pt-4">
                <button type="button" disabled={saving}
                  onClick={() => { setPanelMode("view"); setMutationError(""); }}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#DDE3EF] px-4 py-2 text-sm font-semibold text-[#536981] disabled:opacity-50">
                  <X size={15} /> Cancel
                </button>
                <button type="submit" disabled={saving}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#729FD6] px-4 py-2 text-sm font-semibold text-white hover:bg-[#5D8CC8] disabled:opacity-50">
                  <Save size={15} /> {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          ) : (
          <dl className="mt-2">
            <DetailField
              label="Student ID"
              value={selected.studentId}
            />
            <DetailField
              label="Citizen ID Number"
              value={selected.citizenId}
            />
            <DetailField
              label="Full Name"
              value={selected.fullName}
            />
            <DetailField
              label="Date of Birth"
              value={selected.dateOfBirth}
            />
            <DetailField
              label="Email"
              value={selected.email}
            />
            <DetailField
              label="Gender"
              value={selected.gender}
            />
            <DetailField
              label="Phone Number"
              value={selected.phoneNumber}
            />
            <DetailField
              label="Faculty"
              value={selected.facultyName}
            />
            <DetailField
              label="Major"
              value={selected.majorName}
            />

            <div className="border-b border-[#EEF0F8] py-3 sm:grid sm:grid-cols-[180px_minmax(0,1fr)] sm:gap-4">
              <dt className="text-sm text-[#727B8D]">
                Academic Status
              </dt>

              <dd className="mt-1 sm:mt-0">
                <StatusBadge status={selected.academicStatus} />
              </dd>
            </div>
          </dl>
          )}
        </section>
      )}

      {deleteTarget && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#1B294A]/50 p-4"
          role="presentation"
        >
          <section role="dialog" aria-modal="true" aria-labelledby="delete-student-title"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center gap-2 text-[#B13D51]">
              <AlertTriangle size={21} />
              <h2 id="delete-student-title" className="text-lg font-bold">
                Confirm Delete Student
              </h2>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#42546D]">
              Are you sure you want to delete <strong>{deleteTarget.fullName}</strong>
              {" "}(ID: <strong>{deleteTarget.studentId}</strong>)?
            </p>
            <p className="mt-2 text-xs leading-5 text-[#8A5962]">
              This action cannot be undone. Students with enrollment or
              semester-result records are protected and cannot be deleted.
            </p>
            {deleteError && (
              <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {deleteError}
              </p>
            )}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" disabled={deleting}
                onClick={() => { setDeleteTarget(null); setDeleteError(""); }}
                className="rounded-lg border border-[#DDE3EF] px-4 py-2 text-sm font-semibold text-[#4E5D75] disabled:opacity-50">
                Cancel
              </button>
              <button type="button" disabled={deleting} onClick={confirmDelete}
                className="inline-flex items-center gap-2 rounded-lg bg-[#C05262] px-4 py-2 text-sm font-semibold text-white hover:bg-[#AD3E50] disabled:opacity-50">
                <Trash2 size={15} /> {deleting ? "Deleting..." : "Delete Student"}
              </button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}

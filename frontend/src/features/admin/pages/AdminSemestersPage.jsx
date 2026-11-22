
import { useEffect, useMemo, useState } from "react";

import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  Eye,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  createAdminSemester,
  deleteAdminSemester,
  fetchAdminSemesters,
  updateAdminSemester,
} from "../api/adminSemestersApi";

// =========================================
// FORM CONFIGURATION
// =========================================

const EMPTY_FORM = {
  semesterName: "",
  academicYear: "",
  startDate: "",
  endDate: "",
};

const INPUT_STYLE =
  "mt-1.5 w-full rounded-xl border border-[#D4E3F4] " +
  "bg-white px-3.5 py-2.5 text-sm text-[#385B82] " +
  "outline-none focus:border-[#82B0E3] " +
  "focus:ring-2 focus:ring-[#E1EFFC] " +
  "disabled:bg-[#F2F5FA]";

// =========================================
// HELPERS
// =========================================

function formatDate(value) {
  if (!value) return "-";

  const [year, month, day] = value.split("-");

  return `${day}/${month}/${year}`;
}

function hasAcademicLinks(semester) {
  return (
    Number(semester.classSectionCount || 0) > 0 ||
    Number(semester.semesterResultCount || 0) > 0
  );
}

// =========================================
// MAIN PAGE
// =========================================

export default function AdminSemestersPage() {
  const [semesters, setSemesters] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [refreshKey, setRefreshKey] = useState(0);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formMode, setFormMode] = useState(null);
  const [editingId, setEditingId] = useState("");

  const [viewing, setViewing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  // =========================================
  // LOAD SEMESTERS
  // =========================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadSemesters() {
      setLoading(true);

      try {
        const records = await fetchAdminSemesters({
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setSemesters(records);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err.message || "Unable to load semesters."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadSemesters();

    return () => controller.abort();
  }, [refreshKey]);

  // =========================================
  // SEARCH
  // =========================================

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return semesters;

    return semesters.filter((semester) =>
      [
        semester.semesterId,
        semester.semesterName,
        semester.academicYear,
      ].some((value) =>
        String(value || "")
          .toLowerCase()
          .includes(term)
      )
    );
  }, [semesters, search]);

  // =========================================
  // CREATE
  // =========================================

  function openCreate() {
    setFormMode("create");
    setEditingId("");
    setForm({ ...EMPTY_FORM });
    setViewing(null);
    setError("");
    setSuccess("");
  }

  // =========================================
  // EDIT
  // =========================================

  function openEdit(semester) {
    setFormMode("edit");
    setEditingId(semester.semesterId);

    setForm({
      semesterName: semester.semesterName,
      academicYear: semester.academicYear,
      startDate: semester.startDate,
      endDate: semester.endDate,
    });

    setViewing(null);
    setError("");
    setSuccess("");
  }

  // =========================================
  // CANCEL
  // =========================================

  function closeForm() {
    if (busy) return;

    setFormMode(null);
    setEditingId("");
    setForm({ ...EMPTY_FORM });
  }

  // =========================================
  // SAVE FORM
  // =========================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (busy || !formMode) return;

    setError("");
    setSuccess("");

    if (form.endDate <= form.startDate) {
      setError(
        "End Date must be after Start Date."
      );
      return;
    }

    setBusy(true);

    try {
      const response =
        formMode === "create"
          ? await createAdminSemester(form)
          : await updateAdminSemester(
              editingId,
              form
            );

      setSuccess(
        response.message ||
          "Semester saved successfully."
      );

      setFormMode(null);
      setEditingId("");
      setForm({ ...EMPTY_FORM });

      setRefreshKey((n) => n + 1);
    } catch (err) {
      setError(
        err.message || "Unable to save semester."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // DELETE SEMESTER
  // =========================================

  async function handleDelete(semester) {
    if (busy) return;

    setError("");
    setSuccess("");

    if (hasAcademicLinks(semester)) {
      setError(
        "This semester is linked to class sections " +
        "or academic results and cannot be deleted."
      );
      return;
    }

    const confirmed = window.confirm(
      `Delete ${semester.semesterName} ` +
        `(${semester.academicYear})?\n\n` +
        "This action cannot be undone."
    );

    if (!confirmed) return;

    setBusy(true);

    try {
      const response = await deleteAdminSemester(
        semester.semesterId
      );

      setSuccess(
        response.message ||
          "Semester deleted successfully."
      );

      if (
        viewing?.semesterId === semester.semesterId
      ) {
        setViewing(null);
      }

      setRefreshKey((n) => n + 1);
    } catch (err) {
      setError(
        err.message || "Unable to delete semester."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // RENDER
  // =========================================

  return (
    <div className="space-y-5 pb-6">
      {/* PAGE HEADER */}
      <section className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E4F1FD] to-[#F3F0FC] p-5">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-[#476FA9] shadow-sm">
            <CalendarDays size={22} />
          </div>

          <div>
            <h1 className="text-xl font-bold text-[#365D91]">
              Semester Management
            </h1>

            <p className="text-xs text-[#718DA9]">
              Create, view, configure and delete academic semesters.
            </p>
          </div>
        </div>

        <button
          type="button"
          disabled={busy}
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-xl bg-[#476FA9] px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-[#3E6498] disabled:opacity-50"
        >
          <Plus size={17} />
          Create Semester
        </button>
      </section>

      {/* ERROR MESSAGE */}
      {error && (
        <p
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-[#F2D1D1] bg-[#FFF7F6] px-4 py-3 text-sm text-[#A64A4A]"
        >
          <AlertCircle
            size={17}
            className="shrink-0"
          />
          {error}
        </p>
      )}

      {/* SUCCESS MESSAGE */}
      {success && (
        <p
          role="status"
          className="flex items-center gap-2 rounded-xl border border-[#CEE9DC] bg-[#F0FAF5] px-4 py-3 text-sm text-[#387966]"
        >
          <CheckCircle2 size={17} />
          {success}
        </p>
      )}

      {/* SEMESTER TABLE */}
      <section className="rounded-2xl border border-[#DFEAF6] bg-white p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full max-w-sm">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7B98B7]"
            />

            <input
              type="search"
              placeholder="Search semester, academic year or ID"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              className="w-full rounded-xl border border-[#D4E3F4] bg-[#F9FBFF] py-2.5 pl-9 pr-3 text-sm text-[#365D91] outline-none focus:border-[#82B0E3]"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-[#8197B0]">
              {filtered.length} semester(s)
            </span>

            <button
              type="button"
              disabled={loading || busy}
              onClick={() => {
                setError("");
                setRefreshKey((n) => n + 1);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[#E8F2FC] px-3 py-2 text-xs font-semibold text-[#476FA9] hover:bg-[#DCEBFA] disabled:opacity-50"
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
          <table className="w-full min-w-[860px] text-left text-xs">
            <thead className="bg-[#EAF3FD] text-[#446B98]">
              <tr>
                <th className="rounded-l-lg px-3 py-3">
                  Semester
                </th>
                <th className="px-3 py-3">
                  Academic Year
                </th>
                <th className="px-3 py-3">
                  Start Date
                </th>
                <th className="px-3 py-3">
                  End Date
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
              {filtered.map((semester) => (
                <tr
                  key={semester.semesterId}
                  className="hover:bg-[#F8FBFF]"
                >
                  <td className="px-3 py-3">
                    <div className="font-semibold text-[#365D91]">
                      {semester.semesterName}
                    </div>

                    <div className="mt-1 text-[10px] text-[#91A6BC]">
                      {semester.semesterId}
                    </div>
                  </td>

                  <td className="px-3 py-3 text-[#5A7797]">
                    {semester.academicYear}
                  </td>

                  <td className="px-3 py-3 text-[#5A7797]">
                    {formatDate(semester.startDate)}
                  </td>

                  <td className="px-3 py-3 text-[#5A7797]">
                    {formatDate(semester.endDate)}
                  </td>

                  <td className="px-3 py-3 text-[#5A7797]">
                    <div>
                      {semester.classSectionCount} class section(s)
                    </div>

                    <div className="mt-1 text-[10px]">
                      {semester.semesterResultCount} result(s)
                    </div>
                  </td>

                  <td className="px-3 py-3">
                    <div className="flex justify-center gap-1.5">
                      {/* VIEW */}
                      <button
                        type="button"
                        title="View"
                        disabled={busy}
                        onClick={() => {
                          setViewing(semester);
                          setFormMode(null);
                        }}
                        className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                      >
                        <Eye size={15} />
                      </button>

                      {/* EDIT */}
                      <button
                        type="button"
                        title="Configure"
                        disabled={busy}
                        onClick={() =>
                          openEdit(semester)
                        }
                        className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                      >
                        <Pencil size={15} />
                      </button>

                      {/* DELETE */}
                      <button
                        type="button"
                        title={
                          hasAcademicLinks(semester)
                            ? "Linked academic data - deletion not allowed"
                            : "Delete"
                        }
                        disabled={
                          busy ||
                          hasAcademicLinks(semester)
                        }
                        onClick={() =>
                          handleDelete(semester)
                        }
                        className="rounded-lg bg-[#FFF1EE] p-2 text-[#B96657] hover:bg-[#FFE2DD] disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {!loading && filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-8 text-center text-[#859AB0]"
                  >
                    No semesters found.
                  </td>
                </tr>
              )}

              {loading && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-8 text-center text-[#859AB0]"
                  >
                    Loading semesters...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* VIEW SEMESTER DETAILS */}
      {viewing && !formMode && (
        <section className="rounded-2xl border border-[#DCE9F7] bg-white p-5 shadow-sm">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-bold text-[#365D91]">
              Semester Details
            </h2>

            <button
              type="button"
              onClick={() => setViewing(null)}
              className="text-[#7D94AC]"
              aria-label="Close details"
            >
              <X size={18} />
            </button>
          </div>

          <div className="grid gap-3 text-sm text-[#5A7797] sm:grid-cols-2 lg:grid-cols-3">
            <p>
              <strong>Semester ID:</strong>{" "}
              {viewing.semesterId}
            </p>

            <p>
              <strong>Semester Name:</strong>{" "}
              {viewing.semesterName}
            </p>

            <p>
              <strong>Academic Year:</strong>{" "}
              {viewing.academicYear}
            </p>

            <p>
              <strong>Start Date:</strong>{" "}
              {formatDate(viewing.startDate)}
            </p>

            <p>
              <strong>End Date:</strong>{" "}
              {formatDate(viewing.endDate)}
            </p>

            <p>
              <strong>Linked Records:</strong>{" "}
              {Number(viewing.classSectionCount) +
                Number(viewing.semesterResultCount)}
            </p>
          </div>
        </section>
      )}

      {/* CREATE / CONFIGURE FORM */}
      {formMode && (
        <section className="rounded-2xl border border-[#DCE9F7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-[#365D91]">
                {formMode === "create"
                  ? "Create Semester"
                  : "Configure Semester"}
              </h2>

              {formMode === "edit" && (
                <p className="text-xs text-[#8AA1B8]">
                  {editingId}
                </p>
              )}
            </div>

            <button
              type="button"
              disabled={busy}
              onClick={closeForm}
              className="text-[#7891AD] disabled:opacity-50"
              aria-label="Close form"
            >
              <X size={19} />
            </button>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              {/* SEMESTER NAME */}
              <label className="text-xs font-semibold text-[#466C98]">
                Semester Name *
                <input
                  required
                  maxLength={50}
                  value={form.semesterName}
                  className={INPUT_STYLE}
                  placeholder="2027-2028 Semester 1"
                  onChange={(event) =>
                    setForm((old) => ({
                      ...old,
                      semesterName: event.target.value,
                    }))
                  }
                />
              </label>

              {/* ACADEMIC YEAR */}
              <label className="text-xs font-semibold text-[#466C98]">
                Academic Year *
                <input
                  required
                  maxLength={9}
                  value={form.academicYear}
                  className={INPUT_STYLE}
                  placeholder="2027-2028"
                  pattern="[0-9]{4}-[0-9]{4}"
                  onChange={(event) =>
                    setForm((old) => ({
                      ...old,
                      academicYear: event.target.value,
                    }))
                  }
                />
              </label>

              {/* START DATE */}
              <label className="text-xs font-semibold text-[#466C98]">
                Start Date *
                <input
                  required
                  type="date"
                  value={form.startDate}
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    setForm((old) => ({
                      ...old,
                      startDate: event.target.value,
                    }))
                  }
                />
              </label>

              {/* END DATE */}
              <label className="text-xs font-semibold text-[#466C98]">
                End Date *
                <input
                  required
                  type="date"
                  min={form.startDate || undefined}
                  value={form.endDate}
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    setForm((old) => ({
                      ...old,
                      endDate: event.target.value,
                    }))
                  }
                />
              </label>
            </div>

            <p className="text-xs text-[#8BA1B7]">
              End Date must be after Start Date.
              Semester Name must be unique.
            </p>

            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-xl bg-[#476FA9] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#3E6498] disabled:opacity-50"
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
                    ? "Create Semester"
                    : "Save Changes"}
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={closeForm}
                className="rounded-xl bg-[#EDF2F8] px-5 py-2.5 text-sm font-semibold text-[#607A98] hover:bg-[#E0EAF6] disabled:opacity-50"
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

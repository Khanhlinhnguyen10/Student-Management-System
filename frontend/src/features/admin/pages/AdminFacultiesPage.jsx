
import { useEffect, useMemo, useState } from "react";

import {
  AlertCircle,
  Building2,
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
  createAdminFaculty,
  deleteAdminFaculty,
  fetchAdminFaculties,
  updateAdminFaculty,
} from "../api/adminFacultiesApi";

// =========================================
// CONSTANTS
// =========================================

const EMPTY_FORM = {
  facultyCode: "",
  facultyName: "",
  email: "",
  phoneNumber: "",
};

const INPUT_STYLE =
  "mt-1.5 w-full rounded-xl border border-[#D4E3F4] " +
  "bg-white px-3.5 py-2.5 text-sm text-[#385B82] " +
  "outline-none transition focus:border-[#82B0E3] " +
  "focus:ring-2 focus:ring-[#E1EFFC] " +
  "disabled:cursor-not-allowed disabled:bg-[#F2F5FA]";

const PRIMARY_BUTTON =
  "inline-flex items-center justify-center gap-2 " +
  "rounded-xl bg-[#476FA9] px-4 py-2.5 " +
  "text-sm font-semibold text-white " +
  "transition hover:bg-[#3E6498] " +
  "disabled:cursor-not-allowed disabled:opacity-50";

const SECONDARY_BUTTON =
  "inline-flex items-center justify-center gap-2 " +
  "rounded-xl bg-[#E8F2FC] px-4 py-2.5 " +
  "text-sm font-semibold text-[#476FA9] " +
  "transition hover:bg-[#DCEBFA] " +
  "disabled:cursor-not-allowed disabled:opacity-50";

// =========================================
// HELPERS
// =========================================

function hasAcademicLinks(faculty) {
  return (
    Number(faculty.majorCount || 0) > 0 ||
    Number(faculty.lecturerCount || 0) > 0 ||
    Number(faculty.courseCount || 0) > 0
  );
}

function safeText(value) {
  return value == null || value === ""
    ? "-"
    : String(value);
}

function LinkCount({ count, label }) {
  return (
    <div className="text-[11px] leading-5 text-[#6783A3]">
      <span className="font-bold text-[#476FA9]">
        {Number(count || 0)}
      </span>{" "}
      {label}
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div className="rounded-xl bg-[#F5F9FF] p-3">
      <p className="text-[11px] font-semibold text-[#8BA0B8]">
        {label}
      </p>

      <p className="mt-1 break-words text-sm font-semibold text-[#466989]">
        {safeText(value)}
      </p>
    </div>
  );
}

// =========================================
// MAIN PAGE
// =========================================

export default function AdminFacultiesPage() {
  const [faculties, setFaculties] = useState([]);
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [refreshKey, setRefreshKey] = useState(0);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formMode, setFormMode] = useState(null);
  const [editingId, setEditingId] = useState("");

  const [form, setForm] = useState(EMPTY_FORM);
  const [viewing, setViewing] = useState(null);

  // =========================================
  // FETCH FACULTIES
  // =========================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadFaculties() {
      setLoading(true);
      setError("");

      try {
        const records = await fetchAdminFaculties({
          signal: controller.signal,
        });

        if (controller.signal.aborted) return;

        setFaculties(records);
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(
            err.message ||
              "Unable to load faculties."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadFaculties();

    return () => controller.abort();
  }, [refreshKey]);

  // =========================================
  // SEARCH
  // =========================================

  const filtered = useMemo(() => {
    const keyword = search
      .trim()
      .toLowerCase();

    if (!keyword) return faculties;

    return faculties.filter((faculty) =>
      [
        faculty.facultyId,
        faculty.facultyCode,
        faculty.facultyName,
        faculty.email,
        faculty.phoneNumber,
      ].some((value) =>
        String(value ?? "")
          .toLowerCase()
          .includes(keyword)
      )
    );
  }, [faculties, search]);

  // =========================================
  // CREATE FORM
  // =========================================

  function openCreate() {
    if (busy) return;

    setFormMode("create");
    setEditingId("");
    setForm({ ...EMPTY_FORM });
    setViewing(null);
    setError("");
    setSuccess("");
  }

  // =========================================
  // UPDATE FORM
  // =========================================

  function openEdit(faculty) {
    if (busy) return;

    setFormMode("edit");
    setEditingId(faculty.facultyId);

    setForm({
      facultyCode: faculty.facultyCode,
      facultyName: faculty.facultyName,
      email: faculty.email || "",
      phoneNumber: faculty.phoneNumber || "",
    });

    setViewing(null);
    setError("");
    setSuccess("");
  }

  // =========================================
  // VIEW DETAILS
  // =========================================

  function openView(faculty) {
    if (busy) return;

    setViewing(faculty);
    setFormMode(null);
    setError("");
    setSuccess("");
  }

  // =========================================
  // CLOSE FORM
  // =========================================

  function closeForm() {
    if (busy) return;

    setFormMode(null);
    setEditingId("");
    setForm({ ...EMPTY_FORM });
  }

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  // =========================================
  // SAVE FACULTY
  // =========================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (busy || !formMode) return;

    setError("");
    setSuccess("");

    const isCreating = formMode === "create";

    const payload = isCreating
      ? {
          facultyCode: form.facultyCode
            .trim()
            .toUpperCase(),
          facultyName: form.facultyName.trim(),
          email: form.email.trim(),
          phoneNumber: form.phoneNumber.trim(),
        }
      : {
          facultyName: form.facultyName.trim(),
          email: form.email.trim(),
          phoneNumber: form.phoneNumber.trim(),
        };

    setBusy(true);

    try {
      const response = isCreating
        ? await createAdminFaculty(payload)
        : await updateAdminFaculty(
            editingId,
            payload
          );

      setSuccess(
        response.message ||
          "Faculty saved successfully."
      );

      setFormMode(null);
      setEditingId("");
      setForm({ ...EMPTY_FORM });

      setRefreshKey((number) => number + 1);
    } catch (err) {
      setError(
        err.message ||
          "Unable to save faculty."
      );
    } finally {
      setBusy(false);
    }
  }

  // =========================================
  // DELETE FACULTY
  // =========================================

  async function handleDelete(faculty) {
    if (busy) return;

    setError("");
    setSuccess("");

    if (hasAcademicLinks(faculty)) {
      setError(
        "Cannot delete a faculty linked " +
          "to majors, lecturers or courses."
      );
      return;
    }

    const confirmed = window.confirm(
      `Delete ${faculty.facultyName} ` +
        `(${faculty.facultyCode})?\n\n` +
        "This action cannot be undone."
    );

    if (!confirmed) return;

    setBusy(true);

    try {
      const response = await deleteAdminFaculty(
        faculty.facultyId
      );

      setSuccess(
        response.message ||
          "Faculty deleted successfully."
      );

      if (
        viewing?.facultyId === faculty.facultyId
      ) {
        setViewing(null);
      }

      setRefreshKey((number) => number + 1);
    } catch (err) {
      setError(
        err.message ||
          "Unable to delete faculty."
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
            <Building2 size={21} />
          </div>

          <div>
            <h1 className="text-xl font-bold text-[#365D91]">
              Faculty Management
            </h1>

            <p className="mt-1 text-xs text-[#718DA9]">
              Create, view, update and delete faculty records.
            </p>
          </div>
        </div>

        <button
          type="button"
          className={PRIMARY_BUTTON}
          disabled={busy}
          onClick={openCreate}
        >
          <Plus size={17} />
          Create Faculty
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

      {/* FACULTY TABLE */}
      <section className="rounded-2xl border border-[#DFEAF6] bg-white p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="relative w-full max-w-sm">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7B98B7]"
            />

            <input
              type="search"
              value={search}
              placeholder="Search faculty name, code or ID"
              onChange={(event) =>
                setSearch(event.target.value)
              }
              className="w-full rounded-xl border border-[#D4E3F4] bg-[#F9FBFF] py-2.5 pl-9 pr-3 text-sm text-[#365D91] outline-none focus:border-[#82B0E3]"
            />
          </div>

          <div className="flex items-center gap-3">
            <span className="whitespace-nowrap text-xs text-[#8197B0]">
              {filtered.length} faculty record(s)
            </span>

            <button
              type="button"
              disabled={loading || busy}
              className={SECONDARY_BUTTON}
              onClick={() =>
                setRefreshKey((n) => n + 1)
              }
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
          <table className="w-full min-w-[980px] text-left text-xs">
            <thead className="bg-[#EAF3FD] text-[#446B98]">
              <tr>
                <th className="rounded-l-lg px-3 py-3">
                  Faculty
                </th>

                <th className="px-3 py-3">
                  Faculty Code
                </th>

                <th className="px-3 py-3">
                  Email
                </th>

                <th className="px-3 py-3">
                  Phone Number
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
              {!loading &&
                filtered.map((faculty) => (
                  <tr
                    key={faculty.facultyId}
                    className="hover:bg-[#F8FBFF]"
                  >
                    <td className="px-3 py-3">
                      <p className="font-bold text-[#365D91]">
                        {faculty.facultyName}
                      </p>

                      <p className="mt-1 text-[10px] text-[#91A6BC]">
                        {faculty.facultyId}
                      </p>
                    </td>

                    <td className="px-3 py-3 font-semibold text-[#476FA9]">
                      {faculty.facultyCode}
                    </td>

                    <td className="px-3 py-3 text-[#607E9D]">
                      {safeText(faculty.email)}
                    </td>

                    <td className="px-3 py-3 text-[#607E9D]">
                      {safeText(faculty.phoneNumber)}
                    </td>

                    <td className="px-3 py-3">
                      <LinkCount
                        count={faculty.majorCount}
                        label="major(s)"
                      />

                      <LinkCount
                        count={faculty.lecturerCount}
                        label="lecturer(s)"
                      />

                      <LinkCount
                        count={faculty.courseCount}
                        label="course(s)"
                      />
                    </td>

                    <td className="px-3 py-3">
                      <div className="flex justify-center gap-1.5">
                        {/* VIEW */}
                        <button
                          type="button"
                          title="View Faculty"
                          aria-label={`View ${faculty.facultyName}`}
                          disabled={busy}
                          onClick={() =>
                            openView(faculty)
                          }
                          className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                        >
                          <Eye size={15} />
                        </button>

                        {/* EDIT */}
                        <button
                          type="button"
                          title="Update Faculty"
                          aria-label={`Edit ${faculty.facultyName}`}
                          disabled={busy}
                          onClick={() =>
                            openEdit(faculty)
                          }
                          className="rounded-lg bg-[#EAF2FD] p-2 text-[#476FA9] hover:bg-[#D9EAFB] disabled:opacity-50"
                        >
                          <Pencil size={15} />
                        </button>

                        {/* DELETE */}
                        <button
                          type="button"
                          title={
                            hasAcademicLinks(faculty)
                              ? "Faculty has linked academic data"
                              : "Delete Faculty"
                          }
                          aria-label={`Delete ${faculty.facultyName}`}
                          disabled={
                            busy ||
                            hasAcademicLinks(faculty)
                          }
                          onClick={() =>
                            handleDelete(faculty)
                          }
                          className="rounded-lg bg-[#FFF1EE] p-2 text-[#B96657] hover:bg-[#FFE2DD] disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          {hasAcademicLinks(faculty) ? (
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
                    colSpan={6}
                    className="px-3 py-8 text-center text-[#8197B0]"
                  >
                    Loading faculties...
                  </td>
                </tr>
              )}

              {!loading && filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-8 text-center text-[#8197B0]"
                  >
                    No faculties found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* FACULTY DETAILS */}
      {viewing && !formMode && (
        <section className="rounded-2xl border border-[#DCE9F7] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold text-[#365D91]">
              Faculty Details
            </h2>

            <button
              type="button"
              aria-label="Close Faculty Details"
              onClick={() => setViewing(null)}
              className="text-[#7891AD]"
            >
              <X size={18} />
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <DetailItem
              label="Faculty ID"
              value={viewing.facultyId}
            />

            <DetailItem
              label="Faculty Code"
              value={viewing.facultyCode}
            />

            <DetailItem
              label="Faculty Name"
              value={viewing.facultyName}
            />

            <DetailItem
              label="Email"
              value={viewing.email}
            />

            <DetailItem
              label="Phone Number"
              value={viewing.phoneNumber}
            />

            <DetailItem
              label="Linked Academic Records"
              value={
                Number(viewing.majorCount || 0) +
                Number(viewing.lecturerCount || 0) +
                Number(viewing.courseCount || 0)
              }
            />
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
                  ? "Create Faculty"
                  : "Update Faculty"}
              </h2>

              {formMode === "edit" && (
                <p className="mt-1 text-xs text-[#8AA1B8]">
                  {editingId}
                </p>
              )}
            </div>

            <button
              type="button"
              aria-label="Close Faculty Form"
              disabled={busy}
              onClick={closeForm}
              className="text-[#7891AD] disabled:opacity-50"
            >
              <X size={19} />
            </button>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              {/* FACULTY CODE */}
              <label className="text-xs font-semibold text-[#466C98]">
                Faculty Code *
                <input
                  required
                  maxLength={10}
                  pattern="[A-Za-z0-9]{1,10}"
                  value={form.facultyCode}
                  disabled={busy || formMode === "edit"}
                  placeholder="TESTFA"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "facultyCode",
                      event.target.value.toUpperCase()
                    )
                  }
                />
                {formMode === "edit" && (
                  <span className="mt-1 block text-[10px] font-normal text-[#8BA1B7]">
                    Faculty Code cannot be changed.
                  </span>
                )}
              </label>

              {/* FACULTY NAME */}
              <label className="text-xs font-semibold text-[#466C98]">
                Faculty Name *
                <input
                  required
                  maxLength={100}
                  value={form.facultyName}
                  disabled={busy}
                  placeholder="Test Faculty"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "facultyName",
                      event.target.value
                    )
                  }
                />
              </label>

              {/* EMAIL */}
              <label className="text-xs font-semibold text-[#466C98]">
                Email *
                <input
                  required
                  type="email"
                  maxLength={100}
                  value={form.email}
                  disabled={busy}
                  placeholder="faculty@example.test"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "email",
                      event.target.value
                    )
                  }
                />
              </label>

              {/* PHONE */}
              <label className="text-xs font-semibold text-[#466C98]">
                Phone Number *
                <input
                  required
                  type="tel"
                  maxLength={15}
                  pattern="\+?[0-9]{8,15}"
                  value={form.phoneNumber}
                  disabled={busy}
                  placeholder="0280000000"
                  className={INPUT_STYLE}
                  onChange={(event) =>
                    updateForm(
                      "phoneNumber",
                      event.target.value
                    )
                  }
                />
              </label>
            </div>

            <p className="text-xs text-[#8BA1B7]">
              Faculty Code must be unique.
              All four fields are required.
            </p>

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
                    ? "Create Faculty"
                    : "Save Changes"}
              </button>

              <button
                type="button"
                disabled={busy}
                className={SECONDARY_BUTTON}
                onClick={closeForm}
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

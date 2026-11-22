
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Search,
  Trash2,
  UserRound,
  X,
} from "lucide-react";

import {
  deleteAdminLecturer,
  fetchAdminLecturerById,
  fetchAdminLecturers,
  fetchLecturerFacultyOptions,
  updateAdminLecturer,
} from "../api/adminLecturerApi";

const PAGE_SIZE = 10;

const EMPTY_FORM = {
  citizenId: "",
  fullName: "",
  dateOfBirth: "",
  email: "",
  gender: "",
  phoneNumber: "",
  facultyId: "",
};

const LABELS = [
  ["lecturerId", "Lecturer ID"],
  ["citizenId", "Citizen ID"],
  ["fullName", "Full Name"],
  ["dateOfBirth", "Date of Birth"],
  ["email", "Email"],
  ["gender", "Gender"],
  ["phoneNumber", "Phone Number"],
  ["facultyName", "Faculty"],
];

function formFromRecord(record) {
  return Object.fromEntries(
    Object.keys(EMPTY_FORM).map((key) => [
      key,
      record[key] ?? "",
    ])
  );
}

function showValue(value) {
  return value === null ||
    value === undefined ||
    value === ""
    ? "—"
    : String(value);
}

function validateForm(form) {
  if (!form.citizenId.trim()) {
    return "Citizen ID is required.";
  }

  if (form.citizenId.trim().length > 12) {
    return "Citizen ID must not exceed 12 characters.";
  }

  if (!form.fullName.trim()) {
    return "Full name is required.";
  }

  if (form.fullName.trim().length > 200) {
    return "Full name must not exceed 200 characters.";
  }

  if (!form.facultyId) {
    return "Please select a faculty.";
  }

  if (
    form.email.trim() &&
    !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(
      form.email.trim()
    )
  ) {
    return "Invalid email address.";
  }

  return "";
}

function TextField({
  label,
  name,
  value,
  onChange,
  type = "text",
  maxLength,
  required = false,
}) {
  return (
    <label className="block min-w-0 space-y-1">
      <span className="text-[12px] font-semibold text-[#45678F]">
        {label}
        {required && (
          <span className="ml-1 text-[#BD5365]">*</span>
        )}
      </span>

      <input
        name={name}
        type={type}
        value={value}
        maxLength={maxLength}
        required={required}
        onChange={(event) =>
          onChange(name, event.target.value)
        }
        className={[
          "h-10 w-full rounded-lg",
          "border border-[#CEDFF1] bg-[#F9FCFF]",
          "px-3 text-[12px] text-[#365D91]",
          "outline-none transition",
          "focus:border-[#7DA8DA]",
          "focus:ring-2 focus:ring-[#E0EEFC]",
        ].join(" ")}
      />
    </label>
  );
}

function LecturerDialog({
  mode,
  record,
  form,
  faculties,
  busy,
  onChange,
  onClose,
  onSave,
}) {
  const editing = mode === "edit";

  return (
    <div
      className={[
        "fixed inset-0 z-50",
        "flex items-center justify-center",
        "bg-[#163451]/45 p-3 sm:p-5",
      ].join(" ")}
      role="presentation"
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="lecturer-dialog-title"
        className={[
          "flex max-h-[88dvh] w-full max-w-[690px]",
          "flex-col overflow-hidden rounded-2xl",
          "border border-[#D6E5F6] bg-white",
          "shadow-[0_16px_55px_rgba(34,72,118,0.18)]",
        ].join(" ")}
      >
        <div
          className={[
            "flex shrink-0 items-center justify-between gap-3",
            "border-b border-[#DFEAF7]",
            "bg-gradient-to-r",
            "from-[#E8F3FF] to-[#F4EFFC]",
            "px-5 py-3.5",
          ].join(" ")}
        >
          <div className="flex items-center gap-2.5">
            <UserRound
              size={20}
              className="text-[#527FB7]"
            />

            <div>
              <h2
                id="lecturer-dialog-title"
                className="text-[16px] font-bold text-[#365D91]"
              >
                {editing
                  ? "Edit Lecturer Profile"
                  : "Lecturer Details"}
              </h2>

              <p className="text-[11px] text-[#7594B7]">
                {record.lecturerId}
              </p>
            </div>
          </div>

          <button
            type="button"
            disabled={busy}
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-2 text-[#688BB1] hover:bg-white/70 disabled:opacity-50"
          >
            <X size={19} />
          </button>
        </div>

        {editing ? (
          <form
            id="lecturer-edit-form"
            onSubmit={onSave}
            className="min-h-0 overflow-y-auto px-5 py-4"
          >
            <div className="mb-3 rounded-lg bg-[#EDF5FE] px-3 py-2 text-[11px] text-[#557BA6]">
              Lecturer ID:{" "}
              <strong>{record.lecturerId}</strong>
              {" · "}Identification code cannot be changed.
            </div>

            <fieldset
              disabled={busy}
              className="grid gap-3 sm:grid-cols-2"
            >
              <TextField
                label="Citizen ID"
                name="citizenId"
                value={form.citizenId}
                onChange={onChange}
                maxLength={12}
                required
              />

              <TextField
                label="Full Name"
                name="fullName"
                value={form.fullName}
                onChange={onChange}
                maxLength={200}
                required
              />

              <TextField
                label="Date of Birth"
                name="dateOfBirth"
                value={form.dateOfBirth}
                onChange={onChange}
                type="date"
              />

              <TextField
                label="Gender"
                name="gender"
                value={form.gender}
                onChange={onChange}
                maxLength={20}
              />

              <TextField
                label="Email"
                name="email"
                value={form.email}
                onChange={onChange}
                type="email"
                maxLength={100}
              />

              <TextField
                label="Phone Number"
                name="phoneNumber"
                value={form.phoneNumber}
                onChange={onChange}
                maxLength={15}
              />

              <label className="block min-w-0 space-y-1 sm:col-span-2">
                <span className="text-[12px] font-semibold text-[#45678F]">
                  Faculty
                  <span className="ml-1 text-[#BD5365]">*</span>
                </span>

                <select
                  name="facultyId"
                  value={form.facultyId}
                  required
                  onChange={(event) =>
                    onChange("facultyId", event.target.value)
                  }
                  className={[
                    "h-10 w-full rounded-lg",
                    "border border-[#CEDFF1] bg-[#F9FCFF]",
                    "px-3 text-[12px] text-[#365D91]",
                    "outline-none focus:border-[#7DA8DA]",
                  ].join(" ")}
                >
                  <option value="">Select faculty</option>

                  {faculties.map((faculty) => (
                    <option
                      key={faculty.facultyId}
                      value={faculty.facultyId}
                    >
                      {faculty.facultyName}
                    </option>
                  ))}
                </select>
              </label>
            </fieldset>
          </form>
        ) : (
          <div className="min-h-0 overflow-y-auto px-5 py-4">
            <dl className="grid gap-3 sm:grid-cols-2">
              {LABELS.map(([key, label]) => (
                <div
                  key={key}
                  className={[
                    "rounded-lg border border-[#E4EDF7]",
                    "bg-[#F9FCFF] px-3 py-2.5",
                  ].join(" ")}
                >
                  <dt className="text-[11px] text-[#829BB6]">
                    {label}
                  </dt>

                  <dd className="mt-1 break-words text-[12px] font-semibold leading-5 text-[#365D91]">
                    {showValue(record[key])}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        <div
          className={[
            "flex shrink-0 justify-end gap-2",
            "border-t border-[#E5EFF9]",
            "bg-white px-5 py-3",
          ].join(" ")}
        >
          <button
            type="button"
            disabled={busy}
            onClick={onClose}
            className="rounded-lg border border-[#D1E1F2] px-4 py-2 text-[12px] font-semibold text-[#6484A8] disabled:opacity-50"
          >
            Close
          </button>

          {editing && (
            <button
              type="submit"
              form="lecturer-edit-form"
              disabled={busy}
              className={[
                "inline-flex items-center gap-2",
                "rounded-lg bg-[#476FA9]",
                "px-4 py-2 text-[12px]",
                "font-semibold text-white",
                "hover:bg-[#3B629A]",
                "disabled:opacity-50",
              ].join(" ")}
            >
              <Save size={15} />
              {busy ? "Saving..." : "Save Changes"}
            </button>
          )}
        </div>
      </section>
    </div>
  );
}

export default function AdminLecturersPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [dialog, setDialog] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [faculties, setFaculties] = useState([]);

  const pageCount = Math.max(
    1,
    Math.ceil(total / PAGE_SIZE)
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadRecords() {
      setLoading(true);
      setError("");

      try {
        const result = await fetchAdminLecturers({
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
          search,
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setItems(result.items || []);
          setTotal(Number(result.total || 0));
        }
      } catch (requestError) {
        if (!controller.signal.aborted) {
          setItems([]);
          setError(
            requestError.message ||
              "Unable to load lecturers."
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadRecords();

    return () => controller.abort();
  }, [page, search, reloadKey]);

  function handleSearch(event) {
    event.preventDefault();
    setNotice("");
    setPage(1);
    setSearch(searchInput.trim());
    setReloadKey((value) => value + 1);
  }

  function refreshRecords() {
    setNotice("");
    setReloadKey((value) => value + 1);
  }

  function updateField(name, value) {
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function openDialog(mode, lecturerId) {
    if (busy) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      const detail = await fetchAdminLecturerById(
        lecturerId
      );

      const record = detail.lecturer;
      let facultyList = [];

      if (mode === "edit") {
        const result = await fetchLecturerFacultyOptions();
        facultyList = result.items || [];
      }

      setFaculties(facultyList);
      setForm(formFromRecord(record));
      setDialog({ mode, record });
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to load lecturer details."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleSave(event) {
    event.preventDefault();

    if (!dialog || dialog.mode !== "edit" || busy) {
      return;
    }

    const validationError = validateForm(form);

    if (validationError) {
      setError(validationError);
      return;
    }

    setBusy(true);
    setError("");

    const payload = {
      citizenId: form.citizenId.trim(),
      fullName: form.fullName.trim(),
      dateOfBirth: form.dateOfBirth || null,
      email: form.email.trim() || null,
      gender: form.gender.trim() || null,
      phoneNumber: form.phoneNumber.trim() || null,
      facultyId: form.facultyId,
    };

    try {
      await updateAdminLecturer(
        dialog.record.lecturerId,
        payload
      );

      setDialog(null);
      setNotice("Lecturer profile updated successfully.");
      setReloadKey((value) => value + 1);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to update lecturer."
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(lecturer) {
    if (busy) return;

    const confirmed = window.confirm(
      `Delete lecturer ${lecturer.fullName} ` +
      `(${lecturer.lecturerId})?\n\n` +
      "This action removes the linked lecturer account. " +
      "A lecturer assigned to class sections cannot be deleted."
    );

    if (!confirmed) return;

    setBusy(true);
    setError("");
    setNotice("");

    try {
      await deleteAdminLecturer(lecturer.lecturerId);

      setNotice("Lecturer deleted successfully.");

      if (items.length === 1 && page > 1) {
        setPage((current) => current - 1);
      } else {
        setReloadKey((value) => value + 1);
      }
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to delete lecturer."
      );
    } finally {
      setBusy(false);
    }
  }

  const first = total === 0
    ? 0
    : (page - 1) * PAGE_SIZE + 1;

  const last = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="min-w-0 space-y-3 pb-3">
      {/* COMPACT HEADER */}
      <section
        className={[
          "flex flex-wrap items-center",
          "justify-between gap-3",
          "rounded-xl border border-[#D8E5F6]",
          "bg-gradient-to-r",
          "from-[#E5F1FD] to-[#F3EFFB]",
          "px-4 py-3",
        ].join(" ")}
      >
        <div className="flex items-center gap-3">
          <div
            className={[
              "flex h-10 w-10 items-center justify-center",
              "rounded-xl bg-white/90 text-[#476FA9]",
            ].join(" ")}
          >
            <UserRound size={20} />
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.13em] text-[#7599C5]">
              Administrator / User Management
            </p>

            <h1 className="text-[20px] font-bold leading-6 text-[#365D91]">
              Lecturers
            </h1>

            <p className="text-[11px] text-[#7190B1]">
              View and manage lecturer profiles.
            </p>
          </div>
        </div>

        <Link
          to="/admin/create-account"
          className={[
            "inline-flex h-9 items-center gap-2",
            "rounded-lg bg-[#476FA9] px-3",
            "text-[12px] font-semibold text-white",
            "hover:bg-[#3D659B]",
          ].join(" ")}
        >
          <Plus size={15} />
          Create Account
        </Link>
      </section>

      {/* SEARCH */}
      <section className="rounded-xl border border-[#DCE8F7] bg-white p-3 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <form
            onSubmit={handleSearch}
            role="search"
            className="flex min-w-[260px] flex-1 items-center gap-2"
          >
            <div className="relative min-w-0 flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#91A8C2]"
              />

              <input
                type="search"
                value={searchInput}
                onChange={(event) =>
                  setSearchInput(event.target.value)
                }
                maxLength={100}
                placeholder="Search by Lecturer ID or name"
                aria-label="Search lecturer records"
                className={[
                  "h-9 w-full rounded-lg",
                  "border border-[#D3E1F2]",
                  "bg-[#F9FCFF] pl-9 pr-3",
                  "text-[12px] text-[#365D91]",
                  "outline-none focus:border-[#77A3D6]",
                ].join(" ")}
              />
            </div>

            <button
              type="submit"
              disabled={loading || busy}
              className="h-9 rounded-lg bg-[#E5F0FC] px-3 text-[12px] font-semibold text-[#476FA9] disabled:opacity-50"
            >
              Search
            </button>
          </form>

          <button
            type="button"
            disabled={loading || busy}
            onClick={refreshRecords}
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-[#D7E5F5] px-3 text-[12px] font-semibold text-[#6486AD] disabled:opacity-50"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg border border-[#F3D0D3] bg-[#FFF3F3] px-3 py-2 text-[12px] text-[#AC4B56]"
        >
          <AlertCircle size={16} className="shrink-0" />
          {error}
        </div>
      )}

      {notice && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-lg border border-[#CCEBDD] bg-[#F0FAF5] px-3 py-2 text-[12px] text-[#397F6B]"
        >
          <CheckCircle2 size={16} />
          {notice}
        </div>
      )}

      {/* LECTURER TABLE */}
      <section className="overflow-hidden rounded-xl border border-[#DCE8F7] bg-white shadow-sm">
        <div className="flex items-center justify-between gap-2 border-b border-[#E7EFF8] px-4 py-2.5">
          <h2 className="text-[14px] font-bold text-[#365D91]">
            Lecturer Records
          </h2>

          <span className="rounded-full bg-[#E5F5EF] px-2.5 py-1 text-[11px] font-semibold text-[#397C6B]">
            {total} lecturers
          </span>
        </div>

        <div className="max-h-[440px] overflow-auto">
          <table className="w-full min-w-[880px] text-left text-[12px]">
            <thead className="sticky top-0 z-10 bg-[#EAF3FD] text-[#426794]">
              <tr>
                <th className="px-3 py-2.5">Lecturer ID</th>
                <th className="px-3 py-2.5">Full Name</th>
                <th className="px-3 py-2.5">Citizen ID</th>
                <th className="px-3 py-2.5">Faculty</th>
                <th className="px-3 py-2.5">Email</th>
                <th className="px-3 py-2.5 text-center">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#EDF2F8]">
              {loading ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-7 text-center text-[#7893B2]"
                  >
                    Loading lecturer records...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-7 text-center text-[#7893B2]"
                  >
                    No lecturer records found.
                  </td>
                </tr>
              ) : (
                items.map((lecturer) => (
                  <tr
                    key={lecturer.lecturerId}
                    className="hover:bg-[#F9FCFF]"
                  >
                    <td className="px-3 py-3 font-bold text-[#476FA9]">
                      {lecturer.lecturerId}
                    </td>

                    <td className="px-3 py-3 font-semibold leading-5 text-[#365D91]">
                      {lecturer.fullName}
                    </td>

                    <td className="px-3 py-3 text-[#6784A5]">
                      {lecturer.citizenId}
                    </td>

                    <td className="px-3 py-3 text-[#6784A5]">
                      {lecturer.facultyName}
                    </td>

                    <td className="px-3 py-3 text-[#6784A5]">
                      {showValue(lecturer.email)}
                    </td>

                    <td className="px-3 py-2.5">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            openDialog("view", lecturer.lecturerId)
                          }
                          title="View lecturer"
                          className="rounded-lg bg-[#E9F3FD] p-2 text-[#527DAF] disabled:opacity-50"
                        >
                          <Eye size={15} />
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            openDialog("edit", lecturer.lecturerId)
                          }
                          title="Edit lecturer"
                          className="rounded-lg bg-[#E8F5EE] p-2 text-[#3C8B72] disabled:opacity-50"
                        >
                          <Pencil size={15} />
                        </button>

                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => handleDelete(lecturer)}
                          title="Delete lecturer"
                          className="rounded-lg bg-[#FFF0F1] p-2 text-[#B65A67] disabled:opacity-50"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PAGINATION */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#E7EFF8] px-4 py-3">
          <p className="text-[11px] text-[#7B91AC]">
            Showing {first}–{last} of {total} lecturers
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={page <= 1 || loading || busy}
              onClick={() =>
                setPage((current) => current - 1)
              }
              className="rounded-lg border border-[#D6E5F5] p-2 text-[#527DAF] disabled:opacity-35"
              aria-label="Previous page"
            >
              <ChevronLeft size={15} />
            </button>

            <span className="text-[11px] font-semibold text-[#56789E]">
              Page {page} / {pageCount}
            </span>

            <button
              type="button"
              disabled={
                page >= pageCount || loading || busy
              }
              onClick={() =>
                setPage((current) => current + 1)
              }
              className="rounded-lg border border-[#D6E5F5] p-2 text-[#527DAF] disabled:opacity-35"
              aria-label="Next page"
            >
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </section>

      {dialog && (
        <LecturerDialog
          mode={dialog.mode}
          record={dialog.record}
          form={form}
          faculties={faculties}
          busy={busy}
          onChange={updateField}
          onClose={() => {
            setDialog(null);
            setError("");
          }}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

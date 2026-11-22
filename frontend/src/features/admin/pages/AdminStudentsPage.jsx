
import { useEffect, useRef, useState } from "react";
import {
  fetchStudentById,
  fetchStudents,
} from "../api/adminStudentApi";
import { useAuth } from "../../auth/context/AuthContext";

const PAGE_SIZE = 10;

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
  if (!value) return "—";

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
        {value || "—"}
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

  const detailsController = useRef(null);

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
  }, [page, search, refreshUser]);

  useEffect(() => {
    return () => detailsController.current?.abort();
  }, []);

  function closeDetails() {
    detailsController.current?.abort();
    setSelected(null);
    setDetailsLoading(false);
    setDetailError("");
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

  async function openDetails(studentId) {
    detailsController.current?.abort();

    const controller = new AbortController();
    detailsController.current = controller;

    setSelected(null);
    setDetailsLoading(true);
    setDetailError("");

    try {
      const response = await fetchStudentById(
        studentId,
        controller.signal
      );

      if (controller.signal.aborted) return;

      setSelected(response.student);
      void refreshUser();
    } catch (err) {
      if (controller.signal.aborted) return;

      setDetailError(
        err.message || "Không thể tải hồ sơ sinh viên."
      );

      if (err.status === 401) {
        void refreshUser();
      }
    } finally {
      if (!controller.signal.aborted) {
        setDetailsLoading(false);
      }
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
            <table className="w-full min-w-[970px] text-left text-xs">
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
                      <button
                        type="button"
                        onClick={() =>
                          openDetails(student.studentId)
                        }
                        className="inline-flex items-center gap-1.5 rounded-md px-2 py-1.5 font-semibold text-[#173D8B] hover:bg-[#EBF0FD]"
                        aria-label={`View ${student.fullName}`}
                      >
                        <EyeIcon />
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-[#EDF0F7] px-5 py-4">
          <p className="text-xs text-[#697181]">
            Showing {firstRow}–{lastRow} of {total} students
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
          aria-label="Student details"
          className="mt-6 rounded-xl border border-[#EDF0F7] bg-white p-5 shadow-sm sm:p-6"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDF0F7] pb-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#5974B0]">
                Student Profile
              </p>

              <h2 className="mt-1 text-xl font-bold text-[#092B70]">
                {selected.fullName}
              </h2>
            </div>

            <button
              type="button"
              onClick={closeDetails}
              className="rounded-lg border border-[#DDE3EF] px-4 py-2 text-sm font-medium text-[#4E5D75] hover:bg-[#F7F8FC]"
            >
              Close
            </button>
          </div>

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
        </section>
      )}
    </main>
  );
}

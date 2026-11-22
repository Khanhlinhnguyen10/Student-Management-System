
const API_URL = "/api/admin/students";
const CSRF_URL = "/api/auth/csrf";

/**
 * Parse JSON response and handle HTTP errors.
 */
async function parseResponse(response, fallbackMessage) {
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      payload.error || fallbackMessage
    );

    error.status = response.status;
    throw error;
  }

  return payload;
}

/**
 * GET request for student records.
 */
async function getJSON(url, signal) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  return parseResponse(
    response,
    "Không thể tải dữ liệu sinh viên."
  );
}

/**
 * Retrieve the session-bound CSRF token.
 * Uses the existing authentication API.
 */
async function getCsrfToken(signal) {
  const response = await fetch(CSRF_URL, {
    method: "GET",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const payload = await parseResponse(
    response,
    "Không thể lấy CSRF Token."
  );

  if (
    typeof payload.csrfToken !== "string" ||
    !payload.csrfToken
  ) {
    throw new Error("CSRF Token không hợp lệ.");
  }

  return payload.csrfToken;
}

/**
 * Shared request for PUT and DELETE.
 * Retrieves a fresh CSRF token before each write request.
 */
async function writeJSON(url, method, body, signal) {
  const csrfToken = await getCsrfToken(signal);

  const headers = {
    Accept: "application/json",
    "X-CSRF-Token": csrfToken,
  };

  const options = {
    method,
    credentials: "same-origin",
    signal,
    headers,
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  return parseResponse(
    response,
    "Không thể thực hiện thao tác với sinh viên."
  );
}

/**
 * GET: Retrieve paginated student records.
 */
export function fetchStudents({
  limit = 10,
  offset = 0,
  search = "",
  signal,
} = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    search,
  });

  return getJSON(
    `${API_URL}?${params.toString()}`,
    signal
  );
}

/**
 * GET: Retrieve one student by ID.
 */
export function fetchStudentById(studentId, signal) {
  return getJSON(
    `${API_URL}/${encodeURIComponent(studentId)}`,
    signal
  );
}

/**
 * PUT: Update an existing student.
 */
export function updateStudent(
  studentId,
  studentData,
  signal
) {
  return writeJSON(
    `${API_URL}/${encodeURIComponent(studentId)}`,
    "PUT",
    studentData,
    signal
  );
}

/**
 * DELETE: Delete an existing student.
 */
export function deleteStudent(studentId, signal) {
  return writeJSON(
    `${API_URL}/${encodeURIComponent(studentId)}`,
    "DELETE",
    undefined,
    signal
  );
}

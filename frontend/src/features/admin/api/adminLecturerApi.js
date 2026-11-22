
/**
 * Administrator Lecturer Management API - Group 05.
 * Uses existing SQL-backed session authentication.
 */

const BASE_URL = "/api/admin/lecturers";

export class AdminLecturerApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "AdminLecturerApiError";
    this.status = status;
  }
}

async function requestJson(url, options = {}) {
  let response;

  try {
    response = await fetch(url, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    if (error?.name === "AbortError") {
      throw error;
    }

    throw new AdminLecturerApiError(
      "Cannot connect to the server."
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      typeof data.error === "string" && data.error
        ? data.error
        : response.status === 401
          ? "Session expired. Please log in again."
          : response.status === 403
            ? "Access denied."
            : "Unable to process this request.";

    throw new AdminLecturerApiError(
      message,
      response.status
    );
  }

  return data;
}

async function getCsrfToken() {
  const data = await requestJson("/api/auth/csrf");

  if (typeof data.csrfToken !== "string") {
    throw new AdminLecturerApiError(
      "Unable to obtain CSRF token."
    );
  }

  return data.csrfToken;
}

export async function fetchAdminLecturers({
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

  return requestJson(`${BASE_URL}?${params}`, {
    signal,
  });
}

export async function fetchAdminLecturerById(
  lecturerId
) {
  return requestJson(
    `${BASE_URL}/${encodeURIComponent(lecturerId)}`
  );
}

export async function fetchLecturerFacultyOptions() {
  return requestJson(`${BASE_URL}/faculties`);
}

export async function updateAdminLecturer(
  lecturerId,
  payload
) {
  const csrfToken = await getCsrfToken();

  return requestJson(
    `${BASE_URL}/${encodeURIComponent(lecturerId)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify(payload),
    }
  );
}

export async function deleteAdminLecturer(
  lecturerId
) {
  const csrfToken = await getCsrfToken();

  return requestJson(
    `${BASE_URL}/${encodeURIComponent(lecturerId)}`,
    {
      method: "DELETE",
      headers: {
        "X-CSRF-Token": csrfToken,
      },
    }
  );
}

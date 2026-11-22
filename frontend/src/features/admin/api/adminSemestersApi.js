
const BASE_URL = "/api/admin/semesters";

// =========================================
// HANDLE API RESPONSE
// =========================================

async function readResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.error || fallbackMessage
    );

    error.status = response.status;
    throw error;
  }

  return data;
}

// =========================================
// CSRF TOKEN
// =========================================

async function getCsrfToken() {
  const response = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to obtain CSRF token."
  );

  if (
    typeof data.csrfToken !== "string" ||
    !data.csrfToken
  ) {
    throw new Error("Invalid CSRF token response.");
  }

  return data.csrfToken;
}

// =========================================
// SHARED WRITE REQUEST
// =========================================

async function sendWrite(method, url, payload) {
  const csrfToken = await getCsrfToken();

  const response = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-CSRF-Token": csrfToken,
      ...(payload == null
        ? {}
        : { "Content-Type": "application/json" }),
    },
    ...(payload == null
      ? {}
      : { body: JSON.stringify(payload) }),
  });

  return readResponse(
    response,
    "Unable to save semester changes."
  );
}

// =========================================
// GET ALL SEMESTERS
// =========================================

export async function fetchAdminSemesters(
  { signal } = {}
) {
  const response = await fetch(BASE_URL, {
    method: "GET",
    credentials: "same-origin",
    signal,
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to load semesters."
  );

  if (!Array.isArray(data.semesters)) {
    throw new Error(
      "Invalid semesters response."
    );
  }

  return data.semesters;
}

// =========================================
// CREATE SEMESTER
// =========================================

export function createAdminSemester(payload) {
  return sendWrite(
    "POST",
    BASE_URL,
    payload
  );
}

// =========================================
// UPDATE SEMESTER
// =========================================

export function updateAdminSemester(
  semesterId,
  payload
) {
  return sendWrite(
    "PUT",
    `${BASE_URL}/${encodeURIComponent(semesterId)}`,
    payload
  );
}

// =========================================
// DELETE SEMESTER
// =========================================

export function deleteAdminSemester(semesterId) {
  return sendWrite(
    "DELETE",
    `${BASE_URL}/${encodeURIComponent(semesterId)}`
  );
}

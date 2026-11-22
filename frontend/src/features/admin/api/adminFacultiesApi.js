
const BASE_URL = "/api/admin/faculties";

// =========================================
// HANDLE JSON RESPONSE
// =========================================

async function readResponse(response, fallbackMessage) {
  const data = await response
    .json()
    .catch(() => ({}));

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
// GET CSRF TOKEN
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
    throw new Error(
      "Invalid CSRF token response."
    );
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
    "Unable to save faculty changes."
  );
}

// =========================================
// GET FACULTIES
// =========================================

export async function fetchAdminFaculties(
  { signal } = {}
) {
  const response = await fetch(BASE_URL, {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to load faculties."
  );

  if (!Array.isArray(data.faculties)) {
    throw new Error(
      "Invalid faculties response."
    );
  }

  return data.faculties;
}

// =========================================
// GET FACULTY DETAILS
// =========================================

export async function fetchAdminFaculty(
  facultyId,
  { signal } = {}
) {
  if (!facultyId) {
    throw new Error(
      "Faculty ID is required."
    );
  }

  const response = await fetch(
    `${BASE_URL}/${encodeURIComponent(facultyId)}`,
    {
      method: "GET",
      credentials: "same-origin",
      cache: "no-store",
      signal,
      headers: {
        Accept: "application/json",
      },
    }
  );

  const data = await readResponse(
    response,
    "Unable to load faculty details."
  );

  if (!data.faculty) {
    throw new Error(
      "Invalid faculty details response."
    );
  }

  return data.faculty;
}

// =========================================
// CREATE FACULTY
// =========================================

export function createAdminFaculty(payload) {
  return sendWrite(
    "POST",
    BASE_URL,
    payload
  );
}

// =========================================
// UPDATE FACULTY
// =========================================

export function updateAdminFaculty(
  facultyId,
  payload
) {
  if (!facultyId) {
    throw new Error(
      "Faculty ID is required."
    );
  }

  return sendWrite(
    "PUT",
    `${BASE_URL}/${encodeURIComponent(facultyId)}`,
    payload
  );
}

// =========================================
// DELETE FACULTY
// =========================================

export function deleteAdminFaculty(facultyId) {
  if (!facultyId) {
    throw new Error(
      "Faculty ID is required."
    );
  }

  return sendWrite(
    "DELETE",
    `${BASE_URL}/${encodeURIComponent(facultyId)}`
  );
}

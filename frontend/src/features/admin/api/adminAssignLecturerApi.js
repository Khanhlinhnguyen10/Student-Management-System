
/**
 * Assign Lecturer API - Group 05.
 *
 * Use Case 40: Assign Lecturer to Class Sections.
 *
 * Uses the existing Vite /api proxy,
 * cookie-based authentication, and CSRF protection.
 */

const BASE_URL = "/api/admin/assign-lecturer";

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

async function getJson(url, signal) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  return readResponse(
    response,
    "Unable to retrieve data."
  );
}

// =========================================
// GET SEMESTERS
// =========================================

export async function fetchAssignmentSemesters(signal) {
  const data = await getJson(
    `${BASE_URL}/semesters`,
    signal
  );

  return data.items ?? [];
}

// =========================================
// GET CLASS SECTIONS BY SEMESTER
// =========================================

export async function fetchAssignmentSections(
  semesterId,
  signal
) {
  if (!semesterId) {
    return [];
  }

  const params = new URLSearchParams({
    semesterId,
  });

  const data = await getJson(
    `${BASE_URL}/sections?${params.toString()}`,
    signal
  );

  return data.items ?? [];
}

// =========================================
// GET LECTURERS
// =========================================

export async function fetchAssignmentLecturers(signal) {
  const data = await getJson(
    `${BASE_URL}/lecturers`,
    signal
  );

  return data.items ?? [];
}

// =========================================
// GET CSRF TOKEN
// =========================================

async function fetchCsrfToken() {
  const response = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to verify the current session."
  );

  if (
    typeof data.csrfToken !== "string" ||
    !data.csrfToken
  ) {
    throw new Error(
      "CSRF token is missing. Please sign in again."
    );
  }

  return data.csrfToken;
}

// =========================================
// POST ASSIGN LECTURER
// =========================================

export async function submitLecturerAssignment({
  classSectionId,
  lecturerId,
}) {
  const csrfToken = await fetchCsrfToken();

  const response = await fetch(
    `${BASE_URL}/assign`,
    {
      method: "POST",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        classSectionId,
        lecturerId,
      }),
    }
  );

  return readResponse(
    response,
    "Unable to assign lecturer."
  );
}


/**
 * Administrator Class Section Management API.
 *
 * Use Cases 35-39.
 * Lecturer assignment remains in Use Case 40.
 */

const BASE_URL = "/api/admin/class-sections";

// =========================================
// HANDLE SERVER RESPONSE
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
// SHARED GET REQUEST
// =========================================

async function sendGet(url, fallbackMessage, signal) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  return readResponse(response, fallbackMessage);
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
        : {
            "Content-Type": "application/json",
          }),
    },
    ...(payload == null
      ? {}
      : {
          body: JSON.stringify(payload),
        }),
  });

  return readResponse(
    response,
    "Unable to save Class Section changes."
  );
}

// =========================================
// 1. GET CLASS SECTION LIST
// =========================================

export async function fetchAdminClassSections(
  semesterId = "",
  { signal } = {}
) {
  const params = new URLSearchParams();

  if (semesterId) {
    params.set("semesterId", semesterId);
  }

  const query = params.toString();

  const url = query
    ? `${BASE_URL}?${query}`
    : BASE_URL;

  const data = await sendGet(
    url,
    "Unable to load Class Sections.",
    signal
  );

  if (!Array.isArray(data.sections)) {
    throw new Error(
      "Invalid Class Sections response."
    );
  }

  return data.sections;
}

// =========================================
// 2. GET CLASS SECTION DETAILS
// =========================================

export async function fetchAdminClassSection(
  sectionId,
  { signal } = {}
) {
  if (!sectionId) {
    throw new Error(
      "Class Section ID is required."
    );
  }

  const data = await sendGet(
    `${BASE_URL}/${encodeURIComponent(sectionId)}`,
    "Unable to load Class Section details.",
    signal
  );

  if (!data.section) {
    throw new Error(
      "Invalid Class Section details response."
    );
  }

  return data.section;
}

// =========================================
// 3. GET SEMESTERS FOR DROPDOWN
// =========================================

export async function fetchClassSectionSemesters(
  { signal } = {}
) {
  const data = await sendGet(
    `${BASE_URL}/semesters`,
    "Unable to load semesters.",
    signal
  );

  if (!Array.isArray(data.semesters)) {
    throw new Error(
      "Invalid semesters response."
    );
  }

  return data.semesters;
}

// =========================================
// 4. GET COURSES FOR DROPDOWN
// =========================================

export async function fetchClassSectionCourses(
  { signal } = {}
) {
  const data = await sendGet(
    `${BASE_URL}/courses`,
    "Unable to load courses.",
    signal
  );

  if (!Array.isArray(data.courses)) {
    throw new Error(
      "Invalid courses response."
    );
  }

  return data.courses;
}

// =========================================
// 5. CREATE CLASS SECTION
// =========================================

export async function createAdminClassSection(payload) {
  return sendWrite(
    "POST",
    BASE_URL,
    payload
  );
}

// =========================================
// 6. UPDATE CLASS SECTION
// =========================================

export async function updateAdminClassSection(
  sectionId,
  payload
) {
  if (!sectionId) {
    throw new Error(
      "Class Section ID is required."
    );
  }

  return sendWrite(
    "PUT",
    `${BASE_URL}/${encodeURIComponent(sectionId)}`,
    payload
  );
}

// =========================================
// 7. DELETE CLASS SECTION
// =========================================

export async function deleteAdminClassSection(sectionId) {
  if (!sectionId) {
    throw new Error(
      "Class Section ID is required."
    );
  }

  return sendWrite(
    "DELETE",
    `${BASE_URL}/${encodeURIComponent(sectionId)}`
  );
}

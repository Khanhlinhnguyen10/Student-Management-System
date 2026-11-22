
const BASE_URL = "/api/admin/courses";

// =========================================
// READ JSON RESPONSE
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
    "Unable to save course changes."
  );
}

// =========================================
// GET COURSE LIST
// =========================================

export async function fetchAdminCourses(
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
    "Unable to load courses."
  );

  if (!Array.isArray(data.courses)) {
    throw new Error("Invalid courses response.");
  }

  return data.courses;
}

// =========================================
// GET COURSE DETAILS
// =========================================

export async function fetchAdminCourse(
  courseId,
  { signal } = {}
) {
  if (!courseId) {
    throw new Error("Course ID is required.");
  }

  const response = await fetch(
    `${BASE_URL}/${encodeURIComponent(courseId)}`,
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
    "Unable to load course details."
  );

  if (!data.course) {
    throw new Error("Invalid course details response.");
  }

  return data.course;
}

// =========================================
// CREATE COURSE
// =========================================

export function createAdminCourse(payload) {
  return sendWrite("POST", BASE_URL, payload);
}

// =========================================
// UPDATE COURSE
// =========================================

export function updateAdminCourse(courseId, payload) {
  if (!courseId) {
    throw new Error("Course ID is required.");
  }

  return sendWrite(
    "PUT",
    `${BASE_URL}/${encodeURIComponent(courseId)}`,
    payload
  );
}

// =========================================
// DELETE COURSE
// =========================================

export function deleteAdminCourse(courseId) {
  if (!courseId) {
    throw new Error("Course ID is required.");
  }

  return sendWrite(
    "DELETE",
    `${BASE_URL}/${encodeURIComponent(courseId)}`
  );
}


const PROFILE_URL = "/api/student/profile";
const CSRF_URL = "/api/auth/csrf";

async function readJSON(response, fallbackMessage) {
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

function extractProfile(data) {
  if (
    !data.profile ||
    typeof data.profile !== "object" ||
    Array.isArray(data.profile)
  ) {
    throw new Error(
      "Invalid student profile response."
    );
  }

  return data.profile;
}

/**
 * View the authenticated student's own profile.
 * The server derives userId from the SQL-backed session.
 */
export async function fetchStudentProfile({
  signal,
} = {}) {
  const response = await fetch(PROFILE_URL, {
    method: "GET",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readJSON(
    response,
    "Unable to load student profile."
  );

  return extractProfile(data);
}

/**
 * Retrieve an existing session-bound CSRF token.
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

  const data = await readJSON(
    response,
    "Unable to retrieve CSRF token."
  );

  if (
    typeof data.csrfToken !== "string" ||
    !data.csrfToken
  ) {
    throw new Error("Invalid CSRF token response.");
  }

  return data.csrfToken;
}

/**
 * Only email and phoneNumber may be submitted.
 */
export async function updateStudentProfile(
  { email, phoneNumber },
  { signal } = {}
) {
  const csrfToken = await getCsrfToken(signal);

  const response = await fetch(PROFILE_URL, {
    method: "PUT",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify({
      email,
      phoneNumber,
    }),
  });

  const data = await readJSON(
    response,
    "Unable to update contact information."
  );

  return extractProfile(data);
}

export async function fetchStudentCurriculum({
  signal,
} = {}) {
  const response = await fetch(
    "/api/student/curriculum",
    {
      method: "GET",
      credentials: "same-origin",
      signal,
      headers: {
        Accept: "application/json",
      },
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.error || "Unable to load curriculum."
    );

    error.status = response.status;
    throw error;
  }

  if (
    !data.curriculum ||
    !Array.isArray(data.curriculum.courses)
  ) {
    throw new Error(
      "Invalid curriculum response from server."
    );
  }

  return data.curriculum;
}

export async function fetchStudentTranscript({
  signal,
} = {}) {
  const response = await fetch(
    "/api/student/transcript",
    {
      method: "GET",
      credentials: "same-origin",
      signal,
      headers: {
        Accept: "application/json",
      },
    }
  );

  const data = await readJSON(
    response,
    "Unable to load transcript."
  );

  if (
    !data.transcript ||
    !Array.isArray(data.transcript.semesters)
  ) {
    throw new Error(
      "Invalid transcript response from server."
    );
  }

  return data.transcript;
}

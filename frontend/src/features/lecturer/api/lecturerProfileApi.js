
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

// GET: Load current Lecturer profile.
export async function fetchLecturerProfile({ signal } = {}) {
  const response = await fetch("/api/lecturer/profile", {
    method: "GET",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to load lecturer profile."
  );

  if (!data.profile) {
    throw new Error("Invalid lecturer profile response.");
  }

  return data.profile;
}

// PUT: Update only email and phone number.
export async function updateLecturerProfile(contact) {
  const csrfResponse = await fetch("/api/auth/csrf", {
    method: "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  const csrfData = await readResponse(
    csrfResponse,
    "Unable to get CSRF token."
  );

  if (
    typeof csrfData.csrfToken !== "string" ||
    !csrfData.csrfToken
  ) {
    throw new Error("Invalid CSRF token response.");
  }

  const response = await fetch("/api/lecturer/profile", {
    method: "PUT",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfData.csrfToken,
    },
    body: JSON.stringify({
      email: contact.email,
      phoneNumber: contact.phoneNumber,
    }),
  });

  const data = await readResponse(
    response,
    "Unable to update lecturer profile."
  );

  if (!data.profile) {
    throw new Error("Profile update was not confirmed.");
  }

  return data.profile;
}

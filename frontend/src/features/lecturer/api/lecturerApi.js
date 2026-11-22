
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

// 1. Get Lecturer's assigned class sections.
export async function fetchAssignedSections({ signal } = {}) {
  const response = await fetch("/api/lecturer/sections", {
    method: "GET",
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const data = await readResponse(
    response,
    "Unable to load assigned classes."
  );

  if (!Array.isArray(data.sections)) {
    throw new Error("Invalid assigned classes response.");
  }

  return data.sections;
}

// 2. Get Gradebook for a selected class.
export async function fetchSectionGradebook(
  sectionId,
  { signal } = {}
) {
  if (!sectionId) {
    throw new Error("Class section ID is required.");
  }

  const response = await fetch(
    `/api/lecturer/sections/${encodeURIComponent(sectionId)}/gradebook`,
    {
      method: "GET",
      credentials: "same-origin",
      signal,
      headers: {
        Accept: "application/json",
      },
    }
  );

  const data = await readResponse(
    response,
    "Unable to load gradebook."
  );

  if (
    !data.section ||
    !Array.isArray(data.students)
  ) {
    throw new Error("Invalid gradebook response.");
  }

  return data;
}

// 3. Get CSRF token for protected write requests.
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
    "Unable to get CSRF token."
  );

  if (
    typeof data.csrfToken !== "string" ||
    !data.csrfToken
  ) {
    throw new Error("Invalid CSRF token response.");
  }

  return data.csrfToken;
}

// 4. Shared helper for saving marks.
async function sendGrades(url, marks) {
  const csrfToken = await getCsrfToken();

  const response = await fetch(url, {
    method: "PUT",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfToken,
    },
    body: JSON.stringify(marks),
  });

  const data = await readResponse(
    response,
    "Unable to save grades."
  );

  if (!data.gradebook) {
    throw new Error("Invalid gradebook save response.");
  }

  return data.gradebook;
}

// 5. Save Draft, without recalculating GPA.
export async function saveGradebookDraft(
  sectionId,
  enrollmentId,
  marks
) {
  if (!sectionId || !enrollmentId) {
    throw new Error("Class and enrollment are required.");
  }

  const url =
    `/api/lecturer/sections/${encodeURIComponent(sectionId)}` +
    `/gradebook/${encodeURIComponent(enrollmentId)}`;

  return sendGrades(url, marks);
}

// 6. Save Final, calculate final grade and GPA.
export async function saveFinalGrade(
  sectionId,
  enrollmentId,
  marks
) {
  if (!sectionId || !enrollmentId) {
    throw new Error("Class and enrollment are required.");
  }

  const url =
    `/api/lecturer/sections/${encodeURIComponent(sectionId)}` +
    `/gradebook/${encodeURIComponent(enrollmentId)}/finalize`;

  const result = await sendGrades(url, marks);

  if (result.isFinalized !== true) {
    throw new Error(
      "Grade finalization was not confirmed."
    );
  }

  return result;
}


/**
 * Administrator - Create Account API
 * Student Management System - Group 05
 *
 * Requirement: Use Case 11
 *
 * Uses existing Flask endpoints.
 * No mocked data or hard-coded academic options.
 */

const BASE_URL = "/api/admin/create-account";

async function parseResponse(response) {
  let data = {};

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    const error = new Error(
      data?.error ||
        `Request failed with status ${response.status}.`
    );

    error.status = response.status;
    error.data = data;

    throw error;
  }

  return data;
}

async function getJson(url, { signal } = {}) {
  const response = await fetch(url, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    signal,
  });

  return parseResponse(response);
}

// -----------------------------------------
// Load majors from dbo.Majors
// -----------------------------------------

export async function fetchCreateAccountMajors(options = {}) {
  const data = await getJson(`${BASE_URL}/majors`, options);

  if (!Array.isArray(data.majors)) {
    throw new Error("Invalid major list response.");
  }

  return data.majors;
}

// -----------------------------------------
// Load faculties from dbo.Faculties
// -----------------------------------------

export async function fetchCreateAccountFaculties(options = {}) {
  const data = await getJson(`${BASE_URL}/faculties`, options);

  if (!Array.isArray(data.faculties)) {
    throw new Error("Invalid faculty list response.");
  }

  return data.faculties;
}

// -----------------------------------------
// Create Student or Lecturer account
// -----------------------------------------

export async function createAdminAccount(payload) {
  // Reuse existing authentication CSRF endpoint.
  const csrfData = await getJson("/api/auth/csrf");

  if (
    typeof csrfData.csrfToken !== "string" ||
    !csrfData.csrfToken
  ) {
    throw new Error("Unable to verify the current session.");
  }

  const response = await fetch(BASE_URL, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": csrfData.csrfToken,
    },
    body: JSON.stringify(payload),
  });

  return parseResponse(response);
}

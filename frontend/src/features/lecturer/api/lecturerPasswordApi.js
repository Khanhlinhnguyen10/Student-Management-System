
/**
 * Lecturer Change Password API
 *
 * Reuses the existing Group 05 authentication endpoints.
 * Authentication: HttpOnly session cookie.
 * CSRF: Obtained from the current authenticated session.
 */

const CSRF_ENDPOINT = "/api/auth/csrf";
const CHANGE_PASSWORD_ENDPOINT = "/api/auth/change-password";


export class LecturerPasswordApiError extends Error {
  constructor(message, status = 0) {
    super(message);

    this.name = "LecturerPasswordApiError";
    this.status = status;
  }
}


async function readResponse(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}


function getErrorMessage(data, fallback) {
  if (
    data &&
    typeof data.error === "string" &&
    data.error.trim()
  ) {
    return data.error;
  }

  return fallback;
}


/**
 * Obtain CSRF token from the authenticated session.
 */
async function getCsrfToken() {
  let response;

  try {
    response = await fetch(CSRF_ENDPOINT, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });
  } catch {
    throw new LecturerPasswordApiError(
      "Cannot connect to the authentication server."
    );
  }

  const data = await readResponse(response);

  if (!response.ok) {
    throw new LecturerPasswordApiError(
      getErrorMessage(
        data,
        "Unable to verify your login session."
      ),
      response.status
    );
  }

  if (
    typeof data.csrfToken !== "string" ||
    !data.csrfToken
  ) {
    throw new LecturerPasswordApiError(
      "The server did not return a valid CSRF token."
    );
  }

  return data.csrfToken;
}


/**
 * Change the current authenticated Lecturer password.
 *
 * Never store passwords or CSRF tokens in localStorage.
 * Never send userId from the frontend.
 */
export async function changeLecturerPassword({
  currentPassword,
  newPassword,
  confirmPassword,
}) {
  const csrfToken = await getCsrfToken();

  let response;

  try {
    response = await fetch(
      CHANGE_PASSWORD_ENDPOINT,
      {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
          confirmPassword,
        }),
      }
    );
  } catch {
    throw new LecturerPasswordApiError(
      "Cannot connect to the authentication server."
    );
  }

  const data = await readResponse(response);

  if (!response.ok) {
    throw new LecturerPasswordApiError(
      getErrorMessage(
        data,
        "Unable to change your password."
      ),
      response.status
    );
  }

  return data;
}

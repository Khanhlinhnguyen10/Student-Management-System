
const BASE_URL = "/api/auth";

async function request(path, options = {}) {
  const { headers = {}, ...rest } = options;

  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: "same-origin",
    ...rest,
    headers: {
      ...(rest.body ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.error || "Không thể kết nối với hệ thống."
    );
    error.status = response.status;
    throw error;
  }

  return data;
}

export async function loginAccount(credentials) {
  return request("/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function getCurrentUser() {
  return request("/me");
}

export async function logoutAccount() {
  const { csrfToken } = await request("/csrf");

  return request("/logout", {
    method: "POST",
    headers: {
      "X-CSRF-Token": csrfToken,
    },
  });
}

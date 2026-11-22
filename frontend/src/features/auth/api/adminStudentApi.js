
const API_URL = "/api/admin/students";

async function getJSON(url, signal) {
  const response = await fetch(url, {
    credentials: "same-origin",
    signal,
    headers: {
      Accept: "application/json",
    },
  });

  const payload = await response
    .json()
    .catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      payload.error || "Không thể tải dữ liệu sinh viên."
    );

    error.status = response.status;
    throw error;
  }

  return payload;
}

export function fetchStudents({
  limit = 10,
  offset = 0,
  search = "",
  signal,
} = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    search,
  });

  return getJSON(
    `${API_URL}?${params.toString()}`,
    signal
  );
}

export function fetchStudentById(studentId, signal) {
  return getJSON(
    `${API_URL}/${encodeURIComponent(studentId)}`,
    signal
  );
}


import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Mail,
  Pencil,
  Phone,
  Save,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";

import {
  fetchLecturerProfile,
  updateLecturerProfile,
} from "../api/lecturerProfileApi";

function InfoItem({ label, value }) {
  return (
    <div className="min-w-0 border-b border-[#EDF2F8] py-2">
      <p className="text-[11px] text-[#8BA0B7]">
        {label}
      </p>
      <p className="mt-1 break-words text-[13px] font-semibold text-[#476C9A]">
        {value || "—"}
      </p>
    </div>
  );
}

function toContact(profile) {
  return {
    email: profile.email || "",
    phoneNumber: profile.phoneNumber || "",
  };
}

export default function LecturerProfilePage() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    email: "",
    phoneNumber: "",
  });

  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);

      try {
        const data = await fetchLecturerProfile({
          signal: controller.signal,
        });

        if (!controller.signal.aborted) {
          setProfile(data);
          setForm(toContact(data));
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => controller.abort();
  }, []);

  function beginEdit() {
    setForm(toContact(profile));
    setError("");
    setSuccess("");
    setEditing(true);
  }

  function cancelEdit() {
    setForm(toContact(profile));
    setEditing(false);
    setError("");
  }

  async function saveContact(event) {
    event.preventDefault();

    if (!profile || saving) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const updated = await updateLecturerProfile({
        email: form.email.trim() || null,
        phoneNumber: form.phoneNumber.trim() || null,
      });

      setProfile(updated);
      setForm(toContact(updated));
      setEditing(false);
      setSuccess("Contact information updated successfully.");
    } catch (err) {
      setError(err.message || "Unable to update profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-w-0 space-y-3 pb-3">
      {/* COMPACT PAGE HEADER */}
      <header className="flex items-center gap-3 rounded-2xl border border-[#D8E8F8] bg-gradient-to-r from-[#E6F3FF] to-[#F4F1FC] px-4 py-3">
        <div className="rounded-xl bg-white p-2.5 text-[#5A86B9]">
          <UserRound size={20} />
        </div>

        <div>
          <h1 className="text-xl font-bold text-[#436F9E]">
            My Profile
          </h1>
          <p className="mt-0.5 text-[11px] text-[#7897B8]">
            Personal details and contact information
          </p>
        </div>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700"
        >
          {error}
        </p>
      )}

      {success && (
        <p
          role="status"
          className="flex items-center gap-2 rounded-xl bg-[#E7F6EF] px-4 py-2 text-xs text-[#397C6B]"
        >
          <CheckCircle2 size={16} />
          {success}
        </p>
      )}

      {loading && (
        <p
          role="status"
          className="rounded-xl bg-white p-4 text-sm text-[#7897B8]"
        >
          Loading lecturer profile...
        </p>
      )}

      {profile && !loading && (
        <div className="grid items-start gap-3 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,1fr)]">
          {/* PERSONAL DETAILS */}
          <section className="min-w-0 rounded-2xl border border-[#DCE9F7] bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <ShieldCheck
                  size={18}
                  className="text-[#5986BB]"
                />
                <h2 className="text-sm font-bold text-[#456F9E]">
                  Personal Information
                </h2>
              </div>

              <span className="rounded-full bg-[#ECF3FC] px-2.5 py-1 text-[10px] font-semibold text-[#7794B3]">
                Read Only
              </span>
            </div>

            <div className="grid grid-cols-2 gap-x-5">
              <InfoItem
                label="Lecturer ID"
                value={profile.lecturerId}
              />
              <InfoItem
                label="Username"
                value={profile.username}
              />
              <InfoItem
                label="Full Name"
                value={profile.fullName}
              />
              <InfoItem
                label="Gender"
                value={profile.gender}
              />
              <InfoItem
                label="Date of Birth"
                value={profile.dateOfBirth}
              />
              <InfoItem
                label="Citizen ID"
                value={profile.citizenId}
              />
              <InfoItem
                label="Faculty ID"
                value={profile.facultyId}
              />
              <InfoItem
                label="Faculty"
                value={profile.facultyName}
              />
            </div>

            <p className="mt-3 rounded-lg bg-[#F5F9FE] px-3 py-2 text-[11px] leading-relaxed text-[#8299B3]">
              Identification and faculty information
              cannot be modified by lecturers.
            </p>
          </section>

          {/* CONTACT DETAILS */}
          <section className="min-w-0 rounded-2xl border border-[#DCE9F7] bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-2">
              <h2 className="text-sm font-bold text-[#456F9E]">
                Contact Information
              </h2>

              {!editing && (
                <button
                  type="button"
                  onClick={beginEdit}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[#DDEEFF] px-3 py-2 text-[11px] font-bold text-[#4779B5] hover:bg-[#CEE5FC]"
                >
                  <Pencil size={13} />
                  Edit Contact
                </button>
              )}
            </div>

            <form
              onSubmit={saveContact}
              className="space-y-4"
            >
              <div>
                <label
                  htmlFor="lecturer-email"
                  className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-[#6989AC]"
                >
                  <Mail size={15} />
                  Email
                </label>

                <input
                  id="lecturer-email"
                  type="email"
                  maxLength={100}
                  value={form.email}
                  disabled={!editing || saving}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      email: event.target.value,
                    }))
                  }
                  className="w-full rounded-xl border border-[#D5E5F5] bg-[#F8FBFF] px-3 py-2.5 text-[13px] text-[#416D9C] outline-none focus:border-[#7CA9DC] disabled:opacity-80"
                />
              </div>

              <div>
                <label
                  htmlFor="lecturer-phone"
                  className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-[#6989AC]"
                >
                  <Phone size={15} />
                  Phone Number
                </label>

                <input
                  id="lecturer-phone"
                  type="tel"
                  maxLength={15}
                  value={form.phoneNumber}
                  disabled={!editing || saving}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      phoneNumber: event.target.value,
                    }))
                  }
                  className="w-full rounded-xl border border-[#D5E5F5] bg-[#F8FBFF] px-3 py-2.5 text-[13px] text-[#416D9C] outline-none focus:border-[#7CA9DC] disabled:opacity-80"
                />
              </div>

              {editing ? (
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    type="button"
                    onClick={cancelEdit}
                    disabled={saving}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#EDF2F8] px-3 py-2 text-xs font-semibold text-[#67819F] disabled:opacity-50"
                  >
                    <X size={14} />
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#5B8CC8] px-3 py-2 text-xs font-semibold text-white hover:bg-[#4777B6] disabled:opacity-50"
                  >
                    <Save size={14} />
                    {saving ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              ) : (
                <p className="rounded-lg bg-[#F6FAFE] px-3 py-2 text-[11px] leading-relaxed text-[#91A5BC]">
                  You can update your email and phone number.
                </p>
              )}
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

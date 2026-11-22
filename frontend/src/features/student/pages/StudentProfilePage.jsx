
import { useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  GraduationCap,
  Mail,
  Pencil,
  RefreshCw,
  Save,
  UserRound,
  X,
} from "lucide-react";

import { useAuth } from "../../auth/context/AuthContext";

import {
  fetchStudentProfile,
  updateStudentProfile,
} from "../api/studentApi";

// =============================================
// HELPERS
// =============================================

function display(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  return String(value);
}

function ProfileField({ label, value }) {
  return (
    <div className="min-w-0 rounded-xl bg-[#F7FAFE] px-3 py-2.5">
      <p className="text-[11px] text-[#8295AA]">
        {label}
      </p>

      <p className="mt-1 break-words text-sm font-semibold text-[#365D91]">
        {display(value)}
      </p>
    </div>
  );
}

function SectionTitle({ Icon, children }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <Icon size={17} className="text-[#6389B7]" />
      <h2 className="text-sm font-bold text-[#365D91]">
        {children}
      </h2>
    </div>
  );
}

// =============================================
// STUDENT PROFILE PAGE
// =============================================

export default function StudentProfilePage() {
  const { user } = useAuth();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const [message, setMessage] = useState("");
  const [saveError, setSaveError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadProfile() {
      setLoading(true);
      setLoadError("");

      try {
        const result = await fetchStudentProfile({
          signal: controller.signal,
        });

        if (controller.signal.aborted) return;

        setProfile(result);
        setEmail(result.email ?? "");
        setPhoneNumber(result.phoneNumber ?? "");
        setEditing(false);
      } catch (error) {
        if (controller.signal.aborted) return;

        setLoadError(
          error.message || "Unable to load student profile."
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadProfile();

    return () => controller.abort();
  }, [reloadKey]);

  function startEditing() {
    if (!profile) return;

    setEmail(profile.email ?? "");
    setPhoneNumber(profile.phoneNumber ?? "");
    setMessage("");
    setSaveError("");
    setEditing(true);
  }

  function cancelEditing() {
    if (saving) return;

    setEmail(profile.email ?? "");
    setPhoneNumber(profile.phoneNumber ?? "");
    setSaveError("");
    setEditing(false);
  }

  async function handleSave(event) {
    event.preventDefault();

    if (!editing || saving) return;

    setSaving(true);
    setSaveError("");
    setMessage("");

    try {
      const updated = await updateStudentProfile({
        email: email.trim(),
        phoneNumber: phoneNumber.trim(),
      });

      setProfile(updated);
      setEmail(updated.email ?? "");
      setPhoneNumber(updated.phoneNumber ?? "");
      setEditing(false);

      setMessage("Contact information updated successfully.");
    } catch (error) {
      setSaveError(
        error.message || "Unable to update contact information."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-w-0 space-y-3 pb-2">

      {/* COMPACT HEADER */}

      <section>
        <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#6389B7]">
          Student / Personal Information
        </p>

        <h1 className="mt-1 text-2xl font-bold text-[#365D91]">
          My Profile
        </h1>

        <p className="mt-1 text-xs text-[#71849A]">
          View your academic identity and manage contact information.
        </p>
      </section>

      {/* LOADING */}

      {loading && (
        <div
          role="status"
          className="aca-panel flex items-center gap-2 p-5 text-sm text-[#71849A]"
        >
          <RefreshCw size={18} className="animate-spin" />
          Loading profile...
        </div>
      )}

      {/* ERROR */}

      {!loading && loadError && (
        <section className="aca-panel p-5" role="alert">
          <p className="flex items-center gap-2 text-sm text-[#B9384A]">
            <AlertCircle size={18} />
            {loadError}
          </p>

          <button
            type="button"
            onClick={() => setReloadKey((n) => n + 1)}
            className="mt-3 rounded-lg bg-[#E5F0FC] px-4 py-2 text-sm font-semibold text-[#476FA9]"
          >
            Try Again
          </button>
        </section>
      )}

      {/* PROFILE CONTENT */}

      {!loading && !loadError && profile && (
        <>
          {/* SHORT IDENTITY BANNER */}

          <section className="flex items-center gap-3 rounded-2xl border border-[#DCE9F7] bg-gradient-to-r from-[#E6F1FC] to-[#F3F0FC] px-4 py-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/85 text-[#476FA9]">
              <UserRound size={23} />
            </div>

            <div className="min-w-0 flex-1">
              <p className="truncate text-base font-bold text-[#365D91]">
                {display(profile.fullName ?? user?.fullName)}
              </p>

              <p className="mt-0.5 text-xs text-[#7189A4]">
                Student ID: {display(profile.studentId)}
                {"  ·  "}
                Account: {display(profile.username ?? user?.username)}
              </p>
            </div>

            <span className="hidden rounded-full bg-white/85 px-3 py-1 text-xs font-semibold text-[#397C6B] sm:inline-flex">
              Student
            </span>
          </section>

          {/* MAIN TWO-COLUMN LAYOUT */}

          <div className="grid items-start gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(320px,1fr)]">

            {/* LEFT: READ-ONLY INFORMATION */}

            <section className="aca-panel min-w-0 p-4">

              <SectionTitle Icon={UserRound}>
                Personal Information
              </SectionTitle>

              <div className="grid grid-cols-2 gap-2">
                <ProfileField
                  label="Full Name"
                  value={profile.fullName ?? user?.fullName}
                />

                <ProfileField
                  label="Student ID"
                  value={profile.studentId}
                />

                <ProfileField
                  label="Username"
                  value={profile.username ?? user?.username}
                />

                <ProfileField
                  label="Citizen ID"
                  value={profile.citizenId}
                />

                <ProfileField
                  label="Date of Birth"
                  value={
                    typeof profile.dateOfBirth === "string"
                      ? profile.dateOfBirth.slice(0, 10)
                      : profile.dateOfBirth
                  }
                />

                <ProfileField
                  label="Gender"
                  value={profile.gender}
                />
              </div>

              <div className="my-4 border-t border-[#E8EFF7]" />

              <SectionTitle Icon={GraduationCap}>
                Academic Information
              </SectionTitle>

              <div className="grid grid-cols-2 gap-2">
                <ProfileField
                  label="Major"
                  value={profile.majorName}
                />

                <ProfileField
                  label="Faculty"
                  value={profile.facultyName}
                />

                <div className="col-span-2">
                  <ProfileField
                    label="Academic Status"
                    value={profile.academicStatus}
                  />
                </div>
              </div>
            </section>

            {/* RIGHT: EDITABLE CONTACT INFORMATION */}

            <section className="aca-panel min-w-0 p-4">

              <div className="mb-4 flex items-center justify-between gap-2">
                <SectionTitle Icon={Mail}>
                  Contact Information
                </SectionTitle>

                {!editing && (
                  <button
                    type="button"
                    onClick={startEditing}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#E5F0FC] px-3 py-2 text-xs font-semibold text-[#476FA9] hover:bg-[#D7E8FA]"
                  >
                    <Pencil size={14} />
                    Edit
                  </button>
                )}
              </div>

              <form onSubmit={handleSave} className="space-y-3">

                <div>
                  <label
                    htmlFor="profile-email"
                    className="mb-1.5 block text-xs font-semibold text-[#536D8D]"
                  >
                    Email Address
                  </label>

                  <input
                    id="profile-email"
                    type="email"
                    autoComplete="email"
                    maxLength={100}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={!editing || saving}
                    className="h-10 w-full rounded-xl border border-[#D9E6F3] bg-[#F8FBFF] px-3 text-sm text-[#365D91] outline-none focus:border-[#83ACDD] focus:ring-2 focus:ring-[#DCEAFB] disabled:opacity-75"
                  />
                </div>

                <div>
                  <label
                    htmlFor="profile-phone"
                    className="mb-1.5 block text-xs font-semibold text-[#536D8D]"
                  >
                    Phone Number
                  </label>

                  <input
                    id="profile-phone"
                    type="tel"
                    autoComplete="tel"
                    maxLength={15}
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    disabled={!editing || saving}
                    className="h-10 w-full rounded-xl border border-[#D9E6F3] bg-[#F8FBFF] px-3 text-sm text-[#365D91] outline-none focus:border-[#83ACDD] focus:ring-2 focus:ring-[#DCEAFB] disabled:opacity-75"
                  />
                </div>

                {saveError && (
                  <p
                    role="alert"
                    className="flex items-start gap-2 rounded-lg bg-[#FFF1F2] p-3 text-xs text-[#AE4757]"
                  >
                    <AlertCircle size={15} className="shrink-0" />
                    {saveError}
                  </p>
                )}

                {message && (
                  <p
                    role="status"
                    className="flex items-start gap-2 rounded-lg bg-[#EBF8F1] p-3 text-xs text-[#35775F]"
                  >
                    <CheckCircle2 size={15} className="shrink-0" />
                    {message}
                  </p>
                )}

                {editing && (
                  <div className="flex gap-2 pt-1">
                    <button
                      type="button"
                      disabled={saving}
                      onClick={cancelEditing}
                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-[#D9E6F3] px-3 py-2.5 text-sm font-semibold text-[#68819D] disabled:opacity-60"
                    >
                      <X size={16} />
                      Cancel
                    </button>

                    <button
                      type="submit"
                      disabled={saving}
                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-[#729FD6] px-3 py-2.5 text-sm font-semibold text-white hover:bg-[#5D8CC8] disabled:opacity-60"
                    >
                      <Save size={16} />
                      {saving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                )}
              </form>

              <div className="mt-4 border-t border-[#E8EFF7] pt-3">
                <div className="flex items-start gap-2">
                  <BookOpen
                    size={16}
                    className="shrink-0 text-[#7197C4]"
                  />

                  <p className="text-xs leading-5 text-[#8295AA]">
                    Only Email Address and Phone Number can
                    be updated. Personal and academic records
                    are read-only.
                  </p>
                </div>
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

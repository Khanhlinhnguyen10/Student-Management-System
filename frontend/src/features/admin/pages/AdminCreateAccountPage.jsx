
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import {
  AlertCircle,
  BookOpen,
  Building2,
  CheckCircle2,
  GraduationCap,
  Loader2,
  RefreshCw,
  ShieldCheck,
  UserPlus,
} from "lucide-react";

import {
  createAdminAccount,
  fetchCreateAccountFaculties,
  fetchCreateAccountMajors,
} from "../api/adminCreateAccountApi";

// =========================================
// FORM INITIAL STATE
// =========================================

const EMPTY_FORM = {
  username: "",
  citizenId: "",
  fullName: "",
  dateOfBirth: "",
  email: "",
  phoneNumber: "",
  gender: "",
  majorId: "",
  facultyId: "",
  academicStatus: "",
};

const INPUT_CLASS =
  "w-full min-w-0 rounded-xl border border-[#D7E4F3] " +
  "bg-[#FAFCFF] px-3.5 py-2.5 text-sm text-[#304862] " +
  "outline-none transition placeholder:text-[#A0AEC0] " +
  "focus:border-[#80B6E8] focus:bg-white " +
  "focus:ring-2 focus:ring-[#DDEFFD] " +
  "disabled:cursor-not-allowed disabled:opacity-60";

const LABEL_CLASS =
  "mb-1.5 block text-xs font-semibold text-[#496681]";

// =========================================
// REUSABLE FORM FIELD
// =========================================

function FormField({
  name,
  label,
  value,
  onChange,
  type = "text",
  maxLength,
  placeholder,
  required = true,
  autoComplete = "off",
}) {
  return (
    <div className="min-w-0">
      <label htmlFor={`account-${name}`} className={LABEL_CLASS}>
        {label}
        {required && (
          <span className="ml-1 text-[#D77E8A]">*</span>
        )}
      </label>

      <input
        id={`account-${name}`}
        name={name}
        type={type}
        value={value}
        onChange={(event) =>
          onChange(name, event.target.value)
        }
        maxLength={maxLength}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        className={INPUT_CLASS}
      />
    </div>
  );
}

// =========================================
// ACCOUNT TYPE CARD
// =========================================

function AccountTypeCard({
  type,
  label,
  description,
  icon: Icon,
  active,
  disabled,
  onClick,
}) {
  return (
    <button
      type="button"
      onClick={() => onClick(type)}
      disabled={disabled}
      aria-pressed={active}
      className={[
        "flex w-full items-center gap-3 rounded-2xl",
        "border px-4 py-3 text-left transition",
        "disabled:cursor-not-allowed disabled:opacity-60",
        active
          ? "border-[#8CBCEB] bg-[#EAF4FF] shadow-sm"
          : "border-[#E1EAF4] bg-white hover:bg-[#F6FAFF]",
      ].join(" ")}
    >
      <div
        className={[
          "flex h-11 w-11 shrink-0 items-center",
          "justify-center rounded-xl",
          active
            ? "bg-[#D2E8FD] text-[#397EBB]"
            : "bg-[#EFF4FA] text-[#8298B0]",
        ].join(" ")}
      >
        <Icon size={21} strokeWidth={1.9} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="text-sm font-bold text-[#344E6B]">
          {label}
        </div>

        <div className="mt-0.5 text-xs text-[#7990A6]">
          {description}
        </div>
      </div>

      <span
        className={[
          "flex h-5 w-5 shrink-0 items-center",
          "justify-center rounded-full border",
          active
            ? "border-[#79B3EB] bg-[#7DB9EE]"
            : "border-[#C8D6E5] bg-white",
        ].join(" ")}
      >
        {active && (
          <span className="h-2 w-2 rounded-full bg-white" />
        )}
      </span>
    </button>
  );
}

// =========================================
// MAIN PAGE
// =========================================

export default function AdminCreateAccountPage() {
  const [searchParams] = useSearchParams();

  // Supports navigation from Students page:
  // /admin/create-account?type=student
  const requestedType =
    searchParams.get("type")?.toLowerCase() === "lecturer"
      ? "Lecturer"
      : "Student";

  const [accountType, setAccountType] = useState(requestedType);
  const [form, setForm] = useState({ ...EMPTY_FORM });

  const [options, setOptions] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [optionsError, setOptionsError] = useState("");
  const [reloadIndex, setReloadIndex] = useState(0);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [outcome, setOutcome] = useState(null);

  // =========================================
  // SYNC WITH ROUTE
  // =========================================

  useEffect(() => {
    setAccountType(requestedType);
  }, [requestedType]);

  // =========================================
  // LOAD MAJORS / FACULTIES
  // =========================================

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    async function loadOptions() {
      setLoadingOptions(true);
      setOptions([]);
      setOptionsError("");

      try {
        const data =
          accountType === "Student"
            ? await fetchCreateAccountMajors({
                signal: controller.signal,
              })
            : await fetchCreateAccountFaculties({
                signal: controller.signal,
              });

        if (active) {
          setOptions(data);
        }
      } catch (err) {
        if (active && err.name !== "AbortError") {
          setOptionsError(
            err.message || "Unable to load academic options."
          );
        }
      } finally {
        if (active) {
          setLoadingOptions(false);
        }
      }
    }

    loadOptions();

    return () => {
      active = false;
      controller.abort();
    };
  }, [accountType, reloadIndex]);

  // =========================================
  // HANDLE FORM CHANGES
  // =========================================

  function handleFieldChange(name, value) {
    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
  }

  function handleAccountTypeChange(type) {
    if (submitting || type === accountType) {
      return;
    }

    setAccountType(type);
    setError("");
    setOutcome(null);

    setForm((current) => ({
      ...current,
      majorId: "",
      facultyId: "",
      academicStatus: "",
    }));
  }

  function handleNewAccount() {
    setForm({ ...EMPTY_FORM });
    setError("");
    setOutcome(null);
  }

  // =========================================
  // SUBMIT CREATE ACCOUNT
  // =========================================

  async function handleSubmit(event) {
    event.preventDefault();

    if (
      submitting ||
      loadingOptions ||
      optionsError ||
      options.length === 0 ||
      outcome
    ) {
      return;
    }

    setSubmitting(true);
    setError("");

    const payload = {
      accountType,
      username: form.username.trim(),
      citizenId: form.citizenId.trim(),
      fullName: form.fullName.trim(),
      dateOfBirth: form.dateOfBirth,
      email: form.email.trim(),
      phoneNumber: form.phoneNumber.trim(),
      gender: form.gender.trim(),
    };

    if (accountType === "Student") {
      payload.majorId = form.majorId;
      payload.academicStatus = form.academicStatus.trim();
    } else {
      payload.facultyId = form.facultyId;
    }

    try {
      const result = await createAdminAccount(payload);

      setOutcome({
        kind: "success",
        account: result.account,
      });

      setForm({ ...EMPTY_FORM });
    } catch (err) {
      // A delivery failure happens AFTER SQL commit.
      // Block an immediate retry to avoid duplicate creation.
      if (err.status === 502) {
        setOutcome({
          kind: "deliveryFailed",
          account: err.data?.account || null,
          message: err.message,
        });
      } else {
        setError(
          err.message || "Unable to create account."
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  const isStudent = accountType === "Student";

  const optionsUnavailable =
    loadingOptions ||
    Boolean(optionsError) ||
    options.length === 0;

  // =========================================
  // PAGE RENDER
  // =========================================

  return (
    <div className="mx-auto w-full max-w-6xl min-w-0 space-y-4 pb-6">
      {/* HEADER */}
      <div
        className="rounded-2xl border border-[#DFEAF7] px-5 py-4"
        style={{
          background:
            "linear-gradient(110deg, #EDF6FF 0%, #F6FAFF 65%, #F5F0FF 100%)",
        }}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/85 text-[#609ED6] shadow-sm">
            <UserPlus size={22} strokeWidth={1.9} />
          </div>

          <div className="min-w-0">
            <h1 className="text-xl font-bold text-[#345575]">
              Create Account
            </h1>

            <p className="mt-0.5 text-xs text-[#738DA7]">
              Create student and lecturer accounts
            </p>
          </div>
        </div>
      </div>

      {/* ACCOUNT TYPE */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <AccountTypeCard
          type="Student"
          label="Student Account"
          description="Create a student account and record"
          icon={GraduationCap}
          active={isStudent}
          disabled={submitting}
          onClick={handleAccountTypeChange}
        />

        <AccountTypeCard
          type="Lecturer"
          label="Lecturer Account"
          description="Create a lecturer account and profile"
          icon={Building2}
          active={!isStudent}
          disabled={submitting}
          onClick={handleAccountTypeChange}
        />
      </div>

      {/* VALIDATION ERROR */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-[#F4CED4] bg-[#FFF5F6] px-4 py-3 text-sm text-[#A94D5B]"
        >
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SUCCESS / DELIVERY RESULT */}
      {outcome && (
        <div
          role="status"
          className={[
            "rounded-2xl border px-4 py-4",
            outcome.kind === "success"
              ? "border-[#C5E6D6] bg-[#F0FBF5]"
              : "border-[#F0D8B5] bg-[#FFF9EE]",
          ].join(" ")}
        >
          <div className="flex items-start gap-3">
            {outcome.kind === "success" ? (
              <CheckCircle2
                size={21}
                className="mt-0.5 shrink-0 text-[#419C79]"
              />
            ) : (
              <AlertCircle
                size={21}
                className="mt-0.5 shrink-0 text-[#C28B42]"
              />
            )}

            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-[#3D5A6A]">
                {outcome.kind === "success"
                  ? "Account created successfully"
                  : "Account created, but notification failed"}
              </p>

              <p className="mt-1 text-xs leading-relaxed text-[#688096]">
                {outcome.kind === "success"
                  ? "The account was saved and credential delivery was submitted."
                  : "The database transaction may already be committed. Do not submit the same account again."}
              </p>

              {outcome.account && (
                <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs font-semibold text-[#4C718D]">
                  <span>
                    User ID: {outcome.account.userId}
                  </span>

                  {outcome.account.studentId && (
                    <span>
                      Student ID: {outcome.account.studentId}
                    </span>
                  )}

                  {outcome.account.lecturerId && (
                    <span>
                      Lecturer ID: {outcome.account.lecturerId}
                    </span>
                  )}
                </div>
              )}

              <button
                type="button"
                onClick={handleNewAccount}
                className="mt-3 rounded-lg border border-[#A8CEE9] bg-white px-3 py-2 text-xs font-semibold text-[#397DAE] transition hover:bg-[#F3F9FF]"
              >
                Create another account
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MAIN FORM */}
      <form
        onSubmit={handleSubmit}
        className="overflow-hidden rounded-2xl border border-[#E0E9F4] bg-white shadow-sm"
      >
        <fieldset disabled={submitting || Boolean(outcome)}>
          {/* PERSONAL INFORMATION */}
          <div className="border-b border-[#EDF1F7] px-5 py-4">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-lg bg-[#EAF4FF] p-2 text-[#669CD0]">
                <UserPlus size={17} />
              </div>

              <div>
                <h2 className="text-sm font-bold text-[#385571]">
                  Personal Information
                </h2>

                <p className="text-xs text-[#8A9DB0]">
                  Enter information from the official record
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              <FormField
                name="fullName"
                label="Full Name"
                value={form.fullName}
                onChange={handleFieldChange}
                maxLength={200}
                placeholder="Enter full name"
              />

              <FormField
                name="citizenId"
                label="Citizen ID Number"
                value={form.citizenId}
                onChange={handleFieldChange}
                maxLength={12}
                placeholder="Enter Citizen ID"
              />

              <FormField
                name="dateOfBirth"
                label="Date of Birth"
                type="date"
                value={form.dateOfBirth}
                onChange={handleFieldChange}
              />

              <FormField
                name="gender"
                label="Gender"
                value={form.gender}
                onChange={handleFieldChange}
                maxLength={20}
                placeholder="Enter gender"
              />

              <FormField
                name="email"
                label="Email"
                type="email"
                value={form.email}
                onChange={handleFieldChange}
                maxLength={100}
                placeholder="Enter email address"
              />

              <FormField
                name="phoneNumber"
                label="Phone Number"
                type="tel"
                value={form.phoneNumber}
                onChange={handleFieldChange}
                maxLength={15}
                placeholder="Enter phone number"
              />
            </div>
          </div>

          {/* ACCOUNT INFORMATION */}
          <div className="border-b border-[#EDF1F7] px-5 py-4">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-lg bg-[#F0ECFF] p-2 text-[#9480CF]">
                <ShieldCheck size={17} />
              </div>

              <div>
                <h2 className="text-sm font-bold text-[#385571]">
                  Account Information
                </h2>

                <p className="text-xs text-[#8A9DB0]">
                  IDs and initial credentials are generated by the system
                </p>
              </div>
            </div>

            <div className="max-w-md">
              <FormField
                name="username"
                label="Username"
                value={form.username}
                onChange={handleFieldChange}
                maxLength={50}
                placeholder="Enter username"
              />
            </div>
          </div>

          {/* ACADEMIC INFORMATION */}
          <div className="px-5 py-4">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="rounded-lg bg-[#E8F7F2] p-2 text-[#56A794]">
                  <BookOpen size={17} />
                </div>

                <div>
                  <h2 className="text-sm font-bold text-[#385571]">
                    Academic Information
                  </h2>

                  <p className="text-xs text-[#8A9DB0]">
                    {isStudent
                      ? "Select the student's major and status"
                      : "Select the lecturer's faculty"}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() =>
                  setReloadIndex((current) => current + 1)
                }
                disabled={loadingOptions || submitting}
                className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-semibold text-[#568FBE] hover:bg-[#F0F7FF] disabled:opacity-50"
              >
                <RefreshCw size={14} />
                Refresh
              </button>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="min-w-0">
                <label
                  htmlFor="academic-option"
                  className={LABEL_CLASS}
                >
                  {isStudent ? "Major" : "Faculty"}
                  <span className="ml-1 text-[#D77E8A]">
                    *
                  </span>
                </label>

                <select
                  id="academic-option"
                  name={isStudent ? "majorId" : "facultyId"}
                  required
                  value={
                    isStudent ? form.majorId : form.facultyId
                  }
                  onChange={(event) =>
                    handleFieldChange(
                      isStudent ? "majorId" : "facultyId",
                      event.target.value
                    )
                  }
                  disabled={optionsUnavailable}
                  className={INPUT_CLASS}
                >
                  <option value="">
                    {loadingOptions
                      ? "Loading..."
                      : isStudent
                        ? "Select major"
                        : "Select faculty"}
                  </option>

                  {options.map((option) =>
                    isStudent ? (
                      <option
                        key={option.majorId}
                        value={option.majorId}
                      >
                        {option.majorName}
                        {option.facultyName
                          ? ` - ${option.facultyName}`
                          : ""}
                      </option>
                    ) : (
                      <option
                        key={option.facultyId}
                        value={option.facultyId}
                      >
                        {option.facultyName}
                      </option>
                    )
                  )}
                </select>

                {optionsError && (
                  <p
                    role="alert"
                    className="mt-1.5 text-xs text-[#C15F6B]"
                  >
                    {optionsError}
                  </p>
                )}

                {!loadingOptions &&
                  !optionsError &&
                  options.length === 0 && (
                    <p className="mt-1.5 text-xs text-[#A27F56]">
                      No academic options are available.
                    </p>
                  )}
              </div>

              {isStudent && (
                <FormField
                  name="academicStatus"
                  label="Academic Status"
                  value={form.academicStatus}
                  onChange={handleFieldChange}
                  maxLength={60}
                  placeholder="Enter academic status"
                />
              )}
            </div>
          </div>

          {/* FORM ACTIONS */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#EDF1F7] bg-[#FAFCFF] px-5 py-4">
            <p className="max-w-lg text-xs leading-relaxed text-[#8296AB]">
              Account creation requires an active Administrator
              session and configured credential delivery.
            </p>

            <button
              type="submit"
              disabled={
                submitting ||
                optionsUnavailable ||
                Boolean(outcome)
              }
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-[#70ACE2] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#5B9CD7] disabled:cursor-not-allowed disabled:opacity-55"
            >
              {submitting ? (
                <>
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />
                  Creating...
                </>
              ) : (
                <>
                  <UserPlus size={17} />
                  Create {accountType} Account
                </>
              )}
            </button>
          </div>
        </fieldset>
      </form>
    </div>
  );
}

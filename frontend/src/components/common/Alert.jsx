
import {
  CheckCircle2,
  CircleAlert,
  TriangleAlert,
  Info,
} from "lucide-react";

// Quy chuẩn giao diện thông báo dùng chung
const ALERT_VARIANTS = {
  success: {
    Icon: CheckCircle2,
    title: "Success",
    container: "border-green-200 bg-green-50",
    text: "text-green-800",
  },

  error: {
    Icon: CircleAlert,
    title: "Error",
    container: "border-red-200 bg-red-50",
    text: "text-red-800",
  },

  warning: {
    Icon: TriangleAlert,
    title: "Warning",
    container: "border-amber-200 bg-amber-50",
    text: "text-amber-800",
  },

  info: {
    Icon: Info,
    title: "Information",
    container: "border-blue-200 bg-[#EAF4FF]",
    text: "text-blue-800",
  },
};

function Alert({
  variant = "info",
  title,
  children,
}) {
  const config =
    ALERT_VARIANTS[variant] ?? ALERT_VARIANTS.info;

  const Icon = config.Icon;

  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={`
        rounded-xl border px-4 py-3
        ${config.container}
      `}
    >
      <div className="flex items-start gap-3">
        <Icon
          size={19}
          strokeWidth={1.8}
          aria-hidden="true"
          className={`mt-0.5 shrink-0 ${config.text}`}
        />

        <div className="min-w-0">
          <p
            className={`text-sm font-semibold ${config.text}`}
          >
            {title ?? config.title}
          </p>

          {children && (
            <div
              className={`mt-1 text-sm leading-5 ${config.text}`}
            >
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Alert;


import { Inbox } from "lucide-react";

function EmptyState({
  title = "No data found",
  description = "There is no information to display.",
  icon: Icon = Inbox,
  action,
}) {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center rounded-xl border border-dashed border-[#C9DFF2] bg-white/60 px-6 py-8 text-center">

      {/* Empty state icon */}
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#E6F1FF] text-[#3674B6]">
        <Icon
          size={27}
          strokeWidth={1.7}
          aria-hidden="true"
        />
      </div>

      {/* Message */}
      <h3 className="mt-4 text-base font-semibold text-[#194B7C]">
        {title}
      </h3>

      <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
        {description}
      </p>

      {/* Optional action */}
      {action && (
        <div className="mt-5">
          {action}
        </div>
      )}

    </div>
  );
}

export default EmptyState;

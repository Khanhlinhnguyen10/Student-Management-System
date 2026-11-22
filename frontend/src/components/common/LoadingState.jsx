
import { LoaderCircle } from "lucide-react";

function LoadingState({
  message = "Loading data...",
  fullPage = false,
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={`
        flex flex-col items-center justify-center
        px-6 py-10 text-center
        ${fullPage ? "min-h-dvh" : "min-h-[180px]"}
      `}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E6F1FF]">
        <LoaderCircle
          size={25}
          strokeWidth={1.8}
          aria-hidden="true"
          className="animate-spin text-[#3674B6]"
        />
      </div>

      <p className="mt-4 text-sm font-medium text-[#456987]">
        {message}
      </p>
    </div>
  );
}

export default LoadingState;


import { useEffect, useRef } from "react";
import { TriangleAlert } from "lucide-react";

function ConfirmDialog({
  isOpen,
  title = "Confirm Action",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  variant = "danger",
  isLoading = false,
  onConfirm,
  onCancel,
}) {
  const dialogRef = useRef(null);

  // Đồng bộ trạng thái React với HTML dialog
  useEffect(() => {
    const dialog = dialogRef.current;

    if (!dialog) return;

    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  const isDanger = variant === "danger";

  const handleCancel = () => {
    if (isLoading) return;
    onCancel?.();
  };

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      onCancel={(event) => {
        event.preventDefault();
        handleCancel();
      }}
      className="w-[calc(100%-2rem)] max-w-md rounded-2xl border border-slate-200 bg-white p-0 text-slate-800 shadow-2xl backdrop:bg-slate-900/40"
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start gap-4">
          <div
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${
              isDanger
                ? "bg-red-50 text-red-600"
                : "bg-blue-50 text-blue-700"
            }`}
          >
            <TriangleAlert
              size={22}
              strokeWidth={1.8}
              aria-hidden="true"
            />
          </div>

          <div className="min-w-0">
            <h2
              id="confirm-dialog-title"
              className="text-lg font-semibold text-slate-900"
            >
              {title}
            </h2>

            <p
              id="confirm-dialog-message"
              className="mt-2 text-sm leading-6 text-slate-600"
            >
              {message}
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-7 flex justify-end gap-3">
          <button
            type="button"
            onClick={handleCancel}
            disabled={isLoading}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {cancelText}
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`rounded-lg px-4 py-2.5 text-sm font-semibold text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
              isDanger
                ? "bg-red-600 hover:bg-red-700"
                : "bg-[#3674B6] hover:bg-[#28649F]"
            }`}
          >
            {isLoading ? "Processing..." : confirmText}
          </button>
        </div>
      </div>
    </dialog>
  );
}

export default ConfirmDialog;

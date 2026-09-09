import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import type { CatalogItem, CatalogItemInput } from "../../lib/catalog";
import { inputClass } from "../../lib/styles";

type TierRow = { min_qty: string; unit_price: string };

function toTierRows(item: CatalogItem | null): TierRow[] {
  if (!item || item.tiers.length === 0) return [{ min_qty: "", unit_price: "" }];
  return [...item.tiers]
    .sort((a, b) => a.min_qty - b.min_qty)
    .map((t) => ({ min_qty: String(t.min_qty), unit_price: String(t.unit_price) }));
}

export function CatalogItemDialog({
  item,
  isSaving,
  errorMessage,
  onCancel,
  onSave,
}: {
  /** null = creating a new item */
  item: CatalogItem | null;
  isSaving: boolean;
  errorMessage: string | null;
  onCancel: () => void;
  onSave: (input: CatalogItemInput) => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [name, setName] = useState(item?.name ?? "");
  const [unit, setUnit] = useState(item?.unit ?? "");
  const [tiers, setTiers] = useState<TierRow[]>(toTierRows(item));
  const [formError, setFormError] = useState<string | null>(null);

  // Native <dialog>: open on mount, treat Escape as cancel via onClose below.
  // No close() in cleanup: StrictMode double-invokes this effect (run,
  // cleanup, run again) on mount, and dialog.close() fires a real "close"
  // event that onClose picks up as a user cancel — closing the dialog
  // before it's ever seen. Guard showModal() itself against a dialog
  // that's already open, since the double-invoke calls this twice.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);

  function updateTier(index: number, field: keyof TierRow, value: string) {
    setTiers((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  }

  function addTier() {
    setTiers((rows) => [...rows, { min_qty: "", unit_price: "" }]);
  }

  function removeTier(index: number) {
    setTiers((rows) => rows.filter((_, i) => i !== index));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);

    const parsedTiers = tiers.map((row) => ({
      min_qty: Number(row.min_qty),
      unit_price: Number(row.unit_price),
    }));

    const isValidPositiveInt = (n: number) => Number.isInteger(n) && n > 0;
    if (parsedTiers.some((t) => !isValidPositiveInt(t.min_qty) || !isValidPositiveInt(t.unit_price))) {
      setFormError("Quantity and price must be whole numbers greater than 0.");
      return;
    }

    const seenQty = new Set(parsedTiers.map((t) => t.min_qty));
    if (seenQty.size !== parsedTiers.length) {
      setFormError("Each tier needs a different starting quantity.");
      return;
    }

    onSave({ name, unit, tiers: parsedTiers });
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onCancel}
      className="w-[min(480px,calc(100vw-32px))] rounded-[14px] border border-line bg-surface p-0 text-ink shadow-[var(--shadow)] backdrop:bg-black/40 backdrop:backdrop-blur-sm"
    >
      <form
        onSubmit={handleSubmit}
        className="flex max-h-[85vh] flex-col gap-4 overflow-y-auto p-[clamp(20px,5vw,28px)]"
      >
        <h2 className="font-serif text-xl font-semibold tracking-tight">
          {item ? "Edit item" : "Add item"}
        </h2>

        <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink-2">
          Name
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Faïence 20×20"
            className={inputClass}
          />
        </label>

        <label className="flex flex-col gap-1.5 text-[13px] font-medium text-ink-2">
          Unit
          <input
            required
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            placeholder="m²"
            className={inputClass}
          />
        </label>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[13px] font-medium text-ink-2">Quantity tiers</span>
            <button
              type="button"
              onClick={addTier}
              className="rounded text-[13px] font-semibold text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              + Add tier
            </button>
          </div>

          {tiers.map((tier, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                required
                type="number"
                min={1}
                step={1}
                value={tier.min_qty}
                onChange={(e) => updateTier(index, "min_qty", e.target.value)}
                placeholder="From qty"
                className={`${inputClass} w-1/2`}
              />
              <input
                required
                type="number"
                min={1}
                step={1}
                value={tier.unit_price}
                onChange={(e) => updateTier(index, "unit_price", e.target.value)}
                placeholder="Price (DA)"
                className={`${inputClass} w-1/2`}
              />
              <button
                type="button"
                onClick={() => removeTier(index)}
                disabled={tiers.length === 1}
                aria-label="Remove tier"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-ink-3 transition-colors duration-150 hover:bg-surface-2 hover:text-alert disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-ink-3"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        {(formError ?? errorMessage) && (
          <p className="text-[13px] text-alert">{formError ?? errorMessage}</p>
        )}

        <div className="flex justify-end gap-2 border-t border-line pt-3.5">
          <Button type="button" variant="secondary" size="sm" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" size="sm" disabled={isSaving}>
            {isSaving ? "…" : "Save"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}

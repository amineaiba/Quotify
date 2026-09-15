import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import type { CatalogItem } from "../../lib/catalog";
import { formatPrice } from "../../lib/format";

/** Turns raw `min_qty` breakpoints into readable ranges: "1–9", "10+". */
function tierRanges(item: CatalogItem) {
  const sorted = [...item.tiers].sort((a, b) => a.min_qty - b.min_qty);
  return sorted.map((tier, i) => {
    const nextMin = sorted[i + 1]?.min_qty;
    const label = nextMin ? `${tier.min_qty}–${nextMin - 1}` : `${tier.min_qty}+`;
    return { key: tier.id, label, price: formatPrice(tier.unit_price) };
  });
}

function PricingSummary({ item }: { item: CatalogItem }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Badge tone={item.tiers.length > 1 ? "ok" : "neutral"}>
        {item.tiers.length > 1 ? `Tiered · ${item.tiers.length}` : "Flat rate"}
      </Badge>
      <div className="flex flex-col gap-0.5 font-mono text-[13px] text-ink-2">
        {tierRanges(item).map((tier) => (
          <span key={tier.key}>
            {tier.label}: {tier.price}
          </span>
        ))}
      </div>
    </div>
  );
}

type RowActionsProps = {
  item: CatalogItem;
  onEdit: (item: CatalogItem) => void;
  onDelete: (item: CatalogItem) => void;
  isDeleting: boolean;
};

function RowActions({ item, onEdit, onDelete, isDeleting }: RowActionsProps) {
  return (
    <div className="flex gap-2">
      <Button variant="secondary" size="sm" onClick={() => onEdit(item)}>
        Edit
      </Button>
      <Button variant="secondary" size="sm" onClick={() => onDelete(item)} disabled={isDeleting}>
        {isDeleting ? "…" : "Delete"}
      </Button>
    </div>
  );
}

type CatalogTableProps = {
  items: CatalogItem[];
  onEdit: (item: CatalogItem) => void;
  onDelete: (item: CatalogItem) => void;
  deletingId: string | null;
};

export function CatalogTable({ items, onEdit, onDelete, deletingId }: CatalogTableProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1.5 rounded-[14px] border border-dashed border-line-strong bg-surface px-6 py-14 text-center">
        <span className="text-sm font-medium text-ink-2">No items yet</span>
        <span className="text-sm text-ink-3">Add your first catalog item to start pricing quotes.</span>
      </div>
    );
  }

  return (
    <>
      {/* Below sm: stacked cards, so Edit/Delete stay reachable without a horizontal scroll. */}
      <div className="flex flex-col gap-3 sm:hidden">
        {items.map((item) => (
          <div
            key={item.id}
            className="flex flex-col gap-3 rounded-[14px] border border-line bg-surface p-4 shadow-[var(--shadow)]"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-ink-2">{item.unit}</div>
              </div>
              <PricingSummary item={item} />
            </div>
            <RowActions
              item={item}
              onEdit={onEdit}
              onDelete={onDelete}
              isDeleting={deletingId === item.id}
            />
          </div>
        ))}
      </div>

      {/* sm and up: table */}
      <div className="hidden overflow-x-auto rounded-[14px] border border-line bg-surface shadow-[var(--shadow)] sm:block">
        <table className="w-full min-w-[600px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-left text-[13px] font-medium text-ink-3">
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Unit</th>
              <th className="px-4 py-3 font-medium">Pricing</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-b border-line last:border-b-0">
                <td className="px-4 py-3 font-medium align-top">{item.name}</td>
                <td className="px-4 py-3 align-top text-ink-2">{item.unit}</td>
                <td className="px-4 py-3 align-top">
                  <PricingSummary item={item} />
                </td>
                <td className="px-4 py-3 align-top">
                  <div className="flex justify-end">
                    <RowActions
                      item={item}
                      onEdit={onEdit}
                      onDelete={onDelete}
                      isDeleting={deletingId === item.id}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

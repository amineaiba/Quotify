export function formatPrice(amount: number) {
  return `${amount.toLocaleString("fr-FR")} DA`;
}

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Two-letter avatar initials from a name, or the first two digits of a phone number. */
export function initials(name: string | null, phoneNumber: string) {
  if (name) {
    const parts = name.trim().split(/\s+/);
    return parts
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("");
  }
  return phoneNumber.replace(/\D/g, "").slice(-2);
}

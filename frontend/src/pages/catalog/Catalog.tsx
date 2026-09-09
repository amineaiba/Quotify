import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/Button";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import { catalogApi, type CatalogItem, type CatalogItemInput } from "../../lib/catalog";
import type { Theme } from "../../lib/useTheme";
import { CatalogHeader } from "./CatalogHeader";
import { CatalogItemDialog } from "./CatalogItemDialog";
import { CatalogTable } from "./CatalogTable";

const CATALOG_QUERY_KEY = ["catalog-items"];

export function Catalog({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editingItem, setEditingItem] = useState<CatalogItem | "new" | null>(null);

  const itemsQuery = useQuery({ queryKey: CATALOG_QUERY_KEY, queryFn: catalogApi.list });

  const createMutation = useMutation({
    mutationFn: (input: CatalogItemInput) => catalogApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATALOG_QUERY_KEY });
      setEditingItem(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: CatalogItemInput }) =>
      catalogApi.update(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATALOG_QUERY_KEY });
      setEditingItem(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => catalogApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CATALOG_QUERY_KEY }),
  });

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  function handleDelete(item: CatalogItem) {
    if (window.confirm(`Delete "${item.name}"? This can't be undone.`)) {
      deleteMutation.mutate(item.id);
    }
  }

  // Clear any error left over from a previous save so a fresh dialog never
  // shows a stale message from a different item's failed attempt.
  function openDialog(item: CatalogItem | "new") {
    createMutation.reset();
    updateMutation.reset();
    setEditingItem(item);
  }

  function closeDialog() {
    setEditingItem(null);
  }

  const saveMutation = editingItem === "new" ? createMutation : updateMutation;
  const saveErrorMessage =
    saveMutation.error instanceof ApiError ? saveMutation.error.detail : null;

  return (
    <div className="min-h-screen bg-bg text-ink">
      <CatalogHeader theme={theme} onToggleTheme={onToggleTheme} onLogout={handleLogout} />

      <main className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-8 sm:px-10">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="font-serif text-2xl font-semibold tracking-tight">Catalog</h1>
            <p className="text-sm text-ink-2">Items and quantity tiers your quotes are priced from.</p>
          </div>
          <Button variant="primary" size="sm" onClick={() => openDialog("new")}>
            Add item
          </Button>
        </div>

        {itemsQuery.isLoading && <p className="text-sm text-ink-3">Loading…</p>}
        {itemsQuery.isError && (
          <p className="text-sm text-alert">Couldn't load the catalog. Try reloading the page.</p>
        )}
        {itemsQuery.data && (
          <CatalogTable
            items={itemsQuery.data}
            onEdit={openDialog}
            onDelete={handleDelete}
            deletingId={deleteMutation.isPending ? (deleteMutation.variables ?? null) : null}
          />
        )}
      </main>

      {editingItem && (
        <CatalogItemDialog
          item={editingItem === "new" ? null : editingItem}
          isSaving={saveMutation.isPending}
          errorMessage={saveErrorMessage}
          onCancel={closeDialog}
          onSave={(input) => {
            if (editingItem === "new") createMutation.mutate(input);
            else updateMutation.mutate({ id: editingItem.id, input });
          }}
        />
      )}
    </div>
  );
}

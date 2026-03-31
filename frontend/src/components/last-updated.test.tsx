import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LastUpdated } from "@/components/last-updated";
import { dashboardCopy } from "@/features/dashboard/copy";

describe("LastUpdated", () => {
  it("shows a placeholder when no timestamp is available", () => {
    render(<LastUpdated lastUpdated={null} onRefresh={vi.fn()} />);
    expect(screen.getByText("Last updated -")).toBeInTheDocument();
  });

  it("disables refresh while loading and shows the status message", () => {
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={vi.fn()}
        isRefreshing
      />
    );

    expect(screen.getByRole("button", { name: dashboardCopy.states.refresh })).toBeDisabled();
    expect(screen.getByText(dashboardCopy.states.refreshing)).toBeInTheDocument();
  });

  it("calls the refresh callback when pressed", async () => {
    const onRefresh = vi.fn();
    const user = userEvent.setup();
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={onRefresh}
      />
    );

    await user.click(screen.getByRole("button", { name: dashboardCopy.states.refresh }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

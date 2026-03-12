import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LastUpdated } from "@/components/last-updated";

describe("最終更新表示", () => {
  it("まだ更新が完了していないときはプレースホルダーを表示する", () => {
    render(<LastUpdated lastUpdated={null} onRefresh={vi.fn()} />);

    expect(screen.getByText("Last updated: -")).toBeInTheDocument();
  });

  it("更新中は Refresh を無効化して loading 表示を出す", () => {
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={vi.fn()}
        isRefreshing
      />
    );

    expect(screen.getByRole("button", { name: "Refresh" })).toBeDisabled();
    expect(screen.getByText("Updating...")).toBeInTheDocument();
  });

  it("Refresh 操作で公開 callback を呼び出す", async () => {
    const onRefresh = vi.fn();
    const user = userEvent.setup();
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={onRefresh}
      />
    );

    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
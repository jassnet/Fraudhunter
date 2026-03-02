import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LastUpdated } from "@/components/last-updated";

describe("最終更新表示コンポーネント", () => {
  it("更新時刻がない場合はハイフンを表示する", () => {
    render(
      <LastUpdated lastUpdated={null} onRefresh={vi.fn()} />
    );

    expect(screen.getByText("Last updated: -")).toBeInTheDocument();
  });

  it("更新中はボタンを無効化して進行表示する", () => {
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

  it("Refreshボタン押下で再取得処理を呼び出す", async () => {
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

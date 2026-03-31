import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LastUpdated } from "@/components/last-updated";

describe("最終更新表示", () => {
  it("更新時刻がないときはプレースホルダーを表示する", () => {
    render(<LastUpdated lastUpdated={null} onRefresh={vi.fn()} />);
    expect(screen.getByText("最終更新 -")).toBeInTheDocument();
  });

  it("更新中は再読み込みを無効化して状態を表示する", () => {
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={vi.fn()}
        isRefreshing
      />
    );

    expect(screen.getByRole("button", { name: "更新" })).toBeDisabled();
    expect(screen.getByText("更新中")).toBeInTheDocument();
  });

  it("再読み込み押下で callback を呼ぶ", async () => {
    const onRefresh = vi.fn();
    const user = userEvent.setup();
    render(
      <LastUpdated
        lastUpdated={new Date("2026-01-21T03:30:00Z")}
        onRefresh={onRefresh}
      />
    );

    await user.click(screen.getByRole("button", { name: "更新" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

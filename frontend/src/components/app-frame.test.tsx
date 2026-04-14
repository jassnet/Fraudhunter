import type { ComponentPropsWithoutRef } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { AppFrame } from "./app-frame";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: ComponentPropsWithoutRef<"a">) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

describe("AppFrame", () => {
  it("closes the mobile menu when Escape is pressed", async () => {
    const user = userEvent.setup();
    render(
      <AppFrame>
        <div>content</div>
      </AppFrame>,
    );

    await user.click(screen.getByRole("button", { name: "メニューを開く" }));
    expect(screen.getByRole("dialog", { name: "メインメニュー" })).toBeInTheDocument();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog", { name: "メインメニュー" })).not.toBeInTheDocument();
  });

  it("shows advanced-only navigation after the display mode is switched", async () => {
    const user = userEvent.setup();
    render(
      <AppFrame>
        <div>content</div>
      </AppFrame>,
    );

    expect(screen.queryByRole("link", { name: "検知の仕組み" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "検知設定" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "詳細表示に切り替える" }));

    expect(screen.getByRole("link", { name: "検知の仕組み" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "検知設定" })).toBeInTheDocument();
  });
});

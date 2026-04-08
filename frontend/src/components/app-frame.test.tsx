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
    expect(screen.getByRole("dialog", { name: "主なナビゲーション" })).toBeInTheDocument();

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog", { name: "主なナビゲーション" })).not.toBeInTheDocument();
  });
});

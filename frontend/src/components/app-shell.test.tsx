import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/app-shell";

const navigation = vi.hoisted(() => ({
  pathname: "/",
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
}));

describe("AppShell", () => {
  it("keeps a compact desktop sidebar width and supports collapsed mode", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    const aside = container.querySelector("aside");
    expect(aside).not.toBeNull();
    expect(aside?.className).toContain("w-[216px]");

    const sidebarButtons = within(aside as HTMLElement).getAllByRole("button");
    await user.click(sidebarButtons[1]);

    expect(aside?.className).toContain("w-16");
    expect(within(aside as HTMLElement).getByText("ダ")).toBeInTheDocument();
  });

  it("writes the selected theme to the document root", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    const aside = container.querySelector("aside");
    expect(aside).not.toBeNull();

    const themeToggle = within(aside as HTMLElement).getByRole("button", {
      name: "ライトテーマに切り替える",
    });
    await user.click(themeToggle);

    await waitFor(() => {
      expect(document.documentElement.dataset.theme).toBe("light");
    });
  });

  it("shows the current page title in the mobile header", () => {
    navigation.pathname = "/suspicious/conversions";

    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.getByText("不審コンバージョン", { selector: "div" })).toBeInTheDocument();
  });
});

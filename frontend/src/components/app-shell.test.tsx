import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "@/components/app-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

describe("AppShell", () => {
  it("keeps fixed desktop sidebar widths and supports compact mode", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    const aside = container.querySelector("aside");
    expect(aside).not.toBeNull();
    expect(aside?.className).toContain("w-[240px]");

    const sidebarButtons = within(aside as HTMLElement).getAllByRole("button");
    await user.click(sidebarButtons[1]);

    expect(aside?.className).toContain("w-16");
    expect(within(aside as HTMLElement).getByText("DB")).toBeInTheDocument();
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

    const themeToggle = within(aside as HTMLElement).getByText("LIGHT");
    await user.click(themeToggle);

    await waitFor(() => {
      expect(document.documentElement.dataset.theme).toBe("light");
    });
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DateQuickSelect } from "@/components/date-quick-select";

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

describe("DateQuickSelect", () => {
  it("selects the latest available date from the latest shortcut", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value="2026-01-20"
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-20"]}
      />
    );

    await user.click(screen.getByRole("button", { name: "最新" }));
    expect(onChange).toHaveBeenCalledWith("2026-01-21");
  });

  it("selects today when it is available", async () => {
    const today = formatDate(new Date());
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DateQuickSelect value="" onChange={onChange} availableDates={[today, "2026-01-20"]} />);

    await user.click(screen.getByRole("button", { name: "今日" }));
    expect(onChange).toHaveBeenCalledWith(today);
  });

  it("falls back to the latest date when yesterday is unavailable", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value=""
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-19"]}
      />
    );

    await user.click(screen.getByRole("button", { name: "昨日" }));
    expect(onChange).toHaveBeenCalledWith("2026-01-21");
  });

  it("updates the target date when the select value changes", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value="2026-01-21"
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-20"]}
      />
    );

    await user.selectOptions(screen.getByLabelText("対象日"), "2026-01-20");
    expect(onChange).toHaveBeenCalledWith("2026-01-20");
  });
});

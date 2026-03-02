import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DateQuickSelect } from "@/components/date-quick-select";

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

describe("日付クイック選択コンポーネント", () => {

  it("Latestボタンで先頭日付を選択する", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value="2026-01-20"
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-20"]}
      />
    );

    await user.click(screen.getByRole("button", { name: "Latest" }));
    expect(onChange).toHaveBeenCalledWith("2026-01-21");
  });

  it("Todayボタンで当日日付を選択する", async () => {
    const today = formatDate(new Date());
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value=""
        onChange={onChange}
        availableDates={[today, "2026-01-20"]}
      />
    );

    await user.click(screen.getByRole("button", { name: "Today" }));
    expect(onChange).toHaveBeenCalledWith(today);
  });

  it("Yesterdayが候補にない場合は先頭日付を選択する", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value=""
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-19"]}
      />
    );

    await user.click(screen.getByRole("button", { name: "Yesterday" }));
    expect(onChange).toHaveBeenCalledWith("2026-01-21");
  });

  it("ドロップダウン選択で日付を変更する", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(
      <DateQuickSelect
        value="2026-01-21"
        onChange={onChange}
        availableDates={["2026-01-21", "2026-01-20"]}
      />
    );

    await user.selectOptions(screen.getByLabelText("Select date"), "2026-01-20");
    expect(onChange).toHaveBeenCalledWith("2026-01-20");
  });
});

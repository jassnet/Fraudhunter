import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DateQuickSelect } from "@/components/date-quick-select";

const formatDate = (date: Date) => date.toISOString().slice(0, 10);

describe("日付クイック選択", () => {
  it("最新ボタンで利用可能な最新日を選ぶ", async () => {
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

  it("今日ボタンで利用可能な当日を選ぶ", async () => {
    const today = formatDate(new Date());
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<DateQuickSelect value="" onChange={onChange} availableDates={[today, "2026-01-20"]} />);

    await user.click(screen.getByRole("button", { name: "今日" }));
    expect(onChange).toHaveBeenCalledWith(today);
  });

  it("昨日が利用不可なら最新日に寄せる", async () => {
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

  it("セレクト変更で対象日を直接選べる", async () => {
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

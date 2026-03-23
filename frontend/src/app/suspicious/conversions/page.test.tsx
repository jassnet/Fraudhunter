import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";

describe("不審コンバージョン画面", () => {
  it("画面タイトルと CV 数列を表示する", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: "不審コンバージョン" });
    expect(
      await screen.findByRole("columnheader", { name: "CV 数" })
    ).toBeInTheDocument();
  });
});

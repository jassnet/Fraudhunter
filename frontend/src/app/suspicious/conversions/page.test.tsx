import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";

describe("不正 CV 一覧画面", () => {
  it("画面タイトルと CV 件数列を表示する", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: "Suspicious Conversions" });
    expect(
      await screen.findByRole("columnheader", { name: "Conversions" })
    ).toBeInTheDocument();
  });
});
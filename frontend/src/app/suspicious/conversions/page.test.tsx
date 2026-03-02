import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SuspiciousConversionsPage from "@/app/suspicious/conversions/page";

describe("不正コンバージョン画面", () => {
  it("一覧タイトルとコンバージョン列を表示する", async () => {
    render(<SuspiciousConversionsPage />);

    await screen.findByRole("heading", { name: "Suspicious Conversions" });
    expect(
      await screen.findByRole("columnheader", { name: "Conversions" })
    ).toBeInTheDocument();
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, recordPayChange } from "@/lib/api";

import { PayChangeForm } from "./pay-change-form";

const refresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return { ...actual, recordPayChange: vi.fn() };
});

const recordPayChangeMock = vi.mocked(recordPayChange);

function renderForm() {
  return render(
    <PayChangeForm
      employeeId={42}
      currency="USD"
      hiredOn="2023-01-01"
      current="100000.00"
    />,
  );
}

describe("PayChangeForm", () => {
  beforeEach(() => {
    refresh.mockReset();
    recordPayChangeMock.mockReset();
  });

  it("uses a cents-aware number input and submits a valid pay change", async () => {
    recordPayChangeMock.mockResolvedValue({
      employee_id: 42,
      entry: {
        effective_from: "2026-01-15",
        amount: { amount: "110000.00", currency: "USD" },
        base_amount: { amount: "110000.00", currency: "USD" },
        reason: "merit",
        note: null,
      },
      compa_ratio: "1.100",
      band_position: "within",
      in_effect: true,
    });
    renderForm();

    const amount = screen.getByLabelText("New salary (USD)") as HTMLInputElement;
    expect(amount.type).toBe("number");
    expect(amount.min).toBe("0.01");
    expect(amount.step).toBe("0.01");

    fireEvent.change(amount, { target: { value: "110000.00" } });
    fireEvent.click(screen.getByRole("button", { name: "Record change" }));

    await waitFor(() => {
      expect(recordPayChangeMock).toHaveBeenCalledWith(
        42,
        expect.objectContaining({ amount: "110000.00", reason: "merit" }),
      );
    });
    expect(refresh).toHaveBeenCalledOnce();
    expect(screen.getByRole("status").textContent).toContain("This is their pay now.");
  });

  it("shows the API validation message when a pay change is rejected", async () => {
    recordPayChangeMock.mockRejectedValue(
      new ApiError("A pay record already takes effect on 2026-01-15", 409),
    );
    renderForm();

    fireEvent.change(screen.getByLabelText("New salary (USD)"), {
      target: { value: "110000.00" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record change" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("A pay record already takes effect on 2026-01-15");
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Filters } from "./filters";

const push = vi.fn();
const searchParams = new URLSearchParams("country=IN&page=2");

vi.mock("next/navigation", () => ({
  usePathname: () => "/employees",
  useRouter: () => ({ push }),
  useSearchParams: () => searchParams,
}));

const reference = {
  countries: [{ code: "IN", name: "India", currency: "INR" }],
  departments: ["Engineering"],
  families: ["Software"],
  levels: [{ code: "L3", rank: 3 }],
};

describe("Filters", () => {
  beforeEach(() => {
    push.mockReset();
    searchParams.delete("as_of");
  });

  it("shows the job-family filter and sends the historical date through the URL", async () => {
    render(
      <Filters
        reference={reference}
        showPosition={false}
        showStatus={false}
        showSearch={false}
      />,
    );

    expect(screen.getByLabelText("Job family")).toBeDefined();

    fireEvent.change(screen.getByLabelText("As of date"), {
      target: { value: "2025-12-31" },
    });

    await waitFor(() => {
      expect(push).toHaveBeenCalledWith("/employees?country=IN&as_of=2025-12-31");
    });
  });
});

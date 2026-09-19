import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "../src/App";

describe("App", () => {
  it("renders the product navigation and accessible uploader", () => {
    render(<App />);
    expect(screen.getByRole("link", { name: "MigrateFlow home" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Drop CSV or XLSX files/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Choose employee files")).toHaveAttribute("multiple");
  });

  it("shows an unmistakable empty live state", async () => {
    render(<App />);
    screen.getByRole("button", { name: /Live run/ }).click();
    expect(await screen.findByText("No active migration")).toBeInTheDocument();
  });

  it("rejects an unsupported upload before calling the API", () => {
    render(<App />);
    const input = screen.getByLabelText("Choose employee files");
    fireEvent.change(input, { target: { files: [new File(["x"], "employees.exe")] } });
    expect(screen.getByRole("alert")).toHaveTextContent("not a CSV or XLSX");
    expect(screen.getByRole("button", { name: "Create migration" })).toBeDisabled();
  });
});

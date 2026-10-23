import { describe, expect, test } from "bun:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import App from "/app/src/App";

describe("App", () => {
  test("renders Hello World", () => {
    const output = renderToStaticMarkup(createElement(App));
    expect(output).toContain("Hello, Terminal Tasks!");
  });
});

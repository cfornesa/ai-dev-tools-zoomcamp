import {defineConfig,devices} from "@playwright/test";

export default defineConfig({
  testDir:"./e2e",
  timeout:60_000,
  expect:{timeout:10_000},
  fullyParallel:false,
  reporter:"line",
  use:{baseURL:process.env.E2E_BASE_URL||"http://localhost:5173",trace:"on-first-retry",...devices["Desktop Chrome"]},
});

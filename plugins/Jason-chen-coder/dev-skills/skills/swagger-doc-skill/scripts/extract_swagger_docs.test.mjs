#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptPath = fileURLToPath(new URL("./extract_swagger_docs.mjs", import.meta.url));
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "swagger-doc-skill-"));
const specPath = path.join(tempDir, "example-response.json");

const spec = {
  openapi: "3.0.0",
  info: { title: "Example Response API", version: "1.0" },
  servers: [{ url: "https://api.example.com/v1" }],
  security: [{ BearerAuth: [] }],
  paths: {
    "/login": {
      post: {
        tags: ["User"],
        summary: "Login",
        security: [],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["username", "password"],
                properties: {
                  username: { type: "string", description: "Login name" },
                  password: { type: "string", format: "password" },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "OK",
            content: {
              "application/json": {
                schema: {
                  example: {
                    code: 200,
                    message: "Success",
                    success: true,
                    data: {
                      token: "abc",
                      expiresIn: 3600,
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/profile": {
      get: {
        tags: ["User"],
        summary: "Profile",
        responses: {
          200: {
            description: "OK",
            content: {
              "application/json": {
                schema: {
                  originalRef: "UserProfile",
                },
              },
            },
          },
        },
      },
    },
  },
  components: {
    securitySchemes: {
      BearerAuth: {
        type: "http",
        scheme: "bearer",
        bearerFormat: "JWT",
      },
    },
    schemas: {
      UserProfile: {
        type: "object",
        required: ["id"],
        properties: {
          id: {
            type: "string",
            description: "User ID",
          },
          name: {
            type: "string",
            description: "Display name",
          },
        },
      },
    },
  },
};

fs.writeFileSync(specPath, JSON.stringify(spec), "utf8");

const output = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "endpoints", "--details", "--path", "/login"],
  { encoding: "utf8" }
);

assert.match(output, /Content-Type: `application\/json`; type: `object`/);
assert.match(output, /`code`: integer - example: 200/);
assert.match(output, /`message`: string - example: "Success"/);
assert.match(output, /`success`: boolean - example: true/);
assert.match(output, /`data`: object/);
assert.match(output, /`token`: string - example: "abc"/);
assert.doesNotMatch(output, /type: `any`\n\s+- any/);

const originalRefOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "endpoints", "--details", "--path", "/profile"],
  { encoding: "utf8" }
);
assert.match(originalRefOutput, /Content-Type: `application\/json`; type: `object`/);
assert.match(originalRefOutput, /`id`: string required - User ID/);
assert.match(originalRefOutput, /`name`: string - Display name/);

const semanticSearchOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "endpoints", "--search", "登录"],
  { encoding: "utf8" }
);
assert.match(semanticSearchOutput, /POST \| `\/login` \| Login/);

const integrationOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "integration", "--search", "登录"],
  { encoding: "utf8" }
);
assert.match(integrationOutput, /## Integration Guide/);
assert.match(integrationOutput, /Request URL: `POST https:\/\/api\.example\.com\/v1\/login`/);
assert.match(integrationOutput, /Auth: none documented for this endpoint/);
assert.match(integrationOutput, /curl --request POST/);
assert.match(integrationOutput, /"username": "string"/);
assert.match(integrationOutput, /await fetch\("https:\/\/api\.example\.com\/v1\/login"/);

const authenticatedIntegrationOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "integration", "--path", "/profile", "--method", "GET"],
  { encoding: "utf8" }
);
assert.match(authenticatedIntegrationOutput, /Request URL: `GET https:\/\/api\.example\.com\/v1\/profile`/);
assert.match(authenticatedIntegrationOutput, /Auth: `BearerAuth` \(http bearer JWT\)/);
assert.match(authenticatedIntegrationOutput, /--header 'Authorization: Bearer <token>'/);

const endpointAliasOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "endpoint", "--path", "/profile", "--method", "GET"],
  { encoding: "utf8" }
);
assert.match(endpointAliasOutput, /## Endpoint Index/);
assert.match(endpointAliasOutput, /### GET \/profile/);

const configPath = path.join(tempDir, "swagger.config.json");
fs.writeFileSync(
  configPath,
  JSON.stringify({
    swaggerUrl: specPath,
  }),
  "utf8"
);
const configOutput = execFileSync(
  process.execPath,
  [scriptPath, "--config", configPath, "--mode", "modules"],
  { encoding: "utf8" }
);
assert.match(configOutput, /Module List/);
assert.match(configOutput, /User \| 2 \| GET 1, POST 1/);

const copiedSkillDir = path.join(tempDir, "copied-skill");
const copiedScriptsDir = path.join(copiedSkillDir, "scripts");
fs.mkdirSync(copiedScriptsDir, { recursive: true });
const copiedScriptPath = path.join(copiedScriptsDir, "extract_swagger_docs.mjs");
fs.copyFileSync(scriptPath, copiedScriptPath);
fs.writeFileSync(
  path.join(copiedSkillDir, "swagger.config.json"),
  JSON.stringify({
    swaggerUrl: specPath,
  }),
  "utf8"
);
let implicitConfigFailed = false;
try {
  execFileSync(process.execPath, [copiedScriptPath, "--mode", "modules"], { encoding: "utf8", stdio: "pipe" });
} catch (error) {
  implicitConfigFailed = true;
  assert.match(String(error.stderr), /Missing Swagger\/OpenAPI URL/);
}
assert.equal(implicitConfigFailed, true, "default skill config should not be loaded implicitly");

const outputPath = path.join(tempDir, "api.md");
const successOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "document", "--output", outputPath],
  { encoding: "utf8" }
);
const writtenMarkdown = fs.readFileSync(outputPath, "utf8");
assert.match(successOutput, /Parsed Swagger\/OpenAPI document successfully\./);
assert.match(successOutput, /Output: .*api\.md/);
assert.match(successOutput, /Modules: 1/);
assert.match(successOutput, /Endpoints: 2/);
assert.match(successOutput, /Types: 1/);
assert.doesNotMatch(successOutput, /# API Documentation Summary/);
assert.match(writtenMarkdown, /# API Documentation Summary/);
assert.match(writtenMarkdown, /POST \/login/);

const cachePath = path.join(tempDir, "spec-cache.json");
const cacheWriteOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "modules", "--cache", cachePath],
  { encoding: "utf8" }
);
assert.match(cacheWriteOutput, /Module List/);
assert.ok(fs.existsSync(cachePath), "cache file should be written after a successful fetch");
fs.unlinkSync(specPath);
const cacheReadOutput = execFileSync(
  process.execPath,
  [scriptPath, specPath, "--mode", "modules", "--cache", cachePath],
  { encoding: "utf8" }
);
assert.match(cacheReadOutput, /Module List/);
assert.match(cacheReadOutput, /User \| 2 \| GET 1, POST 1/);

const hangingServer = http.createServer(() => {});
await new Promise((resolve) => hangingServer.listen(0, "127.0.0.1", resolve));
try {
  const port = hangingServer.address().port;
  const startedAt = Date.now();
  let failed = false;
  try {
    execFileSync(
      process.execPath,
      [scriptPath, `http://127.0.0.1:${port}/doc#/`, "--timeout", "0.2", "--mode", "modules"],
      { encoding: "utf8", stdio: "pipe", timeout: 2500 }
    );
  } catch (error) {
    failed = true;
    assert.match(String(error.stderr), /Could not access Swagger document URL/);
  }
  assert.equal(failed, true);
  assert.ok(Date.now() - startedAt < 2000, "unreachable entry URL should fail fast");
} finally {
  await new Promise((resolve) => hangingServer.close(resolve));
}

console.log("extract_swagger_docs regression tests passed");

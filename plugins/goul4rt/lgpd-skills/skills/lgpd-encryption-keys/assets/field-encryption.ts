import {
  createCipheriv,
  createDecipheriv,
  createHmac,
  randomBytes,
} from "node:crypto";

const CIPHERTEXT_PREFIX = "enc:v";
const IV_LENGTH = 12;
const AUTH_TAG_LENGTH = 16;

export interface Keyring {
  /** Versão ativa usada para novas gravações (ex.: 1, 2). */
  currentVersion: number;
  /** Mapa versão -> chave AES-256 de exatos 32 bytes. */
  keys: Readonly<Record<number, Buffer>>;
}

export function assertValidKeyring(keyring: Keyring): void {
  const activeKey = keyring.keys[keyring.currentVersion];
  if (!activeKey || activeKey.byteLength !== 32) {
    throw new Error(
      `Invalid active AES-256 key for version ${keyring.currentVersion}: expected 32 bytes.`,
    );
  }
  for (const [ver, key] of Object.entries(keyring.keys)) {
    if (key.byteLength !== 32) {
      throw new Error(`Invalid AES-256 key for version ${ver}: expected 32 bytes.`);
    }
  }
}

export function isEncryptedField(value: unknown): value is string {
  return typeof value === "string" && /^enc:v\d+:[A-Za-z0-9+/=]+$/.test(value);
}

/**
 * Cifra um atributo em nível de aplicação com AES-256-GCM autenticado,
 * versionamento de chave (`enc:v{N}:...`) para rotação sem downtime e
 * AAD opcional (`context`, ex.: `"User.cpf"`) para impedir transplante entre colunas.
 */
export function encryptField(
  plaintext: string,
  keyring: Keyring,
  aadContext?: string,
): string {
  assertValidKeyring(keyring);
  if (isEncryptedField(plaintext)) {
    return plaintext;
  }

  const version = keyring.currentVersion;
  const key = keyring.keys[version]!;
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  if (aadContext) {
    cipher.setAAD(Buffer.from(aadContext, "utf8"));
  }

  const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  const packed = Buffer.concat([iv, authTag, ciphertext]).toString("base64");
  return `${CIPHERTEXT_PREFIX}${version}:${packed}`;
}

export function decryptField(
  encoded: string,
  keyring: Keyring,
  aadContext?: string,
): string {
  assertValidKeyring(keyring);
  if (!encoded.startsWith(CIPHERTEXT_PREFIX)) {
    throw new Error("Malformed encrypted field: missing enc:v{N}: prefix.");
  }

  const sepIdx = encoded.indexOf(":", CIPHERTEXT_PREFIX.length);
  if (sepIdx === -1) {
    throw new Error("Malformed encrypted field: missing payload separator.");
  }

  const version = Number(encoded.slice(CIPHERTEXT_PREFIX.length, sepIdx));
  const key = keyring.keys[version];
  if (!key) {
    throw new Error(`Unknown encryption key version: v${version}`);
  }

  const raw = Buffer.from(encoded.slice(sepIdx + 1), "base64");
  if (raw.byteLength < IV_LENGTH + AUTH_TAG_LENGTH) {
    throw new Error("Malformed encrypted field: payload too short.");
  }

  const iv = raw.subarray(0, IV_LENGTH);
  const authTag = raw.subarray(IV_LENGTH, IV_LENGTH + AUTH_TAG_LENGTH);
  const ciphertext = raw.subarray(IV_LENGTH + AUTH_TAG_LENGTH);

  const decipher = createDecipheriv("aes-256-gcm", key, iv);
  if (aadContext) {
    decipher.setAAD(Buffer.from(aadContext, "utf8"));
  }
  decipher.setAuthTag(authTag);

  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

/**
 * Gera índice cego determinístico (HMAC-SHA256 com chave segregada da chave de cifragem)
 * para permitir buscas por igualdade (`WHERE cpfBlindIndex = ...`) sem expor o dado em claro.
 */
export function computeBlindIndex(
  blindKey: Buffer,
  normalizedValue: string,
): string {
  if (blindKey.byteLength < 32) {
    throw new Error("Blind index HMAC key must be at least 32 bytes.");
  }
  return createHmac("sha256", blindKey)
    .update(normalizedValue.trim().toLowerCase(), "utf8")
    .digest("hex");
}

export interface EncryptedFieldSpec {
  field: string;
  aadContext?: string;
  blindIndexField?: string;
  normalizeForBlindIndex?: (plain: string) => string;
}

export interface FieldEncryptionOptions {
  keyring: Keyring;
  blindKey?: Buffer;
  fields: ReadonlyArray<EncryptedFieldSpec>;
}

function transformWriteRecord(
  data: Record<string, unknown>,
  options: FieldEncryptionOptions,
): Record<string, unknown> {
  const out: Record<string, unknown> = { ...data };

  for (const spec of options.fields) {
    const rawVal = out[spec.field];
    if (rawVal === undefined || rawVal === null) {
      if (rawVal === null && spec.blindIndexField) {
        out[spec.blindIndexField] = null;
      }
      continue;
    }

    let plain: string | null = null;
    if (typeof rawVal === "string") {
      plain = rawVal;
      out[spec.field] = encryptField(rawVal, options.keyring, spec.aadContext);
    } else if (
      typeof rawVal === "object" &&
      "set" in (rawVal as Record<string, unknown>)
    ) {
      const setVal = (rawVal as { set: unknown }).set;
      if (typeof setVal === "string") {
        plain = setVal;
        out[spec.field] = {
          ...(rawVal as Record<string, unknown>),
          set: encryptField(setVal, options.keyring, spec.aadContext),
        };
      } else if (setVal === null && spec.blindIndexField) {
        out[spec.blindIndexField] = null;
      }
    }

    if (
      plain !== null &&
      !isEncryptedField(plain) &&
      spec.blindIndexField &&
      options.blindKey
    ) {
      const normalized = spec.normalizeForBlindIndex
        ? spec.normalizeForBlindIndex(plain)
        : plain;
      out[spec.blindIndexField] = computeBlindIndex(options.blindKey, normalized);
    }
  }

  return out;
}

function transformReadRecord(
  record: unknown,
  options: FieldEncryptionOptions,
): unknown {
  if (!record || typeof record !== "object") return record;
  if (Array.isArray(record)) {
    return record.map((item) => transformReadRecord(item, options));
  }

  const out: Record<string, unknown> = { ...(record as Record<string, unknown>) };
  for (const spec of options.fields) {
    const val = out[spec.field];
    if (typeof val === "string" && isEncryptedField(val)) {
      out[spec.field] = decryptField(val, options.keyring, spec.aadContext);
    }
  }
  return out;
}

const WRITE_SINGLE_OPS = new Set(["create", "update"]);
const WRITE_BATCH_OPS = new Set(["createMany", "createManyAndReturn", "updateMany"]);
const READ_OPS = new Set([
  "findUnique",
  "findUniqueOrThrow",
  "findFirst",
  "findFirstOrThrow",
  "findMany",
  "create",
  "createManyAndReturn",
  "update",
  "upsert",
]);

/**
 * Cria handlers compatíveis com `PrismaClient.$extends({ query: { [model]: ... } })`
 * cobrindo `create`, `createMany`, `createManyAndReturn`, `update`, `updateMany`,
 * `upsert`, `findUnique`, `findUniqueOrThrow`, `findFirst`, `findFirstOrThrow` e `findMany`.
 */
export function createPrismaModelEncryptionHandlers(options: FieldEncryptionOptions) {
  assertValidKeyring(options.keyring);

  async function intercept({
    operation,
    args,
    query,
  }: {
    operation: string;
    args: Record<string, unknown>;
    query: (nextArgs: Record<string, unknown>) => Promise<unknown>;
  }): Promise<unknown> {
    const nextArgs: Record<string, unknown> = { ...args };

    if (WRITE_SINGLE_OPS.has(operation) && nextArgs.data && typeof nextArgs.data === "object") {
      nextArgs.data = transformWriteRecord(
        nextArgs.data as Record<string, unknown>,
        options,
      );
    } else if (WRITE_BATCH_OPS.has(operation) && nextArgs.data) {
      if (Array.isArray(nextArgs.data)) {
        nextArgs.data = nextArgs.data.map((item) =>
          transformWriteRecord(item as Record<string, unknown>, options),
        );
      } else if (typeof nextArgs.data === "object") {
        nextArgs.data = transformWriteRecord(
          nextArgs.data as Record<string, unknown>,
          options,
        );
      }
    } else if (operation === "upsert") {
      if (nextArgs.create && typeof nextArgs.create === "object") {
        nextArgs.create = transformWriteRecord(
          nextArgs.create as Record<string, unknown>,
          options,
        );
      }
      if (nextArgs.update && typeof nextArgs.update === "object") {
        nextArgs.update = transformWriteRecord(
          nextArgs.update as Record<string, unknown>,
          options,
        );
      }
    }

    const result = await query(nextArgs);
    if (READ_OPS.has(operation)) {
      return transformReadRecord(result, options);
    }
    return result;
  }

  return {
    create: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "create", ...ctx }),
    createMany: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "createMany", ...ctx }),
    createManyAndReturn: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "createManyAndReturn", ...ctx }),
    update: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "update", ...ctx }),
    updateMany: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "updateMany", ...ctx }),
    upsert: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "upsert", ...ctx }),
    findUnique: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "findUnique", ...ctx }),
    findUniqueOrThrow: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "findUniqueOrThrow", ...ctx }),
    findFirst: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "findFirst", ...ctx }),
    findFirstOrThrow: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "findFirstOrThrow", ...ctx }),
    findMany: (ctx: { args: Record<string, unknown>; query: (a: Record<string, unknown>) => Promise<unknown> }) =>
      intercept({ operation: "findMany", ...ctx }),
  };
}

// grammY 1.46.0 (Bot API 10.3) adapter for Bot API 10.4 widgets.
//
// Verified locally on 2026-11-12 against grammy@1.46.0 / @grammyjs/types@5.0.0:
//  * 10.3 is typed: stopped_message_generation, DisabledButton, force_reply, can_stop…
//  * 10.4 is not: no widget_query / shared_widget_query in Update, no sendWidget types,
//    and DEFAULT_UPDATE_TYPES (used by bot.start() without allowed_updates) omits them.
//  * Middleware still receives the raw update, and bot.api.raw is a Proxy, so any
//    method name reaches the transport (and its transformers) unchanged.
//
// REMOVE WHEN: the lockfile has a grammY whose @grammyjs/types includes WidgetQuery;
// then use bot.on("widget_query") and typed ctx.api methods.
import grammy, { type Bot, type Context } from "grammy";

// grammy is CommonJS: take values from the default export under Node ESM.
const { API_CONSTANTS } = grammy;
export const DEFAULT_UPDATE_TYPES: readonly string[] = API_CONSTANTS.DEFAULT_UPDATE_TYPES;

export const ALLOWED_UPDATES = [...DEFAULT_UPDATE_TYPES, "widget_query", "shared_widget_query"] as const;

export type WidgetQuery = {
  id: string; from: { id: number }; data: string; widget_id?: string; chat_instance?: string;
  chat?: { id: number; type: string }; message_id?: number; inline_message_id?: string; type: { type: string };
};
type WidgetHandler = (kind: "widget_query" | "shared_widget_query", q: WidgetQuery, api: WidgetApi) => Promise<void>;

export type WidgetApi = {
  sendWidget(p: { chat_id: number | string; html: string; caption?: string; chat_data?: string; public_data?: string;
    allow_queries?: boolean; is_shared?: boolean }): Promise<{ message_id: number; widget?: { id?: string } }>;
  answerWidgetQuery(p: { widget_query_id: string; data?: string }): Promise<true>;
  editMessageWidgetData(p: { chat_id?: number | string; message_id?: number; inline_message_id?: string;
    chat_data?: string; public_data?: string }): Promise<true>;
  editSharedWidgetData(p: { widget_id: string; public_data: string; cache_time?: number }): Promise<true>;
};

// bot.api.raw is a Proxy over method names: the cast only adds the missing 10.4 types.
export const widgetApi = (bot: Bot<Context>): WidgetApi => bot.api.raw as unknown as WidgetApi;

export function installWidgetRouting(bot: Bot<Context>, handler: WidgetHandler): void {
  bot.use(async (ctx, next) => {
    const raw = ctx.update as unknown as Record<string, unknown>;
    for (const kind of ["widget_query", "shared_widget_query"] as const) {
      if (raw[kind]) return handler(kind, raw[kind] as WidgetQuery, widgetApi(bot));
    }
    return next();
  });
}

// Always pass the list explicitly: allowed_updates is sticky on Telegram's side.
export const startPolling = (bot: Bot<Context>) => bot.start({ allowed_updates: [...ALLOWED_UPDATES] as never });

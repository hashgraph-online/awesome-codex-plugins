/**
 * Plugin lifecycle projector — handles plugin discovered, activated, hook executed, hook failed,
 * and plugins registered events.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { clone, normalizePlugins } from './helpers.mts';
import type { ExecutionState, PluginSummary, RuntimeEvent } from './types.mts';

export function projectPluginLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.PLUGIN_DISCOVERED: {
      if (!state.pluginLifecycle || typeof state.pluginLifecycle !== 'object') {
        state.pluginLifecycle = { discovered: [], activated: [], executed: [], failed: [] };
      }
      state.pluginLifecycle.discovered = normalizePlugins([
        ...(state.pluginLifecycle.discovered ?? []),
        event.data.plugin,
      ]);
      return state;
    }

    case EVENT_TYPES.PLUGIN_ACTIVATED: {
      if (!state.pluginLifecycle || typeof state.pluginLifecycle !== 'object') {
        state.pluginLifecycle = { discovered: [], activated: [], executed: [], failed: [] };
      }
      state.pluginLifecycle.activated = normalizePlugins([
        ...(state.pluginLifecycle.activated ?? []),
        event.data.plugin,
      ]);
      state.plugins = normalizePlugins([...(state.plugins ?? []), event.data.plugin]);
      return state;
    }

    case EVENT_TYPES.PLUGIN_HOOK_EXECUTED: {
      if (!state.pluginLifecycle || typeof state.pluginLifecycle !== 'object') {
        state.pluginLifecycle = { discovered: [], activated: [], executed: [], failed: [] };
      }
      state.pluginLifecycle.executed = (state.pluginLifecycle.executed ?? []).concat({
        plugin: clone(event.data.plugin as PluginSummary),
        hook: String(event.data.hook),
        stage: event.data.stage == null ? null : Number(event.data.stage),
        exitCode: Number(event.data.exitCode),
        timestamp: event.timestamp,
      });
      return state;
    }

    case EVENT_TYPES.PLUGIN_HOOK_FAILED: {
      if (!state.pluginLifecycle || typeof state.pluginLifecycle !== 'object') {
        state.pluginLifecycle = { discovered: [], activated: [], executed: [], failed: [] };
      }
      state.pluginLifecycle.failed = (state.pluginLifecycle.failed ?? []).concat({
        plugin: clone(event.data.plugin as PluginSummary),
        hook: String(event.data.hook),
        stage: event.data.stage == null ? null : Number(event.data.stage),
        exitCode: Number(event.data.exitCode),
        timestamp: event.timestamp,
      });
      return state;
    }

    case EVENT_TYPES.PLUGINS_REGISTERED: {
      state.plugins = normalizePlugins(event.data.plugins);
      return state;
    }

    default:
      return null;
  }
}

import test from 'node:test';
import assert from 'node:assert/strict';
import { findUpstreamThreadSources, resolveThreadSource } from '../web-src/thread-source-options.mjs';

const node = (id, kind = 'thread', provider_id = '') => ({ id, type: 'agent', executor: { kind, ...(provider_id ? { provider_id } : {}) } });
const edge = (source, target) => ({ id: `${source}-${target}`, source, target });

function collaborativeGraph() {
  return {
    nodes: [
      node('start', 'start'), node('fork', 'parallel'), node('plan', 'thread', 'planning'),
      node('prepare', 'thread', 'production'), node('join', 'join'), node('produce', 'thread', 'production'),
      node('final', 'main'), node('end', 'end'),
    ],
    edges: [
      edge('start', 'fork'), edge('fork', 'plan'), edge('fork', 'prepare'), edge('plan', 'join'),
      edge('prepare', 'join'), edge('join', 'produce'), edge('produce', 'final'), edge('final', 'end'),
    ],
  };
}

test('preset-like plan/prepare/join/produce graph returns actual upstream thread choices', () => {
  const graph = collaborativeGraph();
  assert.deepEqual(findUpstreamThreadSources(graph, 'produce'), [
    { id: 'plan', distance: 2, providerId: 'planning' },
    { id: 'prepare', distance: 2, providerId: 'production' },
  ]);
});

test('source choices do not depend on reversed node or edge array order', () => {
  const graph = collaborativeGraph();
  const reversed = { nodes: [...graph.nodes].reverse(), edges: [...graph.edges].reverse() };
  assert.deepEqual(findUpstreamThreadSources(reversed, 'produce'), findUpstreamThreadSources(graph, 'produce'));
});

test('unique nearest same-provider source is selected automatically', () => {
  const result = resolveThreadSource(collaborativeGraph(), 'produce', { providerId: 'production' });
  assert.equal(result.sourceNodeId, 'prepare');
  assert.equal(result.providerId, 'production');
  assert.equal(result.needsSelection, false);
});

test('incomparable same-provider sources stay empty until explicitly selected', () => {
  const graph = {
    nodes: [node('target', 'thread', 'production'), node('left', 'thread', 'production'), node('right', 'thread', 'production'), node('fork', 'parallel')],
    edges: [edge('left', 'fork'), edge('right', 'fork'), edge('fork', 'target')],
  };
  const unresolved = resolveThreadSource(graph, 'target', { providerId: 'production' });
  assert.equal(unresolved.sourceNodeId, '');
  assert.equal(unresolved.needsSelection, true);
  assert.equal(unresolved.ambiguous, true);
  const selected = resolveThreadSource(graph, 'target', { providerId: 'production', sourceNodeId: 'right' });
  assert.equal(selected.sourceNodeId, 'right');
  assert.equal(selected.needsSelection, false);
});

test('incomparable same-provider sources stay ambiguous even when branch lengths differ', () => {
  const graph = {
    nodes: [
      node('target', 'thread', 'production'), node('left', 'thread', 'production'), node('left-hop', 'join'),
      node('right', 'thread', 'production'), node('right-hop-1', 'join'), node('right-hop-2', 'join'), node('join', 'join'),
    ],
    edges: [
      edge('left', 'left-hop'), edge('left-hop', 'join'), edge('right', 'right-hop-1'),
      edge('right-hop-1', 'right-hop-2'), edge('right-hop-2', 'join'), edge('join', 'target'),
    ],
  };
  const result = resolveThreadSource(graph, 'target', { providerId: 'production' });
  assert.equal(result.sourceNodeId, '');
  assert.equal(result.needsSelection, true);
  assert.equal(result.ambiguous, true);
});

test('malformed cycles and self edges terminate and exclude the selected node', () => {
  const graph = {
    nodes: [node('target', 'thread', 'production'), node('cycle-a', 'thread', 'production'), node('cycle-b', 'thread', 'other')],
    edges: [edge('target', 'target'), edge('cycle-a', 'cycle-b'), edge('cycle-b', 'cycle-a'), edge('cycle-b', 'target')],
  };
  assert.deepEqual(findUpstreamThreadSources(graph, 'target'), [
    { id: 'cycle-b', distance: 1, providerId: 'other' },
    { id: 'cycle-a', distance: 2, providerId: 'production' },
  ]);
});

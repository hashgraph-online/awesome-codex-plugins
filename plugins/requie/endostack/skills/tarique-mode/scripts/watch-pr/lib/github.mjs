// Raw GitHub and git access. Each method returns parsed JSON or a raw
// command result and leaves interpretation to snapshot.mjs. Tests replace
// this whole object with a fake, or keep it and fake the `run` function.

import { QueryError } from './errors.mjs';
import { runJson, commandFailure } from './exec.mjs';

const THREADS_QUERY = `query WatchThreads($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { author { login } body path line originalLine createdAt }
          }
        }
      }
    }
  }
}`;

const ROLLUP_QUERY = `query WatchRollup($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      commits(last: 1) {
        nodes {
          commit {
            oid
            statusCheckRollup {
              contexts(first: 100, after: $cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  __typename
                  ... on CheckRun { name status conclusion detailsUrl checkSuite { workflowRun { workflow { name } } } }
                  ... on StatusContext { context state description targetUrl }
                }
              }
            }
          }
        }
      }
    }
  }
}`;

const COMMITS_QUERY = `query WatchCommits($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      commits(last: 50) {
        nodes { commit { oid statusCheckRollup { state } } }
      }
    }
  }
}`;

export const PR_FIELDS = ['state', 'isDraft', 'mergedAt', 'baseRefName', 'headRefName', 'headRefOid', 'mergeable', 'mergeStateStatus', 'reviewDecision'].join(',');
export const CHECK_FIELDS = 'name,state,description,link,workflow,bucket';
export const LIST_FIELDS = 'number,headRefName,baseRefName,isCrossRepository';

function graphqlArgs(query, vars) {
  const args = ['api', 'graphql', '-f', `query=${query}`];
  for (const k of Object.keys(vars)) {
    const v = vars[k];
    if (v == null) continue;
    // -F sends numbers as numbers; strings go through -f so an owner named
    // "true" or "123" stays a string.
    args.push(typeof v === 'number' ? '-F' : '-f', `${k}=${v}`);
  }
  return args;
}

function pullRequestNode(data, what) {
  const pr = data?.data?.repository?.pullRequest;
  if (!pr || typeof pr !== 'object') {
    const message = data?.errors?.[0]?.message;
    throw new QueryError('missing-field', `${what}: response has no pullRequest${message ? ` (${message})` : ''}`);
  }
  return pr;
}

export function githubReader(run) {
  return {
    async originUrl() {
      const result = await run('git', ['config', '--get', 'remote.origin.url']);
      if (result.code !== 0) return null;
      return result.stdout.trim() || null;
    },

    async lookupPr(number) {
      const args = ['pr', 'view'];
      if (number !== null && number !== undefined) args.push(String(number));
      args.push('--json', 'number,url');
      return runJson(run, 'gh', args);
    },

    async listOpenPrs(owner, repo) {
      return runJson(run, 'gh', ['pr', 'list', '--repo', `${owner}/${repo}`, '--state', 'open', '--limit', '300', '--json', LIST_FIELDS]);
    },

    async prFields(owner, repo, number) {
      return runJson(run, 'gh', ['pr', 'view', String(number), '--repo', `${owner}/${repo}`, '--json', PR_FIELDS]);
    },

    async threadPage(owner, repo, number, cursor) {
      const data = await runJson(run, 'gh', graphqlArgs(THREADS_QUERY, { owner, repo, number, cursor }));
      const conn = pullRequestNode(data, 'review threads').reviewThreads;
      if (!conn || typeof conn !== 'object') throw new QueryError('missing-field', 'review threads: reviewThreads is missing');
      return conn;
    },

    // Returns the raw command result: the caller decides whether the fast
    // path is usable, because gh exits 1 on failing checks and 8 on pending.
    async checksFast(owner, repo, number) {
      return run('gh', ['pr', 'checks', String(number), '--repo', `${owner}/${repo}`, '--json', CHECK_FIELDS]);
    },

    async rollupPage(owner, repo, number, cursor) {
      const data = await runJson(run, 'gh', graphqlArgs(ROLLUP_QUERY, { owner, repo, number, cursor }));
      const commits = pullRequestNode(data, 'check rollup').commits?.nodes;
      if (!Array.isArray(commits)) throw new QueryError('missing-field', 'check rollup: commits are missing');
      const rollup = commits[0]?.commit?.statusCheckRollup;
      if (!rollup) return { nodes: [], pageInfo: { hasNextPage: false, endCursor: null } };
      return rollup.contexts ?? { nodes: [], pageInfo: { hasNextPage: false, endCursor: null } };
    },

    async commitRollups(owner, repo, number) {
      const data = await runJson(run, 'gh', graphqlArgs(COMMITS_QUERY, { owner, repo, number }));
      const nodes = pullRequestNode(data, 'commit rollups').commits?.nodes;
      if (!Array.isArray(nodes)) throw new QueryError('missing-field', 'commit rollups: commits are missing');
      return nodes.map((n) => ({ oid: n?.commit?.oid ?? null, state: n?.commit?.statusCheckRollup?.state ?? null }));
    },
  };
}

export { commandFailure };

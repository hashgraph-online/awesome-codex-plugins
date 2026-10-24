"""Exercise helpers against disposable repositories; never contact a live host."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="stacked-prs-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "checkout"
        self.repo.mkdir()
        self.remote = self.root / "remote.git"
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
        # Do not inherit a caller's repository or index selection.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            self.env.pop(key, None)
        self.run_cmd("git", "init", "-q", "--bare", str(self.remote))
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "core.fileMode", "true")
        self.write("run.sh", "echo old\n")
        self.write("other.txt", "old\n")
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("branch", "develop")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-q", "origin", "main", "develop")

    def run_cmd(self, *command, expected=0):
        result = subprocess.run(command, cwd=self.repo, env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if expected is not None:
            self.assertEqual(result.returncode, expected, result.stdout)
        return result

    def git(self, *args, expected=0):
        return self.run_cmd("git", *args, expected=expected)

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self, subject):
        self.git("add", "-A")
        self.git("commit", "-qm", subject)

    def script(self, name, *args, expected=0):
        return self.run_cmd("/bin/bash", str(ROOT / "scripts" / name), *args, expected=expected)

    def feature(self, name="feature/TEST-1-01-core"):
        self.git("switch", "-qc", name)
        self.write("run.sh", "echo new\n")
        self.commit("change")
        return name

    def plan(self, branch):
        output = self.script("safe-push.sh", branch, expected=3).stdout
        return output.strip().splitlines()[-1].strip()

    def execute_plan(self, plan, expected=0):
        return self.run_cmd("/bin/bash", "-c", plan, expected=expected)

    def remote_ref(self, name, remote=None):
        return self.git("ls-remote", str(remote or self.remote), name).stdout.strip()


class PushTests(GitFixture):
    def test_dry_run_does_not_push_and_approved_plan_pushes_only_branch(self):
        branch = self.feature()
        self.git("config", "push.followTags", "true")
        self.git("tag", "-am", "unapproved", "unapproved-tag")
        plan = self.plan(branch)
        self.assertFalse(self.remote_ref("refs/heads/" + branch))
        self.execute_plan(plan)
        self.assertTrue(self.remote_ref("refs/heads/" + branch))
        self.assertFalse(self.remote_ref("refs/tags/unapproved-tag"))

    def test_head_change_invalidates_plan(self):
        branch = self.feature()
        plan = self.plan(branch)
        self.write("other.txt", "later\n")
        self.commit("later")
        self.assertIn("HEAD changed", self.execute_plan(plan, expected=1).stdout)
        self.assertFalse(self.remote_ref("refs/heads/" + branch))

    def test_destination_change_invalidates_plan(self):
        branch = self.feature()
        plan = self.plan(branch)
        second = self.root / "second.git"
        self.git("init", "-q", "--bare", str(second))
        self.git("remote", "set-url", "--push", "origin", str(second))
        self.assertIn("different push", self.execute_plan(plan, expected=1).stdout)
        self.assertFalse(self.remote_ref("refs/heads/" + branch, second))

    def test_remote_tip_change_invalidates_plan(self):
        branch = self.feature()
        plan = self.plan(branch)
        self.git("push", "-q", "origin", self.base + ":refs/heads/" + branch)
        self.assertIn("now exists", self.execute_plan(plan, expected=1).stdout)

    def test_existing_remote_advancing_to_ancestor_invalidates_plan(self):
        branch = self.feature()
        middle = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("push", "-q", "origin", self.base + ":refs/heads/" + branch)
        self.git("commit", "--allow-empty", "-qm", "another change")
        plan = self.plan(branch)
        self.git("push", "-q", "origin", middle + ":refs/heads/" + branch)
        self.assertIn("moved since", self.execute_plan(plan, expected=1).stdout)

    def test_push_url_is_checked_instead_of_fetch_url(self):
        branch = self.feature()
        second = self.root / "push.git"
        self.git("init", "-q", "--bare", str(second))
        self.git("remote", "set-url", "--push", "origin", str(second))
        self.execute_plan(self.plan(branch))
        self.assertTrue(self.remote_ref("refs/heads/" + branch, second))
        self.assertFalse(self.remote_ref("refs/heads/" + branch))
        self.assertIn("nothing to push", self.script("safe-push.sh", branch).stdout)

    def test_shell_metacharacters_in_branch_and_script_path_are_literal(self):
        branch = self.feature("feature/$(id)")
        directory = self.root / "skill copy"
        directory.mkdir()
        helper = directory / "safe-push.sh"
        helper.symlink_to(ROOT / "scripts" / "safe-push.sh")
        output = self.run_cmd("bash", str(helper), "-P", "release/'*", branch, expected=3).stdout
        self.execute_plan(output.strip().splitlines()[-1].strip())
        self.assertTrue(self.remote_ref("refs/heads/" + branch))

    def test_protected_and_dirty_branches_are_refused(self):
        for branch in ("main", "master", "develop", "release/1", "MAIN"):
            self.script("safe-push.sh", branch, expected=1)
        branch = self.feature()
        self.write("dirty", "uncommitted")
        self.assertIn("uncommitted", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_custom_reference_is_protected(self):
        branch = self.feature()
        self.git("config", "--add", "stacked-prs.protect", branch)
        self.assertIn("protected", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_mirror_and_multiple_push_destinations_are_refused(self):
        branch = self.feature()
        self.git("config", "remote.origin.mirror", "true")
        self.assertIn("mirror", self.script("safe-push.sh", branch, expected=1).stdout)
        self.git("config", "--unset", "remote.origin.mirror")
        self.git("config", "--add", "remote.origin.pushurl", str(self.remote))
        self.git("config", "--add", "remote.origin.pushurl", str(self.root / "other.git"))
        self.assertIn("multiple push", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_non_fast_forward_is_refused(self):
        branch = self.feature()
        self.execute_plan(self.plan(branch))
        self.git("reset", "--hard", self.base)
        self.write("other.txt", "divergent\n")
        self.commit("divergent")
        self.assertIn("commits HEAD doesn't contain", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_large_push_plan_and_unfinished_commit(self):
        branch = self.feature()
        for index in range(110):
            self.git("commit", "--allow-empty", "-qm", f"change {index}")
        self.assertIn("-A", self.plan(branch))
        self.git("commit", "--allow-empty", "-qm", "WIP: incomplete")
        self.assertIn("unfinished", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_work_branch_can_push_only_its_tracking_branch(self):
        branch = self.feature()
        self.execute_plan(self.plan(branch))
        self.git("fetch", "-q", "origin")
        self.git("switch", "-qc", "work/review", "--track", "origin/" + branch)
        self.write("other.txt", "review\n")
        self.commit("review fix")
        self.execute_plan(self.plan(branch))
        self.assertIn("not", self.script("safe-push.sh", "feature/different", expected=1).stdout)

    def test_existing_tip_change_and_invalid_key_are_refused(self):
        branch = self.feature()
        self.git("push", "-q", "origin", self.base + ":refs/heads/" + branch)
        plan = self.plan(branch)
        self.git("push", "-q", "origin", branch)
        self.git("commit", "--allow-empty", "-qm", "new local commit")
        new_plan = self.plan(branch)
        # A key is checked even when the supplied commit and remote tip are valid.
        words = new_plan.split()
        words[words.index("-K") + 1] = "invalid"
        self.assertIn("different push", self.execute_plan(" ".join(words), expected=1).stdout)
        self.assertIn("HEAD changed", self.execute_plan(plan, expected=1).stdout)

    def test_push_source_is_pinned_when_hook_moves_head(self):
        branch = self.feature()
        approved = self.git("rev-parse", "HEAD").stdout.strip()
        plan = self.plan(branch)
        hook = self.repo / ".git" / "hooks" / "pre-push"
        hook.write_text('#!/bin/sh\ngit commit --allow-empty -qm "hook moved head"\n')
        hook.chmod(0o755)
        self.execute_plan(plan)
        self.assertTrue(self.remote_ref("refs/heads/" + branch).startswith(approved))
        self.assertNotEqual(approved, self.git("rev-parse", "HEAD").stdout.strip())

    def test_detached_wrong_branch_and_incomplete_approval_are_refused(self):
        branch = self.feature()
        self.script("safe-push.sh", "another-branch", expected=1)
        self.script("safe-push.sh", "-A", "invalid", branch, expected=2)
        self.script("safe-push.sh", "-A", "invalid", "-T", "none", "-K", "invalid", branch, expected=1)
        self.git("switch", "--detach", "-q")
        self.assertIn("detached", self.script("safe-push.sh", branch, expected=1).stdout)

    def test_failed_destination_is_not_treated_as_a_new_branch(self):
        branch = self.feature()
        self.git("remote", "set-url", "--push", "origin", str(self.root / "nonexistent.git"))
        self.assertIn("can't read", self.script("safe-push.sh", branch, expected=1).stdout)


class CoverageTests(GitFixture):
    def reference(self, changes):
        self.git("switch", "-qc", "reference", self.base)
        changes()
        self.commit("reference change")

    def coverage(self, *slices, expected=0, base="main"):
        return self.script("split-coverage.sh", "-n", base, "reference", *slices, expected=expected).stdout

    def test_content_deletion_rename_and_unusual_paths(self):
        def changes():
            self.write("file with space\tand newline\n.txt", "added\n")
            self.git("mv", "other.txt", "renamed.txt")
            (self.repo / "run.sh").unlink()
        self.reference(changes)
        self.git("branch", "slice")
        self.assertIn("missing: 0", self.coverage("slice"))
        self.git("branch", "empty", self.base)
        self.assertIn("MISSING", self.coverage("empty", expected=1))

    def test_executable_bit_is_required(self):
        self.reference(lambda: (self.repo / "run.sh").chmod(0o755))
        self.git("branch", "empty", self.base)
        self.assertIn("MISSING", self.coverage("empty", expected=1))
        self.git("branch", "slice")
        self.coverage("slice")

    def test_symlink_type_is_required(self):
        def changes():
            (self.repo / "run.sh").unlink()
            (self.repo / "run.sh").symlink_to("other.txt")
        self.reference(changes)
        self.git("branch", "slice")
        self.coverage("slice")
        self.git("switch", "-qc", "wrong", self.base)
        self.write("run.sh", "other.txt")
        self.commit("same blob but wrong type")
        self.assertIn("MISSING", self.coverage("wrong", expected=1))

    def test_unpushed_local_slice_is_preferred_over_stale_remote(self):
        self.reference(lambda: self.write("run.sh", "final\n"))
        self.git("branch", "slice", self.base)
        self.git("push", "-q", "origin", "slice")
        self.git("branch", "-f", "slice", "reference")
        self.coverage("slice")
        self.assertIn("MISSING", self.coverage("origin/slice", expected=1))

    def test_extra_and_intermediate_changes_are_reported(self):
        self.reference(lambda: self.write("run.sh", "final\n"))
        self.git("switch", "-qc", "slice", self.base)
        self.write("run.sh", "halfway\n")
        self.write("extra.txt", "unexpected\n")
        self.commit("intermediate")
        output = self.coverage("slice", expected=1)
        self.assertIn("INTERMEDIATE", output)
        self.assertIn("EXTRA", output)

    def test_base_changes_are_preserved_by_three_way_merge(self):
        self.git("switch", "-qc", "setup", self.base)
        self.write("run.sh", "one\ntwo\nthree\nfour\nfive\n")
        self.commit("setup")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("branch", "-f", "main", self.base)
        self.reference(lambda: self.write("run.sh", "ONE\ntwo\nthree\nfour\nfive\n"))
        self.git("switch", "main")
        self.write("run.sh", "one\ntwo\nthree\nfour\nFIVE\n")
        self.commit("base advances")
        self.git("push", "-q", "origin", "main")
        self.git("switch", "-qc", "slice")
        self.write("run.sh", "ONE\ntwo\nthree\nfour\nFIVE\n")
        self.commit("combined")
        self.coverage("slice")
        self.git("branch", "raw-reference", "reference")
        self.assertIn("REVERTS-BASE", self.coverage("raw-reference", expected=1))

    def test_modify_delete_conflict_requires_decision(self):
        self.reference(lambda: (self.repo / "run.sh").unlink())
        self.git("switch", "main")
        self.write("run.sh", "base modified\n")
        self.commit("base advances")
        self.git("push", "-q", "origin", "main")
        self.git("branch", "slice")
        self.assertIn("DECIDE", self.coverage("slice", expected=1))

    def test_manual_merge_is_flagged_and_ignore_option_is_explicit(self):
        self.reference(lambda: self.write("run.sh", "reference\n"))
        self.git("switch", "main")
        self.write("run.sh", "base changed same line\n")
        self.commit("base advances")
        self.git("push", "-q", "origin", "main")
        self.git("switch", "-qc", "slice")
        self.write("run.sh", "hand merged\n")
        self.commit("manual merge")
        self.assertIn("CHECK", self.coverage("slice", expected=1))
        output = self.script("split-coverage.sh", "-n", "-i", "main", "reference", "slice").stdout
        self.assertIn("skipped 1", output)

    def test_mode_change_and_base_content_change_merge_together(self):
        self.reference(lambda: (self.repo / "run.sh").chmod(0o755))
        self.git("switch", "main")
        self.write("run.sh", "base content\n")
        self.commit("base advances")
        self.git("push", "-q", "origin", "main")
        self.git("switch", "-qc", "slice")
        (self.repo / "run.sh").chmod(0o755)
        self.commit("preserve mode and base")
        self.coverage("slice")

    def test_gitlink_entries_are_checked(self):
        self.git("switch", "-qc", "reference", self.base)
        self.git("update-index", "--add", "--cacheinfo", "160000," + self.base + ",dependency")
        self.git("commit", "-qm", "add gitlink")
        self.git("branch", "slice")
        self.coverage("slice")
        self.git("branch", "empty", self.base)
        self.assertIn("MISSING", self.coverage("empty", expected=1))

    def test_binary_file_content_is_required(self):
        self.reference(lambda: (self.repo / "binary.bin").write_bytes(b"\x00\xffcontent\x00"))
        self.git("branch", "slice")
        self.coverage("slice")
        self.git("branch", "empty", self.base)
        self.assertIn("MISSING", self.coverage("empty", expected=1))

    def test_empty_reference_and_invalid_ref(self):
        self.git("branch", "reference", self.base)
        self.git("branch", "slice", self.base)
        self.assertIn("checked 0", self.coverage("slice"))
        self.assertIn("no branch", self.coverage("missing-branch", expected=1))

    def test_default_fetch_and_pinned_commits(self):
        self.reference(lambda: self.write("run.sh", "reference\n"))
        reference = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("branch", "slice")
        self.script("split-coverage.sh", self.base, reference, "slice")


class InspectionTests(GitFixture):
    def test_detection_matches_exact_ticket_and_reports_unknown_push_history(self):
        branch = self.feature()
        self.git("push", "-q", "origin", branch)
        self.git("push", "-q", "origin", "--delete", branch)
        self.git("fetch", "-q", "--prune", "origin")
        self.git("branch", "feature/TEST-10-01-unrelated")
        output = self.script("stack-detect.sh", "-n", "-b", "main", "TEST-1").stdout
        self.assertIn("push history unknown", output)
        self.assertNotIn("never pushed", output)
        self.assertNotIn("TEST-10", output)

    def test_status_checks_actual_parent_and_fix_ancestry(self):
        branch = self.feature()
        fix = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("switch", "-qc", "feature/TEST-1-02-next", self.base)
        self.write("other.txt", "next\n")
        self.commit("next")
        output = self.script("stack-status.sh", "-n", "-b", "main", "-c", fix, branch + ":main", "feature/TEST-1-02-next:" + branch).stdout
        self.assertIn("NEEDS UPDATE", output)
        self.assertIn("contains " + fix[:7] + ": yes", output)
        self.assertIn("contains " + fix[:7] + ": no", output)

    def test_no_stack_and_missing_base(self):
        output = self.script("stack-detect.sh", "-n", "-b", "main", "UNKNOWN").stdout
        self.assertIn("nothing found", output)
        self.assertIn("no base branch", self.script("stack-detect.sh", "-n", "-b", "missing", "TEST-1", expected=1).stdout)

    def test_detection_reports_remote_local_states_and_worktrees(self):
        branch = self.feature()
        self.git("push", "-qu", "origin", branch)
        self.git("commit", "--allow-empty", "-qm", "local ahead")
        self.assertIn("local ahead", self.script("stack-detect.sh", "-n", "TEST-1").stdout)
        self.git("push", "-q", "origin", branch)
        self.git("reset", "--hard", "HEAD^")
        self.assertIn("local behind", self.script("stack-detect.sh", "-n", "TEST-1").stdout)
        self.git("commit", "--allow-empty", "-qm", "diverged")
        self.assertIn("DIVERGED", self.script("stack-detect.sh", "-n", "TEST-1").stdout)
        worktree = self.root / "TEST-1-detached"
        self.git("worktree", "add", "-q", "--detach", str(worktree), self.base)
        output = self.script("stack-detect.sh", "-n", "TEST-1").stdout
        self.assertIn("[detached]", output)
        self.git("push", "-q", "origin", "--delete", branch)
        self.git("fetch", "-q", "--prune", "origin")
        self.assertIn("WAS PUSHED", self.script("stack-detect.sh", "-n", "TEST-1").stdout)

    def test_status_recognizes_cherry_pick_and_subject_only_match(self):
        owner = self.feature()
        fix = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("switch", "-qc", "child", self.base)
        self.write("other.txt", "child\n")
        self.commit("child prerequisite")
        self.git("cherry-pick", fix)
        output = self.script("stack-status.sh", "-n", "child:main", "-b", "main", "-c", fix).stdout
        self.assertIn("yes (cherry-picked)", output)
        self.git("switch", "-qc", "subject-only", self.base)
        self.write("other.txt", "different patch\n")
        self.commit("change")
        output = self.script("stack-status.sh", "-n", "subject-only:main", "-b", "main", "-c", fix).stdout
        self.assertIn("probably", output)

    def test_status_reports_unpushed_local_copy_and_invalid_commit(self):
        branch = self.feature()
        self.git("push", "-q", "origin", branch)
        self.write("other.txt", "local fix\n")
        self.commit("local fix")
        fix = self.git("rev-parse", "HEAD").stdout.strip()
        output = self.script("stack-status.sh", "-n", "-c", fix, branch + ":develop").stdout
        self.assertIn("ahead of origin", output)
        self.assertIn("local copy: yes", output)
        self.script("stack-status.sh", "-n", "-c", "missing", branch + ":develop", expected=1)

    def test_usage_errors(self):
        for name in ("safe-push.sh", "stack-status.sh", "stack-detect.sh", "split-coverage.sh"):
            self.script(name, expected=2)
        self.script("stack-status.sh", "--unknown", expected=2)
        self.script("stack-status.sh", "-n", "missing:main", expected=1)


if __name__ == "__main__":
    unittest.main()

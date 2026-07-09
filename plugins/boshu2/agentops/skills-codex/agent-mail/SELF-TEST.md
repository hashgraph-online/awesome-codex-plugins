# SELF-TEST — agent-mail

Purpose: Validate the MCP Agent Mail guidance after updates.

## Checklist

1. **Health check**
   - Run the MCP Agent Mail `health_check()` tool.
   - Pass criteria: returns status without error.

2. **Core tool presence**
   - Verify tool schema includes: `macro_start_session`, `file_reservation_paths`, `send_message`, `request_contact`, `release_file_reservations`.
   - Pass criteria: tools listed in schema.

3. **Resource reads**
   - `resource://agents/{project_key}`
   - `resource://inbox/{agent}?project=/abs/path&limit=20`
   - `resource://thread/{thread_id}?project=/abs/path&include_bodies=true`
   - `resource://views/ack-required/{agent}?project=/abs/path`
   - Pass criteria: resources resolve (even if empty lists).

4. **Beads integration wording**
   - Confirm Beads Integration section uses `br` commands (not `bd`).

## Recording

Log timestamps and outputs for each check in the bead notes.

import { GOAL_PROGRESS_ACTIVE_ELEMENT_NAME } from "../../renderer/src/index.js";
import { installGoalProgressPageHost } from "./page-host.js";

if (typeof window !== "undefined") {
  installGoalProgressPageHost(window, {
    elementName: GOAL_PROGRESS_ACTIVE_ELEMENT_NAME,
  });
}

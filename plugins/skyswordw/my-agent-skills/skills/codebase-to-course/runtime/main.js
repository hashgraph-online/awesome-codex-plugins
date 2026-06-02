(() => {
  "use strict";

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
      return;
    }
    callback();
  }

  function query(root, selector) {
    return root.querySelector(selector);
  }

  function queryAll(root, selector) {
    return Array.from(root.querySelectorAll(selector));
  }

  function parseList(value) {
    return String(value || "")
      .split(/[,\s]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function toNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function setFeedback(node, text, state) {
    if (!node) {
      return;
    }
    node.textContent = text || "";
    if (state) {
      node.dataset.state = state;
      return;
    }
    delete node.dataset.state;
  }

  function togglePanels(panels, activeId, dataKey) {
    panels.forEach((panel) => {
      panel.hidden = panel.dataset[dataKey] !== activeId;
    });
  }

  function runWhenVisible(element, callback, options = {}) {
    if (!("IntersectionObserver" in window)) {
      callback();
      return;
    }

    let hasRun = false;
    const threshold = options.threshold ?? 0.25;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }
          if (options.once && hasRun) {
            return;
          }
          hasRun = true;
          callback();
          if (options.once) {
            observer.unobserve(element);
          }
        });
      },
      { threshold }
    );
    observer.observe(element);
  }

  function initReveal(root) {
    const revealables = queryAll(root, "[data-reveal]");
    if (!revealables.length) {
      return;
    }

    if (!("IntersectionObserver" in window)) {
      revealables.forEach((node) => node.classList.add("is-inview"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }
          entry.target.classList.add("is-inview");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.18 }
    );

    revealables.forEach((node) => observer.observe(node));
  }

  function initTranslationBlocks(root) {
    queryAll(root, "[data-translation-block]").forEach((block) => {
      const toggles = queryAll(block, "[data-translation-toggle]");
      const panels = queryAll(block, "[data-translation-panel]");
      const availablePanels = new Set(
        panels.map((panel) => panel.dataset.translationPanel).filter(Boolean)
      );

      if (!availablePanels.size) {
        return;
      }

      function normalizeView(nextView) {
        if (nextView === "split" && availablePanels.has("code") && availablePanels.has("plain")) {
          return "split";
        }
        if (availablePanels.has(nextView)) {
          return nextView;
        }
        if (window.matchMedia("(min-width: 880px)").matches && availablePanels.has("code") && availablePanels.has("plain")) {
          return "split";
        }
        if (availablePanels.has("plain")) {
          return "plain";
        }
        return "code";
      }

      function applyView(nextView) {
        const view = normalizeView(nextView);
        block.dataset.view = view;
        toggles.forEach((toggle) => {
          const active = toggle.dataset.translationToggle === view;
          toggle.classList.toggle("is-selected", active);
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
        });
        panels.forEach((panel) => {
          const panelKind = panel.dataset.translationPanel;
          panel.hidden = view !== "split" && panelKind !== view;
        });
      }

      toggles.forEach((toggle) => {
        toggle.addEventListener("click", () => {
          applyView(toggle.dataset.translationToggle);
        });
      });

      applyView(block.dataset.defaultView);
    });
  }

  function initChoiceActivity(root, config) {
    queryAll(root, config.container).forEach((activity) => {
      const options = queryAll(activity, config.optionSelector);
      const responses = queryAll(activity, config.responseSelector);
      const submit = query(activity, config.submitSelector);
      const reset = query(activity, config.resetSelector);
      const feedback = query(activity, config.feedbackSelector);
      const answerSet = new Set(parseList(activity.dataset[config.answerDataKey]));
      const mode = activity.dataset[config.modeDataKey] || (submit ? "submit" : "instant");
      let selected = "";

      function syncSelection() {
        options.forEach((option) => {
          const optionId = option.dataset[config.optionDataKey];
          const active = optionId === selected;
          option.classList.toggle("is-selected", active);
          option.setAttribute("aria-pressed", active ? "true" : "false");
        });
      }

      function clearEvaluation() {
        options.forEach((option) => {
          option.classList.remove("is-correct", "is-incorrect");
        });
        togglePanels(responses, "__none__", config.responseDataKey);
        setFeedback(feedback, "", "");
      }

      function evaluate() {
        if (!selected) {
          setFeedback(feedback, config.emptyMessage, "incorrect");
          return;
        }

        const correct = answerSet.has(selected);
        options.forEach((option) => {
          const optionId = option.dataset[config.optionDataKey];
          option.classList.toggle("is-correct", answerSet.has(optionId));
          option.classList.toggle("is-incorrect", optionId === selected && !correct);
        });
        togglePanels(responses, selected, config.responseDataKey);
        setFeedback(
          feedback,
          correct ? activity.dataset[config.successMessageKey] || config.successMessage : activity.dataset[config.failureMessageKey] || config.failureMessage,
          correct ? "correct" : "incorrect"
        );
      }

      function resetActivity() {
        selected = "";
        syncSelection();
        clearEvaluation();
      }

      options.forEach((option) => {
        option.addEventListener("click", () => {
          selected = option.dataset[config.optionDataKey] || "";
          syncSelection();
          clearEvaluation();
          if (mode === "instant") {
            evaluate();
          }
        });
      });

      if (submit) {
        submit.addEventListener("click", evaluate);
      }
      if (reset) {
        reset.addEventListener("click", resetActivity);
      }

      resetActivity();
    });
  }

  function initMatching(root) {
    queryAll(root, "[data-match]").forEach((activity) => {
      const bank = query(activity, "[data-match-bank]");
      const tokens = queryAll(activity, "[data-match-token]");
      const slots = queryAll(activity, "[data-match-slot]");
      const feedback = query(activity, "[data-match-feedback]");
      const checkButton = query(activity, "[data-match-check]");
      const resetButton = query(activity, "[data-match-reset]");
      const tokenById = new Map();
      let selectedToken = null;

      if (!bank || !tokens.length || !slots.length) {
        return;
      }

      tokens.forEach((token) => {
        const tokenId = token.dataset.matchToken;
        if (tokenId) {
          tokenById.set(tokenId, token);
        }
      });

      function setSelectedToken(token) {
        selectedToken = token;
        tokens.forEach((candidate) => {
          candidate.classList.toggle("is-selected", candidate === token);
        });
      }

      function clearEvaluation() {
        slots.forEach((slot) => {
          slot.classList.remove("is-correct", "is-incorrect", "is-over");
        });
        setFeedback(feedback, "", "");
      }

      function updateFilledState() {
        slots.forEach((slot) => {
          slot.dataset.filled = query(slot, "[data-match-token]") ? "true" : "false";
        });
      }

      function moveTokenToBank(token) {
        if (!token) {
          return;
        }
        bank.appendChild(token);
        updateFilledState();
      }

      function assignToken(token, slot) {
        if (!token || !slot) {
          return;
        }
        const occupant = query(slot, "[data-match-token]");
        if (occupant && occupant !== token) {
          moveTokenToBank(occupant);
        }
        slot.appendChild(token);
        setSelectedToken(null);
        updateFilledState();
        clearEvaluation();
      }

      function evaluate() {
        let matched = 0;
        let allFilled = true;

        slots.forEach((slot) => {
          const token = query(slot, "[data-match-token]");
          const accepted = parseList(slot.dataset.accept);
          const correct =
            Boolean(token) && accepted.length > 0 && accepted.includes(token.dataset.matchToken);

          if (!token) {
            allFilled = false;
          }
          if (correct) {
            matched += 1;
          }

          slot.classList.toggle("is-correct", correct);
          slot.classList.toggle("is-incorrect", Boolean(token) && !correct);
        });

        const success = allFilled && matched === slots.length;
        const successMessage = activity.dataset.matchSuccess || "Every connection is in the right place.";
        const failureMessage =
          activity.dataset.matchFailure || `Matched ${matched} of ${slots.length}. Revisit the misplaced pairings.`;
        setFeedback(feedback, success ? successMessage : failureMessage, success ? "correct" : "incorrect");
      }

      function resetActivity() {
        tokens.forEach((token) => bank.appendChild(token));
        setSelectedToken(null);
        clearEvaluation();
        updateFilledState();
      }

      tokens.forEach((token) => {
        token.draggable = true;
        token.addEventListener("click", () => {
          if (selectedToken === token) {
            setSelectedToken(null);
            return;
          }
          setSelectedToken(token);
        });
        token.addEventListener("dragstart", (event) => {
          token.classList.add("is-dragging");
          setSelectedToken(token);
          if (event.dataTransfer && token.dataset.matchToken) {
            event.dataTransfer.setData("text/plain", token.dataset.matchToken);
          }
        });
        token.addEventListener("dragend", () => {
          token.classList.remove("is-dragging");
        });
      });

      slots.forEach((slot) => {
        slot.addEventListener("click", () => {
          if (selectedToken) {
            assignToken(selectedToken, slot);
            return;
          }
          const occupant = query(slot, "[data-match-token]");
          if (occupant) {
            moveTokenToBank(occupant);
            clearEvaluation();
          }
        });
        slot.addEventListener("dragover", (event) => {
          event.preventDefault();
          slot.classList.add("is-over");
        });
        slot.addEventListener("dragleave", () => {
          slot.classList.remove("is-over");
        });
        slot.addEventListener("drop", (event) => {
          event.preventDefault();
          slot.classList.remove("is-over");
          const tokenId = event.dataTransfer ? event.dataTransfer.getData("text/plain") : "";
          const token = tokenById.get(tokenId) || selectedToken;
          assignToken(token, slot);
        });
      });

      bank.addEventListener("dragover", (event) => {
        event.preventDefault();
      });
      bank.addEventListener("drop", (event) => {
        event.preventDefault();
        const tokenId = event.dataTransfer ? event.dataTransfer.getData("text/plain") : "";
        const token = tokenById.get(tokenId) || selectedToken;
        moveTokenToBank(token);
        setSelectedToken(null);
        clearEvaluation();
      });

      if (checkButton) {
        checkButton.addEventListener("click", evaluate);
      }
      if (resetButton) {
        resetButton.addEventListener("click", resetActivity);
      }

      resetActivity();
    });
  }

  function initChatDemos(root) {
    queryAll(root, "[data-chat-demo]").forEach((demo) => {
      const messages = queryAll(demo, "[data-chat-message]");
      const playButton = query(demo, "[data-chat-play]");
      const resetButton = query(demo, "[data-chat-reset]");
      const status = query(demo, "[data-chat-status]");
      const baseDelay = toNumber(demo.dataset.chatInterval, 1050);
      let timers = [];
      let running = false;

      if (!messages.length) {
        return;
      }

      function clearTimers() {
        timers.forEach((timer) => window.clearTimeout(timer));
        timers = [];
        running = false;
      }

      function updateStatus(visibleCount) {
        if (!status) {
          return;
        }
        if (!visibleCount) {
          status.textContent = demo.dataset.chatIdle || "Press play to walk through the exchange.";
          return;
        }
        const prefix = demo.dataset.chatProgressPrefix || "Messages revealed";
        status.textContent = `${prefix}: ${visibleCount} of ${messages.length}.`;
      }

      function resetChat() {
        clearTimers();
        messages.forEach((message) => message.classList.remove("is-visible"));
        updateStatus(0);
      }

      function playChat() {
        resetChat();
        running = true;
        let elapsed = 120;
        messages.forEach((message, index) => {
          const stepDelay = toNumber(message.dataset.chatDelay, baseDelay);
          const timer = window.setTimeout(() => {
            message.classList.add("is-visible");
            updateStatus(index + 1);
            if (index === messages.length - 1) {
              running = false;
            }
          }, elapsed);
          timers.push(timer);
          elapsed += stepDelay;
        });
      }

      playButton?.addEventListener("click", () => {
        if (running) {
          clearTimers();
        }
        playChat();
      });
      resetButton?.addEventListener("click", resetChat);

      resetChat();
      if (demo.dataset.autoplay !== "false") {
        runWhenVisible(demo, playChat, { once: true, threshold: 0.35 });
      }
    });
  }

  function initFlowDemos(root) {
    queryAll(root, "[data-flow-demo]").forEach((demo) => {
      const items = queryAll(demo, "[data-flow-item]");
      const steps = queryAll(demo, "[data-flow-step]");
      const caption = query(demo, "[data-flow-caption-output]");
      const prevButton = query(demo, "[data-flow-prev]");
      const nextButton = query(demo, "[data-flow-next]");
      const playButton = query(demo, "[data-flow-play]");
      const resetButton = query(demo, "[data-flow-reset]");
      const interval = toNumber(demo.dataset.flowInterval, 1200);
      let activeIndex = -1;
      let timer = 0;

      if (!steps.length || !items.length) {
        return;
      }

      function clearTimer() {
        if (timer) {
          window.clearTimeout(timer);
          timer = 0;
        }
      }

      function clearStage() {
        items.forEach((item) => item.classList.remove("is-active", "is-muted"));
        steps.forEach((step) => step.classList.remove("is-active"));
        if (caption) {
          caption.textContent = demo.dataset.flowIntro || "";
        }
        activeIndex = -1;
      }

      function showStep(nextIndex) {
        activeIndex = clamp(nextIndex, 0, steps.length - 1);
        const step = steps[activeIndex];
        const targetIds = new Set(parseList(step.dataset.flowTargets));

        steps.forEach((entry, index) => {
          entry.classList.toggle("is-active", index === activeIndex);
        });
        items.forEach((item) => {
          const active = targetIds.has(item.dataset.flowItem);
          item.classList.toggle("is-active", active);
          item.classList.toggle("is-muted", targetIds.size > 0 && !active);
        });
        if (caption) {
          caption.textContent = step.dataset.flowCaption || step.textContent.trim();
        }
      }

      function playSequence() {
        clearTimer();
        let sequenceIndex = 0;
        showStep(sequenceIndex);
        const advance = () => {
          if (sequenceIndex >= steps.length - 1) {
            timer = 0;
            return;
          }
          sequenceIndex += 1;
          showStep(sequenceIndex);
          timer = window.setTimeout(advance, interval);
        };
        timer = window.setTimeout(advance, interval);
      }

      steps.forEach((step, index) => {
        step.addEventListener("click", () => {
          clearTimer();
          showStep(index);
        });
      });
      prevButton?.addEventListener("click", () => {
        clearTimer();
        showStep(activeIndex <= 0 ? 0 : activeIndex - 1);
      });
      nextButton?.addEventListener("click", () => {
        clearTimer();
        showStep(activeIndex < 0 ? 0 : clamp(activeIndex + 1, 0, steps.length - 1));
      });
      playButton?.addEventListener("click", playSequence);
      resetButton?.addEventListener("click", () => {
        clearTimer();
        clearStage();
      });

      if (demo.hasAttribute("data-default-step")) {
        showStep(clamp(toNumber(demo.dataset.defaultStep, 0), 0, steps.length - 1));
      } else {
        clearStage();
      }

      if (demo.dataset.autoplay === "true") {
        runWhenVisible(demo, playSequence, { once: true, threshold: 0.3 });
      }
    });
  }

  function initArchitecture(root) {
    queryAll(root, "[data-architecture]").forEach((diagram) => {
      const nodes = queryAll(diagram, "[data-architecture-node]");
      const panels = queryAll(diagram, "[data-architecture-panel]");
      const controls = queryAll(diagram, "[data-architecture-focus]");
      const nodeIds = new Set(nodes.map((node) => node.dataset.architectureNode).filter(Boolean));

      if (!nodeIds.size) {
        return;
      }

      function activate(nodeId) {
        if (!nodeIds.has(nodeId)) {
          return;
        }

        const activeNode = nodes.find((node) => node.dataset.architectureNode === nodeId);
        const linkedIds = new Set(parseList(activeNode ? activeNode.dataset.links : ""));

        nodes.forEach((node) => {
          const currentId = node.dataset.architectureNode;
          const active = currentId === nodeId;
          const linked = linkedIds.has(currentId);
          node.classList.toggle("is-active", active);
          node.classList.toggle("is-linked", !active && linked);
          node.classList.toggle("is-muted", linkedIds.size > 0 && !active && !linked);
          node.setAttribute("aria-pressed", active ? "true" : "false");
        });
        controls.forEach((control) => {
          const active = control.dataset.architectureFocus === nodeId;
          control.classList.toggle("is-active", active);
          control.setAttribute("aria-pressed", active ? "true" : "false");
        });
        togglePanels(panels, nodeId, "architecturePanel");
      }

      nodes.forEach((node) => {
        node.addEventListener("click", () => activate(node.dataset.architectureNode || ""));
      });
      controls.forEach((control) => {
        control.addEventListener("click", () => activate(control.dataset.architectureFocus || ""));
      });

      activate(diagram.dataset.defaultNode || nodes[0].dataset.architectureNode || "");
    });
  }

  function initLayerDemos(root) {
    queryAll(root, "[data-layer-demo]").forEach((demo) => {
      const layers = queryAll(demo, "[data-layer]");
      const toggles = queryAll(demo, "[data-layer-toggle]");
      const summary = query(demo, "[data-layer-summary]");
      const hiddenLayers = new Set(parseList(demo.dataset.hiddenLayers));

      if (!layers.length) {
        return;
      }

      function updateLayers() {
        const visibleLayers = [];
        layers.forEach((layer) => {
          const layerId = layer.dataset.layer || "";
          const hidden = hiddenLayers.has(layerId);
          layer.classList.toggle("is-hidden", hidden);
          if (!hidden) {
            visibleLayers.push(layerId);
          }
        });
        layers.forEach((layer) => {
          const hidden = hiddenLayers.has(layer.dataset.layer || "");
          layer.classList.toggle("is-emphasized", !hidden && visibleLayers.length === 1);
        });
        toggles.forEach((toggle) => {
          const layerId = toggle.dataset.layerToggle || "";
          const active = !hiddenLayers.has(layerId);
          toggle.classList.toggle("is-active", active);
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
        });
        if (summary) {
          const prefix = demo.dataset.layerSummaryPrefix || "Visible layers";
          const suffix = visibleLayers.length ? ` (${visibleLayers.join(", ")})` : " (none)";
          summary.textContent = `${prefix}: ${visibleLayers.length} of ${layers.length}${suffix}.`;
        }
      }

      toggles.forEach((toggle) => {
        toggle.addEventListener("click", () => {
          const layerId = toggle.dataset.layerToggle || "";
          if (hiddenLayers.has(layerId)) {
            hiddenLayers.delete(layerId);
          } else {
            hiddenLayers.add(layerId);
          }
          updateLayers();
        });
      });

      updateLayers();
    });
  }

  function initBugHunts(root) {
    queryAll(root, "[data-bug-hunt]").forEach((hunt) => {
      const choices = queryAll(hunt, "[data-bug-choice]");
      const markers = queryAll(hunt, "[data-bug-marker]");
      const panels = queryAll(hunt, "[data-bug-panel]");
      const submit = query(hunt, "[data-bug-submit]");
      const reset = query(hunt, "[data-bug-reset]");
      const feedback = query(hunt, "[data-bug-feedback]");
      const answers = new Set(parseList(hunt.dataset.bugAnswer));
      let selected = "";

      function syncSelection() {
        choices.forEach((choice) => {
          const active = choice.dataset.bugChoice === selected;
          choice.classList.toggle("is-selected", active);
          choice.setAttribute("aria-pressed", active ? "true" : "false");
        });
        markers.forEach((marker) => {
          marker.classList.toggle("is-selected", marker.dataset.bugMarker === selected);
        });
      }

      function clearEvaluation() {
        choices.forEach((choice) => choice.classList.remove("is-correct", "is-incorrect"));
        markers.forEach((marker) => marker.classList.remove("is-correct", "is-incorrect"));
        togglePanels(panels, "__none__", "bugPanel");
        setFeedback(feedback, "", "");
      }

      function evaluate() {
        if (!selected) {
          setFeedback(feedback, "Pick the most suspicious line first.", "incorrect");
          return;
        }

        const correct = answers.has(selected);
        choices.forEach((choice) => {
          const choiceId = choice.dataset.bugChoice || "";
          choice.classList.toggle("is-correct", answers.has(choiceId));
          choice.classList.toggle("is-incorrect", choiceId === selected && !correct);
        });
        markers.forEach((marker) => {
          const markerId = marker.dataset.bugMarker || "";
          marker.classList.toggle("is-correct", answers.has(markerId));
          marker.classList.toggle("is-incorrect", markerId === selected && !correct);
        });
        togglePanels(panels, selected, "bugPanel");
        setFeedback(
          feedback,
          correct
            ? hunt.dataset.bugSuccess || "Exactly. That is the bug worth fixing first."
            : hunt.dataset.bugFailure || "Close, but that line is a symptom rather than the root cause.",
          correct ? "correct" : "incorrect"
        );
      }

      function resetActivity() {
        selected = "";
        syncSelection();
        clearEvaluation();
      }

      function choose(nextSelection) {
        selected = nextSelection;
        syncSelection();
        clearEvaluation();
        if (!submit) {
          evaluate();
        }
      }

      choices.forEach((choice) => {
        choice.addEventListener("click", () => {
          choose(choice.dataset.bugChoice || "");
        });
      });
      markers.forEach((marker) => {
        marker.addEventListener("click", () => {
          choose(marker.dataset.bugMarker || "");
        });
      });
      submit?.addEventListener("click", evaluate);
      reset?.addEventListener("click", resetActivity);

      resetActivity();
    });
  }

  function initGlossary(root) {
    const glossaryEntries = queryAll(root, "[data-glossary]");
    let openEntry = null;

    function closeEntry(entry) {
      if (!entry) {
        return;
      }
      const trigger = query(entry, "[data-glossary-trigger]");
      const tooltip = query(entry, "[data-glossary-tooltip]");
      if (tooltip) {
        tooltip.hidden = true;
      }
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
      }
      if (openEntry === entry) {
        openEntry = null;
      }
    }

    function openGlossary(entry) {
      if (openEntry && openEntry !== entry) {
        closeEntry(openEntry);
      }
      const trigger = query(entry, "[data-glossary-trigger]");
      const tooltip = query(entry, "[data-glossary-tooltip]");
      if (!trigger || !tooltip) {
        return;
      }
      tooltip.hidden = false;
      trigger.setAttribute("aria-expanded", "true");
      openEntry = entry;
    }

    glossaryEntries.forEach((entry) => {
      const trigger = query(entry, "[data-glossary-trigger]");
      const tooltip = query(entry, "[data-glossary-tooltip]");
      if (!trigger || !tooltip) {
        return;
      }

      tooltip.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        if (openEntry === entry) {
          closeEntry(entry);
          return;
        }
        openGlossary(entry);
      });
    });

    document.addEventListener("click", (event) => {
      if (!openEntry) {
        return;
      }
      if (openEntry.contains(event.target)) {
        return;
      }
      closeEntry(openEntry);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !openEntry) {
        return;
      }
      const trigger = query(openEntry, "[data-glossary-trigger]");
      closeEntry(openEntry);
      trigger?.focus();
    });
  }

  ready(() => {
    const root = query(document, "[data-course-root]") || document.body;
    root.dataset.runtimeReady = "true";

    initReveal(root);
    initTranslationBlocks(root);
    initChoiceActivity(root, {
      container: "[data-quiz]",
      optionSelector: "[data-quiz-option]",
      optionDataKey: "quizOption",
      answerDataKey: "quizAnswer",
      responseSelector: "[data-quiz-response]",
      responseDataKey: "quizResponse",
      submitSelector: "[data-quiz-submit]",
      resetSelector: "[data-quiz-reset]",
      feedbackSelector: "[data-quiz-feedback]",
      modeDataKey: "quizMode",
      successMessageKey: "quizSuccess",
      failureMessageKey: "quizFailure",
      emptyMessage: "Pick one answer before checking your reasoning.",
      successMessage: "Correct. The runtime can now reveal the explanation panel.",
      failureMessage: "Not quite. Re-read the options and compare the explanation."
    });
    initChoiceActivity(root, {
      container: "[data-scenario-quiz]",
      optionSelector: "[data-scenario-option]",
      optionDataKey: "scenarioOption",
      answerDataKey: "scenarioAnswer",
      responseSelector: "[data-scenario-panel]",
      responseDataKey: "scenarioPanel",
      submitSelector: "[data-scenario-submit]",
      resetSelector: "[data-scenario-reset]",
      feedbackSelector: "[data-scenario-feedback]",
      modeDataKey: "scenarioMode",
      successMessageKey: "scenarioSuccess",
      failureMessageKey: "scenarioFailure",
      emptyMessage: "Choose a path before evaluating the scenario.",
      successMessage: "This branch best matches the course recommendation.",
      failureMessage: "That branch is plausible, but it misses the main tradeoff."
    });
    initMatching(root);
    initChatDemos(root);
    initFlowDemos(root);
    initArchitecture(root);
    initLayerDemos(root);
    initBugHunts(root);
    initGlossary(root);
  });
})();

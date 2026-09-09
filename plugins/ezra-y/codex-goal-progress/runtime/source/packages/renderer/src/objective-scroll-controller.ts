const SCROLLBAR_IDLE_DELAY_MS = 700;

export interface ObjectiveScrollState {
  readonly scrolling: boolean;
  readonly scrollable: boolean;
  readonly thumbSize: number;
  readonly thumbOffset: number;
}

const initialState: ObjectiveScrollState = {
  scrolling: false,
  scrollable: false,
  thumbSize: 0,
  thumbOffset: 0,
};

export class ObjectiveScrollController {
  readonly #onStateChange: (state: ObjectiveScrollState) => void;
  #state = initialState;
  #root: ParentNode | null = null;
  #objectiveList: HTMLElement | null = null;
  #listEvents: AbortController | null = null;
  #resizeObserver: ResizeObserver | null = null;
  #scrollbarTimer: ReturnType<typeof setTimeout> | null = null;
  #activeScrollFrame: number | null = null;
  #restoreScrollFrame: number | null = null;
  #identity: string | null = null;
  #savedScrollTop = 0;
  #pendingActiveScroll = false;

  constructor(onStateChange: (state: ObjectiveScrollState) => void) {
    this.#onStateChange = onStateChange;
  }

  bind(root: ParentNode, identity: string | null = null): void {
    this.#root = root;
    const nextList = root.querySelector<HTMLElement>(".objective-list");
    const identityChanged = identity !== this.#identity;
    if (identityChanged) {
      this.#savedScrollTop = 0;
      this.#pendingActiveScroll = false;
    } else if (this.#objectiveList?.isConnected === true && nextList !== this.#objectiveList) {
      this.#savedScrollTop = this.#objectiveList.scrollTop;
    }
    this.#identity = identity;
    if (nextList === this.#objectiveList) {
      if (identityChanged && nextList) {
        this.#setScrollTop(nextList, 0);
      }
      this.#syncScrollable();
      if (this.#pendingActiveScroll) {
        this.#scheduleActiveObjectiveFrame(root);
      }
      return;
    }
    this.#releaseResources();
    if (this.#state.scrolling) {
      this.#setState({ scrolling: false });
    }
    if (!nextList) {
      this.#setState({
        scrollable: false,
        thumbSize: 0,
        thumbOffset: 0,
      });
      return;
    }

    this.#objectiveList = nextList;
    if (!identityChanged && this.#savedScrollTop > 0) {
      this.#restoreSavedScrollTop(nextList);
    }
    this.#listEvents = new AbortController();
    nextList.addEventListener("scroll", () => this.#onListScroll(nextList), {
      passive: true,
      signal: this.#listEvents.signal,
    });
    if (typeof ResizeObserver !== "undefined") {
      this.#resizeObserver = new ResizeObserver(() => this.#syncScrollable());
      this.#resizeObserver.observe(nextList);
    }
    this.#syncScrollable();
    if (this.#pendingActiveScroll) {
      this.#scheduleActiveObjectiveFrame(root);
    }
  }

  release(): void {
    this.#root = null;
    this.#releaseResources();
    this.#identity = null;
    this.#savedScrollTop = 0;
    this.#pendingActiveScroll = false;
  }

  captureScrollPosition(): void {
    if (this.#objectiveList) {
      this.#savedScrollTop = this.#objectiveList.scrollTop;
    }
  }

  scheduleActiveObjective(root: ParentNode = this.#root ?? document): void {
    this.#pendingActiveScroll = true;
    this.#scheduleActiveObjectiveFrame(root);
  }

  #scheduleActiveObjectiveFrame(root: ParentNode): void {
    if (this.#activeScrollFrame !== null) {
      cancelAnimationFrame(this.#activeScrollFrame);
    }
    this.#activeScrollFrame = requestAnimationFrame(() => {
      this.#activeScrollFrame = null;
      const list = this.#objectiveList;
      const activeObjective = root.querySelector<HTMLElement>(
        '.objective-row[data-status="active"]',
      );
      if (!list) {
        return;
      }
      if (!activeObjective) {
        this.#pendingActiveScroll = false;
        return;
      }
      const listBounds = list.getBoundingClientRect();
      const activeBounds = activeObjective.getBoundingClientRect();
      if (activeBounds.top < listBounds.top) {
        this.#setScrollTop(list, list.scrollTop - (listBounds.top - activeBounds.top));
      } else if (activeBounds.bottom > listBounds.bottom) {
        this.#setScrollTop(list, list.scrollTop + (activeBounds.bottom - listBounds.bottom));
      }
      this.#pendingActiveScroll = false;
    });
  }

  #restoreSavedScrollTop(list: HTMLElement): void {
    const restore = () => {
      if (this.#objectiveList !== list || this.#pendingActiveScroll) {
        return;
      }
      const maximumScroll = Math.max(0, list.scrollHeight - list.clientHeight);
      this.#setScrollTop(list, Math.min(this.#savedScrollTop, maximumScroll));
      this.#updateScrollIndicator();
    };
    restore();
    if (typeof requestAnimationFrame === "function") {
      if (this.#restoreScrollFrame !== null) {
        cancelAnimationFrame(this.#restoreScrollFrame);
      }
      this.#restoreScrollFrame = requestAnimationFrame(() => {
        this.#restoreScrollFrame = null;
        restore();
      });
    }
  }

  #setScrollTop(list: HTMLElement, scrollTop: number): void {
    list.scrollTop = scrollTop;
    this.#savedScrollTop = list.scrollTop;
  }

  #releaseResources(): void {
    this.#listEvents?.abort();
    this.#listEvents = null;
    this.#resizeObserver?.disconnect();
    this.#resizeObserver = null;
    if (this.#scrollbarTimer !== null) {
      clearTimeout(this.#scrollbarTimer);
      this.#scrollbarTimer = null;
    }
    if (this.#activeScrollFrame !== null) {
      cancelAnimationFrame(this.#activeScrollFrame);
      this.#activeScrollFrame = null;
    }
    if (this.#restoreScrollFrame !== null) {
      cancelAnimationFrame(this.#restoreScrollFrame);
      this.#restoreScrollFrame = null;
    }
    this.#objectiveList = null;
  }

  #syncScrollable(): void {
    const scrollable =
      this.#objectiveList !== null &&
      this.#objectiveList.scrollHeight > this.#objectiveList.clientHeight + 1;
    this.#setState({ scrollable });
    this.#updateScrollIndicator();
  }

  #updateScrollIndicator(): void {
    const list = this.#objectiveList;
    if (!list || list.scrollHeight <= list.clientHeight) {
      this.#setState({ thumbSize: 0, thumbOffset: 0 });
      return;
    }
    const trackHeight = Math.max(0, list.clientHeight - 8);
    const thumbSize = Math.max(24, (list.clientHeight / list.scrollHeight) * trackHeight);
    const maximumOffset = Math.max(0, trackHeight - thumbSize);
    const maximumScroll = list.scrollHeight - list.clientHeight;
    const thumbOffset = maximumScroll > 0 ? (list.scrollTop / maximumScroll) * maximumOffset : 0;
    this.#setState({ thumbSize, thumbOffset });
  }

  #onListScroll(list: HTMLElement): void {
    if (list !== this.#objectiveList) {
      return;
    }
    const manualScroll = Math.abs(list.scrollTop - this.#savedScrollTop) > 0.5;
    this.#savedScrollTop = list.scrollTop;
    this.#updateScrollIndicator();
    if (!manualScroll) {
      return;
    }
    if (this.#activeScrollFrame !== null) {
      cancelAnimationFrame(this.#activeScrollFrame);
      this.#activeScrollFrame = null;
    }
    if (this.#restoreScrollFrame !== null) {
      cancelAnimationFrame(this.#restoreScrollFrame);
      this.#restoreScrollFrame = null;
    }
    this.#pendingActiveScroll = false;
    this.#setState({ scrolling: true });
    if (this.#scrollbarTimer !== null) {
      clearTimeout(this.#scrollbarTimer);
    }
    this.#scrollbarTimer = setTimeout(() => {
      this.#scrollbarTimer = null;
      this.#setState({ scrolling: false });
    }, SCROLLBAR_IDLE_DELAY_MS);
  }

  #setState(change: Partial<ObjectiveScrollState>): void {
    const next = { ...this.#state, ...change };
    if (
      next.scrolling === this.#state.scrolling &&
      next.scrollable === this.#state.scrollable &&
      Math.abs(next.thumbSize - this.#state.thumbSize) <= 0.1 &&
      Math.abs(next.thumbOffset - this.#state.thumbOffset) <= 0.1
    ) {
      return;
    }
    this.#state = next;
    this.#onStateChange(next);
  }
}

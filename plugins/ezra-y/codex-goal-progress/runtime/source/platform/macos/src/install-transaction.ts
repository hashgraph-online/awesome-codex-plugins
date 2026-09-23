export interface InstallStepResult<Value> {
  readonly changed: boolean;
  readonly value: Value;
}

export interface InstallRollbackResult {
  readonly step: string;
  readonly ok: boolean;
  readonly error: string | null;
}

interface RegisteredRollback {
  readonly step: string;
  readonly run: () => Promise<void>;
}

export class InstallTransaction {
  readonly #startedSteps: string[] = [];
  readonly #changedSteps: string[] = [];
  readonly #rollbacks: RegisteredRollback[] = [];
  #currentStep: string | null = null;
  #committed = false;

  get partialState() {
    return {
      currentStep: this.#currentStep,
      startedSteps: [...this.#startedSteps],
      changedSteps: [...this.#changedSteps],
    };
  }

  get committed(): boolean {
    return this.#committed;
  }

  async step<Value>(
    name: string,
    apply: () => Promise<InstallStepResult<Value>>,
    rollback: () => Promise<void>,
  ): Promise<Value> {
    if (this.#committed || !name || this.#startedSteps.includes(name)) {
      throw new Error("GOAL_PROGRESS_INSTALL_TRANSACTION_INVALID");
    }
    this.#currentStep = name;
    this.#startedSteps.push(name);
    const registered = { step: name, run: rollback };
    this.#rollbacks.push(registered);
    const result = await apply();
    if (result.changed) {
      this.#changedSteps.push(name);
    } else {
      this.#rollbacks.splice(this.#rollbacks.indexOf(registered), 1);
    }
    this.#currentStep = null;
    return result.value;
  }

  commit(): void {
    if (this.#currentStep !== null) {
      throw new Error("GOAL_PROGRESS_INSTALL_TRANSACTION_ACTIVE");
    }
    this.#committed = true;
    this.#rollbacks.length = 0;
  }

  async rollback(): Promise<readonly InstallRollbackResult[]> {
    const results: InstallRollbackResult[] = [];
    for (const rollback of this.#rollbacks.reverse()) {
      try {
        await rollback.run();
        results.push({ step: rollback.step, ok: true, error: null });
      } catch (error) {
        results.push({
          step: rollback.step,
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }
    this.#rollbacks.length = 0;
    this.#currentStep = null;
    return results;
  }
}

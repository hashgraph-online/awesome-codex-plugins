export type ControllerRegime = "STANDARD" | "ATPP";

export type DsarRightType =
  | "CONFIRMATION_SIMPLIFIED" // Art. 18, I + Art. 19, I
  | "ACCESS_SIMPLIFIED"       // Art. 18, II + Art. 19, I
  | "ACCESS_COMPLETE"         // Art. 18, II + Art. 19, II
  | "CORRECTION"              // Art. 18, III
  | "ANONYMIZATION_BLOCKING_EXCESSIVE" // Art. 18, IV
  | "PORTABILITY"             // Art. 18, V
  | "ERASURE_CONSENT"         // Art. 18, VI
  | "SHARING_INFO"            // Art. 18, VII
  | "NON_CONSENT_INFO"        // Art. 18, VIII
  | "CONSENT_REVOCATION"      // Art. 18, IX + Art. 8º, § 5º
  | "AUTOMATED_DECISION_REVIEW"; // Art. 20

export interface DsarSlaResult {
  immediate: boolean;
  maxCalendarDays: number;
  deadlineAt: Date;
  normativeBasis: string;
}

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * Calcula o prazo normativo de resposta a requisições de titulares (DSAR):
 * - Controlador padrão: formato simplificado = imediato (Art. 19, I);
 *   declaração completa = até 15 dias corridos da requisição (Art. 19, II).
 * - ATPP (Res. CD/ANPD nº 2/2022, Art. 14):
 *   declaração simplificada = até 15 dias (Art. 14, I);
 *   declaração completa e demais prazos dobrados = até 30 dias (Art. 14, caput).
 */
export function calculateDsarSla(input: {
  right: DsarRightType;
  regime: ControllerRegime;
  requestedAt: Date;
}): DsarSlaResult {
  const { right, regime, requestedAt } = input;

  if (right === "CONFIRMATION_SIMPLIFIED" || right === "ACCESS_SIMPLIFIED") {
    if (regime === "ATPP") {
      return {
        immediate: false,
        maxCalendarDays: 15,
        deadlineAt: new Date(requestedAt.getTime() + 15 * MS_PER_DAY),
        normativeBasis: "LGPD Art. 19, I c/c Res. CD/ANPD nº 2/2022, Art. 14, I",
      };
    }
    return {
      immediate: true,
      maxCalendarDays: 0,
      deadlineAt: new Date(requestedAt.getTime()),
      normativeBasis: "LGPD Art. 19, I",
    };
  }

  if (right === "NON_CONSENT_INFO" || right === "CONSENT_REVOCATION") {
    return {
      immediate: true,
      maxCalendarDays: 0,
      deadlineAt: new Date(requestedAt.getTime()),
      normativeBasis:
        right === "CONSENT_REVOCATION"
          ? "LGPD Art. 8º, § 5º e Art. 18, IX"
          : "LGPD Art. 18, VIII",
    };
  }

  const baseDays = 15;
  const maxCalendarDays = regime === "ATPP" ? baseDays * 2 : baseDays;
  return {
    immediate: false,
    maxCalendarDays,
    deadlineAt: new Date(requestedAt.getTime() + maxCalendarDays * MS_PER_DAY),
    normativeBasis:
      regime === "ATPP"
        ? "LGPD Art. 19, II c/c Res. CD/ANPD nº 2/2022, Art. 14, caput"
        : "LGPD Art. 19, II",
  };
}

export interface LegalRetentionObligation {
  documentType: string;
  statutoryBasis: string;
  retainUntil: Date;
  requiredFields: string[];
}

export type ErasureDisposition =
  | {
      mode: "HARD_DELETE";
      retainedFields: [];
      retainUntil: null;
      recordSuppressionTombstone: true;
    }
  | {
      mode: "BLOCK_AND_MINIMIZE";
      retainedFields: string[];
      retainUntil: Date;
      statutoryBases: string[];
      recordSuppressionTombstone: true;
    };

export function planErasureDisposition(
  activeObligations: ReadonlyArray<LegalRetentionObligation>,
  now: Date = new Date(),
): ErasureDisposition {
  const unexpired = activeObligations.filter(
    (o) => o.retainUntil.getTime() > now.getTime(),
  );

  if (unexpired.length === 0) {
    return {
      mode: "HARD_DELETE",
      retainedFields: [],
      retainUntil: null,
      recordSuppressionTombstone: true,
    };
  }

  const fieldSet = new Set<string>();
  const basisSet = new Set<string>();
  let maxDate = unexpired[0]!.retainUntil;

  for (const ob of unexpired) {
    basisSet.add(`${ob.documentType} (${ob.statutoryBasis})`);
    for (const f of ob.requiredFields) {
      fieldSet.add(f);
    }
    if (ob.retainUntil.getTime() > maxDate.getTime()) {
      maxDate = ob.retainUntil;
    }
  }

  return {
    mode: "BLOCK_AND_MINIMIZE",
    retainedFields: [...fieldSet].sort(),
    retainUntil: maxDate,
    statutoryBases: [...basisSet],
    recordSuppressionTombstone: true,
  };
}

export type MinorAgeClassification =
  | "CHILD_UNDER_12"
  | "ADOLESCENT_12_TO_16"
  | "ADOLESCENT_17"
  | "ADULT_18_PLUS";

/**
 * Classifica faixas etárias relevantes conjugando:
 * - LGPD Art. 14 + ECA Art. 2º (< 12 criança; 12–17 adolescente; Enunciado CD/ANPD nº 1/2023)
 * - ECA Digital (Lei 15.211/2025, Art. 24: vinculação a responsável legal até 16 anos quando aplicável)
 */
export function classifyMinorAgeRules(ageYears: number, legalBasisIsConsent: boolean): {
  band: MinorAgeClassification;
  requiresBestInterestAssessment: boolean;
  requiresSpecificParentalConsentUnderArt14: boolean;
  requiresEcaDigitalGuardianLinkIfApplicable: boolean;
  adProfilingProhibited: boolean;
} {
  if (!Number.isFinite(ageYears) || ageYears < 0) {
    throw new Error("Age must be a non-negative finite number.");
  }

  if (ageYears < 12) {
    return {
      band: "CHILD_UNDER_12",
      requiresBestInterestAssessment: true,
      // Enunciado CD/ANPD nº 1/2023: consentimento parental específico do Art. 14, § 1º é exigido
      // quando a base legal adotada para a criança é o consentimento; outras bases dos Arts. 7º/11
      // são possíveis desde que prevaleça o melhor interesse no caso concreto.
      requiresSpecificParentalConsentUnderArt14: legalBasisIsConsent,
      requiresEcaDigitalGuardianLinkIfApplicable: true,
      adProfilingProhibited: true,
    };
  }

  if (ageYears <= 16) {
    return {
      band: "ADOLESCENT_12_TO_16",
      requiresBestInterestAssessment: true,
      requiresSpecificParentalConsentUnderArt14: false,
      // Art. 24 da Lei 15.211/2025: "até 16 (dezesseis) anos". Leitura adotada: 16 anos INCLUSIVE
      // (a mais protetiva, conforme o melhor interesse — Art. 3º). Documente se adotar outra leitura.
      requiresEcaDigitalGuardianLinkIfApplicable: true,
      adProfilingProhibited: true,
    };
  }

  if (ageYears < 18) {
    return {
      band: "ADOLESCENT_17",
      requiresBestInterestAssessment: true,
      requiresSpecificParentalConsentUnderArt14: false,
      requiresEcaDigitalGuardianLinkIfApplicable: false,
      adProfilingProhibited: true,
    };
  }

  return {
    band: "ADULT_18_PLUS",
    requiresBestInterestAssessment: false,
    requiresSpecificParentalConsentUnderArt14: false,
    requiresEcaDigitalGuardianLinkIfApplicable: false,
    adProfilingProhibited: false,
  };
}

export interface FloatingCenterInput {
  readonly safeLeft: number;
  readonly safeRight: number;
  readonly boundaryWidth: number;
  readonly collisionWidth?: number;
  readonly ratio: number;
  readonly obstacleLeft?: number;
  readonly obstacleRight?: number;
  readonly obstacleGap?: number;
}

export interface FloatingCenterResult {
  readonly blocked: boolean;
  readonly center: number;
}

export function projectFloatingCenter(input: FloatingCenterInput): FloatingCenterResult {
  const boundaryHalfWidth = Math.max(0, input.boundaryWidth) / 2;
  const collisionHalfWidth = Math.max(0, input.collisionWidth ?? input.boundaryWidth) / 2;
  const minimumCenter = input.safeLeft + boundaryHalfWidth;
  const maximumCenter = Math.max(minimumCenter, input.safeRight - boundaryHalfWidth);
  const ratio = Math.max(0, Math.min(1, input.ratio));
  const preferred = minimumCenter + ratio * Math.max(0, maximumCenter - minimumCenter);
  if (input.obstacleLeft === undefined || input.obstacleRight === undefined) {
    return { blocked: false, center: preferred };
  }

  const gap = input.obstacleGap ?? 8;
  const forbiddenLeft = input.obstacleLeft - gap - collisionHalfWidth;
  const forbiddenRight = input.obstacleRight + gap + collisionHalfWidth;
  if (preferred <= forbiddenLeft || preferred >= forbiddenRight) {
    return { blocked: false, center: preferred };
  }
  const candidates = [forbiddenLeft, forbiddenRight].filter(
    (candidate) => candidate >= minimumCenter && candidate <= maximumCenter,
  );
  if (candidates.length === 0) {
    return { blocked: true, center: preferred };
  }
  const center = candidates.reduce((nearest, candidate) =>
    Math.abs(candidate - preferred) < Math.abs(nearest - preferred) ? candidate : nearest,
  );
  return { blocked: false, center };
}

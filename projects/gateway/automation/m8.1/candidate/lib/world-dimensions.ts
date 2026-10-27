import type { WorldId } from "./universe-config";

/** Local terrain diameters. Building, character and movement units are unchanged. */
export const DEFAULT_WORLD_DIMENSIONS = Object.freeze({ width: 2.72, depth: 2.32 });
const dimensions: Partial<Record<WorldId, typeof DEFAULT_WORLD_DIMENSIONS>> = {
  tools: Object.freeze({ width: 5.2, depth: 4.4 }),
};

export function worldDimensions(id?: string) {
  return (id && Object.hasOwn(dimensions, id) && dimensions[id as WorldId]) || DEFAULT_WORLD_DIMENSIONS;
}

/** Retain the original fit for unmigrated worlds; cover the larger terrain envelope. */
export function worldInspectionExtent(id?: string) {
  const size = worldDimensions(id);
  return Math.max(2, Math.hypot(size.width / 2, size.depth / 2));
}

/** Preserve the original holding-point distance beyond the terrain's west edge. */
export function worldParkingOffset(id: WorldId) {
  return (worldDimensions(id).width - DEFAULT_WORLD_DIMENSIONS.width) / 2;
}

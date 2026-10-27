import { featuredProjects, type PortfolioCardItem } from "./site-config";
import { projectPrimaryWorld, universePlanets, type Coordinates, type WorldId } from "./universe-config";
import { getProject } from "./ecosystem";

export type ProjectLandmark = {
  id: string;
  projectId: string;
  worldId: WorldId;
  /** Anchor in the diorama's local coordinate system, before all world transforms. */
  anchor: Coordinates;
  /** Stable recipe structure binding, never a part-array index or floating marker. */
  structureId: string;
};

type LocationBase = {
  id: string;
  worldId: WorldId;
  /** Local focus/location anchor; existing occupied anchors are preserved. */
  position: Coordinates;
  rotation?: Coordinates;
};
export type ProjectLocation = LocationBase & (
  | { state: "occupied"; projectId: string; structureId: string }
  | { state: "decorative" | "reserved" | "construction"; projectId?: never; structureId?: never }
);
type Placement = Omit<Extract<ProjectLocation, { state: "occupied" }>, "worldId" | "state">;
const placements: Placement[] = [
  { id: "landmark-page-layr", projectId: "pageLayr", position: [-0.12, 1.85, -0.5], structureId: "city-spire" },
  { id: "landmark-tinyverse", projectId: "tinyverse", position: [0.55, 1.12, -0.4], structureId: "terrain-castle" },
  { id: "landmark-javascriptia", projectId: "javascriptia", position: [-0.22, 0.8, -0.25], structureId: "academy-hall" },
  { id: "landmark-kodestep", projectId: "kodeStep", position: [0.7, 1.3, -0.43], structureId: "academy-tower" },
  { id: "landmark-careerlens", projectId: "careerLens", position: [-0.4, 0.8, -0.25], structureId: "workshop-hall" },
  { id: "landmark-foodie-map", projectId: "foodieMap", position: [-0.55, 0.9, -0.3], structureId: "creative-observatory" },
  { id: "landmark-tcg-hub", projectId: "tcgHub", position: [0.53, 0.92, 0.15], structureId: "creative-sculpture" },
  { id: "landmark-playdeck", projectId: "playdeck", position: [-0.72, 0.6, -0.47], structureId: "campus-north-west" },
  { id: "landmark-neuran", projectId: "neuran", position: [0, 0.85, -0.1], structureId: "campus-center" },
  { id: "landmark-nikah-yuk", projectId: "nikahyuk", position: [0.72, 0.6, -0.47], structureId: "campus-north-east" },
  { id: "landmark-nikah-yuk-prototype", projectId: "nikahyukPrototype", position: [-0.72, 0.6, 0.52], structureId: "campus-south-west" },
  { id: "landmark-nikah-kuy", projectId: "nikahkuy", position: [0.72, 0.6, 0.52], structureId: "campus-south-east" },
];

export function validateProjectLocations(locations: readonly ProjectLocation[]) {
  const ids = new Set<string>(), projects = new Set<string>(), bindings = new Set<string>();
  const coordinates = (value: Coordinates) => Array.isArray(value) && value.length === 3 && value.every(Number.isFinite);
  for (const location of locations) {
    if (!location.id?.trim() || location.id !== location.id.trim() || ids.has(location.id)) throw new Error("Gateway: duplicate or invalid location identity");
    if (!universePlanets.some(world => world.id === location.worldId) || !coordinates(location.position)
      || (location.rotation !== undefined && !coordinates(location.rotation))) throw new Error("Gateway: invalid location transform or world");
    if (!["occupied", "decorative", "reserved", "construction"].includes(location.state)) throw new Error("Gateway: invalid location state");
    if (location.state === "occupied") {
      getProject(location.projectId); // Unknown canonical references must fail, never become placeholder projects.
      const binding = location.worldId + ":" + location.structureId;
      if (projectPrimaryWorld[location.projectId] !== location.worldId) throw new Error("Gateway: location must belong to its project's primary world");
      if (!location.structureId?.trim() || projects.has(location.projectId) || bindings.has(binding)) throw new Error("Gateway: duplicate or invalid occupied binding");
      projects.add(location.projectId); bindings.add(binding);
    } else if (Object.hasOwn(location, "projectId") || Object.hasOwn(location, "structureId")) {
      throw new Error("Gateway: only occupied locations may bind projects or landmarks");
    }
    ids.add(location.id);
  }
}

// The original placement registry remains the owner; membership is still projectPrimaryWorld.
export const projectLocations: ProjectLocation[] = [
  ...placements.map(placement => ({ ...placement, worldId: projectPrimaryWorld[placement.projectId], state: "occupied" as const })),
  { id: "tools-reserve-east", worldId: "tools", position: [1.6, .18, .7], state: "reserved" },
];
validateProjectLocations(projectLocations);

export function validateLandmarks(landmarks: ProjectLandmark[], projects = featuredProjects) {
  const ids = new Set<string>(), projectIds = new Set<string>(), bindings = new Set<string>();
  for (const landmark of landmarks) {
    const binding = landmark.worldId + ":" + landmark.structureId;
    if (!landmark.id || ids.has(landmark.id) || projectIds.has(landmark.projectId) || bindings.has(binding)) throw new Error("Gateway: duplicate landmark identity or structure");
    if (!projects.some(project => project.projectId === landmark.projectId) || projectPrimaryWorld[landmark.projectId] !== landmark.worldId) throw new Error("Gateway: landmark must belong to its Featured project's primary world");
    if (!landmark.structureId || landmark.anchor.length !== 3 || !landmark.anchor.every(Number.isFinite)) throw new Error("Gateway: invalid landmark placement");
    ids.add(landmark.id); projectIds.add(landmark.projectId); bindings.add(binding);
  }
  if (projects.some(project => !projectIds.has(project.projectId))) throw new Error("Gateway: missing Featured project landmark");
}

// World membership has one owner; placement does not introduce another mapping.
export function landmarksFromLocations(locations: readonly ProjectLocation[], projects = featuredProjects): ProjectLandmark[] {
  validateProjectLocations(locations);
  const landmarks = locations.flatMap(location => location.state === "occupied" && projects.some(project => project.projectId === location.projectId)
    ? [{ id: location.id, projectId: location.projectId, worldId: location.worldId, anchor: location.position, structureId: location.structureId }] : []);
  validateLandmarks(landmarks, projects);
  return landmarks;
}
export const projectLandmarks = landmarksFromLocations(projectLocations);

export const landmarksForWorld = (worldId: string) => projectLandmarks.filter(landmark => landmark.worldId === worldId);
export const landmarkProject = (id: string): PortfolioCardItem | undefined => {
  const landmark = projectLandmarks.find(item => item.id === id);
  return featuredProjects.find(project => project.projectId === landmark?.projectId);
};

/** Tracks maximum displacement, so a drag returning to its origin still isn't a click. */
export class LandmarkGesture {
  private start: { pointerId: number; x: number; y: number; landmarkId: string | null; moved: boolean } | null = null;
  begin(pointerId: number, x: number, y: number, landmarkId: string | null) {
    if (this.start) return;
    this.start = { pointerId, x, y, landmarkId, moved: false };
  }
  move(pointerId: number, x: number, y: number) {
    const start = this.start;
    if (start?.pointerId === pointerId && Math.hypot(x - start.x, y - start.y) > 6) start.moved = true;
  }
  finish(pointerId: number, x: number, y: number, landmarkId: string | null) {
    if (this.start?.pointerId !== pointerId) return null;
    this.move(pointerId, x, y);
    const start = this.start;
    this.start = null;
    return !start.moved && start.landmarkId === landmarkId ? landmarkId : null;
  }
  cancel() { this.start = null; }
}

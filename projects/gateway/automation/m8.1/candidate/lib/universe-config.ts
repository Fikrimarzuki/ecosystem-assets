import { destinations, featuredProjects, type PortfolioCardItem } from "./site-config";
import { orbitAt, type OrbitConfig } from "./universe-orbit";
import { worldInspectionExtent, worldParkingOffset } from "./world-dimensions";

export type Coordinates = [number, number, number];
export type WorldId = "latest" | "games" | "learning" | "tools" | "after-hours" | "platforms";
export type PlanetTheme = "city" | "terrain" | "academy" | "workshop" | "creative" | "campus";
export type UniversePlanet = {
  id: WorldId;
  name: string;
  category: string;
  description: string;
  position: Coordinates;
  orbit: OrbitConfig;
  /** World-space height above center, including the landmark and ambient margin. */
  labelTop: number;
  scale: number;
  rotation: Coordinates;
  /** Stable label anchor relative to center, in world units (not animated). */
  labelOffset: Coordinates;
  theme: PlanetTheme;
  color: string;
  surface: string;
  /** Panel links: primary-world projects first, then related hubs. */
  projects: PortfolioCardItem[];
  /** Phase-zero world-space anchors, translated with the frozen orbit. Landing is reserved. */
  travelTarget?: Coordinates;
  /** Rocket holding point in this world's local coordinates; distinct from surface landing. */
  parkingTarget?: Coordinates;
  landingTarget?: Coordinates;
  focusTarget?: Coordinates;
};

// Gateway-owned world assignments by canonical project ID (docs/portfolio-information-architecture.md).
// Each portfolio project has exactly one primary world: its future M4 landmark home.
export const projectPrimaryWorld: Record<string, WorldId> = {
  pageLayr: "latest",
  tinyverse: "games",
  javascriptia: "learning",
  playdeck: "platforms",
  kodeStep: "learning",
  careerLens: "tools",
  foodieMap: "after-hours",
  tcgHub: "after-hours",
  neuran: "platforms",
  nikahyuk: "platforms",
  nikahyukPrototype: "platforms",
  nikahkuy: "platforms",
};

// Ecosystem hubs related to a world are listed as links only; they are never landmarks.
// CV and Projects are intentionally unassigned.
export const hubWorld: Record<string, WorldId> = {
  games: "games",
  learning: "learning",
  roadmap: "learning",
  tools: "tools",
  devtools: "tools",
  playground: "after-hours",
};

const worldLinks = (world: WorldId) => [
  ...featuredProjects.filter((project) => projectPrimaryWorld[project.projectId] === world),
  ...destinations.filter((hub) => hubWorld[hub.projectId] === world),
];

export const universePlanets: UniversePlanet[] = [
  {
    id: "latest", name: "Latest Builds", category: "latest",
    description: "Fresh ideas taking shape. A curated starting point for my newest builds.",
    ...orbitAt(155, -0.8, 0.2), labelTop: 3.8, scale: 1.65, rotation: [0.48, -0.35, -0.04], labelOffset: [0, -2.05, 0],
    theme: "city", color: "#8cd9df", surface: "#416b79",
    projects: worldLinks("latest"),
  },
  {
    id: "games", name: "Games", category: "games",
    description: "Little worlds made to be played. Mechanics, adventures, and creative coding.",
    ...orbitAt(95, -3.4, -0.25), labelTop: 3.2, scale: 1.65, rotation: [0.52, 0.2, 0.06], labelOffset: [-0.7, -1.8, 0],
    theme: "terrain", color: "#b9d78a", surface: "#607a53",
    projects: worldLinks("games"),
  },
  {
    id: "learning", name: "Learning", category: "learning",
    description: "A place for curiosity. Learning paths, knowledge notes, and engineering growth.",
    ...orbitAt(35, -2, 0.4), labelTop: 3.2, scale: 1.55, rotation: [0.46, -0.45, 0.02], labelOffset: [0, -1.9, 0],
    theme: "academy", color: "#dfc99a", surface: "#827357",
    projects: worldLinks("learning"),
  },
  {
    id: "tools", name: "Tools", category: "tools",
    description: "Built for the everyday. Focused utilities that make useful work a little easier.",
    ...orbitAt(215, 2.2, -0.4), labelTop: 2.8, scale: 1.5, rotation: [0.55, 0.3, -0.04], labelOffset: [0, -1.9, 0],
    theme: "workshop", color: "#9cbbdc", surface: "#546b88",
    parkingTarget: [-1.8 - worldParkingOffset("tools"), 1, -0.3],
    projects: worldLinks("tools"),
  },
  {
    id: "after-hours", name: "After-Hours", category: "after-hours",
    description: "Room to experiment. Unusual interfaces, playful ideas, and creative detours.",
    ...orbitAt(275, 1.8, 0.3), labelTop: 2.35, scale: 1.45, rotation: [0.45, -0.3, 0.06], labelOffset: [0, -2, 0],
    theme: "creative", color: "#c4a7d9", surface: "#735e84",
    projects: worldLinks("after-hours"),
  },
  {
    id: "platforms", name: "Platforms / Suites", category: "platforms",
    description: "Connected systems with room to grow. Builders and tools for making something bigger.",
    ...orbitAt(335, 0.4, -0.15), labelTop: 2.5, scale: 1.65, rotation: [0.52, -0.5, 0.03], labelOffset: [0.45, -2.05, 0],
    theme: "campus", color: "#8fcdbc", surface: "#4c796f",
    projects: worldLinks("platforms"),
  },
];

export const gatewayConfig = {
  name: "Fikri Gateway", position: [0.5, 0, 0.8] as Coordinates,
  scale: 1.4, rotation: [0.52, -0.25, 0] as Coordinates,
  labelOffset: [0, 4.2, 0] as Coordinates,
  // Station-local pad shared by the deck and the rocket's departure transform.
  dockingPad: [0.6, 0.16, 0.62] as Coordinates,
};

export const universeCamera = { distance: 28, minHeight: 25.6, minWidth: 29.5 };

/** Fit the complete miniature with space for identity and inspection controls. */
export function inspectionDistance(scale: number, aspect: number, canvasHeight: number, worldId?: string) {
  const halfAngle = Math.min(Math.PI / 9, Math.atan(Math.tan(Math.PI / 9) * aspect));
  return scale * worldInspectionExtent(worldId) / Math.sin(halfAngle) / (canvasHeight < 700 ? 0.72 : 0.78);
}

// Reference-plane bounds; the fixed perspective camera widens its FOV on resize.
export function universeView(width: number, height: number) {
  const aspect = width / Math.max(height, 1);
  const viewHeight = Math.max(universeCamera.minHeight, universeCamera.minWidth / aspect);
  return { width: viewHeight * aspect, height: viewHeight };
}

/** Projection shared by labels and tests; camera faces -Z without free controls. */
export function projectUniversePoint(point: Coordinates, view: { width: number; height: number }) {
  const depth = universeCamera.distance / (universeCamera.distance - point[2]);
  return { x: 0.5 + point[0] * depth / view.width, y: 0.5 - point[1] * depth / view.height };
}

export function labelPosition(world: { position: Coordinates; labelOffset: Coordinates }): Coordinates {
  return world.position.map((value, index) => value + world.labelOffset[index]) as Coordinates;
}

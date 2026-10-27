import type { UniversePlanet } from "@/lib/universe-config";
import type { UniverseController } from "@/lib/universe-controller";
import PlanetDiorama from "./planet-diorama";
import UniverseBody from "./universe-body";
import { DEFAULT_WORLD_DIMENSIONS, worldDimensions } from "@/lib/world-dimensions";

export default function Planet({ planet, selected, hovered, controller, onSelect }: {
  planet: UniversePlanet; selected: boolean; hovered: boolean; controller: UniverseController;
  onSelect: (planet: UniversePlanet) => void;
}) {
  const catchWorld = (id: string | null) => controller.hover("mesh", id);
  const dimensions = worldDimensions(planet.id);
  const terrainScale = Math.max(dimensions.width / DEFAULT_WORLD_DIMENSIONS.width, dimensions.depth / DEFAULT_WORLD_DIMENSIONS.depth);
  return <UniverseBody controller={controller} planet={planet}>
    <group scale={selected || hovered ? 1.025 : 1}
      onPointerOver={(event) => { event.stopPropagation(); catchWorld(planet.id); }}
      onPointerOut={() => catchWorld(null)}
      onClick={(event) => { event.stopPropagation(); onSelect(planet); }}>
      <PlanetDiorama planet={planet} />
      <mesh visible={false}><sphereGeometry args={[1.4 * terrainScale, 8, 6]} /></mesh>
    </group>
    <mesh position={[0, -0.3, 0]} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[1.48 * terrainScale, 0.009, 4, 48]} />
      <meshBasicMaterial color={planet.color} transparent opacity={selected ? 0.6 : hovered ? 0.3 : 0} depthWrite={false} />
    </mesh>
  </UniverseBody>;
}

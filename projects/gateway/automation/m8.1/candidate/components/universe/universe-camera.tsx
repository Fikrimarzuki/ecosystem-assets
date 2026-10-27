import { useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Box3, Euler, Matrix4, PerspectiveCamera, Quaternion, Sphere, Vector3 } from "three";
import { isWalkingMode } from "@/lib/universe-exploration";
import { ThirdPersonCamera } from "@/lib/third-person";
import { PLAYER } from "@/lib/first-person";
import { inspectionDistance, universeCamera, universeView } from "@/lib/universe-config";
import type { UniverseController } from "@/lib/universe-controller";
import { smoothTransition } from "@/lib/universe-orbit";
import { inspectionCameraBasis } from "@/lib/inspection-camera";
import { createLandmarkCameraPose, landmarkCameraPose } from "@/lib/landmark-camera";
import { projectLandmarks } from "@/lib/universe-landmarks";
import type { LandmarkMeshes } from "./landmark-picker";
import { createJourneyCameraPose, sampleJourneyCamera } from "@/lib/journey-camera";

export default function UniverseCamera({ controller, meshes }: { controller: UniverseController; meshes: LandmarkMeshes }) {
  const { get } = useThree();
  const mode = useRef("");
  const thirdPerson = useRef(new ThirdPersonCamera());
  const tpsInitialized = useRef(false);
  const target = useRef(new Vector3());
  const scratch = useRef({ position: new Vector3(), target: new Vector3(), up: new Vector3(),
    flight: createJourneyCameraPose() });
  const start = useRef({ position: new Vector3(), target: new Vector3(), up: new Vector3(0, 1, 0), fov: 45 });
  const focus = useRef({ phase: "planet", id: "", width: 0, height: 0, start: createLandmarkCameraPose(), end: createLandmarkCameraPose() });
  const walking = useRef({ active: false, saved: createLandmarkCameraPose(), quaternion: new Quaternion(), near: .1, matrix: new Matrix4(), rotation: new Quaternion(), origin: new Vector3(), scale: new Vector3(), euler: new Euler(), localEye: new Vector3(), localAim: new Vector3() });
  useFrame((_, delta) => {
    const { camera, size } = get();
    if (!(camera instanceof PerspectiveCamera)) return;
    const state = controller.getSnapshot();
    const view = universeView(size.width, size.height);
    const overviewFov = 2 * Math.atan(view.height / (2 * universeCamera.distance)) * 180 / Math.PI;
    const nextPosition = scratch.current.position.set(0, 0, universeCamera.distance);
    const nextTarget = scratch.current.target.set(0, 0, 0);
    const nextUp = scratch.current.up.set(0, 1, 0);
    let nextFov = overviewFov;
    if (controller.travelling && controller.journey) {
      const { flight } = scratch.current;
      sampleJourneyCamera(controller.journey, controller.travelSeconds, size.width, size.height, flight);
      nextPosition.fromArray(flight.position);
      nextTarget.fromArray(flight.target);
      nextFov = flight.fov;
    } else if (state.mode === "inspecting") {
      const destination = controller.destination;
      if (destination) {
        nextTarget.fromArray(destination.focusTarget);
        nextFov = 40;
        const aspect = size.width / Math.max(size.height, 1);
        const distance = inspectionDistance(destination.scale, aspect, size.height, destination.id);
        const orientation = state.mode === "inspecting" ? controller.inspection.getOrientation() : { yaw: 0, pitch: 0 };
        const basis = inspectionCameraBasis(destination.rotation, orientation);
        nextPosition.copy(basis.offset).multiplyScalar(distance).add(nextTarget);
        nextUp.copy(basis.up);
      }
    }
    const fp = walking.current;
    if (isWalkingMode(state.explorationMode) && controller.destination) {
      if (!fp.active) {
        fp.saved.position.copy(camera.position); fp.saved.target.copy(target.current); fp.saved.up.copy(camera.up); fp.saved.fov = camera.fov;
        fp.quaternion.copy(camera.quaternion); fp.near = camera.near; fp.active = true; thirdPerson.current.reset(); tpsInitialized.current = false;
      }
      const world = controller.destination, player = controller.player;
      fp.matrix.compose(fp.origin.fromArray(world.position), fp.rotation.setFromEuler(fp.euler.set(...world.rotation)), fp.scale.setScalar(world.scale * 1.025));
      fp.localEye.set(player.position.x, player.position.y + PLAYER.eyeHeight, player.position.z);
      fp.localAim.set(-Math.sin(player.yaw) * Math.cos(player.pitch), Math.sin(player.pitch), -Math.cos(player.yaw) * Math.cos(player.pitch)).add(fp.localEye);
      if (state.explorationMode === "third-person" && player.navigation) {
        // Paused/overlay frames retain the last camera pose, including any unfinished smoothing.
        if (state.firstPersonLocked || !tpsInitialized.current) {
          thirdPerson.current.update(player, player.navigation, delta, state.reduced, true, size.width / Math.max(size.height, 1)); tpsInitialized.current = true;
        }
        const pose = thirdPerson.current;
        fp.localEye.set(pose.position.x, pose.position.y, pose.position.z);
        fp.localAim.set(pose.target.x, pose.target.y, pose.target.z);
      }
      camera.position.copy(fp.localEye).applyMatrix4(fp.matrix);
      target.current.copy(fp.localAim).applyMatrix4(fp.matrix);
      camera.up.set(0, 1, 0).applyQuaternion(fp.rotation);
      camera.fov = state.explorationMode === "third-person" ? thirdPerson.current.fov : 65; camera.near = .01 * world.scale; camera.aspect = size.width / Math.max(size.height, 1);
      camera.lookAt(target.current); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
      if (state.explorationMode === "third-person" && state.firstPersonLocked && !thirdPerson.current.settled) get().invalidate();
      controller.markFirstPersonCameraReady();
      return;
    }
    if (fp.active) {
      camera.position.copy(fp.saved.position); camera.quaternion.copy(fp.quaternion); camera.up.copy(fp.saved.up);
      camera.fov = fp.saved.fov; camera.near = fp.near; target.current.copy(fp.saved.target);
      fp.active = false;
    }
    const focused = focus.current;
    const capture = () => {
      focused.start.position.copy(camera.position);
      focused.start.target.copy(target.current);
      focused.start.up.copy(camera.up);
      focused.start.fov = camera.fov;
    };
    if (state.mode === "inspecting" && state.landmarkFocusId) {
      if (state.focusPhase === "approaching" || state.focusPhase === "focused") {
        const entry = meshes.get(state.landmarkFocusId);
        const landmark = projectLandmarks.find(item => item.id === state.landmarkFocusId);
        if (entry && landmark) {
          if (focused.id !== landmark.id || focused.phase === "planet") capture();
          if (focused.id !== landmark.id || focused.phase === "planet" || focused.width !== size.width || focused.height !== size.height) {
            entry.mesh.updateWorldMatrix(true, false);
            const anchor = entry.mesh.localToWorld(new Vector3(...landmark.anchor));
            const structure = new Box3().setFromObject(entry.mesh);
            const bounds = new Box3();
            for (const item of meshes.values()) if (item.worldId === landmark.worldId) bounds.union(new Box3().setFromObject(item.mesh));
            const points = entry.mesh.geometry.getAttribute("position"), vertices: Vector3[] = [];
            for (let i = 0; i < points.count; i++) vertices.push(new Vector3().fromBufferAttribute(points, i).applyMatrix4(entry.mesh.matrixWorld));
            focused.end = landmarkCameraPose(anchor, structure, bounds.getBoundingSphere(new Sphere()), focused.start, size.width, size.height, vertices);
            focused.id = landmark.id; focused.width = size.width; focused.height = size.height;
          }
          const t = state.focusPhase === "focused" ? 1 : smoothTransition(controller.focusProgress);
          nextPosition.lerpVectors(focused.start.position, focused.end.position, t);
          nextTarget.lerpVectors(focused.start.target, focused.end.target, t);
          nextUp.lerpVectors(focused.start.up, focused.end.up, t).normalize();
          nextFov = focused.start.fov + (focused.end.fov - focused.start.fov) * t;
        }
      } else if (state.focusPhase === "returning") {
        if (focused.phase !== "returning") capture();
        const t = smoothTransition(controller.focusProgress);
        nextPosition.lerpVectors(focused.start.position, nextPosition, t);
        nextTarget.lerpVectors(focused.start.target, nextTarget, t);
        nextUp.lerpVectors(focused.start.up, nextUp, t).normalize();
        nextFov = focused.start.fov + (nextFov - focused.start.fov) * t;
      }
    }
    focused.phase = state.focusPhase;
    if (state.focusPhase === "planet") focused.id = "";
    if (mode.current !== state.mode) {
      start.current.position.copy(camera.position);
      start.current.target.copy(target.current);
      start.current.up.copy(camera.up);
      start.current.fov = camera.fov;
      mode.current = state.mode;
    }
    const moving = state.mode === "returning" && !state.reduced;
    const t = moving ? smoothTransition(controller.progress) : 1;
    camera.position.lerpVectors(start.current.position, nextPosition, t);
    target.current.lerpVectors(start.current.target, nextTarget, t);
    camera.fov = start.current.fov + (nextFov - start.current.fov) * t;
    camera.aspect = size.width / Math.max(size.height, 1);
    camera.up.lerpVectors(start.current.up, nextUp, t).normalize();
    camera.lookAt(target.current);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
  }, -3);
  return null;
}

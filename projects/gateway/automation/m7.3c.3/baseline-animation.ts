import { AnimationMixer, LoopRepeat, type AnimationAction, type SkinnedMesh } from "three";
import type { GLTF } from "three/addons/loaders/GLTFLoader.js";
import { AstronautGroundContact } from "./astronaut-ground-contact";

export const ASTRONAUT_FADE_SECONDS = .18;
const START_SPEED = .001, STOP_SPEED = .0005;
type ClipName = "Idle" | "Walk";

/** Per mounted visual only. Navigation, facing and ground placement stay outside the mixer. */
export class AstronautAnimation {
  readonly mixer: AnimationMixer;
  private readonly actions: Record<ClipName, AnimationAction>;
  private target: ClipName = "Idle";
  private elapsed = ASTRONAUT_FADE_SECONDS;
  private fromWalk = 0;
  private reduced = false;
  private disposed = false;
  private transitions = 0;
  private readonly ground: AstronautGroundContact | null;
  private groundLift = 0;

  constructor(private readonly asset: GLTF) {
    const clips = ["Idle", "Walk"].map(name => asset.animations.find(clip => clip.name === name));
    if (clips.some(clip => !clip || !Number.isFinite(clip.duration) || clip.duration <= 0 || !clip.tracks.length || !clip.validate())) {
      throw new Error("Astronaut Idle/Walk clips are missing or invalid");
    }
    const mesh = asset.scene.getObjectsByProperty("isSkinnedMesh", true)[0] as SkinnedMesh | undefined;
    this.ground = mesh ? new AstronautGroundContact(asset.scene, mesh) : null;
    this.mixer = new AnimationMixer(asset.scene);
    this.actions = { Idle: this.mixer.clipAction(clips[0]!), Walk: this.mixer.clipAction(clips[1]!) };
    for (const action of Object.values(this.actions)) action.setLoop(LoopRepeat, Infinity).setEffectiveTimeScale(1);
    this.actions.Idle.setEffectiveWeight(1).play();
    this.actions.Walk.setEffectiveWeight(0);
    this.mixer.update(0);
  }

  update(delta: number, speed: number, playing: boolean, reduced: boolean) {
    if (this.disposed) return;
    if (reduced) {
      if (!this.reduced) {
        this.actions.Walk.stop().setEffectiveWeight(0); this.actions.Idle.reset().setEffectiveWeight(1).play();
        this.target = "Idle"; this.elapsed = ASTRONAUT_FADE_SECONDS;
        this.groundLift = 0;
        this.mixer.update(0);
      }
      this.reduced = true;
      return; // Same reduced-motion policy as the procedural visual: no ambient gait/breath.
    }
    this.reduced = false;
    if (!playing) return; // Pointer unlock, details and offscreen state preserve even a partial fade.
    const dt = Number.isFinite(delta) ? Math.max(0, Math.min(delta, .1)) : 0;
    const moving = Number.isFinite(speed) && speed > (this.target === "Walk" ? STOP_SPEED : START_SPEED);
    const next = moving ? "Walk" : "Idle";
    if (next !== this.target) {
      // Capture the current blend, so reversing during a fade never jumps to a full-weight pose.
      this.fromWalk = this.actions.Walk.getEffectiveWeight();
      this.target = next; this.elapsed = 0; this.transitions++;
      const incoming = this.actions[next];
      if (!incoming.isRunning()) incoming.reset().play();
    }
    if (this.elapsed < ASTRONAUT_FADE_SECONDS) {
      this.elapsed = Math.min(ASTRONAUT_FADE_SECONDS, this.elapsed + dt);
      const amount = this.elapsed / ASTRONAUT_FADE_SECONDS;
      const walk = this.fromWalk + ((this.target === "Walk" ? 1 : 0) - this.fromWalk) * amount;
      this.actions.Walk.setEffectiveWeight(walk); this.actions.Idle.setEffectiveWeight(1 - walk);
    }
    this.mixer.update(dt);
    const outgoing = this.actions[this.target === "Walk" ? "Idle" : "Walk"];
    if (this.elapsed === ASTRONAUT_FADE_SECONDS && outgoing.isScheduled()) outgoing.stop();
    // Exact posed clearance is continuous with the blend; filtering upward would leave penetration.
    // Exclusive Idle/Walk need no lift and retain their original placement.
    this.groundLift = this.elapsed < ASTRONAUT_FADE_SECONDS ? this.ground?.lift() ?? 0 : 0;
  }

  snapshot() {
    return { clip: this.target, time: this.mixer.time, transitions: this.transitions,
      idleTime: this.actions.Idle.time, walkTime: this.actions.Walk.time,
      idleWeight: this.actions.Idle.getEffectiveWeight(), walkWeight: this.actions.Walk.getEffectiveWeight(), groundLift: this.groundLift };
  }

  get visualLift() { return this.groundLift; }

  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    this.mixer.stopAllAction();
    this.mixer.uncacheRoot(this.asset.scene); // Releases bindings; cached model resources belong to the loader.
  }
}

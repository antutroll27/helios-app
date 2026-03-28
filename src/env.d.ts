/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'globe.gl' {
  const Globe: any
  export default Globe
}

declare module 'three' {
  export class DirectionalLight {
    constructor(color: number, intensity: number)
    position: { set(x: number, y: number, z: number): void }
  }
  export class AmbientLight {
    constructor(color: number, intensity: number)
  }
}

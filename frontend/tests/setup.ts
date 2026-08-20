import '@testing-library/jest-dom'
import { vi } from 'vitest'

if (typeof window !== 'undefined') {
  window.scrollTo = vi.fn()

  class PatchedPointerEvent extends MouseEvent {
    pointerId: number
    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params)
      this.pointerId = params.pointerId ?? 0
    }
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  window.PointerEvent = PatchedPointerEvent as any
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  globalThis.PointerEvent = PatchedPointerEvent as any

  // Mock WebGL contexts for Sigma in JSDOM environment
  if (typeof (window as any).WebGLRenderingContext === 'undefined') {
    class MockWebGLRenderingContext {}
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).WebGLRenderingContext = MockWebGLRenderingContext
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(globalThis as any).WebGLRenderingContext = MockWebGLRenderingContext
  }
  if (typeof (window as any).WebGL2RenderingContext === 'undefined') {
    class MockWebGL2RenderingContext {}
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).WebGL2RenderingContext = MockWebGL2RenderingContext
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(globalThis as any).WebGL2RenderingContext = MockWebGL2RenderingContext
  }
}

if (typeof Element !== 'undefined') {
  Element.prototype.scrollTo = vi.fn()
  Element.prototype.scrollIntoView = vi.fn()
  Element.prototype.setPointerCapture = vi.fn()
  Element.prototype.releasePointerCapture = vi.fn()
}

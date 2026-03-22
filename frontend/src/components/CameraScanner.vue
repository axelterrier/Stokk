<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  scan: [barcode: string]
  close: []
}>()

const videoRef = ref<HTMLVideoElement>()
const errorMsg = ref<string | null>(null)
const detected = ref(false)

// ── Cleanup handles ────────────────────────────────────────────────────────

let stream: MediaStream | null = null
let rafId: number | null = null
let zxingStop: (() => void) | null = null

// ── Lifecycle ──────────────────────────────────────────────────────────────

watch(() => props.show, async (val) => {
  if (val) {
    detected.value = false
    errorMsg.value = null
    await nextTick()
    startScanning()
  } else {
    stopScanning()
  }
})

onUnmounted(stopScanning)

// ── Start ──────────────────────────────────────────────────────────────────

async function startScanning() {
  if (!videoRef.value) return
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width:  { ideal: 1280 },
        height: { ideal: 720 },
        // Continuous autofocus — ignoré silencieusement si non supporté
        // @ts-ignore
        focusMode: 'continuous',
      },
    })
    videoRef.value.srcObject = stream
    await videoRef.value.play()

    if (typeof (window as any).BarcodeDetector !== 'undefined') {
      startNativeDetector()
    } else {
      startZxingFallback()
    }
  } catch (e: unknown) {
    handleCameraError(e)
  }
}

// ── Native BarcodeDetector (Android Chrome, iOS 17.4+) ───────────────────

function startNativeDetector() {
  const BD = (window as any).BarcodeDetector
  const detector = new BD({
    formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39'],
  })

  async function poll() {
    if (!videoRef.value || detected.value) return
    if (videoRef.value.readyState >= 2) {
      try {
        const barcodes = await detector.detect(videoRef.value)
        if (barcodes.length > 0) {
          onDetected(barcodes[0].rawValue)
          return
        }
      } catch {
        // frame pas encore prête, on réessaie
      }
    }
    rafId = requestAnimationFrame(poll)
  }
  rafId = requestAnimationFrame(poll)
}

// ── ZXing fallback ─────────────────────────────────────────────────────────

async function startZxingFallback() {
  if (!videoRef.value) return
  try {
    const { BrowserMultiFormatReader } = await import('@zxing/browser')
    const { DecodeHintType, BarcodeFormat } = await import('@zxing/library')

    const hints = new Map()
    hints.set(DecodeHintType.POSSIBLE_FORMATS, [
      BarcodeFormat.EAN_13,
      BarcodeFormat.EAN_8,
      BarcodeFormat.UPC_A,
      BarcodeFormat.UPC_E,
      BarcodeFormat.CODE_128,
      BarcodeFormat.CODE_39,
    ])

    const reader = new BrowserMultiFormatReader(hints)
    // Passe le stream déjà ouvert directement à ZXing
    const controls = await reader.decodeFromStream(
      stream!,
      videoRef.value,
      (result, _err) => {
        if (result && !detected.value) {
          onDetected(result.getText())
        }
      },
    )
    zxingStop = () => controls.stop()
  } catch (e) {
    errorMsg.value = 'Impossible de démarrer le scanner.'
  }
}

// ── Shared ─────────────────────────────────────────────────────────────────

function onDetected(code: string) {
  detected.value = true
  stopScanning()
  emit('scan', code)
}

function stopScanning() {
  if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null }
  zxingStop?.(); zxingStop = null
  stream?.getTracks().forEach(t => t.stop()); stream = null
  if (videoRef.value) videoRef.value.srcObject = null
}

function handleCameraError(e: unknown) {
  if (e instanceof DOMException) {
    if (e.name === 'NotAllowedError') {
      errorMsg.value = 'Accès à la caméra refusé. Autorisez la caméra dans les paramètres de votre navigateur.'
    } else if (e.name === 'NotFoundError') {
      errorMsg.value = 'Aucune caméra détectée sur cet appareil.'
    } else {
      errorMsg.value = `Erreur caméra : ${e.message}`
    }
  } else {
    errorMsg.value = 'Impossible de démarrer la caméra.'
  }
}

function handleClose() {
  stopScanning()
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="cs-fade">
      <div v-if="show" class="cs-overlay" @click.self="handleClose">
        <div class="cs-modal">

          <!-- Header -->
          <div class="cs-header">
            <div class="cs-header__left">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
              <span class="cs-header__title">Scanner via caméra</span>
            </div>
            <button class="cs-close" @click="handleClose" aria-label="Fermer">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <path d="M18 6 6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- Viewport -->
          <div class="cs-viewport">
            <video ref="videoRef" autoplay muted playsinline class="cs-video" />

            <!-- Viewfinder -->
            <div v-if="!errorMsg" class="cs-finder">
              <div class="cs-frame" :class="{ 'cs-frame--detected': detected }">
                <span class="cs-frame__corner cs-frame__corner--tl" />
                <span class="cs-frame__corner cs-frame__corner--tr" />
                <span class="cs-frame__corner cs-frame__corner--bl" />
                <span class="cs-frame__corner cs-frame__corner--br" />
                <div v-if="!detected" class="cs-frame__line" />
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="cs-footer">
            <div v-if="errorMsg" class="cs-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {{ errorMsg }}
            </div>
            <p v-else-if="detected" class="cs-hint cs-hint--ok">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
              Code détecté !
            </p>
            <p v-else class="cs-hint">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                <path d="M3 5v4M3 5h4M21 5h-4M21 5v4M3 19v-4M3 19h4M21 19h-4M21 19v-4"/>
              </svg>
              Pointez la caméra vers le code-barres du produit
            </p>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ── Transition ───────────────────────────────────────────────── */
.cs-fade-enter-active,
.cs-fade-leave-active { transition: opacity .2s ease; }
.cs-fade-enter-from,
.cs-fade-leave-to    { opacity: 0; }

/* ── Overlay ──────────────────────────────────────────────────── */
.cs-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

/* ── Modal ────────────────────────────────────────────────────── */
.cs-modal {
  width: 100%;
  max-width: 460px;
  max-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 80px rgba(0,0,0,.5);
}

/* Full-screen on small phones */
@media (max-width: 500px) {
  .cs-overlay { padding: 0; }
  .cs-modal   { max-width: 100%; border-radius: 0; height: 100dvh; }
}

/* ── Header ───────────────────────────────────────────────────── */
.cs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .85rem 1rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.cs-header__left {
  display: flex;
  align-items: center;
  gap: .5rem;
  color: var(--color-muted);
}
.cs-header__title {
  font-family: var(--font-display);
  font-size: .875rem;
  font-weight: 700;
  color: var(--color-text);
}
.cs-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: var(--color-surface-2);
  color: var(--color-muted);
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
}
.cs-close:hover { background: var(--color-border); color: var(--color-text); }

/* ── Viewport ─────────────────────────────────────────────────── */
.cs-viewport {
  position: relative;
  flex: 1;
  background: #000;
  min-height: 0;
  aspect-ratio: 4 / 3;
}
@media (max-width: 500px) {
  .cs-viewport { aspect-ratio: unset; }
}

.cs-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* ── Viewfinder ───────────────────────────────────────────────── */
.cs-finder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cs-frame {
  position: relative;
  width: min(260px, 72vw);
  height: min(150px, 42vw);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.45);
  border-radius: 4px;
  transition: box-shadow .3s ease;
}
.cs-frame--detected {
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.2), 0 0 0 3px #22c55e;
}

/* L-shaped corner markers */
.cs-frame__corner {
  position: absolute;
  width: 22px;
  height: 22px;
  border-style: solid;
  border-color: var(--color-accent);
}
.cs-frame__corner--tl { top: -2px;    left: -2px;  border-width: 3px 0 0 3px; border-radius: 4px 0 0 0; }
.cs-frame__corner--tr { top: -2px;    right: -2px; border-width: 3px 3px 0 0; border-radius: 0 4px 0 0; }
.cs-frame__corner--bl { bottom: -2px; left: -2px;  border-width: 0 0 3px 3px; border-radius: 0 0 0 4px; }
.cs-frame__corner--br { bottom: -2px; right: -2px; border-width: 0 3px 3px 0; border-radius: 0 0 4px 0; }

/* Animated scan line */
.cs-frame__line {
  position: absolute;
  left: 4px;
  right: 4px;
  height: 2px;
  background: linear-gradient(to right, transparent, var(--color-accent), transparent);
  box-shadow: 0 0 6px var(--color-accent);
  border-radius: 1px;
  animation: scan-line 2s ease-in-out infinite;
}
@keyframes scan-line {
  0%   { top: 4px; }
  50%  { top: calc(100% - 6px); }
  100% { top: 4px; }
}

/* ── Footer ───────────────────────────────────────────────────── */
.cs-footer {
  padding: .85rem 1.25rem;
  flex-shrink: 0;
  border-top: 1px solid var(--color-border);
  min-height: 52px;
  display: flex;
  align-items: center;
}

.cs-hint {
  display: flex;
  align-items: center;
  gap: .45rem;
  font-size: .8rem;
  color: var(--color-muted);
  margin: 0;
}
.cs-hint--ok {
  color: #22c55e;
  font-weight: 600;
}

.cs-error {
  display: flex;
  align-items: flex-start;
  gap: .5rem;
  font-size: .8rem;
  color: #dc2626;
  line-height: 1.4;
}
.cs-error svg { flex-shrink: 0; margin-top: 1px; }
</style>

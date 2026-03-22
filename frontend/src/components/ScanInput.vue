<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CameraScanner from '@/components/CameraScanner.vue'

const emit = defineEmits<{
  scan: [barcode: string]
}>()

const barcode = ref('')
const inputRef = ref<HTMLInputElement>()
const loading = ref(false)
const showCamera = ref(false)

// Lecture USB HID : le scanner envoie les chiffres + Enter très rapidement.
// On écoute keydown pour détecter Enter sans délai.
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && barcode.value.trim()) {
    submit()
  }
}

function submit() {
  const code = barcode.value.trim()
  if (!code) return
  emit('scan', code)
  barcode.value = ''
}

function onCameraScan(code: string) {
  showCamera.value = false
  emit('scan', code)
}

onMounted(() => inputRef.value?.focus())

defineExpose({ focus: () => inputRef.value?.focus() })
</script>

<template>
  <div class="scan-input">
    <div class="scan-input__wrap">
      <span class="scan-input__icon" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 5v4M3 5h4M21 5h-4M21 5v4M3 19v-4M3 19h4M21 19h-4M21 19v-4"/>
          <line x1="7" y1="8" x2="7" y2="16"/><line x1="10" y1="8" x2="10" y2="16"/>
          <line x1="13" y1="8" x2="13" y2="16"/><line x1="16" y1="8" x2="16" y2="11"/>
          <line x1="16" y1="13" x2="16" y2="16"/>
        </svg>
      </span>
      <input
        ref="inputRef"
        v-model="barcode"
        type="text"
        inputmode="numeric"
        autocomplete="off"
        placeholder="Scanner ou saisir un code-barres..."
        class="scan-input__field"
        :disabled="loading"
        @keydown="onKeydown"
      />
      <button
        class="btn btn--primary scan-input__btn"
        :disabled="!barcode.trim() || loading"
        @click="submit"
      >
        Chercher
      </button>
    </div>

    <button class="scan-input__camera-btn" @click="showCamera = true" :disabled="loading">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
        <circle cx="12" cy="13" r="4"/>
      </svg>
      Scanner via la caméra
    </button>

    <p class="scan-input__hint">Appuyez sur <kbd>Entrée</kbd> ou utilisez votre scanner USB</p>

    <CameraScanner :show="showCamera" @scan="onCameraScan" @close="showCamera = false" />
  </div>
</template>

<style scoped>
.scan-input { display: flex; flex-direction: column; gap: .5rem; }

.scan-input__wrap {
  display: flex;
  align-items: center;
  gap: .5rem;
  background: var(--color-surface-2);
  border: 1.5px solid var(--color-border);
  border-radius: 12px;
  padding: .3rem .3rem .3rem .75rem;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.scan-input__wrap:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(249,115,22,.15);
  animation: pulse-ring 1s ease-out;
}

.scan-input__icon { color: var(--color-muted); flex-shrink: 0; display: flex; }

.scan-input__field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 1rem;
  letter-spacing: .05em;
}
.scan-input__field::placeholder { color: var(--color-muted); letter-spacing: 0; }

.scan-input__hint {
  font-size: .72rem;
  color: var(--color-muted);
  padding-left: .25rem;
}
kbd {
  display: inline-block;
  padding: .05rem .3rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: .7rem;
  font-family: var(--font-body);
}

.scan-input__camera-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  width: 100%;
  padding: .6rem 1rem;
  border: 1.5px dashed var(--color-border);
  border-radius: 10px;
  background: transparent;
  color: var(--color-muted);
  font-family: var(--font-body);
  font-size: .825rem;
  cursor: pointer;
  transition: border-color var(--transition), color var(--transition), background var(--transition);
}
.scan-input__camera-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(249, 115, 22, .05);
}
.scan-input__camera-btn:disabled {
  opacity: .4;
  cursor: not-allowed;
}
</style>

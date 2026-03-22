<script setup lang="ts">
defineProps<{ score?: string }>()

const colors: Record<string, string> = {
  A: '#038141',
  B: '#85BB2F',
  C: '#FECB02',
  D: '#EE8100',
  E: '#E63312',
}
</script>

<template>
  <span
    v-if="score"
    class="nutriscore-badge"
    :style="{ background: colors[score] ?? '#aaa' }"
  >
    {{ score }}
  </span>
</template>

<style scoped>
.nutriscore-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.9rem;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,.3);
}
</style>

<script setup lang="ts">
import { onMounted, ref, useId, watch } from 'vue'
const props = defineProps<{
  open: boolean
  title: string
  pending?: boolean
  error?: string
  submitLabel?: string
  danger?: boolean
}>()
const emit = defineEmits<{ close: []; submit: [] }>()
const dialog = ref<HTMLDialogElement>()
const headingId = useId()
function sync() {
  if (props.open && !dialog.value?.open) dialog.value?.showModal()
  else if (!props.open) dialog.value?.close()
}
watch(() => props.open, sync)
onMounted(sync)
function cancel(event: Event) {
  event.preventDefault()
  if (!props.pending) emit('close')
}
</script>

<template>
  <dialog ref="dialog" class="form-dialog" :aria-labelledby="headingId" @cancel="cancel">
    <form @submit.prevent="$emit('submit')">
      <div class="dialog-heading">
        <h2 :id="headingId">{{ title }}</h2>
        <button
          type="button"
          class="icon-button"
          aria-label="Close dialog"
          :disabled="pending"
          @click="$emit('close')"
        >
          ×
        </button>
      </div>
      <div class="dialog-content"><slot /></div>
      <p v-if="error" class="error-message" role="alert">{{ error }}</p>
      <div class="dialog-actions">
        <button type="button" class="button secondary" :disabled="pending" @click="$emit('close')">
          Cancel</button
        ><button class="button" :class="{ danger }" :disabled="pending">
          {{ pending ? 'Saving…' : submitLabel || 'Save changes' }}
        </button>
      </div>
    </form>
  </dialog>
</template>

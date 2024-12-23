<template>
  <Dialog v-model="show" :options="{
    size: 'xl',
    actions: [
      {
        label: __('Submit'),
        variant: 'solid',
        onClick: () => createClockInOut(),
      },
    ],
  }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-gray-900">
          {{ __('Clock In and Clock Out') }}
        </h3> 
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ __('Datetime') }}</div>
          <DateTimePicker ref="datetime" variant="outline" v-model="_clockInOut.datetime" :disabled="true"/>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { DateTimePicker, call } from 'frappe-ui'
import { dayjsLocal } from 'frappe-ui/src/utils/dayjs';
import { ref, watch } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const clockInOut = defineModel('reloadClockInOut')

const emit = defineEmits(['after'])

const editMode = ref(false)
let _clockInOut = ref({
  datetime: dayjsLocal(new Date()).format('YYYY-MM-DD HH:mm:ss')
})

async function createClockInOut() {
  let d = await call('frappe.client.insert', {
    doc: {
      doctype: 'Clock In and Clock Out',
      datetime: _clockInOut.value.datetime
    },
  })
  if (d.name) {
    clockInOut.value?.reload()
    emit('after', d, true)
  }
  show.value = false
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
  }
)
</script>

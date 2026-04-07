<template>
  <div
    v-if="reply?.message"
    class="flex items-center justify-around gap-2 px-3 pt-2 sm:px-10"
  >
    <div
      class="mb-1 ml-13 flex-1 cursor-pointer rounded border-0 border-l-4 border-green-500 bg-gray-100 p-2 text-base text-gray-600"
      :class="reply.type == 'Incoming' ? 'border-green-500' : 'border-blue-400'"
    >
      <div
        class="mb-1 text-sm font-bold"
        :class="reply.type == 'Incoming' ? 'text-green-500' : 'text-blue-400'"
      >
        {{ reply.from_name || __('You') }}
      </div>
      <div class="max-h-12 overflow-hidden" v-html="reply.message" />
    </div>

    <Button variant="ghost" icon="x" @click="reply = {}" />
  </div>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <div class="flex h-8 items-center gap-2">
      <FileUploader @success="(file) => uploadFile(file)" v-if="hasAcceptedStatus()">
        <template v-slot="{ openFileSelector }">
          <div class="flex items-center space-x-2">
            <Dropdown :options="uploadOptions(openFileSelector)">
              <FeatherIcon
                name="plus"
                class="size-4.5 cursor-pointer text-gray-600"
              />
            </Dropdown>
          </div>
        </template>
      </FileUploader>
      <IconPicker
        v-if="hasAcceptedStatus()"
        v-model="emoji"
        v-slot="{ togglePopover }"
        @update:modelValue="
          () => {
            content += emoji
            $refs.textareaRef.el.focus()
            capture('whatsapp_emoji_added')
          }
        "
      >
        <SmileIcon
          @click="togglePopover"
          class="flex size-4.5 cursor-pointer rounded-sm text-xl leading-none text-gray-500"
        />
      </IconPicker>
    </div>
    <Textarea
      ref="textareaRef"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      v-model="content"
      :placeholder="placeholder"
      :disabled="!(hasAcceptedStatus()) || isTextareaLocked"
      @focus="rows = 6"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
    <Button v-if="hasAcceptedStatus() && requiresGenerate" variant="solid" @click="onGenerateClick" :loading="isGenerating">
      <span>{{ hasGenerated ? __('Regenerate') : __('Generate') }}</span>
    </Button>
    <Button v-if="hasAcceptedStatus()" variant="solid" @click="sendWhatsAppMessage()">
      <span>{{ __('Send') }}</span>
    </Button>
  </div>

  <Dialog
    v-model="showBookingConfirmation"
    :options="{ size: 'lg' }"
  >
    <template #body-title>
      <h3 class="text-xl font-semibold text-gray-900">
        {{ __('Create Booking') }}
      </h3>
    </template>
    <template #body-content>
      <div v-if="bookingData" class="rounded border px-3 py-2" style="background-color: var(--surface-blue-2)">
        <div class="flex items-center justify-between">
          <div class="flex-1 text-sm">
            <span class="font-semibold">📍{{ bookingData.outlet }}</span>
          </div>
        </div>
        <div class="flex flex-col gap-1 text-sm">
          <div class="mt-1"><span class="text-gray-600">📅Date &amp; Time:</span> {{ bookingData.booking_date }} {{ bookingData.timeslot }}</div>
          <div class="mt-1"><span class="text-gray-600">👤Customer:</span> {{ bookingData.customer_name }}</div>
          <div class="mt-1"><span class="text-gray-600">👥Pax:</span> {{ bookingData.pax }}</div>
          <div class="mt-1"><span class="text-gray-600">💆Treatment:</span> {{ bookingData.treatment_type }}</div>
          <div class="mt-1"><span class="text-gray-600">⏳Session:</span> {{ bookingData.session }} mins</div>
          <div class="mt-1"><span class="text-gray-600">🧑‍⚕️Therapist:</span> {{ bookingData.preferred_masseur }}</div>
          <div class="mt-1"><span class="text-gray-600">📱Phone:</span> {{ bookingData.phone }}</div>
          <div class="mt-1"><span class="text-gray-600">🎫3rd Party:</span> {{ bookingData.third_party_voucher && !['no', 'false', '0'].includes(String(bookingData.third_party_voucher).toLowerCase()) ? 'Yes' : 'No' }}</div>
          <div class="mt-1"><span class="text-gray-600">🎟️Package:</span> {{ bookingData.using_package && !['no', 'false', '0'].includes(String(bookingData.using_package).toLowerCase()) ? 'Yes' : 'No' }}</div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="onBookingCancel">
          {{ __('Cancel') }}
        </Button>
        <Button variant="solid" @click="onBookingProceed">
          {{ __('Proceed') }}
        </Button>
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model="showDeleteConfirmation"
    :options="{ size: 'lg' }"
  >
    <template #body-title>
      <h3 class="text-xl font-semibold text-gray-900">
        {{ __('Delete Booking Review Information') }}
      </h3>
    </template>
    <template #body-content>
      <div v-if="deleteBookingData" class="rounded border px-3 py-2" style="background-color: var(--surface-red-2, #fef2f2)">
        <div class="flex items-center justify-between">
          <div class="flex-1 text-sm">
            <span class="font-semibold">📍{{ deleteBookingData.outlet }}</span>
          </div>
        </div>
        <div class="flex flex-col gap-1 text-sm">
          <div class="mt-1"><span class="text-gray-600">📅Date &amp; Time:</span> {{ deleteBookingData.booking_date }} {{ deleteBookingData.timeslot }}</div>
          <div class="mt-1"><span class="text-gray-600">👤Customer:</span> {{ deleteBookingData.customer_name }}</div>
          <div class="mt-1"><span class="text-gray-600">👥Pax:</span> {{ deleteBookingData.pax }}</div>
          <div class="mt-1"><span class="text-gray-600">💆Treatment:</span> {{ deleteBookingData.treatment }}</div>
          <div class="mt-1"><span class="text-gray-600">⏳Session:</span> {{ deleteBookingData.session }} mins</div>
          <div class="mt-1"><span class="text-gray-600">🧑‍⚕️Therapist:</span> {{ deleteBookingData.preferred_therapist }}</div>
        </div>
        <div class="mt-2 text-sm font-medium text-red-600">⚠️ This action cannot be undone.</div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="onDeleteCancel">
          {{ __('Cancel') }}
        </Button>
        <Button variant="solid" theme="red" @click="onDeleteProceed">
          {{ __('Confirm Delete') }}
        </Button>
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model="showEditConfirmation"
    :options="{ size: 'lg' }"
  >
    <template #body-title>
      <h3 class="text-xl font-semibold text-gray-900">
        {{ __('Update Booking') }}
      </h3>
    </template>
    <template #body-content>
      <div v-if="editBookingData" class="rounded border px-3 py-2" style="background-color: var(--surface-orange-2, #fff7ed)">
        <div v-if="editBookingData.pending_update_fields" class="mb-2">
          <div class="text-sm font-semibold text-gray-700 mb-1">🔄 Changes:</div>
          <div v-for="(newVal, field) in editBookingData.pending_update_fields" :key="field" class="text-sm ml-2">
            • {{ formatFieldLabel(field) }}: {{ editBookingData[field] || 'N/A' }} → {{ newVal }}
          </div>
        </div>
        <div class="flex flex-col gap-1 text-sm">
          <div class="font-semibold">📋 Updated Booking Details:</div>
          <div class="mt-1"><span class="text-gray-600">📍Outlet:</span> {{ editBookingData.outlet }}</div>
          <div class="mt-1"><span class="text-gray-600">📅Date:</span> {{ editBookingData.booking_date }}</div>
          <div class="mt-1"><span class="text-gray-600">⏰Time:</span> {{ editBookingData.timeslot }}</div>
          <div class="mt-1"><span class="text-gray-600">💆Treatment:</span> {{ editBookingData.treatment_type }}</div>
          <div class="mt-1"><span class="text-gray-600">⏳Session:</span> {{ editBookingData.session }} mins</div>
          <div class="mt-1"><span class="text-gray-600">🧑‍⚕️Therapist:</span> {{ editBookingData.preferred_masseur }}</div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="onEditCancel">
          {{ __('Cancel') }}
        </Button>
        <Button variant="solid" @click="onEditProceed">
          {{ __('Confirm Update') }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import { capture } from '@/telemetry'
import { isBookingCentreMasterAI } from '@/composables/settings'
import { createResource, Textarea, FileUploader, Dropdown, Dialog } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  doc: Object,
  doctype: String,
})

const doc = defineModel()
const whatsapp = defineModel('whatsapp')
const reply = defineModel('reply')
const rows = ref(1)
const textareaRef = ref(null)
const emoji = ref('')

const content = defineModel('content')
const failedMessages = defineModel('failedMessages')
const placeholder = computed(() => {
  if (isTextareaLocked.value) {
    const remaining = 2 - generateClickCount.value
    return __('Click Generate {0} more time(s) to enable', [remaining])
  }
  return __('Type your message here...')
})
const fileType = ref('')

const generateClickCount = ref(0)
const isGenerating = ref(false)
const hasGenerated = ref(false)
const requiresGenerate = computed(() => isBookingCentreMasterAI.value)
const isTextareaLocked = computed(() => requiresGenerate.value && generateClickCount.value < 2)

const showBookingConfirmation = ref(false)
const bookingData = ref(null)
const bookingSuggestion = ref('')

const showDeleteConfirmation = ref(false)
const deleteBookingData = ref(null)
const deleteSuggestion = ref('')

const showEditConfirmation = ref(false)
const editBookingData = ref(null)
const editSuggestion = ref('')

const aiSuggestedReplies = ref([])
const lastIncomingMessage = ref('')

async function onGenerateClick() {
  generateClickCount.value++
  if (isGenerating.value) return
  isGenerating.value = true
  try {
    const res = await createResource({
      url: 'crm.api.whatsapp.suggest_next_action',
      params: {
        reference_doctype: props.doctype,
        reference_name: doc.value.data.name,
      },
      auto: true,
    }).promise
    lastIncomingMessage.value = res?.last_incoming_message || ''
    if (res?.suggestion) {
      aiSuggestedReplies.value.push(res.suggestion)
    }

    if (res?.type === 'booking_confirmation' && res?.booking_data) {
      bookingData.value = res.booking_data
      bookingSuggestion.value = res.suggestion || ''
      content.value = ''
      showBookingConfirmation.value = true
    } else if (res?.type === 'delete_confirmation' && res?.booking_data) {
      deleteBookingData.value = res.booking_data
      deleteSuggestion.value = res.suggestion || ''
      content.value = ''
      showDeleteConfirmation.value = true
    } else if (res?.type === 'edit_confirmation' && res?.booking_data) {
      editBookingData.value = res.booking_data
      editSuggestion.value = res.suggestion || ''
      content.value = ''
      showEditConfirmation.value = true
    } else if (res?.suggestion) {
      content.value = res.suggestion
      rows.value = 6
    }
  } catch (e) {
    console.error('Generate failed:', e)
  } finally {
    isGenerating.value = false
    hasGenerated.value = true
  }
}

function cancelPendingAction() {
  createResource({
    url: 'crm.api.whatsapp.cancel_pending_action',
    params: {
      reference_doctype: props.doctype,
      reference_name: doc.value.data.name,
    },
    auto: true,
  })
}

function onBookingCancel() {
  showBookingConfirmation.value = false
  bookingData.value = null
  bookingSuggestion.value = ''
  cancelPendingAction()
}

function onBookingProceed() {
  content.value = bookingSuggestion.value
  rows.value = 6
  showBookingConfirmation.value = false
  bookingData.value = null
  bookingSuggestion.value = ''
  sendWhatsAppMessage()
}

function onDeleteCancel() {
  showDeleteConfirmation.value = false
  deleteBookingData.value = null
  deleteSuggestion.value = ''
  cancelPendingAction()
}

function onDeleteProceed() {
  content.value = deleteSuggestion.value
  rows.value = 6
  showDeleteConfirmation.value = false
  deleteBookingData.value = null
  deleteSuggestion.value = ''
  sendWhatsAppMessage()
}

function onEditCancel() {
  showEditConfirmation.value = false
  editBookingData.value = null
  editSuggestion.value = ''
  cancelPendingAction()
}

function onEditProceed() {
  content.value = editSuggestion.value
  rows.value = 6
  showEditConfirmation.value = false
  editBookingData.value = null
  editSuggestion.value = ''
  sendWhatsAppMessage()
}

function formatFieldLabel(field) {
  const labels = {
    booking_date: 'Date',
    timeslot: 'Time',
    outlet: 'Outlet',
    pax: 'Pax',
    treatment_type: 'Treatment',
    session: 'Duration',
    preferred_masseur: 'Therapist',
    customer_name: 'Name',
    phone: 'Phone',
  }
  return labels[field] || field
}

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

function uploadFile(file) {
  whatsapp.value.attach = file.file_url
  whatsapp.value.content_type = fileType.value
  sendWhatsAppMessage()
  capture('whatsapp_upload_file')
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  if (content.value === null || content.value === undefined || content.value === '') {
    return
  }
  sendWhatsAppMessage()
  textareaRef.value.el?.blur()
  content.value = ''
  capture('whatsapp_send_message')
}

async function sendWhatsAppMessage() {
  if (whatsapp.value.content_type == "text" && (content.value === null || content.value === undefined || content.value === '')) {
    return
  }
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
    message: content.value,
    to: doc.value.data.mobile_no,
    attach: whatsapp.value.attach || '',
    reply_to: reply.value?.name || '',
    content_type: whatsapp.value.content_type,
  }
  const tempMsg = {
    name: 'failed_' + Date.now(),
    type: 'Outgoing',
    content_type: args.content_type || 'text',
    message: args.message || args.attach,
    attach: args.attach,
    timestamp: new Date().toISOString(),
    is_failed_message: true,
    is_sending: true,
    _send_args: args,
    message_type: '',
    message_id: '',
    is_reply: 0,
    is_forwarded: 0,
    reply_to_message_id: '',
    use_template: 0,
    template: '',
    template_parameters: '',
    template_header_parameters: '',
    owner: '',
  }

  failedMessages.value = [...(failedMessages.value || []), tempMsg]

  createResource({
    url: 'crm.api.whatsapp.log_booking_centre_ai',
    params: {
      message: lastIncomingMessage.value || '',
      ai_suggested_reply: aiSuggestedReplies.value.join('\n---\n') || '',
      final_reply: args.message,
    },
    auto: true,
  })
  aiSuggestedReplies.value = []
  lastIncomingMessage.value = ''

  content.value = ''
  fileType.value = ''
  whatsapp.value.attach = ''
  whatsapp.value.content_type = 'text'
  reply.value = {}
  generateClickCount.value = 0
  hasGenerated.value = false
  createResource({
    url: 'crm.api.whatsapp.create_whatsapp_message',
    params: args,
    auto: true,
    onSuccess() {
      failedMessages.value = (failedMessages.value || []).filter(m => m.name !== tempMsg.name)
      whatsapp.value.reload()
    },
    onError() {
      tempMsg.is_sending = false
      failedMessages.value = [...(failedMessages.value || [])]
    },
  })
}

function hasAcceptedStatus() {
  return props.doc.data._assignments.includes('Accepted');
}

function hasNewStatus() {
  return props.doc.data._assignments.includes('New');
}

function uploadOptions(openFileSelector) {
  return [
    {
      label: __('Upload Document'),
      icon: 'file',
      onClick: () => {
        fileType.value = 'document'
        openFileSelector()
      },
    },
    {
      label: __('Upload Image'),
      icon: 'image',
      onClick: () => {
        fileType.value = 'image'
        openFileSelector('image/*')
      },
    },
    {
      label: __('Upload Video'),
      icon: 'video',
      onClick: () => {
        fileType.value = 'video'
        openFileSelector('video/*')
      },
    },
  ]
}

watch(reply, (value) => {
  if (value?.message) {
    show()
  }
})

defineExpose({ show })
</script>

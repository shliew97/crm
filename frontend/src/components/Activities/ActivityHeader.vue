<template>
  <div
    class="mx-4 my-3 flex items-center justify-between text-lg font-medium sm:mx-10 sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-gray-800">
      {{ __(title) }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      @click="emailBox.show = true"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('New Email') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Comments'"
      variant="solid"
      @click="emailBox.showComment = true"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('New Comment') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Calls'"
      variant="solid"
      @click="makeCall(doc.data.mobile_no)"
    >
      <template #prefix>
        <PhoneIcon class="h-4 w-4" />
      </template>
      <span>{{ __('Make a Call') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      @click="modalRef.showNote()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('New Note') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Tasks'"
      variant="solid"
      @click="modalRef.showTask()"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('New Task') }}</span>
    </Button>
    <Button
      v-else-if="title == 'Attachments'"
      variant="solid"
      @click="showFilesUploader = true"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>{{ __('Upload Attachment') }}</span>
    </Button>
    <div class="flex gap-2 shrink-0" v-else-if="title == 'WhatsApp'">
      <div v-if="isMasterAgent">
        <Button variant="solid" class="flex items-center gap-1" v-if="crmAssignees.length == 0" @click="showAssignmentModal = true">Assign</Button>
        <MultipleAvatar
          :avatars="crmAssignees"
          @click="showAssignmentModal = true"
        />
      </div>
      <Dropdown v-if="isMasterAgent" :options="tagActions" @click.stop>
        <template v-slot="{ open }">
          <Button variant="solid" class="flex items-center gap-1">
            <span>{{ __('Tag') }}</span>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 w-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button variant="solid" theme="red" @click="alertConversation()">
        <span>{{ __('Alert') }}</span>
      </Button>
      <Button
        :label="__('Send Template')"
        :disabled="!(hasAcceptedStatus())"
        @click="showWhatsappTemplates = true"
      />
      <!-- <Button variant="solid" @click="whatsappBox.show()">
        <template #prefix>
          <FeatherIcon name="plus" class="h-4 w-4" />
        </template>
        <span>{{ __('New Message') }}</span>
      </Button> -->
      <Button v-if="hasNewStatus() || (hasCompletedStatus() && isWithin24Hours(props.doc.data.conversation_start_at))" variant="solid" @click="acceptConversation()">
        <span>{{ __('Accept') }}</span>
      </Button>
      <Button v-if="hasAcceptedStatus() && !hasNewStatus()" variant="solid" @click="completeConversation()">
        <span>{{ __('Complete') }}</span>
      </Button>
    </div>
    <Dropdown v-else :options="defaultActions" @click.stop>
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          <span>{{ __('New') }}</span>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
    <AssignmentModal
      v-if="showAssignmentModal"
      v-model="showAssignmentModal"
      v-model:assignees="crmAssignees"
      :doc="props.doc.data"
      doctype="CRM Lead"
    />
  </div>
</template>
<script setup>
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled, callEnabled, isMasterAgent } from '@/composables/settings'
import { Dropdown, call } from 'frappe-ui'
import { computed, h, ref } from 'vue'
import { createResource } from 'frappe-ui'

const emit = defineEmits(['reload'])
const props = defineProps({
  tabs: Array,
  title: String,
  doc: Object,
  modalRef: Object,
  emailBox: Object,
  whatsappBox: Object,
})

const crmAssignees = ref([])
const showAssignmentModal = ref(false)

createResource({
  url: 'crm.api.whatsapp.get_crm_assignees',
  params: {
    crm_lead: props.doc.data.name,
  },
  auto: true,
  onSuccess: (data) => {
    crmAssignees.value = data
  },
})

const { makeCall } = globalStore()

const tabIndex = defineModel()
const showWhatsappTemplates = defineModel('showWhatsappTemplates')
const showFilesUploader = defineModel('showFilesUploader')

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('New Email'),
      onClick: () => (props.emailBox.show = true),
    },
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('New Comment'),
      onClick: () => (props.emailBox.showComment = true),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(props.doc.data.mobile_no),
      condition: () => callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => props.modalRef.showNote(),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('New WhatsApp Message'),
      onClick: () => (tabIndex.value = getTabIndex('WhatsApp')),
      condition: () => whatsappEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

const tagActions = computed(() => {
  return [
    {
      label: __("Booking - Action Required"),
      onClick: () => tagConversation("Booking - Action Required"),
    },
    {
      label: __("Promotion"),
      onClick: () => tagConversation("Promotion"),
    },
  ]
})

function getTabIndex(name) {
  return props.tabs.findIndex((tab) => tab.name === name)
}

async function acceptConversation() {
  let d = await call('crm.fcrm.doctype.crm_lead.api.acceptConversation', {
    crm_lead_name: props.doc.data.name,
  })
  emit('reload', d)
}

async function alertConversation() {
  let d = await call('crm.fcrm.doctype.crm_lead.api.alertConversation', {
    crm_lead_name: props.doc.data.name,
  })
  emit('reload', d)
}

async function completeConversation() {
  let d = await call('crm.fcrm.doctype.crm_lead.api.completeConversation', {
    crm_lead_name: props.doc.data.name,
  })
  emit('reload', d)
}

async function tagConversation(tagging) {
  let d = await call('crm.fcrm.doctype.crm_lead.api.tagConversation', {
    crm_lead_name: props.doc.data.name,
    tagging: tagging
  })
  emit('reload', d)
}

async function assignConversation(user) {
  let d = await call('crm.fcrm.doctype.crm_lead.api.assignConversation', {
    crm_lead_name: props.doc.data.name,
    user: user
  })
  emit('reload', d)
  frappe.show_alert(__("Guess you're not in the mood to talk"))
}

function isWithin24Hours(datetime) {
    const now = new Date();
    const targetTime = new Date(datetime).getTime();
    
    const diff = Math.abs(now.getTime() - targetTime); // Absolute difference in milliseconds
    return diff <= 24 * 60 * 60 * 1000; // Check if the difference is within 24 hours
}

function hasAcceptedStatus() {
  return props.doc.data._assignments.includes('Accepted');
}

function hasNewStatus() {
  return props.doc.data._assignments.includes('New');
}

function hasCompletedStatus() {
  return props.doc.data._assignments.includes('Completed');
}
</script>

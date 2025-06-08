<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Assign To'),
      size: 'xl',
      actions: [
        {
          label: __('Cancel'),
          variant: 'subtle',
          onClick: () => {
            assignees = [...oldAssignees]
            show = false
          },
        },
        {
          label: __('Update'),
          variant: 'solid',
          onClick: () => updateAssignees(),
        },
      ],
    }"
    @close="
      () => {
        assignees = [...oldAssignees]
      }
    "
  >
    <template #body-content>
      <div class="mt-3 flex flex-col justify-center gap-2">
        <div v-for="option in options" :key="option.value" class="flex items-center">
          <input class="form-check-input mr-2" type="checkbox" @change="checkboxOnChange(option)" :checked="assignees.some(assignee => assignee.name === option.value || (assignee.has_bc_role && option.value == 'Booking Centre'))">
          <UserAvatar :user="option.value" size="sm" />
          <span class="ml-2">{{ option.label }}</span>
        </div>
      </div>
      <ErrorMessage class="mt-2" v-if="error" :message="__(error)" />
    </template>
  </Dialog>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { Tooltip, call } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  doc: {
    type: Object,
    default: null,
  },
  docs: {
    type: Set,
    default: new Set(),
  },
  doctype: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['reload'])

const show = defineModel()
const assignees = defineModel('assignees')
const oldAssignees = ref([])
const options = ref([])

const error = ref('')

const { getUser } = usersStore()

const checkboxOnChange = (option) => {
  const is_checked = event.target.checked;
  if (is_checked) {
    addValue(option.value);
  }
  else {
    removeValue(option.value);
  }
}

const removeValue = (value) => {
  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

const owner = computed(() => {
  if (!props.doc) return ''
  if (props.doctype == 'CRM Lead') return props.doc.lead_owner
  return props.doc.deal_owner
})

const getOptions = createResource({
  url: 'crm.api.whatsapp.get_users_with_crm_assignee_role',
  method: 'POST',
  params: {},
  onSuccess: async (data) => {
    let allData = data.map((option) => {
      return {
        label: option.description,
        value: option.value,
      }
    })
    if (!props.hideMe && props.doctype == 'User') {
      allData.unshift({
        label: '@me',
        value: '@me',
      })
    }
    options.value = allData;
  },
}).fetch();

const addValue = (value) => {
  error.value = ''
  let obj = {
    name: value,
    image: getUser(value).user_image,
    label: getUser(value).full_name,
  }
  if (!assignees.value.find((assignee) => assignee.name === value)) {
    assignees.value.push(obj)
  }
}

async function updateAssignees() {
  // const removedAssignees = oldAssignees.value
  //   .filter(
  //     (assignee) => !assignees.value.find((a) => a.name === assignee.name),
  //   )
  //   .map((assignee) => assignee.name)

  // const addedAssignees = assignees.value
  //   .filter(
  //     (assignee) => !oldAssignees.value.find((a) => a.name === assignee.name),
  //   )
  //   .map((assignee) => assignee.name)

  // if (removedAssignees.length) {
  //   for (let a of removedAssignees) {
  //     await call('crm.fcrm.doctype.crm_lead.api.unassignConversation', {
  //       doctype: props.doctype,
  //       name: props.doc.name,
  //       assign_to: a,
  //     })
  //   }
  // }

  // if (addedAssignees.length) {
  if (props.docs.size) {
    capture('bulk_assign_to', { doctype: props.doctype })
    call('crm.fcrm.doctype.crm_lead.api.assignConversation', {
      doctype: props.doctype,
      name: JSON.stringify(Array.from(props.docs)),
      assign_to: assignees.value,
      bulk_assign: true,
      re_assign: true,
    }).then(() => {
      emit('reload')
    })
  } else {
    capture('assign_to', { doctype: props.doctype })
    call('crm.fcrm.doctype.crm_lead.api.assignConversation', {
      doctype: props.doctype,
      name: props.doc.name,
      assign_to: assignees.value,
    })
  }
  // }
  show.value = false
}

onMounted(() => {
  oldAssignees.value = [...assignees.value]
})
</script>

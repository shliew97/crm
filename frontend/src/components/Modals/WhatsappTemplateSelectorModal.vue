<template>
  <div>
    <Dialog
      v-model="show"
      :options="{ title: __('WhatsApp Templates'), size: '4xl' }"
    >
      <template #body-content>
        <TextInput
          ref="searchInput"
          v-model="search"
          type="text"
          :placeholder="__('Welcome Message')"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
          </template>
        </TextInput>
        <div
          v-if="filteredTemplates.length"
          class="mt-2 grid max-h-[560px] grid-cols-1 gap-2 overflow-y-auto sm:grid-cols-3"
        >
          <div
            v-for="template in filteredTemplates"
            :key="template.name"
            class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-gray-100"
            @click="showConfirmationDialog(template.name)"
          >
            <div class="border-b pb-2 text-base font-semibold">
              {{ template.name }}
            </div>
            <TextEditor
              v-if="template.template"
              :content="template.template"
              :editable="false"
              editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
              class="flex-1 overflow-hidden"
            />
          </div>
        </div>
        <div v-else class="mt-2">
          <div class="flex h-56 flex-col items-center justify-center">
            <div class="text-lg text-gray-500">
              {{ __('No templates found') }}
            </div>
            <Button
              :label="__('Create New')"
              class="mt-4"
              @click="newWhatsappTemplate"
            />
          </div>
        </div>
      </template>
    </Dialog>
    <Dialog :options="{
      title: 'Confirm',
      message: 'Are you sure you want to send this template?',
      size: 'xl',
      icon: {
        name: 'alert-triangle',
        appearance: 'warning',
      },
      actions: [
        {
          label: 'Confirm',
          variant: 'solid',
          onClick: () => sendTemplate(),
        },
      ],
    }"
    v-model="showConfirmation">
    </Dialog>
  </div>
</template>

<script setup>
import { TextEditor, createListResource } from 'frappe-ui'
import { ref, computed, nextTick, watch, onMounted } from 'vue'

const props = defineProps({
  doctype: String,
})

const show = defineModel()
const showConfirmation = defineModel('showConfirmation')
const templateSelected = defineModel('templateSelected')
const searchInput = ref('')

const emit = defineEmits(['send'])

const search = ref('')

const templates = createListResource({
  type: 'list',
  doctype: 'WhatsApp Templates',
  cache: ['whatsappTemplates'],
  fields: ['name', 'template'],
  filters: { },
  orderBy: 'modified desc',
  pageLength: 99999,
})

onMounted(() => {
  if (templates.data == null) {
    templates.fetch()
  }
})

const filteredTemplates = computed(() => {
  return (
    templates.data?.filter((template) => {
      return template.name.toLowerCase().includes(search.value.toLowerCase())
    }) ?? []
  )
})

function showConfirmationDialog(template) {
  templateSelected.value = template
  showConfirmation.value = true
}

function newWhatsappTemplate() {
  show.value = false
  showConfirmation.value = false
  window.open('/app/whatsapp-templates/new')
}

function sendTemplate() {
  showConfirmation.value = false;
  emit('send', templateSelected.value);
}

watch(show, (value) => value && nextTick(() => searchInput.value?.el?.focus()))
</script>

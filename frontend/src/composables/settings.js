import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

export const whatsappEnabled = ref(true)
export const isWhatsappInstalled = ref(true)
export const isMasterAgent = ref(false)
export const isBookingCentre = ref(false)
export const username = ref("")

// createResource({
//   url: 'crm.api.whatsapp.is_whatsapp_enabled',
//   cache: 'Is Whatsapp Enabled',
//   auto: true,
//   onSuccess: (data) => {
//     whatsappEnabled.value = Boolean(data)
//   },
// })
// createResource({
//   url: 'crm.api.whatsapp.is_whatsapp_installed',
//   cache: 'Is Whatsapp Installed',
//   auto: true,
//   onSuccess: (data) => {
//     isWhatsappInstalled.value = Boolean(data)
//   },
// })
createResource({
  url: 'crm.api.whatsapp.is_master_agent_and_booking_centre',
  cache: 'Is Master Agent',
  auto: true,
  onSuccess: (data) => {
    isMasterAgent.value = Boolean(data.is_master_agent)
    isBookingCentre.value = Boolean(data.is_booking_centre)
  },
})
createResource({
  url: 'crm.api.whatsapp.get_username',
  cache: 'Get Username',
  auto: true,
  onSuccess: (data) => {
    username.value = data
  },
})

export const callEnabled = ref(false)
// createResource({
//   url: 'crm.integrations.twilio.api.is_enabled',
//   cache: 'Is Twilio Enabled',
//   auto: true,
//   onSuccess: (data) => {
//     callEnabled.value = Boolean(data)
//   },
// })

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)

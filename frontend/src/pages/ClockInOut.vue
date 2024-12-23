<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Clock In / Out" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Clock In / Out')" @click="createClockInOut">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="clockInOut"
    v-model:loadMore="loadMore"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Clock In and Clock Out"
    :options="{
      hideColumnsButton: true,
      defaultViewName: __('Clock In / Out View'),
    }"
  />
  <div class="flex-1 overflow-y-auto">
    <div
      v-if="clockInOut.data?.data?.length"
      class="grid grid-cols-1 gap-2 px-3 pb-2 sm:grid-cols-4 sm:gap-4 sm:px-5 sm:pb-3"
    >
      <div
        v-for="record in clockInOut.data.data"
        class="group flex h-40 cursor-pointer flex-col justify-between gap-2 rounded-lg border px-5 py-4 shadow-sm hover:bg-gray-50"
      >
        <div class="flex flex-col items-start justify-between">
          <div class="truncate text-lg font-medium mb-4">
            {{ `Clock ${record.record_type} at` }}
          </div>
          <div class="truncate text-lg font-medium">
            {{ `${dateFormat(record.datetime, dateTooltipFormat)}` }}
          </div>
          <!-- <Dropdown
            :options="[
              {
                label: __('Delete'),
                icon: 'trash-2',
                onClick: () => deleteClockInOut(record.name),
              },
            ]"
            @click.stop
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="hover:bg-white"
            />
          </Dropdown> -->
        </div>
        <div class="mt-2 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <UserAvatar :user="record.owner" size="xs" />
            <div class="text-sm text-gray-800">
              {{ getUser(record.owner).full_name }}
            </div>
          </div>
          <Tooltip :text="dateFormat(record.modified, dateTooltipFormat)">
            <div class="text-sm text-gray-700">
              {{ __(timeAgo(record.modified)) }}
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
  </div>
  <ListFooter
    v-if="clockInOut.data?.data?.length"
    class="border-t px-3 py-2 sm:px-5"
    v-model="clockInOut.data.page_length_count"
    :options="{
      rowCount: clockInOut.data.row_count,
      totalCount: clockInOut.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div v-else class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <NoteIcon class="h-10 w-10" />
      <span>{{ __('No Record Found') }}</span>
    </div>
  </div>
  <ClockInOutModal
    v-model="showClockInOutModal"
    v-model:reloadClockInOut="clockInOut"
    :clockInOut="currentClockInOut"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import ClockInOutModal from '@/components/Modals/ClockInOutModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { usersStore } from '@/stores/users'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { Tooltip, ListFooter } from 'frappe-ui'
import { ref, watch } from 'vue'

const { getUser } = usersStore()

const showClockInOutModal = ref(false)
const currentClockInOut = ref(null)

const clockInOut = ref({})
const loadMore = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

watch(
  () => clockInOut.value?.data?.page_length_count,
  (val, old_value) => {
    if (!val || val === old_value) return
    updatedPageCount.value = val
  },
)

function createClockInOut() {
  currentClockInOut.value = {
    title: '',
    content: '',
  }
  showClockInOutModal.value = true
}

// async function deleteClockInOut(name) {
//   await call('frappe.client.delete', {
//     doctype: 'Clock In and Clock Out',
//     name,
//   })
//   clockInOut.value.reload()
// }
</script>

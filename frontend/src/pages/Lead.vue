<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <Button class="ml-2" variant="solid" @click="switchToViewBookings">
        {{ __('View Booking') }}
      </Button>
    </template>
    <template #right-header>
      <CustomActions v-if="customActions" :actions="customActions" />
      <!-- <component :is="lead.data._assignedTo?.length == 1 ? 'Button' : 'div'">
        <MultipleAvatar
          :avatars="lead.data._assignedTo"
          @click="showAssignmentModal = true"
        />
      </component> -->
      <!-- <Dropdown :options="statusOptions('lead', updateField, customStatuses)">
        <template #default="{ open }">
          <Button
            :label="lead.data.status"
            :class="getLeadStatus(lead.data.status).colorClass"
          >
            <template #prefix>
              <IndicatorIcon />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown> -->
      <!-- <Button
        :label="__('Convert to Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      /> -->
    </template>
  </LayoutHeader>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <!-- Bookings Panel - Left -->
    <Resizer class="flex flex-col justify-start border-r" side="left">
      <!-- Create Booking View -->
      <template v-if="leftPanelMode === 'create'">
        <div class="flex items-center justify-between border-b px-4 py-3">
          <div class="text-lg font-semibold">{{ __('Create Booking') }}</div>
        </div>
        <div class="flex-1 overflow-y-auto px-4 py-3">
          <div class="flex flex-col gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('👤Customer Name') }}</label>
              <TextInput v-model="bookingForm.customer_name" :placeholder="__('Customer Name')" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📍Outlet') }}</label>
              <FormControl
                type="select"
                v-model="bookingForm.outlet"
                :options="outletOptions"
                :placeholder="__('Select Outlet')"
              />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📱Booking Phone') }}</label>
              <TextInput v-model="bookingForm.phone" :placeholder="__('Phone Number')" />
            </div>
            <div>
              <div class="mb-1 flex items-center gap-1">
                <label class="block text-xs text-gray-600">{{ __('📱Member Account') }}</label>
                <button
                  type="button"
                  class="flex items-center justify-center rounded p-0.5 text-gray-600 hover:bg-gray-100 hover:text-gray-800"
                  :title="__('Search Member Account')"
                  @click="searchMemberAccount"
                  :disabled="membershipSearch.loading"
                >
                  <LoadingIndicator v-if="membershipSearch.loading" class="h-6 w-6" />
                  <FeatherIcon v-else name="search" class="h-6 w-6" />
                </button>
                <button
                  type="button"
                  class="flex items-center justify-center rounded p-0.5 text-gray-600 hover:bg-gray-100 hover:text-gray-800"
                  :title="__('Copy Member Account')"
                  @click="bookingForm.member_account = bookingForm.phone"
                >
                  <FeatherIcon name="copy" class="h-6 w-6" />
                </button>
              </div>
              <TextInput v-model="bookingForm.member_account" :placeholder="__('Enter mobile number')" />
              <!-- Membership Info -->
              <div v-if="membershipInfo" class="mt-2 rounded border border-gray-200 bg-gray-50 p-2 text-xs text-gray-700">
                <div class="grid grid-cols-2 gap-x-3 gap-y-1">
                  <span class="text-gray-500">{{ __('Tier') }}</span>
                  <span>{{ membershipInfo.membership_tier || '-' }}</span>
                  <span class="text-gray-500">{{ __('Validity') }}</span>
                  <span>{{ membershipInfo.membership_validity || '-' }}</span>
                  <span class="text-gray-500">{{ __('Deposit') }}</span>
                  <span>{{ membershipInfo.total_deposit || '-' }}</span>
                  <span class="mt-1">{{ __('This Outlet') }}</span>
                  <span></span>
                  <span class="text-gray-500">{{ __('Package') }}</span>
                  <span>{{ membershipInfo.total_package_current_outlet || '-' }}</span>
                  <span class="text-gray-500">{{ __('Topup') }}</span>
                  <span>{{ membershipInfo.total_topup_current_outlet || '-' }}</span>
                  <span class="text-gray-500">{{ __('Credit') }}</span>
                  <span>{{ membershipInfo.total_credit_current_outlet || '-' }}</span>
                  <span class="mt-1">{{ __('Other Outlet') }}</span>
                  <span></span>
                  <span class="text-gray-500">{{ __('Package') }}</span>
                  <span>{{ membershipInfo.total_package_other_outlet || '-' }}</span>
                  <span class="text-gray-500">{{ __('Topup') }}</span>
                  <span>{{ membershipInfo.total_topup_other_outlet || '-' }}</span>
                  <span class="text-gray-500">{{ __('Credit') }}</span>
                  <span>{{ membershipInfo.total_credit_other_outlet || '-' }}</span>
                </div>
              </div>
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📅Date') }}</label>
              <DatePicker v-model="bookingForm.booking_date" :placeholder="__('Select Date')" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('⏰Preferred Time') }}</label>
              <FormControl type="time" v-model="bookingForm.timeslot" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('👥Number of Pax') }}</label>
              <FormControl type="select" v-model="bookingForm.pax" :options="paxOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('💆Treatment') }}</label>
              <FormControl type="select" v-model="bookingForm.treatment_type" :options="treatmentOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('⏳Session (mins)') }}</label>
              <FormControl type="select" v-model="bookingForm.session" :options="sessionOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🧑‍⚕️Preferred Therapist') }}</label>
              <FormControl type="select" v-model="bookingForm.preferred_masseur" :options="therapistOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🎫3rd Party Voucher') }}</label>
              <FormControl type="select" v-model="bookingForm.third_party_voucher" :options="yesNoOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🎟️Package') }}</label>
              <FormControl type="select" v-model="bookingForm.using_package" :options="yesNoOptions" />
            </div>
          </div>
          <div class="mt-3">
            <Button variant="solid" class="w-full" :loading="bookingSubmitting" @click="submitBooking">
              {{ __('Submit Booking') }}
            </Button>
          </div>
        </div>
      </template>
      <!-- Edit Booking View -->
      <template v-else-if="leftPanelMode === 'edit'">
        <div class="flex items-center justify-between border-b px-4 py-3">
          <div class="text-lg font-semibold">{{ __('Edit Booking') }}</div>
          <Button variant="ghost" @click="leftPanelMode = 'view'">
            <FeatherIcon name="x" class="size-4" />
          </Button>
        </div>
        <div class="flex-1 overflow-y-auto px-4 py-3">
          <div class="flex flex-col gap-3">
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('👤Customer Name') }}</label>
              <TextInput :modelValue="editBookingForm.customer_name" disabled class="opacity-60" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📱Booking Phone') }}</label>
              <TextInput :modelValue="editBookingForm.booking_mobile" disabled class="opacity-60" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📍Outlet') }}</label>
              <TextInput :modelValue="editBookingForm.outlet" disabled class="opacity-60" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('📅Date') }}</label>
              <DatePicker v-model="editBookingForm.booking_date" :placeholder="__('Select Date')" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('⏰Preferred Time') }}</label>
              <FormControl type="time" v-model="editBookingForm.timeslot" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('💆Treatment') }}</label>
              <FormControl type="select" v-model="editBookingForm.treatment" :options="treatmentOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('⏳Session (mins)') }}</label>
              <FormControl type="select" v-model="editBookingForm.session" :options="sessionOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🧑‍⚕️Preferred Therapist') }}</label>
              <FormControl type="select" v-model="editBookingForm.preferred_therapist" :options="therapistOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🎫3rd Party Voucher') }}</label>
              <FormControl type="select" v-model="editBookingForm.third_party_voucher_select" :options="yesNoOptions" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-gray-600">{{ __('🎟️Package') }}</label>
              <FormControl type="select" v-model="editBookingForm.package_select" :options="yesNoOptions" />
            </div>
          </div>
          <div class="mt-3">
            <Button variant="solid" class="w-full" :loading="editBookingSubmitting" @click="submitEditBooking">
              {{ __('Save Changes') }}
            </Button>
          </div>
        </div>
      </template>
      <!-- View Bookings View -->
      <template v-else>
        <div class="flex items-center justify-between border-b px-4 py-3">
          <div class="text-lg font-semibold">{{ __('Bookings') }}</div>
          <div class="flex gap-1">
            <Button variant="ghost" @click="fetchBookingsForPanel">
              <FeatherIcon name="refresh-cw" class="size-4" />
            </Button>
          </div>
        </div>
        <div class="flex-1 overflow-y-auto px-4 py-3">
          <div v-if="fetchingBookings" class="flex items-center justify-center py-4">
            <LoadingIndicator class="size-6" />
          </div>
          <div v-else-if="fetchedBookings.length === 0" class="py-4 text-center text-sm text-gray-500">
            {{ __('No bookings found') }}
          </div>
          <div v-else class="flex flex-col gap-2">
            <div
              v-for="(booking, index) in fetchedBookings"
              :key="index"
              class="rounded border px-3 py-2"
              :style="{ backgroundColor: booking.self_booked ? 'var(--surface-blue-2)' : 'var(--surface-orange-1)' }"
            >
              <div class="flex items-center justify-between">
                <div class="flex-1 text-sm">
                  <span class="font-semibold">📍{{ booking.outlet }}</span>
                </div>
                <div class="flex shrink-0 gap-1">
                  <Button variant="ghost" size="sm" @click="openEditBooking(booking)">
                    <FeatherIcon name="edit-2" class="size-3" />
                  </Button>
                  <Button variant="ghost" size="sm" @click="confirmDeleteBooking(booking)">
                    <FeatherIcon name="trash-2" class="size-3 text-red-600" />
                  </Button>
                </div>
              </div>
              <div class="flex flex-col gap-1 text-sm">
                <div class="mt-1"><span class="text-gray-600">{{ __('📅Date & Time') }}:</span> {{ booking.booking_date }} {{ booking.timeslot }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('👤Customer') }}:</span> {{ booking.customer_name }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('👥Pax') }}:</span> {{ booking.pax }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('💆Treatment') }}:</span> {{ booking.treatment }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('⏳Session') }}:</span> {{ booking.session }} {{ __('mins') }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('🧑‍⚕️Therapist') }}:</span> {{ booking.preferred_therapist }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('📱Phone') }}:</span> {{ booking.booking_mobile }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('📱Member') }}:</span> {{ booking.member_mobile }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('🎫3rd Party') }}:</span> {{ booking.third_party_voucher ? __('Yes') : __('No') }}</div>
                <div class="mt-1"><span class="text-gray-600">{{ __('🎟️Package') }}:</span> {{ booking.package ? __('Yes') : __('No') }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Resizer>
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      <Activities
        ref="activities"
        doctype="CRM Lead"
        :tabs="tabs"
        v-model:reload="reload"
        v-model:tabIndex="tabIndex"
        v-model="lead"
        @createBooking="onCreateBooking"
      />
    </Tabs>
    <Resizer class="flex flex-col justify-start border-l" side="right">
      <Switch v-if="isBookingCentre" size="sm" label="Off Work Mode" description="" :disabled="false" v-model="offWorkMode"/>
      <TextInput v-model="searchText" @keyup.enter="triggerFetchNewLeads()" class="w-full m-1" :placeholder="'Mobile No. e.g. 0112223333'"></TextInput>
      <div class="overflow-y-auto">
        <a :href="`/crm/leads/${lead.name}#whatsapp`" class="flex h-30 cursor-pointer border p-4 shadow-sm flex-col" v-for="(lead, i) in newLeads" :key="lead.name" :style="{ background: getBackground(lead) }">
          <div class="flex justify-between">
            <div class="truncate text-base">{{ lead.lead_name }}</div>
            <div class="flex">
              <IndicatorIcon></IndicatorIcon>
              <div class="truncate text-base">{{ getStatus(lead) }}</div>
            </div>
          </div>
          <div v-if="username == 'administrator'" class="flex mt-2">
            <PhoneIcon></PhoneIcon>
            <div class="ml-2 truncate text-base">{{ lead.mobile_no }}</div>
          </div>
          <div class="mt-2 truncate text-2xs" v-if="isMasterAgent">Last Reply By : {{ lead.last_reply_by }}</div>
          <div class="mt-2 truncate text-ink-white rounded bg-red-500 pl-2" v-if="lead.alert && (username === lead.alert_by || isMasterAgent)">Alert! : by {{ lead.alert_by }}</div>
          <div class="mt-2 truncate text-2xs">Starts at: {{ lead.conversation_start_at ? dateFormat(lead.conversation_start_at, dateTooltipFormat) : "-" }}</div>
          <div class="mt-2 truncate text-2xs">Last Reply: {{ lead.last_reply_at ? dateFormat(lead.last_reply_at, dateTooltipFormat) : "-" }}</div>
          <div class="flex items-end mt-1 flex-col">
            <div v-for="(tagging, i) in lead.taggings" class="truncate text-base mt-1">
              {{ tagging }}
            </div>
          </div>
        </a>
      </div>
    </Resizer>
    <!-- <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium"
        @click="copyToClipboard(lead.data.name)"
      >
        {{ __(lead.data.name) }}
      </div>
      <FileUploader
        @success="(file) => updateField('image', file.file_url)"
        :validateFile="validateFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative size-12">
              <Avatar
                size="3xl"
                class="size-12"
                :label="lead.data.first_name || __('Untitled')"
                :image="lead.data.image"
              />
              <component
                :is="lead.data.image ? Dropdown : 'div'"
                v-bind="
                  lead.data.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: lead.data.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => updateField('image', ''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0.5 left-0 right-0.5 flex h-9 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="size-4 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="lead.data.lead_name || __('Set first name')">
                <div class="truncate text-2xl font-medium">
                  {{ lead.data.lead_name || __('Untitled') }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Tooltip v-if="callEnabled" :text="__('Make a call')">
                  <Button
                    class="h-7 w-7"
                    @click="
                      () =>
                        lead.data.mobile_no
                          ? makeCall(lead.data.mobile_no)
                          : errorMessage(__('No phone number set'))
                    "
                  >
                    <PhoneIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Send an email')">
                  <Button class="h-7 w-7">
                    <Email2Icon
                      class="h-4 w-4"
                      @click="
                        lead.data.email
                          ? openEmailBox()
                          : errorMessage(__('No email set'))
                      "
                    />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Go to website')">
                  <Button class="h-7 w-7">
                    <LinkIcon
                      class="h-4 w-4"
                      @click="
                        lead.data.website
                          ? openWebsite(lead.data.website)
                          : errorMessage(__('No website set'))
                      "
                    />
                  </Button>
                </Tooltip>
                <Tooltip :text="__('Attach a file')">
                  <Button class="h-7 w-7" @click="showFilesUploader = true">
                    <AttachmentIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </template>
      </FileUploader>
      <SLASection
        v-if="lead.data.sla_status"
        v-model="lead.data"
        @updateField="updateField"
      />
      <div
        v-if="fieldsLayout.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in fieldsLayout.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== fieldsLayout.data.length - 1 }"
          >
            <Section :is-opened="section.opened" :label="section.label">
              <SectionFields
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="lead.data"
                @update="updateField"
              />
              <template v-if="i == 0 && isManager()" #actions>
                <Button
                  variant="ghost"
                  class="w-7 mr-2"
                  @click="showSidePanelModal = true"
                >
                  <EditIcon class="h-4 w-4" />
                </Button>
              </template>
            </Section>
          </div>
        </div>
      </div>
    </Resizer> -->
  </div>
  <AssignmentModal
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="lead.data._assignedTo"
    :doc="lead.data"
    doctype="CRM Lead"
  />
  <Dialog
    v-model="showConvertToDealModal"
    :options="{
      title: __('Convert to Deal'),
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-gray-600">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Organization') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingOrganizationChecked" />
        </div>
        <Link
          v-if="existingOrganizationChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingOrganization"
          doctype="CRM Organization"
          @change="(data) => (existingOrganization = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New organization will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-gray-600">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingContactChecked" />
        </div>
        <Link
          v-if="existingContactChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{ __("New contact will be created based on the person's details") }}
        </div>
      </div>
    </template>
  </Dialog>
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    @reload="() => fieldsLayout.reload()"
  />
  <FilesUploader
    v-if="lead.data?.name"
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="lead.data.name"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  openWebsite,
  createToast,
  setupAssignees,
  setupCustomizations,
  errorMessage,
  copyToClipboard,
  dateFormat,
  dateTooltipFormat,
} from '@/utils'
import { getView } from '@/utils/view'
import { globalStore } from '@/stores/global'
import { contactsStore } from '@/stores/contacts'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { whatsappEnabled, isMasterAgent, isBookingCentre, username } from '@/composables/settings'
import { capture } from '@/telemetry'
import {
  createResource,
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  TextInput,
  Tabs,
  Switch,
  Breadcrumbs,
  DatePicker,
  FormControl,
  Autocomplete,
  call,
  usePageMeta,
} from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { $dialog, $socket, makeCall } = globalStore()
const { getContactByName, contacts } = contactsStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { getUser } = usersStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const customActions = ref([])
const customStatuses = ref([])
const newLeads = ref([])
const searchText = ref("")
const offWorkMode = ref(false)
const timeout = ref(undefined)
const lastUpdateTimestamp = ref(undefined)

const lead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  onSuccess: async (data) => {
    let obj = {
      doc: data,
      $dialog,
      $socket,
      router,
      updateField,
      createToast,
      deleteDoc: deleteLead,
      resource: {
        lead,
        fieldsLayout,
      },
      call,
    }
    setupAssignees(data)
    let customization = await setupCustomizations(data, obj)
    customActions.value = customization.actions || []
    customStatuses.value = customization.statuses || []
  },
})

function triggerFetchNewLeads(redirect=false) {
  createResource({
    url: 'crm.fcrm.doctype.crm_lead.api.get_new_leads',
    params: {
      search_text: searchText.value || "",
      off_work_mode: offWorkMode.value,
    },
    onSuccess: async (data) => {
      if (redirect) {
        if (data.length > 0) {
          window.location.href = `/crm/leads/${data[0].name}#whatsapp`;
        }
        else {
          newLeads.value = data;
        }
      }
      else {
        newLeads.value = data;
      }
      lastUpdateTimestamp.value = Date.now();
    },
  }).fetch()
}

onMounted(() => {
  const saved = localStorage.getItem("off_work_mode")
  offWorkMode.value = saved === "true" // convert string to boolean
  $socket.on("new_leads", (data) => {
    const now = Date.now();
    if (lead.data && lead.data.name == data.accepted_lead && data.user != getUser().name) {
      triggerFetchNewLeads(true);
    }
    else {
      if (lastUpdateTimestamp.value && now - lastUpdateTimestamp.value < 15000) {
        return;
      }
      triggerFetchNewLeads();
    }
    lead.fetch()
  })
  triggerFetchNewLeads();
  if (lead.data) {
    fetchBookingsForPanel()
    return
  }
  lead.fetch()
})

const reload = ref(false)
const showAssignmentModal = ref(false)
const showSidePanelModal = ref(false)
const showFilesUploader = ref(false)

// Booking state
const leftPanelMode = ref('create')
const bookingSubmitting = ref(false)
const bookingForm = ref({
  customer_name: '',
  phone: '',
  member_account: '',
  outlet: '',
  booking_date: '',
  timeslot: '',
  pax: '1',
  treatment_type: 'Foot',
  session: '60',
  preferred_masseur: 'Any',
  third_party_voucher: 'No',
  using_package: 'No',
})

// Member Account search
const membershipInfo = ref(null)
const membershipSearch = createResource({
  url: 'crm.api.whatsapp.get_customer_membership_and_balance',
  onSuccess: (data) => {
    membershipInfo.value = data || null
  },
  onError: () => {
    membershipInfo.value = null
    createToast({
      title: __('Error'),
      text: __('Failed to fetch membership info'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
  },
})

function searchMemberAccount() {
  if (!bookingForm.value.member_account) {
    createToast({
      title: __('Missing Info'),
      text: __('Please enter a Member Account (mobile number)'),
      icon: 'alert-triangle',
      iconClasses: 'text-yellow-600',
    })
    return
  }
  if (!bookingForm.value.outlet) {
    createToast({
      title: __('Missing Info'),
      text: __('Please select an Outlet first'),
      icon: 'alert-triangle',
      iconClasses: 'text-yellow-600',
    })
    return
  }
  membershipSearch.submit({
    outlet: bookingForm.value.outlet,
    member_mobile: bookingForm.value.member_account,
  })
}

const paxOptions = ['1', '2', '3', '4', '5']
const treatmentOptions = ['Foot', 'Thai', 'Oil', 'Deep', 'Others']
const sessionOptions = ['60', '90', '120']
const therapistOptions = ['Male', 'Female', 'Any']
const yesNoOptions = ['Yes', 'No']

const outletList = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Outlet',
    fields: ['name', 'branch_code', 'shop_full_name'],
    limit_page_length: 0,
  },
  auto: true,
})

const outletOptions = computed(() => {
  if (!outletList.data) return []
  return outletList.data.map((o) => ({ label: o.shop_full_name, value: o.branch_code }))
})

watch(() => lead.data, (data) => {
  if (data) {
    bookingForm.value.customer_name = data.lead_name || ''
    bookingForm.value.phone = data.mobile_no || ''
    fetchBookingsForPanel()
  }
}, { immediate: true })

function switchToViewBookings() {
  leftPanelMode.value = 'view'
  fetchBookingsForPanel()
}

function extractBookingFromMessage(text) {
  if (!text) return {}
  const msg = text
  const msgLower = msg.toLowerCase()
  const data = {}

  // --- Phone: Malaysian format 01x-xxxxxxx or 01xxxxxxxxx ---
  const phoneMatch = msg.match(/\b(01\d[\s\-]?\d{3,4}[\s\-]?\d{4})\b/)
  if (phoneMatch) {
    data.phone = phoneMatch[1].replace(/[\s\-]/g, '')
  }

  // --- Date: DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, DD-MM-YY, YYYY-MM-DD ---
  const dateMatch = msg.match(/\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})\b/)
  if (dateMatch) {
    let [, p1, p2, p3] = dateMatch
    let year, month, day
    if (p1.length === 4) {
      // YYYY-MM-DD
      year = parseInt(p1); month = parseInt(p2); day = parseInt(p3)
    } else {
      // DD/MM/YYYY or DD/MM/YY
      day = parseInt(p1); month = parseInt(p2)
      year = parseInt(p3)
      if (year < 100) year += 2000
    }
    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      data.booking_date = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`
    }
  }

  // --- Relative dates ---
  if (!data.booking_date) {
    const today = new Date()
    if (/\b(today|tdy)\b/i.test(msg)) {
      data.booking_date = today.toISOString().slice(0,10)
    } else if (/\b(tomorrow|tmr|tmrw)\b/i.test(msg)) {
      today.setDate(today.getDate() + 1)
      data.booking_date = today.toISOString().slice(0,10)
    }
  }

  // --- Time: 2pm, 2:30pm, 14:00, 2.30pm ---
  const time12Match = msg.match(/\b(\d{1,2})[\:\.](\d{2})\s*(am|pm)\b/i)
    || msg.match(/\b(\d{1,2})\s*(am|pm)\b/i)
  if (time12Match) {
    let hour = parseInt(time12Match[1])
    const min = time12Match[2] && /^\d+$/.test(time12Match[2]) ? time12Match[2] : '00'
    const ampm = (time12Match[3] || time12Match[2]).toLowerCase()
    if (ampm === 'pm' && hour < 12) hour += 12
    if (ampm === 'am' && hour === 12) hour = 0
    data.timeslot = `${String(hour).padStart(2,'0')}:${min.padStart(2,'0')}`
  }
  if (!data.timeslot) {
    const time24Match = msg.match(/\b([01]?\d|2[0-3]):([0-5]\d)\b/)
    if (time24Match) {
      data.timeslot = `${String(parseInt(time24Match[1])).padStart(2,'0')}:${time24Match[2]}`
    }
  }

  // --- Pax ---
  const paxMatch = msgLower.match(/\b(\d+)\s*(?:pax|person|people|guest|guests)\b/)
    || msgLower.match(/\bpax\s*[:\-]?\s*(\d+)\b/)
  if (paxMatch) {
    const p = parseInt(paxMatch[1])
    if (p >= 1 && p <= 5) data.pax = String(p)
  }

  // --- Treatment type ---
  const treatments = { 'foot': 'Foot', 'thai': 'Thai', 'oil': 'Oil', 'deep': 'Deep' }
  for (const [kw, val] of Object.entries(treatments)) {
    if (msgLower.includes(kw)) { data.treatment_type = val; break }
  }

  // --- Session duration ---
  const sessionMatch = msgLower.match(/\b(60|90|120)\s*(?:min|mins|minutes?)?\b/)
  if (sessionMatch) {
    data.session = sessionMatch[1]
  } else {
    const hourMatch = msgLower.match(/\b(1|1\.5|2)\s*(?:hour|hours|hr|hrs)\b/)
    if (hourMatch) {
      const h = parseFloat(hourMatch[1])
      data.session = String(h * 60)
    }
  }

  // --- Preferred masseur ---
  if (/\b(female|lady)\b/i.test(msg)) data.preferred_masseur = 'Female'
  else if (/\b(male)\b/i.test(msg)) data.preferred_masseur = 'Male'

  // --- Outlet matching: match against outletList.data ---
  if (outletList.data) {
    let bestMatch = null
    let bestLen = 0
    for (const o of outletList.data) {
      // Try matching shop_full_name or parts of it (e.g. "Puchong", "Kota Damansara", "KLCC")
      const name = o.shop_full_name || ''
      // Extract the location part after "@" or last word
      const atPart = name.includes('@') ? name.split('@')[1].trim() : name
      // Check if the location keyword appears in the message
      const keywords = [atPart, ...atPart.split(/\s+/)]
      for (const kw of keywords) {
        if (kw.length >= 3 && msgLower.includes(kw.toLowerCase()) && kw.length > bestLen) {
          bestMatch = o.branch_code
          bestLen = kw.length
        }
      }
    }
    if (bestMatch) data.outlet = bestMatch
  }

  return data
}

function onCreateBooking(message) {
  // Set defaults from lead data
  bookingForm.value.customer_name = lead.data?.lead_name || message?.from_name || ''
  bookingForm.value.phone = lead.data?.mobile_no || ''
  leftPanelMode.value = 'create'

  // Extract booking details from message using regex
  const messageText = message?.message || ''
  if (!messageText) return

  const d = extractBookingFromMessage(messageText)
  if (d.phone) bookingForm.value.phone = d.phone
  if (d.outlet) bookingForm.value.outlet = d.outlet
  if (d.booking_date) bookingForm.value.booking_date = d.booking_date
  if (d.timeslot) bookingForm.value.timeslot = d.timeslot
  if (d.pax) bookingForm.value.pax = d.pax
  if (d.treatment_type) bookingForm.value.treatment_type = d.treatment_type
  if (d.session) bookingForm.value.session = d.session
  if (d.preferred_masseur) bookingForm.value.preferred_masseur = d.preferred_masseur
}

async function submitBooking() {
  bookingSubmitting.value = true
  try {
    const form = bookingForm.value
    const response = await call('crm.api.whatsapp.create_booking', {
      crm_lead: props.leadId,
      booking_details: {
        customer_name: form.customer_name,
        booking_mobile: lead.data?.mobile_no || form.phone,
        member_mobile: lead.data?.mobile_no || form.phone,
        outlet: form.outlet,
        booking_date: form.booking_date,
        timeslot: form.timeslot ? form.timeslot + ':00' : '',
        pax: parseInt(form.pax),
        treatment: form.treatment_type,
        session: parseInt(form.session),
        preferred_therapist: form.preferred_masseur,
        third_party_voucher: form.third_party_voucher === 'Yes',
        package: form.using_package === 'Yes',
      },
    })
    if (response?.success) {
      createToast({
        title: __('Success'),
        text: __(response.message || 'Booking created successfully'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      if (response?.confirmation_message) {
        activities.value.content = response.confirmation_message
      }
      fetchBookingsForPanel()
    } else {
      createToast({
        title: __('Failed'),
        text: __(response?.message || 'Booking creation failed'),
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    }
  } catch (err) {
    createToast({
      title: __('Failed'),
      text: __(err.messages?.[0] || err.message),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
  } finally {
    bookingSubmitting.value = false
  }
}

function updateLead(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Lead',
      name: props.leadId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      lead.reload()
      reload.value = true
      createToast({
        title: __('Lead updated'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: __('Error updating lead'),
        text: __(err.messages?.[0]),
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = lead.data.fields_meta || {}
  if (meta[fieldname]?.reqd && !value) {
    createToast({
      title: __('Error Updating Lead'),
      text: __('{0} is a required field', [meta[fieldname].label]),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: `${lead.data.lead_name} - ${lead.data.mobile_no}` || __('Untitled'),
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

usePageMeta(() => {
  return {
    title: lead.data?.lead_name || lead.data?.name,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    // {
    //   name: 'Emails',
    //   label: __('Emails'),
    //   icon: EmailIcon,
    // },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    // {
    //   name: 'Calls',
    //   label: __('Calls'),
    //   icon: PhoneIcon,
    //   condition: () => callEnabled.value,
    // },
    // {
    //   name: 'Tasks',
    //   label: __('Tasks'),
    //   icon: TaskIcon,
    // },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

watch(offWorkMode, (newVal) => {
  localStorage.setItem("off_work_mode", newVal.toString())
  triggerFetchNewLeads();
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

watch(tabs, (value) => {
  if (value && route.params.tabName) {
    let index = value.findIndex(
      (tab) => tab.name.toLowerCase() === route.params.tabName.toLowerCase(),
    )
    if (index !== -1) {
      tabIndex.value = index
    }
  }
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

const fieldsLayout = createResource({
  url: 'crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.leadId],
  params: { doctype: 'CRM Lead', name: props.leadId },
  auto: true,
})

function updateField(name, value, callback) {
  updateLead(name, value, () => {
    lead.data[name] = value
    callback?.()
  })
}

const fetchingBookings = ref(false)
const fetchedBookings = ref([])
const editBookingSubmitting = ref(false)
const editBookingForm = ref({})
const editingBookingId = ref(null)

function openEditBooking(booking) {
  editingBookingId.value = booking.order_id || (booking.order_ids && booking.order_ids[0]) || ''
  editBookingForm.value = {
    customer_name: booking.customer_name || '',
    booking_mobile: booking.booking_mobile || '',
    outlet: booking.outlet || '',
    booking_date: booking.booking_date || '',
    timeslot: booking.timeslot || '',
    treatment: booking.treatment || '',
    session: String(booking.session || '60'),
    preferred_therapist: booking.preferred_therapist || 'Any',
    third_party_voucher_select: booking.third_party_voucher ? 'Yes' : 'No',
    package_select: booking.package ? 'Yes' : 'No',
  }
  leftPanelMode.value = 'edit'
}

async function submitEditBooking() {
  editBookingSubmitting.value = true
  try {
    const response = await call('crm.api.whatsapp.edit_booking', {
      order_id: editingBookingId.value,
      booking_details: {
        booking_date: editBookingForm.value.booking_date,
        timeslot: editBookingForm.value.timeslot ? (editBookingForm.value.timeslot.length === 5 ? editBookingForm.value.timeslot + ':00' : editBookingForm.value.timeslot) : '',
        treatment: editBookingForm.value.treatment,
        session: parseInt(editBookingForm.value.session),
        preferred_therapist: editBookingForm.value.preferred_therapist,
        third_party_voucher: editBookingForm.value.third_party_voucher_select === 'Yes',
        package: editBookingForm.value.package_select === 'Yes',
      },
    })
    if (response?.success) {
      createToast({
        title: __('Success'),
        text: __(response.message || 'Booking updated successfully'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      leftPanelMode.value = 'view'
      fetchBookingsForPanel()
    } else {
      createToast({
        title: __('Failed'),
        text: __(response?.message || 'Booking update failed'),
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    }
  } catch (err) {
    createToast({
      title: __('Failed'),
      text: __(err.messages?.[0] || err.message),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
  } finally {
    editBookingSubmitting.value = false
  }
}

function confirmDeleteBooking(booking) {
  const bookingIds = booking.order_ids || []
  if (!bookingIds) {
    createToast({
      title: __('Error'),
      text: __('No booking ID found'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }
  $dialog({
    title: __('Delete Booking'),
    message: __('Are you sure you want to delete this booking for {0}?', [booking.customer_name]),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async ({ close }) => {
          try {
            const response = await call('crm.api.whatsapp.delete_booking', {
              order_ids: bookingIds,
            })
            if (response?.success) {
              createToast({
                title: __('Success'),
                text: __(response.message || 'Booking deleted successfully'),
                icon: 'check',
                iconClasses: 'text-green-600',
              })
              fetchBookingsForPanel()
            } else {
              createToast({
                title: __('Failed'),
                text: __(response?.message || 'Booking deletion failed'),
                icon: 'x',
                iconClasses: 'text-red-600',
              })
            }
          } catch (err) {
            createToast({
              title: __('Failed'),
              text: __(err.messages?.[0] || err.message),
              icon: 'x',
              iconClasses: 'text-red-600',
            })
          }
          close()
        },
      },
    ],
  })
}

async function fetchBookingsForPanel() {
  const phone = lead.data?.mobile_no || ''
  if (!phone) {
    createToast({
      title: __('Error'),
      text: __('No phone number set for this lead'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }
  fetchingBookings.value = true
  fetchedBookings.value = []
  try {
    const res = await call('crm.api.whatsapp.fetch_bookings', {
      booking_mobile: phone,
    })
    fetchedBookings.value = res?.bookings || []
  } catch (e) {
    createToast({
      title: __('Error'),
      text: __('Failed to fetch bookings'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
  } finally {
    fetchingBookings.value = false
  }
}


async function deleteLead(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Lead',
    name,
  })
  router.push({ name: 'Leads' })
}

// Convert to Deal
const showConvertToDealModal = ref(false)
const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)

const existingContact = ref('')
const existingOrganization = ref('')

async function convertToDeal(updated) {
  let valueUpdated = false

  if (existingContactChecked.value && !existingContact.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing contact'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    createToast({
      title: __('Error'),
      text: __('Please select an existing organization'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
    return
  }

  if (existingContactChecked.value && existingContact.value) {
    lead.data.salutation = getContactByName(existingContact.value).salutation
    lead.data.first_name = getContactByName(existingContact.value).first_name
    lead.data.last_name = getContactByName(existingContact.value).last_name
    lead.data.email_id = getContactByName(existingContact.value).email_id
    lead.data.mobile_no = getContactByName(existingContact.value).mobile_no
    existingContactChecked.value = false
    valueUpdated = true
  }

  if (existingOrganizationChecked.value && existingOrganization.value) {
    lead.data.organization = existingOrganization.value
    existingOrganizationChecked.value = false
    valueUpdated = true
  }

  if (valueUpdated) {
    updateLead(
      {
        salutation: lead.data.salutation,
        first_name: lead.data.first_name,
        last_name: lead.data.last_name,
        email_id: lead.data.email_id,
        mobile_no: lead.data.mobile_no,
        organization: lead.data.organization,
      },
      '',
      () => convertToDeal(true),
    )
    showConvertToDealModal.value = false
  } else {
    let deal = await call(
      'crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal',
      {
        lead: lead.data.name,
      },
    )
    if (deal) {
      capture('convert_lead_to_deal')
      if (updated) {
        await contacts.reload()
      }
      router.push({ name: 'Deal', params: { dealId: deal } })
    }
  }
}

const activities = ref(null)

function openEmailBox() {
  activities.value.emailBox.show = true
}

function getStatus(lead) {
  if (lead.status.length > 0 && lead.status.includes("Accepted")) {
    return "Accepted"
  }
  else if (lead.status.length > 0 && lead.status.includes("New")) {
    return "New"
  }
  else if (lead.status.length > 0 && lead.status.includes("Completed")) {
    return "Completed"
  }
  else if (lead.status.length > 0 && lead.status.includes("Case Closed")) {
    return "Case Closed"
  }
}

function getBackground(lead) {
  if (lead.status.length > 0 && lead.status.includes("Accepted")) {
    return "#ffe599ff"
  }
  else if (lead.status.length > 0 && lead.status.includes("New")) {
    if (isWithin8Minutes(lead.last_reply_at)) {
      if (lead.is_special_attention === 1) {
        return "#bdb1f0"
      }
      if (!(lead.last_reply_by_user === null || lead.last_reply_by_user === undefined || lead.last_reply_by_user === '') && lead.last_reply_by_user == getUser().name) {
        return "#b6d7a8"
      }
      else if (!(lead.last_reply_by_user === null || lead.last_reply_by_user === undefined || lead.last_reply_by_user === '')) {
        return "#ea9999"
      }
    }
    if (lead.is_special_attention === 1) {
      return "#bdb1f0"
    }
    return "#c9daf8ff"
  }
  else if (lead.status.length > 0 && lead.status.includes("Completed")) {
    return "#ccccccff"
  }
  else if (lead.status.length > 0 && lead.status.includes("Case Closed")) {
    return "#ffffffff"
  }
}

function isWithin8Minutes(datetime) {
  const now = new Date();
  const targetTime = new Date(datetime).getTime();
  
  const diff = Math.abs(now.getTime() - targetTime); // Absolute difference in milliseconds
  return diff <= 8 * 60 * 1000; // 8 minutes in milliseconds
}
</script>

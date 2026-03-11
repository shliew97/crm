<template>
  <div class="flex h-screen w-screen">
    <div v-if="!isLeadPage" class="h-full border-r bg-gray-50">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <AppHeader />
      <slot />
    </div>
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const isLeadPage = computed(() => route.name === 'Lead')
</script>

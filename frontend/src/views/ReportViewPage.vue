<template>
  <div class="viewer-root">
    <header class="viewer-header">
      <div class="title">
        <h1>{{ report?.title || 'AI Report' }}</h1>
        <span v-if="report?.report_code" class="code">{{ report.report_code }}</span>
      </div>
      <div class="actions">
        <a :href="downloadHref" class="btn" target="_blank" rel="noopener">다운로드</a>
        <button class="btn ghost" @click="goBack">닫기</button>
      </div>
    </header>

    <div v-if="loading" class="loading">불러오는 중…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <iframe v-else class="viewer-frame" :src="reportSrc" title="AI Report Viewer"></iframe>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reportService } from '../services/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const report = ref(null)

const fetchReport = async () => {
  loading.value = true
  error.value = ''
  try {
    let res
    if (route.params.id) {
      res = await reportService.getReport(route.params.id)
    } else if (route.params.code) {
      res = await reportService.getReportByCode(route.params.code)
    }
    report.value = res.data
  } catch (e) {
    error.value = '리포트를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

// Always use backend DB-streaming endpoint so viewer works even if file is missing
const reportSrc = computed(() => report.value?.report_id ? `/api/reports/${report.value.report_id}/content` : '')
const downloadHref = computed(() => report.value?.report_id ? `/api/reports/${report.value.report_id}/download` : '#')

const goBack = () => {
  if (window.opener) {
    window.close()
  } else {
    router.back()
  }
}

onMounted(fetchReport)
</script>

<style scoped>
.viewer-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0b0b0b;
}
.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #111827;
  color: #e5e7eb;
  border-bottom: 1px solid #1f2937;
}
.title { display: flex; align-items: center; gap: 10px; }
.title h1 { font-size: 16px; margin: 0; }
.code { background:#1f2937; padding:2px 8px; border-radius:6px; font-size:12px; color:#93c5fd }
.actions { display: flex; gap: 8px; }
.btn { background:#2563eb; color:white; border:none; padding:8px 12px; border-radius:6px; cursor:pointer; font-weight:600; text-decoration:none }
.btn.ghost { background:#374151; }
.viewer-frame { flex: 1; width: 100%; border: 0; background:white }
.loading, .error { color: #e5e7eb; padding: 20px; }
</style>

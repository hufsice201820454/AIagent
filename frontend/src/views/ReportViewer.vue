<template>
  <div class="reports-page">
    <div class="container">
      <div class="header">
        <h1>AI 리포트</h1>
        <button @click="showGenerateModal = true" class="generate-btn">
          + 새 리포트 생성
        </button>
      </div>
      
      <div v-if="loading" class="loading">로딩 중...</div>
      
      <!-- 리포트 목록 -->
      <div v-else class="reports-grid">
        <div 
          v-for="report in reports" 
          :key="report.report_id" 
          class="report-card"
        >
          <div class="report-header">
            <h2>{{ report.title }}</h2>
            <span class="report-code">{{ report.report_code }}</span>
          </div>
          
          <div class="report-meta">
            <span class="date">
              생성일: {{ formatDate(report.created_at) }}
            </span>
          </div>
          
          <div class="report-actions">
            <button @click="viewReport(report)" class="view-btn">
              📄 보기
            </button>
            <button @click="downloadReport(report)" class="download-btn">
              ⬇️ 다운로드
            </button>
          </div>
        </div>
        
        <p v-if="reports.length === 0" class="no-data">
          생성된 리포트가 없습니다. 새 리포트를 생성해보세요!
        </p>
      </div>
    </div>
    
    <!-- 리포트 생성 모달 -->
    <div v-if="showGenerateModal" class="modal-overlay" @click="showGenerateModal = false">
      <div class="modal" @click.stop>
        <h2>새 리포트 생성</h2>
        
        <form @submit.prevent="generateReport">
          <div class="form-group">
            <label>기업 선택</label>
            <select v-model="generateForm.oem_id" required>
              <option value="">기업을 선택하세요</option>
              <option 
                v-for="company in companies" 
                :key="company.oem_id" 
                :value="company.oem_id"
              >
                {{ company.company_name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>기업명</label>
            <input 
              v-model="generateForm.company_name" 
              type="text" 
              placeholder="기업명 입력"
              required
            />
          </div>
          
          <div class="modal-actions">
            <button 
              type="button" 
              @click="showGenerateModal = false" 
              class="cancel-btn"
            >
              취소
            </button>
            <button 
              type="submit" 
              class="submit-btn"
              :disabled="generating"
            >
              {{ generating ? '생성 중...' : '생성' }}
            </button>
          </div>
          
          <p v-if="generateError" class="error">{{ generateError }}</p>
          <p v-if="generateSuccess" class="success">{{ generateSuccess }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportService, companyService } from '../services/api'

const loading = ref(true)
const reports = ref([])
const companies = ref([])
const showGenerateModal = ref(false)
const generating = ref(false)
const generateError = ref('')
const generateSuccess = ref('')

const generateForm = ref({
  oem_id: '',
  company_name: ''
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', { 
    year: 'numeric',
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadData = async () => {
  loading.value = true
  try {
    const [reportsRes, companiesRes] = await Promise.all([
      reportService.getReports(),
      companyService.getOEMCompanies()
    ])
    
    reports.value = reportsRes.data
    companies.value = companiesRes.data
  } catch (error) {
    console.error('데이터 로딩 실패:', error)
  } finally {
    loading.value = false
  }
}

const generateReport = async () => {
  generating.value = true
  generateError.value = ''
  generateSuccess.value = ''
  
  try {
    const response = await reportService.generateReport({
      company_name: generateForm.value.company_name,
      oem_id: generateForm.value.oem_id
    })
    
    generateSuccess.value = '리포트 생성이 시작되었습니다!'
    
    setTimeout(() => {
      showGenerateModal.value = false
      loadData()
      generateForm.value = { oem_id: '', company_name: '' }
      generateSuccess.value = ''
    }, 2000)
  } catch (error) {
    generateError.value = '리포트 생성 실패. 다시 시도해주세요.'
  } finally {
    generating.value = false
  }
}

const viewReport = (report) => {
  const url = `/report-view/${report.report_id}`
  window.open(url, '_blank', 'noopener')
}

const downloadReport = (report) => {
  const url = `/api/reports/${report.report_id}/download`
  window.open(url, '_blank', 'noopener')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.reports-page {
  padding: 40px 0;
  min-height: 100vh;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

h1 {
  font-size: 32px;
  color: #1f2937;
}

.generate-btn {
  padding: 12px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.generate-btn:hover {
  background: #1d4ed8;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #6b7280;
  font-size: 18px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.report-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
}

.report-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
  margin-bottom: 12px;
}

h2 {
  font-size: 18px;
  color: #1f2937;
  line-height: 1.4;
  flex: 1;
}

.report-code {
  background: #eff6ff;
  color: #2563eb;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.report-meta {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.date {
  color: #6b7280;
  font-size: 14px;
}

.report-actions {
  display: flex;
  gap: 10px;
}

.view-btn, .download-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn {
  background: #f3f4f6;
  color: #374151;
}

.view-btn:hover {
  background: #e5e7eb;
}

.download-btn {
  background: #2563eb;
  color: white;
}

.download-btn:hover {
  background: #1d4ed8;
}

.no-data {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px;
  color: #9ca3af;
  font-size: 16px;
}

/* 모달 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  padding: 32px;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal h2 {
  font-size: 24px;
  margin-bottom: 24px;
  color: #1f2937;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn, .submit-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f3f4f6;
  color: #374151;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

.submit-btn {
  background: #2563eb;
  color: white;
}

.submit-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #ef4444;
  font-size: 14px;
  text-align: center;
  margin-top: 16px;
}

.success {
  color: #10b981;
  font-size: 14px;
  text-align: center;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .reports-grid {
    grid-template-columns: 1fr;
  }
}
</style>

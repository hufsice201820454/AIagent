<template>
  <div class="dashboard">
    <div class="container">
      <h1>대시보드</h1>
      
      <div v-if="loading" class="loading">로딩 중...</div>
      
      <div v-else>
        <!-- 재무 스냅샷 카드 (상단) -->
        <div class="finance-grid">
          <div class="finance-card">
            <h3>Revenue (회사 매출액)</h3>
            <ul>
              <li v-if="financials.our_company">
                {{ financials.our_company.company_name }}:
                {{ formatNumber(financials.our_company.revenue) }}
              </li>
            </ul>
          </div>
          <div class="finance-card">
            <h3>OEM Revenue Change (%)</h3>
            <ul>
              <li v-for="item in financials.oem_revenue_change" :key="item.company_name">
                {{ item.company_name }}:
                <span :class="item.revenue_change_pct >= 0 ? 'pos' : 'neg'">{{ formatPct(item.revenue_change_pct) }}</span>
              </li>
            </ul>
          </div>
          <div class="finance-card">
            <h3>Profit Margin Snapshot (영업이익률)</h3>
            <ul>
              <li v-for="item in financials.profit_margins" :key="item.company_name">
                {{ item.company_name }}:
                <span :class="item.profit_margin >= 0 ? 'pos' : 'neg'">{{ formatPct(item.profit_margin) }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- 주요 통계 카드 (보조) -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <p class="stat-label">총 기업 수</p>
              <p class="stat-value">{{ stats.totalCompanies }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">📰</div>
            <div class="stat-content">
              <p class="stat-label">최신 뉴스</p>
              <p class="stat-value">{{ stats.totalNews }}</p>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon">📄</div>
            <div class="stat-content">
              <p class="stat-label">AI 리포트</p>
              <p class="stat-value">{{ stats.totalReports }}</p>
            </div>
          </div>
        </div>

        <!-- 주요 기업 테이블 -->
        <div class="section">
          <h2>주요 기업</h2>
          <table class="data-table">
            <thead>
              <tr>
                <th>기업명</th>
                <th>티커</th>
                <th>국가</th>
                <th>본사</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="company in topCompanies" :key="company.oem_id">
                <td class="company-name">{{ company.company_name }}</td>
                <td><span class="ticker">{{ company.ticker }}</span></td>
                <td>{{ company.country }}</td>
                <td>{{ company.headquarters }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 최신 뉴스 -->
        <div class="section">
          <h2>최신 뉴스</h2>
          <div class="news-list">
            <div 
              v-for="news in recentNews" 
              :key="news.news_id" 
              class="news-item"
            >
              <h3>{{ news.title }}</h3>
              <div class="news-meta">
                <span class="source">{{ news.source_name }}</span>
                <span class="date">{{ formatDate(news.published_at) }}</span>
              </div>
              <a 
                v-if="news.source_url" 
                :href="news.source_url" 
                target="_blank" 
                class="news-link"
              >
                기사 보기 →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { newsService, companyService, reportService } from '../services/api'

const loading = ref(true)
const stats = ref({
  totalCompanies: 0,
  totalNews: 0,
  totalReports: 0
})
const topCompanies = ref([])
const recentNews = ref([])
const financials = ref({ our_company: null, oem_revenue_change: [], profit_margins: [] })

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', { 
    year: 'numeric',
    month: 'short', 
    day: 'numeric' 
  })
}

const formatNumber = (n) => {
  if (n === null || n === undefined) return '-'
  const num = Number(n)
  if (isNaN(num)) return String(n)
  if (Math.abs(num) >= 1e9) return (num/1e9).toFixed(1) + 'B'
  if (Math.abs(num) >= 1e6) return (num/1e6).toFixed(1) + 'M'
  if (Math.abs(num) >= 1e3) return (num/1e3).toFixed(1) + 'K'
  return num.toLocaleString()
}

const formatPct = (v) => v === null || v === undefined ? '-' : `${Number(v).toFixed(1)}%`

const loadData = async () => {
  loading.value = true
  try {
    const [newsRes, companiesRes, reportsRes, finRes] = await Promise.all([
      newsService.getNews({ limit: 5 }),
      companyService.getOEMCompanies({ limit: 100 }),
      reportService.getReports({ limit: 100 }),
      companyService.getFinancialSummary()
    ])
    
    recentNews.value = newsRes.data
    topCompanies.value = companiesRes.data.slice(0, 8)
    financials.value = finRes.data
    stats.value = {
      totalCompanies: companiesRes.data.length,
      totalNews: newsRes.data.length,
      totalReports: reportsRes.data.length
    }
  } catch (error) {
    console.error('데이터 로딩 실패:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  padding: 40px 0;
  min-height: 100vh;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

h1 {
  font-size: 32px;
  color: #1f2937;
  margin-bottom: 30px;
}

h2 {
  font-size: 22px;
  color: #1f2937;
  margin-bottom: 20px;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #6b7280;
  font-size: 18px;
}

/* 재무 카드 */
.finance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.finance-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.finance-card h3 { margin: 0 0 10px; font-size: 16px; color: #111827 }
.finance-card ul { list-style: none; padding: 0; margin: 0 }
.finance-card li { padding: 4px 0; color: #374151 }
.pos { color: #10b981; font-weight: 600 }
.neg { color: #ef4444; font-weight: 600 }

/* 통계 카드 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 40px;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

/* 섹션 */
.section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

/* 테이블 */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f9fafb;
}

.data-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #6b7280;
}

.company-name {
  font-weight: 600;
  color: #1f2937;
}

.ticker {
  background: #2563eb;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* 뉴스 */
.news-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.news-item {
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 4px solid #2563eb;
}

.news-item h3 {
  font-size: 16px;
  color: #1f2937;
  margin-bottom: 10px;
  line-height: 1.5;
}

.news-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  font-size: 13px;
}

.source {
  color: #2563eb;
  font-weight: 600;
}

.date {
  color: #9ca3af;
}

.news-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.news-link:hover {
  text-decoration: underline;
}
</style>

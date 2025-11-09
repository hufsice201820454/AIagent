<template>
  <div class="news-page">
    <div class="container">
      <div class="header">
        <h1>뉴스 피드</h1>
        
        <!-- 기업 필터 -->
        <select v-model="selectedCompany" @change="filterNews" class="company-filter">
          <option value="">전체 기업</option>
          <option 
            v-for="company in companies" 
            :key="company.oem_id" 
            :value="company.oem_id"
          >
            {{ company.company_name }}
          </option>
        </select>
      </div>
      
      <div v-if="loading" class="loading">로딩 중...</div>
      
      <div v-else class="news-grid">
        <article 
          v-for="news in filteredNews" 
          :key="news.news_id" 
          class="news-card"
        >
          <div class="news-header">
            <h2>{{ news.title }}</h2>
            <span v-if="news.sentiment" :class="['sentiment', news.sentiment]">
              {{ getSentimentText(news.sentiment) }}
            </span>
          </div>
          
          <p v-if="news.summary" class="summary">{{ news.summary }}</p>
          
          <div class="news-footer">
            <div class="meta">
              <span class="source">{{ news.source_name }}</span>
              <span class="date">{{ formatDate(news.published_at) }}</span>
            </div>
            
            <a 
              v-if="news.source_url" 
              :href="news.source_url" 
              target="_blank" 
              class="read-link"
            >
              기사 읽기 →
            </a>
          </div>
        </article>
        
        <p v-if="filteredNews.length === 0" class="no-data">
          뉴스가 없습니다.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { newsService, companyService } from '../services/api'

const loading = ref(true)
const allNews = ref([])
const companies = ref([])
const selectedCompany = ref('')

const filteredNews = computed(() => {
  if (!selectedCompany.value) {
    return allNews.value
  }
  return allNews.value.filter(news => news.oem_id === selectedCompany.value)
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', { 
    year: 'numeric',
    month: 'long', 
    day: 'numeric' 
  })
}

const getSentimentText = (sentiment) => {
  const map = {
    positive: '긍정',
    neutral: '중립',
    negative: '부정'
  }
  return map[sentiment] || ''
}

const filterNews = async () => {
  loading.value = true
  try {
    if (selectedCompany.value) {
      const response = await newsService.getNews({ 
        oem_id: selectedCompany.value,
        limit: 50 
      })
      allNews.value = response.data
    } else {
      const response = await newsService.getNews({ limit: 50 })
      allNews.value = response.data
    }
  } catch (error) {
    console.error('뉴스 로딩 실패:', error)
  } finally {
    loading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const [newsRes, companiesRes] = await Promise.all([
      newsService.getNews({ limit: 50 }),
      companyService.getOEMCompanies()
    ])
    
    allNews.value = newsRes.data
    companies.value = companiesRes.data
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
.news-page {
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

.company-filter {
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  background: white;
  min-width: 200px;
}

.company-filter:focus {
  outline: none;
  border-color: #2563eb;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #6b7280;
  font-size: 18px;
}

.news-grid {
  display: grid;
  gap: 24px;
}

.news-card {
  background: white;
  padding: 28px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  border-left: 4px solid #2563eb;
}

.news-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
  margin-bottom: 12px;
}

h2 {
  font-size: 20px;
  color: #1f2937;
  line-height: 1.5;
  flex: 1;
}

.sentiment {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.sentiment.positive {
  background: #d1fae5;
  color: #065f46;
}

.sentiment.neutral {
  background: #e5e7eb;
  color: #374151;
}

.sentiment.negative {
  background: #fee2e2;
  color: #991b1b;
}

.summary {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 16px;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  flex-wrap: wrap;
  gap: 12px;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.source {
  color: #2563eb;
  font-weight: 600;
}

.date {
  color: #9ca3af;
}

.read-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  font-size: 15px;
  transition: color 0.2s;
}

.read-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.no-data {
  text-align: center;
  padding: 60px;
  color: #9ca3af;
  font-size: 16px;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .company-filter {
    width: 100%;
  }
}
</style>

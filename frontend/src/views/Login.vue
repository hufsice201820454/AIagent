<template>
  <div class="auth-page">
    <div class="auth-box">
      <h1>EVAgent</h1>
      <p class="subtitle">자동차 시장 트렌드 분석</p>
      
      <form @submit.prevent="handleLogin">
        <input 
          v-model="email" 
          type="email" 
          placeholder="이메일"
          required 
        />
        
        <input 
          v-model="password" 
          type="password" 
          placeholder="비밀번호"
          required 
        />
        
        <button type="submit" :disabled="loading">
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
        
        <p v-if="error" class="error">{{ error }}</p>
      </form>
      
      <p class="link">
        계정이 없으신가요? 
        <router-link to="/register">회원가입</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (err) {
    error.value = '로그인 실패. 이메일과 비밀번호를 확인하세요.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
}

h1 {
  text-align: center;
  color: #2563eb;
  margin-bottom: 10px;
  font-size: 32px;
}

.subtitle {
  text-align: center;
  color: #6b7280;
  margin-bottom: 30px;
  font-size: 14px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

input {
  padding: 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: #2563eb;
}

button {
  padding: 14px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #1d4ed8;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #ef4444;
  font-size: 14px;
  text-align: center;
}

.link {
  text-align: center;
  margin-top: 20px;
  color: #6b7280;
  font-size: 14px;
}

.link a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}
</style>

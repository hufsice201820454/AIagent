<template>
  <div class="auth-page">
    <div class="auth-box">
      <h1>회원가입</h1>
      <p class="subtitle">EVAgent에 오신 것을 환영합니다</p>
      
      <form @submit.prevent="handleRegister">
        <input 
          v-model="formData.email" 
          type="email" 
          placeholder="이메일"
          required 
        />
        
        <input 
          v-model="formData.name" 
          type="text" 
          placeholder="이름"
          required 
        />
        
        <input 
          v-model="formData.password" 
          type="password" 
          placeholder="비밀번호"
          required 
        />
        
        <input 
          v-model="confirmPassword" 
          type="password" 
          placeholder="비밀번호 확인"
          required 
        />
        
        <button type="submit" :disabled="loading">
          {{ loading ? '가입 중...' : '회원가입' }}
        </button>
        
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
      </form>
      
      <p class="link">
        이미 계정이 있으신가요? 
        <router-link to="/login">로그인</router-link>
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

const formData = ref({
  email: '',
  name: '',
  password: ''
})
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

const handleRegister = async () => {
  const email = (formData.value.email || '').trim().toLowerCase()
  const name = (formData.value.name || '').trim()
  const password = (formData.value.password || '').trim()

  if (!email || !name || !password) {
    error.value = '이메일/이름/비밀번호를 입력하세요.'
    return
  }
  if (password !== confirmPassword.value) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  if (password.length < 8) {
    error.value = '비밀번호는 8자 이상이어야 합니다.'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    await authStore.register({ email, name, password })
    success.value = '회원가입 완료! 로그인 페이지로 이동합니다...'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (err) {
    // FastAPI 422 구조(detail: [{msg,...}]) 또는 400(detail: str) 모두 처리
    const detail = err?.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(d => d.msg).join(', ')
    } else if (typeof detail === 'string') {
      error.value = detail
    } else {
      error.value = '회원가입 실패'
    }
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
  padding: 20px;
}

.auth-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 450px;
}

h1 {
  text-align: center;
  color: #2563eb;
  margin-bottom: 10px;
  font-size: 28px;
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
  gap: 14px;
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
  margin-top: 6px;
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

.success {
  color: #10b981;
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

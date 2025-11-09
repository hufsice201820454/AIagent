<template>
  <header class="header">
    <div class="container">
      <div class="logo">
        <router-link to="/">EVAgent</router-link>
      </div>
      <nav class="nav">
        <router-link to="/" class="nav-link">대시보드</router-link>
        <router-link to="/news" class="nav-link">뉴스</router-link>
        <router-link to="/reports" class="nav-link">리포트</router-link>
      </nav>
      <div class="user-menu">
        <span class="user-name">{{ user?.name || '사용자' }}</span>
        <button @click="handleLogout" class="logout-btn">로그아웃</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const user = computed(() => authStore.user)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

.logo a {
  font-size: 24px;
  font-weight: 700;
  color: #2563eb;
  text-decoration: none;
}

.nav {
  display: flex;
  gap: 30px;
}

.nav-link {
  color: #374151;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: #2563eb;
  background: #eff6ff;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  color: #374151;
  font-weight: 500;
}

.logout-btn {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: #dc2626;
}

@media (max-width: 768px) {
  .container {
    flex-wrap: wrap;
    height: auto;
    padding: 15px 20px;
  }
  
  .nav {
    width: 100%;
    order: 3;
    justify-content: center;
    margin-top: 10px;
  }
}
</style>

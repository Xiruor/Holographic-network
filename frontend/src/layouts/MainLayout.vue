<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo-container">
        <span class="logo-text" v-show="!isCollapsed">全息网络洞察系统</span>
        <span class="logo-icon" v-show="isCollapsed">H</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        background-color="#304156"
        text-color="#fff"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Monitor /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>
        <el-menu-item index="/data/upload">
          <el-icon><Upload /></el-icon>
          <template #title>数据上传</template>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据分析</template>
        </el-menu-item>
        <el-menu-item index="/analysis/ai">
          <el-icon><Cpu /></el-icon>
          <template #title>AI 分析</template>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <el-icon><DataBoard /></el-icon>
          <template #title>可视化看板</template>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><WarningFilled /></el-icon>
          <template #title>告警中心</template>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <template #title>报表中心</template>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 主区域 -->
    <div class="main-container">
      <!-- 顶栏 -->
      <div class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleSidebar">
            <Fold v-if="!isCollapsed" />
            <Expand v-else />
          </el-icon>
          <span class="header-title">全息网络洞察系统</span>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>管理员</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 内容区域（缓存页面状态，最多缓存 10 个页面防止内存溢出） -->
      <div class="content">
        <router-view v-slot="{ Component }">
          <keep-alive :max="10">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Odometer,
  Monitor,
  Upload,
  DataAnalysis,
  Cpu,
  DataBoard,
  WarningFilled,
  Document,
  Fold,
  Expand,
  User,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'
import { authAPI } from '../api'

const router = useRouter()
const route = useRoute()

const isCollapsed = ref(false)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 详情页路由回退到父级菜单，保持侧边栏高亮正确
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/alerts/')) return '/alerts'
  if (path.startsWith('/devices/')) return '/devices'
  return path
})

const handleLogout = async () => {
  try {
    await authAPI.logout()
  } catch {
    // 即使后端登出失败，前端也要清除本地状态
  }
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('userRole')
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ---- 侧边栏 ---- */
.sidebar {
  width: 220px;
  background-color: #304156;
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  width: 64px;
}

.logo-container {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

.logo-icon {
  font-size: 22px;
}

/* ---- 主区域 ---- */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ---- 顶栏 ---- */
.header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #333;
}

.collapse-btn:hover {
  color: #409eff;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
}

.user-info:hover {
  color: #409eff;
}

/* ---- 内容区域 ---- */
.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f0f2f5;
}

/* 覆盖 el-menu 默认样式 */
:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  display: flex;
  align-items: center;
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(64, 158, 255, 0.2) !important;
}
</style>

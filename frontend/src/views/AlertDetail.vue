<template>
  <div class="alert-detail-container">
    <!-- 返回按钮 -->
    <div class="back-row">
      <el-button text :icon="ArrowLeft" @click="goBack">返回告警中心</el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 告警详情 -->
    <template v-if="!loading && alertData">
      <div class="detail-header">
        <h2 class="page-title">{{ alertData.alertType }}</h2>
        <el-tag
          :color="levelColor(alertData.level)"
          effect="dark"
          size="small"
          class="level-tag"
        >
          {{ alertData.level }}
        </el-tag>
      </div>

      <el-card class="info-card" shadow="hover">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">{{ alertData.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(alertData.status)" size="small" effect="plain">
              {{ alertData.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关联设备">{{ alertData.deviceName }}</el-descriptions-item>
          <el-descriptions-item label="告警类型">{{ alertData.alertType }}</el-descriptions-item>
          <el-descriptions-item label="发生时间">{{ alertData.time }}</el-descriptions-item>
          <el-descriptions-item label="处理时间">{{ alertData.processTime || '未处理' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="desc-card" shadow="hover">
        <template #header>
          <span class="card-title">告警描述</span>
        </template>
        <p class="desc-text">{{ alertData.message }}</p>
      </el-card>

      <el-card class="action-card" shadow="hover">
        <template #header>
          <span class="card-title">操作</span>
        </template>
        <div class="action-buttons">
          <el-button
            v-if="alertData.status !== '已处理'"
            type="success"
            @click="handleProcess"
          >标记已处理</el-button>
          <el-button
            type="primary"
            link
            @click="goToDevice"
          >查看关联设备 <el-icon><ArrowRight /></el-icon></el-button>
        </div>
      </el-card>
    </template>

    <!-- 未找到 -->
    <el-empty v-if="!loading && !alertData" description="未找到该告警信息" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { alertAPI } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const alertData = ref(null)

// 加载告警数据的函数
const loadAlertData = async () => {
  loading.value = true
  try {
    const res = await alertAPI.detail(route.params.id)
    if (res.code === 200 && res.data) {
      // 优先使用路由查询参数中的状态（从告警中心跳转时传入，保持状态同步）
      alertData.value = {
        ...res.data,
        status: route.query.s || res.data.status,
        processTime: route.query.pt || res.data.processTime || ''
      }
    } else {
      alertData.value = null
    }
  } catch {
    alertData.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadAlertData)

// 使用 keep-alive 缓存后，切换路由参数时重新加载数据
watch(() => route.params.id, loadAlertData)

const goBack = () => {
  router.push('/alerts')
}

const goToDevice = () => {
  // 跳转到设备详情页（通过设备名匹配设备ID）
  router.push(`/devices?name=${encodeURIComponent(alertData.value.deviceName)}`)
}

const handleProcess = async () => {
  try {
    const res = await alertAPI.process(alertData.value.id)
    if (res.code === 200) {
      alertData.value.status = '已处理'
      const now = new Date()
      alertData.value.processTime = now.toISOString().replace('T', ' ').substring(0, 19)
      ElMessage.success(res.message || '已标记为已处理')
    }
  } catch {
    ElMessage.error('操作失败，请重试')
  }
}

const levelColor = (level) => {
  const map = { '紧急': '#F56C6C', '严重': '#E6A23C', '警告': '#909399', '信息': '#67C23A' }
  return map[level] || '#909399'
}

const statusTagType = (status) => {
  const map = { '未处理': 'danger', '已处理': 'success' }
  return map[status] || 'info'
}
</script>

<style scoped>
.alert-detail-container {
  padding: 20px;
}

.back-row {
  margin-bottom: 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.level-tag {
  font-size: 13px;
  padding: 4px 12px;
}

.info-card,
.desc-card,
.action-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.desc-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
  padding: 8px 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.loading-wrapper {
  padding: 40px 20px;
}
</style>

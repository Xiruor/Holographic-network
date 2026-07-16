<template>
  <div class="device-detail-container">
    <!-- 返回按钮 -->
    <div class="back-row">
      <el-button text :icon="ArrowLeft" @click="goBack">返回设备管理</el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 设备详情 -->
    <template v-if="!loading && deviceData">
      <div class="detail-header">
        <h2 class="page-title">{{ deviceData.name }}</h2>
        <el-tag
          :type="statusTagType(deviceData.status)"
          effect="dark"
          size="small"
        >
          {{ deviceData.status }}
        </el-tag>
      </div>

      <!-- 基本信息 -->
      <el-card class="info-card" shadow="hover">
        <template #header>
          <span class="card-title">基本信息</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备名称">{{ deviceData.name }}</el-descriptions-item>
          <el-descriptions-item label="设备类型">
            <el-tag :type="typeTagType(deviceData.type)" effect="plain" size="small">
              {{ deviceData.type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="IP 地址">{{ deviceData.ip }}</el-descriptions-item>
          <el-descriptions-item label="端口号">{{ deviceData.port }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(deviceData.status)" size="small" effect="dark">
              {{ deviceData.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="位置">{{ deviceData.location || '未设置' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 性能指标 -->
      <el-card class="metric-card" shadow="hover">
        <template #header>
          <span class="card-title">性能指标</span>
        </template>
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="metric-item">
              <div class="metric-label">CPU 使用率</div>
              <el-progress
                :percentage="deviceData.cpuUsage"
                :color="progressColor(deviceData.cpuUsage)"
                :stroke-width="18"
                :text-inside="true"
              />
            </div>
          </el-col>
          <el-col :span="12">
            <div class="metric-item">
              <div class="metric-label">内存使用率</div>
              <el-progress
                :percentage="deviceData.memUsage"
                :color="progressColor(deviceData.memUsage)"
                :stroke-width="18"
                :text-inside="true"
              />
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 关联告警 -->
      <el-card class="alerts-card" shadow="hover">
        <template #header>
          <div class="alerts-header">
            <span class="card-title">关联告警</span>
            <el-button text type="primary" size="small" @click="goToAlerts">
              查看全部 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>
        <el-table :data="relatedAlerts" stripe style="width: 100%">
          <el-table-column prop="alertType" label="告警类型" min-width="140" />
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag :color="levelColor(row.level)" effect="dark" size="small">
                {{ row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="alertStatusTagType(row.status)" size="small" effect="plain">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="time" label="发生时间" width="170" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="goToAlert(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="relatedAlerts.length === 0" description="暂无关联告警" :image-size="80" />
      </el-card>
    </template>

    <!-- 未找到 -->
    <el-empty v-if="!loading && !deviceData" description="未找到该设备信息" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { deviceAPI, metricsAPI } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const deviceData = ref(null)
const relatedAlerts = ref([])

onMounted(async () => {
  try {
    const id = parseInt(route.params.id)
    const res = await deviceAPI.detail(id)
    if (res.code === 200) {
      const data = res.data
      deviceData.value = {
        name: data.name,
        type: data.type,
        ip: data.ip,
        port: data.port,
        status: data.status,
        location: data.location,
        cpuUsage: data.cpuUsage,
        memUsage: data.memUsage
      }
      relatedAlerts.value = data.related_alerts || []
    } else {
      ElMessage.error(res.message || '获取设备详情失败')
    }
  } catch (err) {
    ElMessage.error(err.message || '获取设备详情失败')
  } finally {
    loading.value = false
  }
})

const goBack = () => {
  router.push('/devices')
}

const goToAlerts = () => {
  router.push('/alerts')
}

const goToAlert = (row) => {
  router.push(`/alerts/${row.id}`)
}

const typeTagType = (type) => {
  const map = { 路由器: 'primary', 交换机: 'success', 防火墙: 'warning', 服务器: 'danger' }
  return map[type] || 'info'
}

const statusTagType = (status) => {
  const map = { 在线: 'success', 离线: 'info', 告警: 'danger' }
  return map[status] || 'info'
}

const progressColor = (percent) => {
  if (percent >= 90) return '#F56C6C'
  if (percent >= 70) return '#E6A23C'
  return '#67C23A'
}

const levelColor = (level) => {
  const map = { '紧急': '#F56C6C', '严重': '#E6A23C', '警告': '#909399', '信息': '#67C23A' }
  return map[level] || '#909399'
}

const alertStatusTagType = (status) => {
  const map = { '未确认': 'danger', '已确认': 'warning', '已处理': 'success' }
  return map[status] || 'info'
}
</script>

<style scoped>
.device-detail-container {
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

.info-card,
.metric-card,
.alerts-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.metric-item {
  margin-bottom: 12px;
}

.metric-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-wrapper {
  padding: 40px 20px;
}
</style>

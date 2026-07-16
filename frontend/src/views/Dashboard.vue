<template>
  <div class="dashboard-container">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card stat-clickable" shadow="hover" @click="goToPage('/devices')">
        <div class="stat-content">
          <div class="stat-icon" style="background: #e6f7ff">
            <el-icon :size="28" color="#1890ff"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ deviceCount }}</div>
            <div class="stat-label">设备总数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card stat-clickable" shadow="hover" @click="goToPage('/devices')">
        <div class="stat-content">
          <div class="stat-icon" style="background: #f0fdf4">
            <el-icon :size="28" color="#52c41a"><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ onlineCount }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card stat-clickable" shadow="hover" @click="goToPage('/alerts')">
        <div class="stat-content">
          <div class="stat-icon" style="background: #fff2f0">
            <el-icon :size="28" color="#ff4d4f"><WarningFilled /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ todayAlertCount }}</div>
            <div class="stat-label">今日告警</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card stat-clickable" shadow="hover" @click="goToPage('/visualization')">
        <div class="stat-content">
          <div class="stat-icon" style="background: #f0f5ff">
            <el-icon :size="28" color="#722ed1"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ cpuAverage }}%</div>
            <div class="stat-label">CPU平均使用率</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">设备流量趋势</span>
        </template>
        <div ref="lineChartRef" class="chart-container"></div>
      </el-card>

      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">设备类型分布</span>
        </template>
        <div ref="pieChartRef" class="chart-container"></div>
      </el-card>
    </div>

    <!-- 最近告警表格 -->
    <el-card class="alerts-card" shadow="hover">
      <template #header>
        <div class="alerts-header">
          <span class="card-title">最近告警</span>
          <el-link type="primary" underline="never" @click="goToPage('/alerts')">查看全部</el-link>
        </div>
      </template>

      <el-table :data="recentAlerts" stripe style="width: 100%" @row-click="goToAlert">
        <el-table-column label="设备名称" width="180">
          <template #default="{ row }">{{ row.deviceName }}</template>
        </el-table-column>
        <el-table-column label="告警类型" width="180">
          <template #default="{ row }">{{ row.alertType }}</template>
        </el-table-column>
        <el-table-column label="级别" width="120">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.level)" size="small" effect="dark">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.time) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { dashboardAPI } from '../api'

const router = useRouter()

const goToPage = (path) => {
  router.push(path)
}

const goToAlert = (row) => {
  if (row.alert_id) {
    router.push(`/alerts/${row.alert_id}`)
  } else {
    router.push('/alerts')
  }
}

// --- 统计数据 ---
const deviceCount = ref(0)
const onlineCount = ref(0)
const todayAlertCount = ref(0)
const cpuTrend = ref([])
const networkTrend = ref([])
const deviceTypeDist = ref([])
const recentAlerts = ref([])

const cpuAverage = computed(() => {
  const arr = cpuTrend.value
  if (!arr || arr.length === 0) return '0.0'
  const sum = arr.reduce((acc, cur) => acc + (typeof cur === 'number' ? cur : parseFloat(cur.cpu_usage) || 0), 0)
  return (sum / arr.length).toFixed(1)
})

// --- 图表 ---
const lineChartRef = ref(null)
const pieChartRef = ref(null)
let lineChartInstance = null
let pieChartInstance = null
let lineResizeHandler = null
let pieResizeHandler = null

const emptyGraphic = {
  type: 'text',
  left: 'center',
  top: 'center',
  style: {
    text: '暂无数据',
    textAlign: 'center',
    fill: '#909399',
    fontSize: 14
  }
}

const initLineChart = () => {
  if (!lineChartRef.value) return

  lineChartInstance = echarts.init(lineChartRef.value)
  const days = networkTrend.value.map(item => item.time)
  const inboundData = networkTrend.value.map(item => item.network_in)
  const outboundData = networkTrend.value.map(item => item.network_out)

  const hasData = days.length > 0
  lineChartInstance.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: hasData ? ['网络流入', '网络流出'] : [],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      top: '8%',
      containLabel: true
    },
    xAxis: hasData ? {
      type: 'category',
      data: days,
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    } : { show: false },
    yAxis: hasData ? {
      type: 'value',
      name: 'Mbps',
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    } : { show: false },
    series: hasData ? [
      {
        name: '网络流入',
        type: 'line',
        smooth: true,
        data: inboundData,
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' }
          ])
        }
      },
      {
        name: '网络流出',
        type: 'line',
        smooth: true,
        data: outboundData,
        itemStyle: { color: '#67C23A' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103,194,58,0.3)' },
            { offset: 1, color: 'rgba(103,194,58,0.02)' }
          ])
        }
      }
    ] : [],
    graphic: hasData ? [] : [emptyGraphic]
  })

  // 响应式自适应
  lineResizeHandler = () => lineChartInstance.resize()
  window.addEventListener('resize', lineResizeHandler)
}

const initPieChart = () => {
  if (!pieChartRef.value) return

  pieChartInstance = echarts.init(pieChartRef.value)

  const hasData = deviceTypeDist.value.length > 0
  pieChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 台 ({d}%)'
    },
    legend: hasData ? {
      orient: 'vertical',
      right: '5%',
      top: 'center'
    } : { show: false },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: deviceTypeDist.value
      }
    ],
    graphic: hasData ? [] : [emptyGraphic]
  })

  // 响应式自适应
  pieResizeHandler = () => pieChartInstance.resize()
  window.addEventListener('resize', pieResizeHandler)
}

onMounted(async () => {
  try {
    const res = await dashboardAPI.summary()
    if (res.code === 200) {
      const data = res.data
      deviceCount.value = data.device_count
      onlineCount.value = data.online_count
      todayAlertCount.value = data.today_alert_count
      cpuTrend.value = data.cpu_trend || []
      networkTrend.value = data.network_trend || []
      deviceTypeDist.value = data.device_type_dist || []
      recentAlerts.value = data.recent_alerts || []
    }
  } catch (e) {
    console.error('加载仪表盘数据失败', e)
  }

  nextTick(() => {
    initLineChart()
    initPieChart()
  })
})

onUnmounted(() => {
  if (lineResizeHandler) {
    window.removeEventListener('resize', lineResizeHandler)
  }
  if (pieResizeHandler) {
    window.removeEventListener('resize', pieResizeHandler)
  }
  lineChartInstance?.dispose()
  pieChartInstance?.dispose()
})

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const d = new Date(timeStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const levelTagType = (level) => {
  const map = {
    '严重': 'warning',
    '警告': 'info',
    '信息': 'success',
    '紧急': 'danger'
  }
  return map[level] || 'info'
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  border-radius: 8px;
}

.stat-clickable {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 图表 */
.charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  flex: 1;
  border-radius: 8px;
}

.chart-container {
  width: 100%;
  height: 320px;
}

/* 区域标题 */
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 告警 */
.alerts-card {
  border-radius: 8px;
}

.alerts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>

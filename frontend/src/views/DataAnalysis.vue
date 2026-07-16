<template>
  <div class="analysis-container">
    <h2 class="page-title">数据分析与统计</h2>

    <!-- 分析控制面板 -->
    <el-card class="control-card" shadow="hover">
      <el-form :inline="true" label-width="auto">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="分析维度">
          <el-select v-model="analysisDimension" style="width: 160px">
            <el-option label="按设备分析" value="device" />
            <el-option label="按时间分析" value="time" />
            <el-option label="按指标分析" value="metric" />
          </el-select>
        </el-form-item>
        <el-form-item label="分析类型">
          <el-select v-model="analysisType" style="width: 160px">
            <el-option label="描述性统计" value="descriptive" />
            <el-option label="趋势分析" value="trend" />
            <el-option label="对比分析" value="comparison" />
            <el-option label="Top-N排行" value="topn" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleStartAnalysis">开始分析</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计摘要卡片 -->
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(totalMetrics) }}</div>
            <div class="stat-label">数据总量</div>
          </div>
          <div class="stat-unit">条</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-info">
            <div class="stat-value">{{ totalDevices }}</div>
            <div class="stat-label">设备数量</div>
          </div>
          <div class="stat-unit">台</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-info">
            <div class="stat-value">{{ collectionDays }}</div>
            <div class="stat-label">采集周期</div>
          </div>
          <div class="stat-unit">天</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-info">
            <div class="stat-value">{{ onlineCount }}</div>
            <div class="stat-label">在线设备</div>
          </div>
          <div class="stat-unit">台</div>
        </div>
      </el-card>
    </div>

    <!-- 分析结果图表 -->
    <div class="charts-row">
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">CPU &amp; 内存使用率对比</span>
        </template>
        <div ref="cpuChartRef" class="chart-container"></div>
      </el-card>
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <span class="card-title">设备流量 Top-N</span>
        </template>
        <div ref="trafficChartRef" class="chart-container"></div>
      </el-card>
    </div>

    <!-- 分析数据表格 -->
    <el-card class="data-table-card" shadow="hover">
      <template #header>
        <span class="card-title">设备指标明细</span>
      </template>
      <el-table :data="deviceStats" v-loading="loading" stripe style="width: 100%" @row-click="goToDeviceDetail">
        <el-table-column prop="name" label="设备名称" min-width="150" />
        <el-table-column prop="type" label="设备类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="dark">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cpu_usage" label="CPU使用率(%)" width="130">
          <template #default="{ row }">
            <el-progress
              :percentage="row.cpu_usage"
              :color="cpuColor(row.cpu_usage)"
              :stroke-width="14"
              :show-text="false"
            />
            <span class="progress-value">{{ row.cpu_usage }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="memory_usage" label="内存使用率(%)" width="130">
          <template #default="{ row }">
            <el-progress
              :percentage="row.memory_usage"
              :color="memColor(row.memory_usage)"
              :stroke-width="14"
              :show-text="false"
            />
            <span class="progress-value">{{ row.memory_usage }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_in" label="网络流入(Mbps)" width="160" />
        <el-table-column prop="net_out" label="网络流出(Mbps)" width="160" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { analysisAPI } from '../api'

const router = useRouter()

const goToDeviceDetail = (row) => {
  router.push(`/devices?name=${encodeURIComponent(row.name)}`)
}

/* ---------- 控制面板 ---------- */
const dateRange = ref([])
const analysisDimension = ref('device')
const analysisType = ref('descriptive')
const loading = ref(false)

/* ---------- 统计数据 ---------- */
const totalMetrics = ref(0)
const totalDevices = ref(0)
const deviceStats = ref([])
let cpuChartInstance = null
let trafficChartInstance = null

// 计算采集周期
const collectionDays = computed(() => {
  if (dateRange.value && dateRange.value.length === 2) {
    const start = new Date(dateRange.value[0])
    const end = new Date(dateRange.value[1])
    const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
    return diff > 0 ? diff : 1
  }
  return '—'
})

// 统计在线设备数
const onlineCount = computed(() => {
  return deviceStats.value.filter(d => d.status === '在线').length
})

/* ---------- 数据获取 ---------- */
const fetchAnalysisData = async () => {
  loading.value = true
  try {
    const params = {
      dimension: analysisDimension.value,
      type: analysisType.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await analysisAPI.statistics(params)
    if (res.code === 200) {
      const data = res.data
      totalMetrics.value = data.total_metrics || 0
      totalDevices.value = data.total_devices || 0
      deviceStats.value = (data.device_stats || []).map(d => ({
        ...d,
        avg_cpu: parseFloat(d.avg_cpu) || 0,
        avg_mem: parseFloat(d.avg_mem) || 0,
        avg_net_in: parseFloat(d.avg_net_in) || 0,
        avg_net_out: parseFloat(d.avg_net_out) || 0,
        cpu_usage: parseFloat(d.cpu_usage) || 0,
        memory_usage: parseFloat(d.memory_usage) || 0,
        net_in: parseFloat(d.net_in) || 0,
        net_out: parseFloat(d.net_out) || 0
      }))
    }
  } catch (e) {
    console.error('获取分析数据失败', e)
    ElMessage.error('获取分析数据失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const handleStartAnalysis = () => {
  fetchAnalysisData().then(() => {
    initCharts()
  })
}

/* ---------- 格式化 ---------- */
const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return Number(num).toLocaleString()
}

/* ---------- 图表 ---------- */
const cpuChartRef = ref(null)
const trafficChartRef = ref(null)

const initCpuChart = () => {
  if (!cpuChartRef.value) return
  if (deviceStats.value.length === 0) return

  if (cpuChartInstance) cpuChartInstance.dispose()
  cpuChartInstance = echarts.init(cpuChartRef.value)

  const names = deviceStats.value.map(d => d.name)
  const cpuData = deviceStats.value.map(d => d.avg_cpu)
  const memData = deviceStats.value.map(d => d.avg_mem)

  cpuChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['平均CPU(%)', '平均内存(%)'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '22%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: { rotate: 25, interval: 0, fontSize: 11 },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    yAxis: {
      type: 'value',
      name: '百分比(%)',
      max: 100,
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    },
    series: [
      {
        name: '平均CPU(%)',
        type: 'bar',
        barWidth: 18,
        data: cpuData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: 'rgba(64,158,255,0.25)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      },
      {
        name: '平均内存(%)',
        type: 'bar',
        barWidth: 18,
        data: memData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#67C23A' },
            { offset: 1, color: 'rgba(103,194,58,0.25)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      }
    ]
  })
}

const initTrafficChart = () => {
  if (!trafficChartRef.value) return
  if (deviceStats.value.length === 0) return

  if (trafficChartInstance) trafficChartInstance.dispose()
  trafficChartInstance = echarts.init(trafficChartRef.value)

  // 按最新流入流量降序排列，取前 N 条
  const sorted = [...deviceStats.value].sort((a, b) => b.net_in - a.net_in).slice(0, 5)
  const names = sorted.map(d => d.name)
  const values = sorted.map(d => d.net_in)
  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#722ed1', '#f56c6c']

  trafficChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>流入: ${p.value} Mbps`
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: 'Mbps',
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    series: [
      {
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: colors[i] }
        })),
        barWidth: 24,
        label: {
          show: true,
          position: 'right',
          formatter: '{c} Mbps'
        }
      }
    ]
  })
}

const initCharts = () => {
  nextTick(() => {
    initCpuChart()
    initTrafficChart()
  })
}

/* ---------- 生命周期 ---------- */
onMounted(async () => {
  await fetchAnalysisData()
  initCharts()
})

// keep-alive 缓存激活时重新拉取数据
onActivated(async () => {
  await fetchAnalysisData()
  initCharts()
})

onBeforeUnmount(() => {
  if (cpuChartInstance) cpuChartInstance.dispose()
  if (trafficChartInstance) trafficChartInstance.dispose()
})

/* ---------- 颜色辅助 ---------- */
const cpuColor = (val) => {
  if (val >= 80) return '#f56c6c'
  if (val >= 60) return '#e6a23c'
  return '#67c23a'
}

const memColor = (val) => {
  if (val >= 80) return '#f56c6c'
  if (val >= 60) return '#e6a23c'
  return '#67c23a'
}

const statusTagType = (status) => {
  const map = { '在线': 'success', '离线': 'info', '告警': 'danger' }
  return map[status] || 'info'
}
</script>

<style scoped>
.analysis-container {
  padding: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
}

/* 控制卡片 */
.control-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.control-card :deep(.el-form) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.control-card :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 18px;
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

.stat-content {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
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

.stat-unit {
  font-size: 14px;
  color: #c0c4cc;
  padding-bottom: 4px;
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

/* 表格卡片 */
.data-table-card {
  border-radius: 8px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.progress-value {
  margin-left: 8px;
  font-size: 13px;
  color: #606266;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-progress) {
  display: inline-flex;
  width: 80px;
  vertical-align: middle;
}
</style>

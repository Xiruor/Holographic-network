<template>
  <div class="visualization-container">
    <!-- 页面标题 -->
    <h2 class="page-title">可视化看板</h2>

    <!-- 筛选行 -->
    <el-card class="filter-card" shadow="hover">
      <el-row :gutter="16" align="middle">
        <el-col :span="7">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="5">
          <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 100%">
            <el-option
              v-for="dev in deviceOptions"
              :key="dev"
              :label="dev"
              :value="dev"
            />
          </el-select>
        </el-col>
        <el-col :span="2">
          <el-button type="primary" :icon="Refresh" @click="refreshData">刷新</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表 2x2 网格 -->
    <el-row :gutter="16" class="charts-row">
      <!-- 左上：热力图 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">流量时段分布热力图</span>
          </template>
          <div ref="heatmapChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 右上：CPU 使用率排行 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">CPU 使用率排行</span>
          </template>
          <div ref="pieChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 左下：网络延迟趋势 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">网络延迟趋势</span>
          </template>
          <div ref="lineChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 右下：告警数量趋势 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span class="card-title">告警数量趋势</span>
          </template>
          <div ref="radarChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onActivated, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'
import { visualizationAPI } from '../api'
import { useDevices } from '../composables/useDevices'

// --- 筛选条件 ---
const dateRange = ref([])
const selectedDevice = ref('全部设备')

const { deviceOptions, fetchDevices } = useDevices({ includeAll: true })

// --- API 数据 ---
const chartData = ref(null)

// --- 图表引用 ---
const heatmapChartRef = ref(null)
const pieChartRef = ref(null)
const lineChartRef = ref(null)
const radarChartRef = ref(null)

// 存储图表实例用于自适应
const chartInstances = []

// 安全初始化图表：如果 DOM 上已有实例则复用，避免重复初始化警告
const initChart = (domRef) => {
  if (!domRef) return null
  let chart = echarts.getInstanceByDom(domRef)
  if (!chart) {
    chart = echarts.init(domRef)
    chartInstances.push(chart)
  }
  return chart
}

// --- 格式化日期为 YYYY-MM-DD ---
const formatDate = (date) => {
  if (!date) return null
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// --- 获取可视化数据（带筛选参数）---
const fetchVisualizationData = async () => {
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = formatDate(dateRange.value[0])
      params.end_date = formatDate(dateRange.value[1])
    }
    if (selectedDevice.value && selectedDevice.value !== '全部设备') {
      params.device_name = selectedDevice.value
    }
    const res = await visualizationAPI.data(params)
    if (res.code === 200) {
      chartData.value = res.data
    }
  } catch (err) {
    console.error('获取可视化数据失败:', err)
  }
}

const refreshData = async () => {
  await fetchVisualizationData()
  nextTick(() => {
    // 先销毁旧图表实例，重新初始化
    chartInstances.forEach((chart) => chart.dispose())
    chartInstances.length = 0
    initCharts()
  })
}

// --- 监听筛选条件变化，自动刷新 ---
watch([dateRange, selectedDevice], () => {
  refreshData()
})

const initHeatmapChart = () => {
  if (!heatmapChartRef.value || !chartData.value) return
  const chart = initChart(heatmapChartRef.value)
  if (!chart) return

  const { data, hours, days } = chartData.value.heatmap

  chart.setOption({
    tooltip: {
      position: (point, params, dom, rect, size) => {
        const [mouseX, mouseY] = point
        const tooltipW = size.contentSize[0]
        const tooltipH = size.contentSize[1]
        const viewW = size.viewSize[0]
        let x = mouseX + 10
        if (mouseX + 10 + tooltipW > viewW) {
          x = mouseX - tooltipW - 10
        }
        let y = mouseY - tooltipH - 10
        if (mouseY - tooltipH < 10) {
          y = mouseY + 10
        }
        return [x, y]
      },
      formatter: (params) => {
        return `${days[params.value[1]]} ${hours[params.value[0]]}<br/>流量: ${params.value[2]}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: { show: true },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#e6f7ff', '#91d5ff', '#40a9ff', '#1890ff', '#096dd9', '#0050b3']
      }
    },
    series: [
      {
        type: 'heatmap',
        data: data,
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' }
        }
      }
    ]
  })
}

const initCpuRankingChart = () => {
  if (!pieChartRef.value || !chartData.value) return
  const chart = initChart(pieChartRef.value)
  if (!chart) return

  const rawData = chartData.value.cpu_ranking || []
  const names = rawData.map((d) => d.name)
  const values = rawData.map((d) => d.cpu)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>CPU 使用率: ${p.value}%`
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '8%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: 'CPU (%)',
      max: 100,
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
      axisLabel: { formatter: '{value}%' }
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { fontSize: 11 }
    },
    series: [
      {
        type: 'bar',
        data: values.reverse().map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 80 ? '#f56c6c' : v >= 50 ? '#e6a23c' : '#67c23a'
          }
        })),
        barWidth: 20,
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          fontSize: 11
        }
      }
    ]
  })
}

const initLineChart = () => {
  if (!lineChartRef.value || !chartData.value) return
  const chart = initChart(lineChartRef.value)
  if (!chart) return

  const timePoints = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const lineColors = ['#409EFF', '#67C23A', '#E6A23C', '#722ed1']

  const rawData = chartData.value.cpu_trend
  const seriesData = rawData.map((item, index) => ({
    name: item.name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 4,
    data: item.data,
    itemStyle: { color: lineColors[index % lineColors.length] },
    lineStyle: { width: 2 }
  }))

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = `<div>${params[0].axisValue}</div>`
        params.forEach((p) => {
          result += `<div style="display:flex;align-items:center;gap:4px;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};"></span>
            ${p.seriesName}: ${p.value}ms
          </div>`
        })
        return result
      }
    },
    legend: {
      data: seriesData.map((d) => d.name),
      bottom: 0,
      textStyle: { fontSize: 12 }
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
      data: timePoints,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { interval: 3 }
    },
    yAxis: {
      type: 'value',
      name: '响应时间 (ms)',
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    },
    series: seriesData
  })
}

const initAlertTrendChart = () => {
  if (!radarChartRef.value || !chartData.value) return
  const chart = initChart(radarChartRef.value)
  if (!chart) return

  const rawData = chartData.value.alert_trend || []
  const dates = rawData.map((d) => d.date)
  const counts = rawData.map((d) => d.count)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>告警数量: ${p.value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
      axisLabel: { rotate: dates.length > 5 ? 30 : 0 }
    },
    yAxis: {
      type: 'value',
      name: '告警数',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } }
    },
    series: [
      {
        type: 'bar',
        data: counts.map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 5 ? '#f56c6c' : v >= 2 ? '#e6a23c' : '#409eff'
          }
        })),
        barWidth: 30,
        label: {
          show: true,
          position: 'top',
          formatter: '{c}',
          fontSize: 12
        }
      }
    ]
  })
}

const initCharts = () => {
  if (!chartData.value) return
  initHeatmapChart()
  initCpuRankingChart()
  initLineChart()
  initAlertTrendChart()
}

// 窗口大小变化处理
const handleResize = () => {
  chartInstances.forEach((chart) => {
    chart.resize()
  })
}

onMounted(() => {
  fetchVisualizationData().then(() => {
    nextTick(() => {
      initCharts()
      window.addEventListener('resize', handleResize)
    })
  })
})

onActivated(() => {
  // keep-alive 恢复时刷新设备列表和图表数据
  fetchDevices()
  fetchVisualizationData().then(() => {
    nextTick(() => {
      // dispose 旧实例再重新初始化，避免 keep-alive 缓存导致的残留
      chartInstances.forEach((chart) => chart.dispose())
      chartInstances.length = 0
      initCharts()
    })
  })
})
</script>

<style scoped>
.visualization-container {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

.filter-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.charts-row {
  margin-bottom: 0;
}

.chart-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.chart-container {
  width: 100%;
  height: 340px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
</style>

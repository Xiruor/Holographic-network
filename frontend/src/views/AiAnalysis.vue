<template>
  <div class="ai-analysis-container">
    <h2 class="page-title">AI 大模型智能分析</h2>

    <!-- 输入区域 -->
    <el-card class="input-card" shadow="hover">
      <el-form label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分析场景">
              <el-select v-model="scenario" style="width: 100%">
                <el-option label="网络异常检测" value="anomaly" />
                <el-option label="流量模式识别" value="pattern" />
                <el-option label="根因分析" value="rootcause" />
                <el-option label="网络优化建议" value="optimize" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标设备">
              <el-select v-model="targetDevice" style="width: 100%">
                <el-option
                  v-for="dev in deviceOptions"
                  :key="dev"
                  :label="dev"
                  :value="dev"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分析需求">
              <el-input
                v-model="prompt"
                type="textarea"
                :rows="4"
                placeholder="请输入分析需求或问题描述..."
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" :icon="Cpu" :loading="isAnalyzing" @click="handleStartAnalysis">
              开始分析
            </el-button>
            <el-button @click="handleClear">清空</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 分析状态步骤 -->
    <el-card v-if="isAnalyzing" class="status-card" shadow="hover">
      <el-steps :active="currentStep" align-center finish-status="success">
        <el-step title="数据加载中" description="正在读取设备数据" />
        <el-step title="模型推理中" description="AI模型进行分析" />
        <el-step title="报告生成中" description="生成分析报告" />
      </el-steps>
    </el-card>

    <!-- 分析结果 -->
    <el-card v-if="showResult" class="result-card" shadow="hover">
      <template #header>
        <div class="result-header">
          <div class="result-header-left">
            <el-tag type="primary" effect="dark" size="small">{{ scenarioLabel }}</el-tag>
            <span class="result-time">{{ resultTime }}</span>
          </div>
          <el-tag type="success" effect="plain" size="small">分析完成</el-tag>
        </div>
      </template>

      <!-- 分析结论 -->
      <div class="conclusion-section">
        <h4 class="section-subtitle">分析结论</h4>
        <el-card shadow="never" class="conclusion-card">
          <p class="conclusion-text">
            {{ conclusionText }}
          </p>
        </el-card>
      </div>

      <!-- 异常检测表格 -->
      <div class="anomaly-section">
        <h4 class="section-subtitle">异常检测结果</h4>
        <el-table :data="anomalyData" stripe style="width: 100%" max-height="320">
          <el-table-column prop="deviceName" label="设备名称" min-width="140" />
          <el-table-column prop="anomalyType" label="异常类型" min-width="140" />
          <el-table-column prop="level" label="异常等级" width="100">
            <template #default="{ row }">
              <el-tag :type="levelTagType(row.level)" size="small" effect="dark">
                {{ row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="time" label="发生时间" width="160" />
          <el-table-column prop="detail" label="详情描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="{ row }">
              <el-tag
                :type="confidenceTagType(row.confidence)"
                size="small"
              >
                {{ row.confidence }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 优化建议 -->
      <div class="suggestion-section">
        <h4 class="section-subtitle">优化建议</h4>
        <el-collapse v-model="activeSuggestion" accordion>
          <el-collapse-item
            v-for="(item, index) in suggestionData"
            :key="index"
            :title="item.title"
            :name="index"
          >
            <p class="suggestion-text">{{ item.description }}</p>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import { deepseekAPI, analysisAPI, alertAPI } from '@/api'
import { useDevices } from '@/composables/useDevices'

/* ---------- 表单状态 ---------- */
const scenario = ref('anomaly')
const targetDevice = ref('全部设备')
const dateRange = ref([])
const prompt = ref('')

const { deviceOptions } = useDevices({ includeAll: true })

/* ---------- 分析状态 ---------- */
const isAnalyzing = ref(false)
const showResult = ref(false)
const currentStep = ref(0)
const resultTime = ref('')

const scenarioLabel = computed(() => {
  const map = {
    anomaly: '网络异常检测',
    pattern: '流量模式识别',
    rootcause: '根因分析',
    optimize: '网络优化建议'
  }
  return map[scenario.value] || '网络异常检测'
})

/* ---------- 分析结果数据 ---------- */
const conclusionText = ref('')
const anomalyData = ref([])
const suggestionData = ref([])
const activeSuggestion = ref(0)

const levelTagType = (level) => {
  const map = { '严重': 'danger', '警告': 'warning', '提示': 'info' }
  return map[level] || 'info'
}

const confidenceTagType = (val) => {
  const num = parseInt(val)
  if (num >= 90) return 'success'
  if (num >= 80) return 'warning'
  return 'info'
}

/* ===========================================================
 *  step 1 — 从「数据分析 + 告警中心」拉取真实数据
 * =========================================================== */
const fetchRealData = async () => {
  const realData = { deviceStats: [], alerts: [], dateInfo: '' }

  realData.dateInfo = dateRange.value.length === 2
    ? `${dateRange.value[0]} 至 ${dateRange.value[1]}`
    : '最近7天'

  /* ---- 1.1 数据分析接口 —— 同 DataAnalysis.vue ---- */
  try {
    const params = { dimension: 'device', type: 'descriptive' }
    if (dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await analysisAPI.statistics(params)
    if (res.code === 200) {
      let stats = (res.data.device_stats || []).map((d) => ({
        name: d.name,
        type: d.type || '',
        status: d.status || '',
        cpu_usage: parseFloat(d.cpu_usage) || 0,
        memory_usage: parseFloat(d.memory_usage) || 0,
        net_in: parseFloat(d.net_in) || 0,
        net_out: parseFloat(d.net_out) || 0
      }))
      if (targetDevice.value !== '全部设备') {
        stats = stats.filter((d) => d.name === targetDevice.value)
      }
      realData.deviceStats = stats
    }
  } catch { /* statistics 非必需 */ }

  /* ---- 1.2 告警中心接口 —— 同 Alerts.vue ---- */
  try {
    const alertParams = { page: 1, page_size: 50 }
    if (dateRange.value.length === 2) {
      alertParams.start_date = dateRange.value[0]
      alertParams.end_date = dateRange.value[1]
    }
    if (targetDevice.value !== '全部设备') {
      alertParams.device = targetDevice.value
    }
    const alertRes = await alertAPI.list(alertParams)
    const raw = alertRes.data?.list || []

    // 直接映射为 anomalyData 格式，不经过 AI
    realData.alerts = raw.map((a) => ({
      deviceName: a.deviceName || targetDevice.value,
      anomalyType: a.alertType || '未知',
      level: a.level === '紧急' ? '严重' : (a.level || '提示'),
      time: a.time || '',
      detail: a.message || a.detail || '',
      confidence: a.level === '紧急' || a.level === '严重' ? '95%'
                 : a.level === '警告' ? '82%' : '70%'
    }))
  } catch { /* 告警非必需 */ }

  return realData
}

/* ---------- AI 提示词（仅用于结论 + 建议） ---------- */
const buildSystemPrompt = () => {
  return `你是一位专业的网络运维分析专家。请根据我提供的**真实设备指标和告警记录**进行分析。

你的任务：
1. 结论（conclusion）：综合所有数据，给出 200-300 字的分析结论
2. 优化建议（suggestions）：基于真实问题给出可操作的优化方案，至少 2 条

异常检测结果已经在下方直接给出，请**不要重复生成异常检测数据**。

请**仅返回一个 JSON 对象**（不要 markdown 代码块标记），严格使用以下格式：
{
  "conclusion": "综合分析结论",
  "suggestions": [
    { "title": "优化建议标题", "description": "优化建议详细描述" }
  ]
}

注意事项：
- 必须基于提供的数据进行分析，不得编造不存在的数据
- 结论要引用真实数据中的具体数值`
}

const buildUserPrompt = (realData) => {
  const scenarioMap = {
    anomaly: '网络异常检测',
    pattern: '流量模式识别',
    rootcause: '根因分析',
    optimize: '网络优化建议'
  }

  let msg = `===== 分析任务 =====\n`
  msg += `分析场景：${scenarioMap[scenario.value] || '网络异常检测'}\n`
  msg += `目标设备：${targetDevice.value}\n`
  msg += `时间范围：${realData.dateInfo}\n`
  msg += `分析需求：${prompt.value.trim()}\n\n`

  if (realData.deviceStats.length > 0) {
    msg += `===== 设备指标数据（来自数据分析） =====\n`
    msg += JSON.stringify(realData.deviceStats, null, 2) + '\n\n'
  }

  if (realData.alerts.length > 0) {
    msg += `===== 告警记录（来自告警中心） =====\n`
    msg += JSON.stringify(realData.alerts.map((a) => ({
      设备: a.deviceName,
      异常类型: a.anomalyType,
      级别: a.level,
      发生时间: a.time,
      描述: a.detail
    })), null, 2) + '\n\n'
  }

  msg += `请基于以上真实数据给出分析结论和优化建议。`
  return msg
}

/* ---------- 解析模型返回的 JSON ---------- */
const parseResponse = (content) => {
  let jsonStr = content.trim()
  if (jsonStr.startsWith('```')) {
    jsonStr = jsonStr.replace(/^```(?:json)?\s*/, '').replace(/\s*```$/, '')
  }
  return JSON.parse(jsonStr)
}

/* ---------- 操作处理函数 ---------- */
const handleStartAnalysis = async () => {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入分析需求或问题描述')
    return
  }

  isAnalyzing.value = true
  showResult.value = false
  currentStep.value = 0
  conclusionText.value = ''
  anomalyData.value = []
  suggestionData.value = []

  const now = new Date()
  resultTime.value = now.toLocaleString('zh-CN', { hour12: false })

  const stepTimer = setInterval(() => {
    if (currentStep.value < 2) currentStep.value++
  }, 800)

  try {
    /* ---- step 1：拉取真实数据 ---- */
    currentStep.value = 0
    const realData = await fetchRealData()

    /* ---- 直接填充 anomalyData —— 告警中心真实数据 ---- */
    anomalyData.value = realData.alerts

    /* ---- step 2：AI 仅生成结论 + 建议 ---- */
    currentStep.value = 1
    const response = await deepseekAPI.analyze({
      scenario: scenario.value,
      targetDevice: targetDevice.value,
      dateRange: dateRange.value,
      prompt: buildUserPrompt(realData),
      systemPrompt: buildSystemPrompt()
    })

    clearInterval(stepTimer)
    currentStep.value = 2

    const content = response.choices[0].message.content
    const result = parseResponse(content)

    conclusionText.value = result.conclusion || 'AI 分析完成，未生成结论。'
    suggestionData.value = result.suggestions || []
    activeSuggestion.value = 0

    showResult.value = true
  } catch (error) {
    clearInterval(stepTimer)
    console.error('AI 分析失败:', error)

    /* ---- AI 失败时仍展示真实告警 ---- */
    if (anomalyData.value.length === 0) {
      try {
        const alertParams = { page: 1, page_size: 50 }
        if (dateRange.value.length === 2) {
          alertParams.start_date = dateRange.value[0]
          alertParams.end_date = dateRange.value[1]
        }
        if (targetDevice.value !== '全部设备') {
          alertParams.device = targetDevice.value
        }
        const alertRes = await alertAPI.list(alertParams)
        anomalyData.value = (alertRes.data?.list || []).map((a) => ({
          deviceName: a.deviceName || targetDevice.value,
          anomalyType: a.alertType || '未知',
          level: a.level === '紧急' ? '严重' : (a.level || '提示'),
          time: a.time || '',
          detail: a.message || a.detail || '',
          confidence: a.level === '紧急' || a.level === '严重' ? '95%'
                     : a.level === '警告' ? '82%' : '70%'
        }))
      } catch { /* 静默 */ }
    }

    conclusionText.value = 'AI 分析暂不可用，以下展示数据库中的真实告警数据。'
    showResult.value = true

    let errorMsg = 'AI 分析请求失败'
    if (error.response) {
      errorMsg = `API 错误 (${error.response.status}): ${error.response.data?.error?.message || error.response.statusText}`
    } else if (error.message) {
      errorMsg = error.message
    }
    ElMessage.warning(errorMsg + '，已展示真实告警数据')
  } finally {
    isAnalyzing.value = false
  }
}

const handleClear = () => {
  scenario.value = 'anomaly'
  targetDevice.value = '全部设备'
  dateRange.value = []
  prompt.value = ''
  isAnalyzing.value = false
  showResult.value = false
  currentStep.value = 0
  conclusionText.value = ''
  anomalyData.value = []
  suggestionData.value = []
}
</script>

<style scoped>
.ai-analysis-container {
  padding: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
}

/* 输入卡片 */
.input-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: -80px;
}

/* 状态卡片 */
.status-card {
  margin-bottom: 20px;
  border-radius: 8px;
  padding: 20px 0;
}

/* 结果卡片 */
.result-card {
  border-radius: 8px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-time {
  font-size: 13px;
  color: #909399;
}

/* 区域副标题 */
.section-subtitle {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

/* 结论 */
.conclusion-section {
  margin-bottom: 24px;
}

.conclusion-card {
  border-left: 4px solid #67c23a;
  border-radius: 6px;
  background-color: #fafafa;
}

.conclusion-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
  text-indent: 2em;
}

/* 异常区域 */
.anomaly-section {
  margin-bottom: 24px;
}

/* 建议区域 */
.suggestion-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  margin: 0;
  padding: 4px 0;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>

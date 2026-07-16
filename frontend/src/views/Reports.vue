<template>
  <div class="reports-container">
    <div class="page-header">
      <h2 class="page-title">报表中心</h2>
      <p class="page-desc">生成和下载网络运行分析报告</p>
    </div>

    <!-- 生成报告卡片 -->
    <el-card class="generate-card" shadow="hover">
      <template #header>
        <span class="card-title">生成新报告</span>
      </template>

      <el-form :model="reportForm" label-width="110px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="报告标题">
              <el-input v-model="reportForm.title" placeholder="请输入报告标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="报告类型">
              <el-select v-model="reportForm.type" placeholder="请选择报告类型" style="width: 100%">
                <el-option
                  v-for="t in reportTypeOptions"
                  :key="t.value"
                  :label="t.label"
                  :value="t.value"
                >
                  <span class="option-icon">{{ t.icon }}</span>
                  <span>{{ t.label }}</span>
                  <span class="option-desc">{{ t.desc }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="reportForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="包含内容">
          <el-checkbox-group v-model="reportForm.contents">
            <el-checkbox
              v-for="c in contentOptions"
              :key="c.value"
              :value="c.value"
            >
              <span>{{ c.label }}</span>
              <el-tag v-if="c.source" size="small" type="info" style="margin-left: 6px">
                {{ c.source }}
              </el-tag>
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <div class="generate-actions" v-if="!isGenerating">
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          <el-icon style="margin-right: 4px"><DocumentAdd /></el-icon>
          生成报告
        </el-button>
      </div>

      <div class="progress-area" v-if="isGenerating">
        <el-progress :percentage="progressPercent" :stroke-width="16" :text-inside="true" :status="progressStatus" />
        <p class="progress-hint">{{ progressHint }}</p>
      </div>
    </el-card>

    <!-- 报告列表卡片 -->
    <el-card class="list-card" shadow="hover" style="margin-top: 20px">
      <template #header>
        <div class="list-header">
          <span class="card-title">历史报告</span>
          <el-button size="small" :icon="Refresh" @click="fetchReportList">刷新</el-button>
        </div>
      </template>

      <el-table :data="paginatedReports" v-loading="listLoading" stripe style="width: 100%">
        <el-table-column prop="title" label="报告标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="报告类型" width="160">
          <template #default="{ row }">
            <el-tag :type="reportTagType(row.type)" effect="plain" size="small">
              {{ reportTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" width="170" />
        <el-table-column prop="contents" label="包含内容" min-width="200">
          <template #default="{ row }">
            <div class="chart-tags">
              <el-tag
                v-for="item in (row.contents || [])"
                :key="item"
                size="small"
                class="chart-tag"
              >
                {{ item }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="dark">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              :disabled="row.status !== '已完成'"
              :loading="downloadingId === row.id"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              size="small"
              type="danger"
              text
              :loading="deletingId === row.id"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="reportList.length"
          layout="prev, pager, next, total"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { DocumentAdd, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportAPI } from '../api'

// ============================================================
// 报表类型 — 基于系统现有页面功能
// ============================================================
const reportTypeOptions = [
  { value: 'network_traffic',    label: '网络流量分析报告',    icon: '📊', desc: '流量趋势、带宽使用、热力图' },
  { value: 'device_performance', label: '设备性能评估报告',    icon: '🖥',  desc: 'CPU/内存使用率排行、设备对比' },
  { value: 'alert_summary',      label: '告警汇总分析报告',    icon: '🔔', desc: '告警数量趋势、类型分布' },
  { value: 'ai_analysis',        label: 'AI 智能分析报告',     icon: '🤖', desc: 'AI 异常检测、根因分析' },
  { value: 'comprehensive',      label: '综合运行报告',        icon: '📋', desc: '全维度网络运行态势汇总' }
]

const contentOptions = [
  { value: 'basic_stats',       label: '基础统计概览',   source: '仪表盘' },
  { value: 'traffic_trend',     label: '设备流量趋势',   source: '仪表盘' },
  { value: 'device_type_dist',  label: '设备类型分布',   source: '仪表盘' },
  { value: 'cpu_ranking',       label: 'CPU 使用率排行', source: '可视化看板' },
  { value: 'memory_analysis',   label: '内存使用率分析', source: '数据分析' },
  { value: 'latency_trend',     label: '网络延迟趋势',   source: '可视化看板' },
  { value: 'traffic_heatmap',   label: '流量时段热力图', source: '可视化看板' },
  { value: 'alert_trend',       label: '告警数量趋势',   source: '告警中心' },
  { value: 'ai_conclusion',     label: 'AI 分析结论',    source: 'AI 分析' },
  { value: 'optimization',      label: '优化建议',       source: 'AI 分析' }
]

const contentLabelMap = Object.fromEntries(contentOptions.map(c => [c.value, c.label]))
const contentLabel = (val) => contentLabelMap[val] || val

const reportTypeLabelMap = Object.fromEntries(reportTypeOptions.map(t => [t.value, t.label]))
const reportTypeLabel = (val) => reportTypeLabelMap[val] || val

// 类型 → 预选内容映射
const typeContentMap = {
  network_traffic:    ['basic_stats', 'traffic_trend', 'latency_trend', 'traffic_heatmap'],
  device_performance: ['basic_stats', 'cpu_ranking', 'memory_analysis', 'device_type_dist'],
  alert_summary:      ['basic_stats', 'alert_trend'],
  ai_analysis:        ['ai_conclusion', 'optimization', 'alert_trend'],
  comprehensive:      ['basic_stats', 'traffic_trend', 'device_type_dist', 'cpu_ranking',
                       'memory_analysis', 'latency_trend', 'traffic_heatmap', 'alert_trend',
                       'ai_conclusion', 'optimization']
}

// 标签颜色映射
const reportTagType = (type) => {
  const map = { network_traffic: 'primary', device_performance: 'success', alert_summary: 'warning', ai_analysis: 'info', comprehensive: 'danger' }
  return map[type] || 'info'
}

const statusTagType = (status) => {
  const map = { '已完成': 'success', '生成中': 'warning', '失败': 'danger' }
  return map[status] || 'info'
}

// ============================================================
// 表单
// ============================================================
const reportForm = ref({ title: '', type: '', dateRange: null, contents: [] })

const generating = ref(false)
const isGenerating = ref(false)
const progressPercent = ref(0)
const progressStatus = ref('')
const progressHint = ref('')

const handleGenerate = async () => {
  if (!reportForm.value.title) { ElMessage.warning('请输入报告标题'); return }
  if (!reportForm.value.type) { ElMessage.warning('请选择报告类型'); return }

  let contents = reportForm.value.contents
  if (contents.length === 0) {
    contents = typeContentMap[reportForm.value.type] || []
  }

  generating.value = true
  isGenerating.value = true
  progressPercent.value = 0
  progressStatus.value = ''
  progressHint.value = '正在提交生成任务...'

  try {
    const params = {
      title: reportForm.value.title,
      type: reportForm.value.type,
      contents,
      start_date: reportForm.value.dateRange?.[0] || null,
      end_date: reportForm.value.dateRange?.[1] || null
    }

    const interval = setInterval(() => {
      progressPercent.value += 3
      if (progressPercent.value >= 70) { clearInterval(interval); progressPercent.value = 70 }
    }, 200)

    const res = await reportAPI.generate(params)
    clearInterval(interval)

    if (res.code === 200) {
      progressPercent.value = 100
      progressStatus.value = 'success'
      progressHint.value = '报告生成成功！'
      setTimeout(() => {
        isGenerating.value = false
        generating.value = false
        progressPercent.value = 0
        ElMessage.success('报告生成成功')
        reportForm.value = { title: '', type: '', dateRange: null, contents: [] }
        fetchReportList()
      }, 800)
    } else {
      throw new Error(res.message || '生成失败')
    }
  } catch (err) {
    progressStatus.value = 'exception'
    progressHint.value = '生成失败，请重试'
    ElMessage.error('报告生成失败：' + (err.message || '未知错误'))
    setTimeout(() => { isGenerating.value = false; generating.value = false; progressPercent.value = 0 }, 1500)
  }
}

// ============================================================
// 列表
// ============================================================
const reportList = ref([])
const listLoading = ref(false)

const fetchReportList = async () => {
  listLoading.value = true
  try {
    const res = await reportAPI.list({ page: 1, page_size: 100 })
    if (res.code === 200) {
      reportList.value = (res.data?.list || []).map(item => ({
        id: item.id,
        title: item.title || '未命名报告',
        type: item.type || 'comprehensive',
        created_at: item.created_at || '',
        contents: item.contents || [],
        status: item.status || '已完成'
      }))
    }
  } catch (err) {
    console.error('获取报告列表失败:', err)
    ElMessage.error('获取报告列表失败')
  } finally {
    listLoading.value = false
  }
}

// ============================================================
// 分页
// ============================================================
const currentPage = ref(1)
const pageSize = ref(5)

const paginatedReports = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return reportList.value.slice(start, start + pageSize.value)
})

// 类型变化时自动填充内容
watch(() => reportForm.value.type, (newType) => {
  if (newType && typeContentMap[newType] && reportForm.value.contents.length === 0) {
    reportForm.value.contents = [...typeContentMap[newType]]
  }
})

// ============================================================
// 下载
// ============================================================
const downloadingId = ref(null)

const handleDownload = async (row) => {
  downloadingId.value = row.id
  try {
    const blob = await reportAPI.download(row.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.title || '报告'}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 报告已开始下载')
  } catch (err) {
    ElMessage.error('下载失败：' + (err.message || '未知错误'))
  } finally {
    downloadingId.value = null
  }
}

// ============================================================
// 删除
// ============================================================
const deletingId = ref(null)

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除报告「${row.title}」吗？此操作不可恢复。`, '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    deletingId.value = row.id
    await reportAPI.delete(row.id)
    ElMessage.success('报告已删除')
    fetchReportList()
  } catch (err) {
    if (err !== 'cancel') { ElMessage.error('删除失败：' + (err.message || '未知错误')) }
  } finally {
    deletingId.value = null
  }
}

// ============================================================
// 初始化
// ============================================================
onMounted(() => { fetchReportList() })
</script>

<style scoped>
.reports-container { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 700; color: #303133; margin: 0 0 6px 0; }
.page-desc { font-size: 14px; color: #909399; margin: 0; }
.card-title { font-size: 16px; font-weight: 600; color: #303133; }
.generate-card { border-radius: 8px; }
.generate-actions { padding-left: 110px; }
.progress-area { padding: 10px 0; }
.progress-hint { font-size: 13px; color: #909399; margin: 10px 0 0 0; text-align: center; }

.option-icon { margin-right: 6px; }
.option-desc { float: right; color: #c0c4cc; font-size: 12px; margin-left: 12px; }

.list-header { display: flex; justify-content: space-between; align-items: center; }
.chart-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.chart-tag { font-size: 11px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }

:deep(.el-table th.el-table__cell) { background-color: #f5f7fa; color: #606266; font-weight: 600; }
:deep(.el-select-dropdown__item) { height: auto; padding: 8px 12px; line-height: 1.5; }
:deep(.el-select-dropdown__item .option-desc) { display: block; font-size: 11px; color: #c0c4cc; }
</style>

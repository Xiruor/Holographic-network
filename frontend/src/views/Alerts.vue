<template>
  <div class="alerts-container">
    <!-- 页面标题 -->
    <h2 class="page-title">告警中心</h2>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="hover">
      <el-row :gutter="16" align="middle">
        <el-col :span="5">
          <el-select v-model="filterLevel" placeholder="告警级别" style="width: 100%">
            <el-option label="全部" value="全部" />
            <el-option label="紧急" value="紧急" />
            <el-option label="严重" value="严重" />
            <el-option label="警告" value="警告" />
            <el-option label="信息" value="信息" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filterStatus" placeholder="状态" style="width: 100%">
            <el-option label="全部" value="全部" />
            <el-option label="未处理" value="未处理" />
            <el-option label="已处理" value="已处理" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-select v-model="filterDevice" placeholder="关联设备" style="width: 100%">
            <el-option label="全部" value="全部" />
            <el-option label="核心路由器-01" value="核心路由器-01" />
            <el-option label="汇聚交换机-01" value="汇聚交换机-01" />
            <el-option label="汇聚交换机-02" value="汇聚交换机-02" />
            <el-option label="防火墙-FW01" value="防火墙-FW01" />
            <el-option label="防火墙-FW02" value="防火墙-FW02" />
            <el-option label="应用服务器-01" value="应用服务器-01" />
            <el-option label="应用服务器-02" value="应用服务器-02" />
            <el-option label="数据库服务器-01" value="数据库服务器-01" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="filterDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="3" style="text-align: right">
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计摘要 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card stat-pending" shadow="hover">
          <div class="stat-content">
            <div class="stat-label">待处理告警</div>
            <div class="stat-value">{{ pendingCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card stat-today" shadow="hover">
          <div class="stat-content">
            <div class="stat-label">今日新增</div>
            <div class="stat-value">{{ todayCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card stat-response" shadow="hover">
          <div class="stat-content">
            <div class="stat-label">平均响应时间</div>
            <div class="stat-value">{{ avgResponseTime }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警表格 -->
    <el-card class="table-card" shadow="hover">
      <!-- 批量操作栏 -->
      <div v-if="selectedIds.length > 0" class="batch-bar">
        <span class="batch-info">已选择 {{ selectedIds.length }} 项</span>
        <el-button size="small" type="success" @click="batchProcess">批量处理</el-button>
      </div>

      <el-table
        ref="tableRef"
        :data="alertData"
        stripe
        style="width: 100%"
        v-loading="loading"
        @row-click="handleRowClick"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="告警ID" width="160" />
        <el-table-column prop="deviceName" label="设备名称" width="150" />
        <el-table-column prop="alertType" label="告警类型" width="150" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :color="levelColor(row.level)" effect="dark" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="plain">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="发生时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== '已处理'"
              type="success"
              link
              size="small"
              @click.stop="handleProcess(row)"
            >处理</el-button>
            <span v-if="row.status === '已处理'" style="color:#909399;font-size:12px;">已处理</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="onPageSizeChange"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <!-- 告警详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" title="告警详情" width="600px" :close-on-click-modal="false">
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID" :span="2">{{ detailData.id }}</el-descriptions-item>
          <el-descriptions-item label="关联设备">{{ detailData.deviceName }}</el-descriptions-item>
          <el-descriptions-item label="告警类型">{{ detailData.alertType }}</el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :color="levelColor(detailData.level)" effect="dark" size="small">
              {{ detailData.level }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detailData.status)" size="small" effect="plain">
              {{ detailData.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="发生时间" :span="2">{{ detailData.time }}</el-descriptions-item>
          <el-descriptions-item label="处理时间" :span="2">{{ detailData.processTime || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="detail-description">
          <div class="detail-description-label">告警描述</div>
          <el-input type="textarea" :model-value="detailData.message" :rows="3" readonly />
        </div>
      </template>
      <template #footer>
        <el-button
          v-if="detailData && detailData.status !== '已处理'"
          type="success"
          @click="handleProcess(detailData)"
        >标记已处理</el-button>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { alertAPI } from '../api'

const router = useRouter()

// --- 筛选条件 ---
const filterLevel = ref('全部')
const filterStatus = ref('全部')
const filterDevice = ref('全部')
const filterDateRange = ref([])

const handleQuery = () => {
  currentPage.value = 1
  fetchAlerts()
}

const handleReset = () => {
  filterLevel.value = '全部'
  filterStatus.value = '全部'
  filterDevice.value = '全部'
  filterDateRange.value = []
  currentPage.value = 1
  fetchAlerts()
}

// --- 统计数据 ---
const pendingCount = ref(0)
const todayCount = ref(0)
const avgResponseTime = ref('15min')

// --- 数据与分页 ---
const alertData = ref([])
const total = ref(0)
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterLevel.value !== '全部') params.level = filterLevel.value
    if (filterStatus.value !== '全部') params.status = filterStatus.value
    if (filterDevice.value !== '全部') params.device = filterDevice.value
    params.page = currentPage.value
    params.page_size = pageSize.value
    const res = await alertAPI.list(params)
    alertData.value = res.data.list
    total.value = res.data.total
    pendingCount.value = res.data.pending_count
    todayCount.value = res.data.today_count
  } catch (err) {
    ElMessage.error('获取告警列表失败')
  } finally {
    loading.value = false
  }
}

const onPageSizeChange = () => {
  currentPage.value = 1
  fetchAlerts()
}

const onPageChange = () => {
  fetchAlerts()
}

// --- 选择操作 ---
const selectedIds = ref([])
const tableRef = ref(null)

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map((item) => item.id)
}

const batchProcess = async () => {
  try {
    const count = selectedIds.value.length
    await alertAPI.batchProcess({ ids: selectedIds.value })
    selectedIds.value = []
    tableRef.value?.clearSelection()
    ElMessage.success(`已处理 ${count} 项`)
    await fetchAlerts()
  } catch (err) {
    ElMessage.error('批量处理失败')
  }
}

// --- 详情对话框 ---
const detailDialogVisible = ref(false)
const detailData = ref(null)

const handleRowClick = (row) => {
  router.push({
    path: `/alerts/${row.id}`,
    query: { s: row.status, pt: row.processTime || '' }
  })
}

const handleProcess = async (row) => {
  try {
    await alertAPI.process(row.id)
    ElMessage.success(`告警 ${row.id} 已标记为已处理`)
    await fetchAlerts()
  } catch (err) {
    ElMessage.error('处理告警失败')
  }
}

// --- 辅助函数 ---
const levelColor = (level) => {
  const map = {
    '紧急': '#F56C6C',
    '严重': '#E6A23C',
    '警告': '#909399',
    '信息': '#67C23A'
  }
  return map[level] || '#909399'
}

const statusTagType = (status) => {
  const map = {
    '未处理': 'danger',
    '已处理': 'success'
  }
  return map[status] || 'info'
}

// 组件激活时刷新（支持 keep-alive）
onActivated(() => {
  fetchAlerts()
})
</script>

<style scoped>
.alerts-container {
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

/* 统计行 */
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
  border-left: 4px solid transparent;
}

.stat-pending {
  border-left-color: #F56C6C;
  background: linear-gradient(135deg, #fef0ef 0%, #fff 100%);
}

.stat-today {
  border-left-color: #E6A23C;
  background: linear-gradient(135deg, #fdf6ec 0%, #fff 100%);
}

.stat-response {
  border-left-color: #67C23A;
  background: linear-gradient(135deg, #f0f9eb 0%, #fff 100%);
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

/* 表格 */
.table-card {
  border-radius: 8px;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  margin-bottom: 12px;
}

.batch-info {
  font-size: 13px;
  color: #606266;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 详情对话框 */
.detail-description {
  margin-top: 16px;
}

.detail-description-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>

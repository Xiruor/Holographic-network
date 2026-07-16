<template>
  <div class="devices-container">
    <!-- 标题栏 -->
    <div class="header-row">
      <h2 class="page-title">设备管理</h2>
      <el-button type="primary" :icon="Plus" @click="handleAdd">添加设备</el-button>
    </div>

    <!-- 搜索 / 筛选 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" :model="filterForm">
        <el-form-item>
          <el-input v-model="filterForm.keyword" placeholder="搜索设备名称/IP" clearable style="width: 220px" />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="filterForm.deviceType" placeholder="全部" style="width: 140px" clearable>
            <el-option label="全部" value="" />
            <el-option label="路由器" value="路由器" />
            <el-option label="交换机" value="交换机" />
            <el-option label="防火墙" value="防火墙" />
            <el-option label="服务器" value="服务器" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" style="width: 130px" clearable>
            <el-option label="全部" value="" />
            <el-option label="在线" value="在线" />
            <el-option label="离线" value="离线" />
            <el-option label="告警" value="告警" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 设备表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="deviceList" v-loading="loading" stripe style="width: 100%" empty-text="无相关数据" @row-click="goToDevice">
        <el-table-column prop="name" label="设备名称" min-width="160" />
        <el-table-column prop="type" label="设备类型" width="140">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.type)" effect="plain" size="small">
              <el-icon style="margin-right: 4px; vertical-align: middle">
                <component :is="typeIcon(row.type)" />
              </el-icon>
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP 地址" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="dark">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" min-width="140" />
        <el-table-column label="CPU使用率" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.cpuUsage" :color="progressColor(row.cpuUsage)" :stroke-width="14" />
          </template>
        </el-table-column>
        <el-table-column label="内存使用率" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.memUsage" :color="progressColor(row.memUsage)" :stroke-width="14" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <!-- 添加 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑设备' : '添加设备'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择设备类型" style="width: 100%">
            <el-option label="路由器" value="路由器" />
            <el-option label="交换机" value="交换机" />
            <el-option label="防火墙" value="防火墙" />
            <el-option label="服务器" value="服务器" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="formData.ip" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="端口号" prop="port">
          <el-input-number v-model="formData.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="在线" value="在线" />
            <el-option label="离线" value="离线" />
            <el-option label="告警" value="告警" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="formData.location" placeholder="请输入设备位置，如：机房A-01机柜" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { deviceAPI } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()

const goToDevice = (row) => {
  router.push(`/devices/${row.id}`)
}

/* ---------- 列表数据 ---------- */
const deviceList = ref([])
const total = ref(0)
const loading = ref(false)

const fetchDevices = () => {
  loading.value = true
  const params = { page: currentPage.value, page_size: pageSize.value }
  if (filterForm.value.keyword) params.keyword = filterForm.value.keyword
  if (filterForm.value.deviceType) params.device_type = filterForm.value.deviceType
  if (filterForm.value.status) params.status = filterForm.value.status
  deviceAPI.list(params).then(res => {
    deviceList.value = (res.data.list || []).map(d => ({
      ...d,
      cpuUsage: Number(d.cpuUsage) || 0,
      memUsage: Number(d.memUsage) || 0
    }))
    total.value = res.data.total
  }).catch(() => {
    ElMessage.error('获取设备列表失败')
  }).finally(() => {
    loading.value = false
  })
}

onMounted(() => { fetchDevices() })
onActivated(() => { fetchDevices() })

/* ---------- 筛选 ---------- */
const filterForm = ref({
  keyword: '',
  deviceType: '',
  status: ''
})

/* ---------- 分页 ---------- */
const currentPage = ref(1)
const pageSize = ref(10)

/* ---------- Dialog ---------- */
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref(null)
const editingId = ref(null)

const defaultForm = {
  name: '',
  type: '',
  ip: '',
  port: 22,
  status: '在线',
  location: ''
}

const formData = ref({ ...defaultForm })

const formRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  ip: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '请输入正确的IP地址', trigger: 'blur' }
  ],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

/* ---------- 操作处理 ---------- */
const handleQuery = () => {
  currentPage.value = 1
  fetchDevices()
}

const handleAdd = () => {
  isEditing.value = false
  editingId.value = null
  formData.value = { ...defaultForm }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEditing.value = true
  editingId.value = row.id
  formData.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = (row) => {
  deviceAPI.delete(row.id).then(() => {
    ElMessage.success('删除成功')
    fetchDevices()
  }).catch(() => {
    ElMessage.error('删除失败')
  })
}

const handleSave = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  const action = isEditing.value
    ? deviceAPI.update(editingId.value, formData.value)
    : deviceAPI.create(formData.value)

  action.then(() => {
    ElMessage.success(isEditing.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    fetchDevices()
  }).catch(() => {
    ElMessage.error('操作失败')
  })
}

/* ---------- Helpers ---------- */
const typeTagType = (type) => {
  const map = { 路由器: 'primary', 交换机: 'success', 防火墙: 'warning', 服务器: 'danger' }
  return map[type] || 'info'
}

const typeIcon = (type) => {
  const icons = { 路由器: 'Monitor', 交换机: 'Connection', 防火墙: 'WarningFilled', 服务器: 'Cpu' }
  return icons[type] || 'Monitor'
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
</script>

<style scoped>
.devices-container {
  padding: 20px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.filter-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.table-card {
  border-radius: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
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

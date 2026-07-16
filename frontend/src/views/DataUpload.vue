<template>
  <div class="upload-container">
    <h2 class="page-title">数据上传</h2>

    <!-- 上传区域 -->
    <el-card class="upload-card" shadow="hover" v-loading="uploading" element-loading-text="正在解析文件...">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :show-file-list="false"
        accept=".csv,.xlsx,.xls,.txt"
        :on-change="handleFileChange"
        class="upload-area"
        :disabled="uploading"
      >
        <el-icon class="upload-icon" :size="48">
          <UploadFilled />
        </el-icon>
        <div class="upload-text">将文件拖拽至此处上传</div>
        <template #tip>
          <div class="upload-hint">
            <p>支持 CSV、Excel、TXT 格式</p>
            <p class="file-limit">单文件不超过 50MB</p>
          </div>
        </template>
      </el-upload>
    </el-card>

    <!-- 数据预览 -->
    <el-card v-if="uploadedFileName" class="preview-card" shadow="hover">
      <template #header>
        <div class="section-header">
          <span class="section-title">数据预览</span>
          <span class="file-name">当前文件：{{ uploadedFileName }}</span>
        </div>
      </template>

      <el-table :data="previewData" stripe style="width: 100%" max-height="360">
        <el-table-column prop="timestamp" label="时间戳" width="170" />
        <el-table-column prop="deviceName" label="设备名称" width="140" />
        <el-table-column prop="cpuUsage" label="CPU使用率" width="120">
          <template #default="{ row }">
            {{ row.cpuUsage }}%
          </template>
        </el-table-column>
        <el-table-column prop="memUsage" label="内存使用率" width="120">
          <template #default="{ row }">
            {{ row.memUsage }}%
          </template>
        </el-table-column>
        <el-table-column prop="netIn" label="网络流入" width="120">
          <template #default="{ row }">
            {{ row.netIn }} Mbps
          </template>
        </el-table-column>
        <el-table-column prop="netOut" label="网络流出" width="120">
          <template #default="{ row }">
            {{ row.netOut }} Mbps
          </template>
        </el-table-column>
        <el-table-column prop="lossRate" label="丢包率" width="100">
          <template #default="{ row }">
            <span :class="lossRateClass(row.lossRate)">{{ row.lossRate }}%</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 导入选项 -->
      <div class="import-section">
        <div class="import-options">
          <span class="import-label">导入方式：</span>
          <el-radio-group v-model="importMode">
            <el-radio value="append">追加到已有数据</el-radio>
            <el-radio value="overwrite">覆盖已有数据</el-radio>
          </el-radio-group>
        </div>
        <div class="import-actions">
          <el-button type="primary" @click="handleConfirmImport">确认导入</el-button>
          <el-button @click="handleCancelImport">取消</el-button>
        </div>
      </div>
    </el-card>

    <!-- 上传历史 -->
    <el-card class="history-card" shadow="hover">
      <template #header>
        <span class="section-title">上传历史</span>
      </template>
      <el-table :data="uploadHistory" stripe style="width: 100%">
        <el-table-column prop="fileName" label="文件名" min-width="160" />
        <el-table-column prop="uploadTime" label="上传时间" width="170" />
        <el-table-column prop="dataCount" label="数据量(条)" width="100" />
        <el-table-column prop="fileSize" label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.fileSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '成功' ? 'success' : 'danger'" size="small" effect="dark">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handlePreviewHistory(row)">
              预览
            </el-button>
            <el-button type="primary" size="small" link @click="handleDownloadFile(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 历史文件预览弹窗 -->
    <el-dialog v-model="historyPreviewVisible" title="历史文件预览" width="850px" destroy-on-close>
      <template v-if="historyPreviewData.length">
        <p class="preview-hint">文件：{{ historyPreviewFileName }}（仅显示前 20 行）</p>
        <el-table :data="historyPreviewData" stripe style="width: 100%" max-height="420">
          <el-table-column prop="timestamp" label="时间戳" width="170" />
          <el-table-column prop="deviceName" label="设备名称" width="140" />
          <el-table-column prop="cpuUsage" label="CPU使用率" width="110">
            <template #default="{ row }">{{ row.cpuUsage }}%</template>
          </el-table-column>
          <el-table-column prop="memUsage" label="内存使用率" width="110">
            <template #default="{ row }">{{ row.memUsage }}%</template>
          </el-table-column>
          <el-table-column prop="netIn" label="网络流入" width="100">
            <template #default="{ row }">{{ row.netIn }} Mbps</template>
          </el-table-column>
          <el-table-column prop="netOut" label="网络流出" width="100">
            <template #default="{ row }">{{ row.netOut }} Mbps</template>
          </el-table-column>
          <el-table-column prop="lossRate" label="丢包率" width="90">
            <template #default="{ row }">{{ row.lossRate }}%</template>
          </el-table-column>
        </el-table>
      </template>
      <el-empty v-else description="暂无预览数据" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { dataAPI } from '../api'
import { ElMessage } from 'element-plus'

/* ---------- 上传 ---------- */
const uploadRef = ref(null)
const uploadedFileName = ref('')
const currentFile = ref(null)
const uploading = ref(false)

const handleFileChange = (file) => {
  currentFile.value = file.raw || file
  uploadedFileName.value = file.name
  uploadForPreview()
}

/** 将文件上传到后端，获取真实解析预览 */
const uploadForPreview = async () => {
  const file = currentFile.value
  if (!file) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await dataAPI.upload(formData)
    previewData.value = res.data.preview || []
    ElMessage.success(`文件「${res.data.file_name}」解析成功，预览前 ${previewData.value.length} 行`)
  } catch (e) {
    ElMessage.error('文件解析失败，请检查文件格式是否正确')
    previewData.value = []
  } finally {
    uploading.value = false
  }
}

/* ---------- 预览数据 ---------- */
const previewData = ref([])

/* ---------- 导入选项 ---------- */
const importMode = ref('append')

const handleConfirmImport = () => {
  dataAPI.confirmImport({ mode: importMode.value }).then((res) => {
    ElMessage.success(res.message || (importMode.value === 'append' ? '数据已追加成功' : '数据已覆盖导入成功'))
    // 清空状态
    uploadedFileName.value = ''
    previewData.value = []
    currentFile.value = null
    // 刷新历史
    dataAPI.history().then(res => { uploadHistory.value = res.data }).catch(() => {})
  }).catch((err) => {
    ElMessage.error(err?.message || '导入失败，请重试')
  })
}

const handleCancelImport = () => {
  uploadedFileName.value = ''
  previewData.value = []
  currentFile.value = null
}

/* ---------- 丢包率样式 ---------- */
const lossRateClass = (rate) => {
  const r = Number(rate)
  if (r > 0.02) return 'loss-high'
  if (r > 0) return 'loss-mid'
  return 'loss-low'
}

/* ---------- 上传历史 ---------- */
const uploadHistory = ref([])

/* ---------- 历史文件预览 ---------- */
const historyPreviewVisible = ref(false)
const historyPreviewData = ref([])
const historyPreviewFileName = ref('')

const handlePreviewHistory = async (row) => {
  try {
    const res = await dataAPI.previewHistory(row.id)
    historyPreviewData.value = res.data.preview || []
    historyPreviewFileName.value = res.data.file_name || row.fileName
    historyPreviewVisible.value = true
  } catch (e) {
    ElMessage.error('预览失败：' + (e?.message || '请求异常'))
  }
}

const handleDownloadFile = async (row) => {
  try {
    const blob = await dataAPI.downloadFile(row.id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.fileName
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('文件下载成功')
  } catch (e) {
    ElMessage.error('下载失败：' + (e?.message || '请求异常'))
  }
}

const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const fetchData = () => {
  dataAPI.history().then(res => { uploadHistory.value = res.data }).catch(() => {})
}

onMounted(fetchData)
// For keep-alive:
onActivated(fetchData)
</script>

<style scoped>
.upload-container {
  padding: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
}

/* 上传卡片 */
.upload-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.upload-icon {
  margin-bottom: 16px;
  color: #409eff;
}

.upload-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-hint {
  text-align: center;
}

.upload-hint p {
  margin: 2px 0;
  font-size: 13px;
  color: #909399;
}

.file-limit {
  color: #c0c4cc !important;
}

/* 预览卡片 */
.preview-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.file-name {
  font-size: 13px;
  color: #909399;
}

.import-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.import-options {
  display: flex;
  align-items: center;
  gap: 12px;
}

.import-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.import-actions {
  display: flex;
  gap: 12px;
}

/* 历史卡片 */
.history-card {
  border-radius: 8px;
}

.preview-hint {
  font-size: 13px;
  color: #909399;
  margin: 0 0 12px 0;
}

/* 丢包率 */
.loss-low {
  color: #67c23a;
}

.loss-mid {
  color: #e6a23c;
}

.loss-high {
  color: #f56c6c;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>

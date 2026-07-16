<template>
  <div class="admin-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2 class="page-title">系统管理</h2>
    </div>

    <el-card class="admin-card" shadow="hover">
      <el-tabs v-model="activeTab">
        <!-- 标签页 1：用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="tab-header">
            <el-button type="primary" @click="openAddDialog">添加用户</el-button>
          </div>

          <el-table :data="userList" stripe style="width: 100%" v-loading="userLoading">
            <el-table-column prop="username" label="用户名" width="140" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column label="角色" width="140">
              <template #default="{ row }">
                <el-tag :color="roleColor(row.role)" effect="dark" size="small" style="color: #fff; border: none">
                  {{ row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.isEnabled" disabled />
              </template>
            </el-table-column>
            <el-table-column prop="registerTime" label="注册时间" width="170" />
            <el-table-column prop="lastLogin" label="最后登录" width="170" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button size="small" text type="danger" @click="handleDeleteUser(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="userPage"
              v-model:page-size="userPageSize"
              :total="userTotal"
              layout="prev, pager, next, total"
              @current-change="fetchUsers"
            />
          </div>
        </el-tab-pane>

        <!-- 标签页 2：操作日志 -->
        <el-tab-pane label="操作日志" name="logs">
          <div class="filter-row">
            <el-date-picker
              v-model="logDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
            <el-button type="primary" @click="handleQueryLogs">查询</el-button>
          </div>

          <el-table :data="logList" stripe style="width: 100%; margin-top: 16px" v-loading="logLoading">
            <el-table-column prop="createTime" label="操作时间" width="170" />
            <el-table-column prop="username" label="操作人" width="120" />
            <el-table-column label="操作类型" width="110">
              <template #default="{ row }">
                <el-tag :type="logTagType(row.actionType)" size="small" effect="dark">
                  {{ row.actionType }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="targetType" label="操作对象" width="140" />
            <el-table-column prop="ipAddress" label="IP地址" width="140" />
            <el-table-column prop="detail" label="操作详情" min-width="200" show-overflow-tooltip />
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="logPage"
              v-model:page-size="logPageSize"
              :total="logTotal"
              layout="prev, pager, next, total"
              @current-change="fetchLogs"
            />
          </div>
        </el-tab-pane>

        <!-- 标签页 3：系统配置 -->
        <el-tab-pane label="系统配置" name="config">
          <el-form :model="configForm" label-width="140px" style="max-width: 560px">
            <el-form-item label="系统名称">
              <el-input v-model="configForm.systemName" />
            </el-form-item>
            <el-form-item label="数据保留天数">
              <el-input-number v-model="configForm.retentionDays" :min="30" :max="365" />
            </el-form-item>
            <el-form-item label="告警检查间隔">
              <el-input-number v-model="configForm.alertInterval" :min="1" :max="60" />
              <span class="suffix-label">分钟</span>
            </el-form-item>
            <el-form-item label="日志级别">
              <el-select v-model="configForm.logLevel" style="width: 100%">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARN" value="WARN" />
                <el-option label="ERROR" value="ERROR" />
              </el-select>
            </el-form-item>
            <el-form-item label="大模型API地址">
              <el-input v-model="configForm.apiUrl" placeholder="https://api.example.com" />
            </el-form-item>
            <el-form-item label="大模型API密钥">
              <el-input v-model="configForm.apiKey" show-password placeholder="请输入API密钥" />
            </el-form-item>
            <el-form-item label="邮件通知开关">
              <el-switch v-model="configForm.emailNotify" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig">保存配置</el-button>
              <el-button @click="handleResetConfig">恢复默认</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 添加用户弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="添加用户"
      width="480px"
    >
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="运维工程师" value="operator" />
            <el-option label="普通用户" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveUser">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onActivated } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI, authAPI } from '../api'

// --- 标签页 ---
const activeTab = ref('users')

// ========== 标签页 1：用户管理 ==========
const userList = ref([])
const userTotal = ref(0)
const userLoading = ref(false)
const userPage = ref(1)
const userPageSize = ref(10)

const fetchUsers = async () => {
  userLoading.value = true
  try {
    const res = await adminAPI.users({ page: userPage.value, page_size: userPageSize.value })
    userList.value = res.data.list
    userTotal.value = res.data.total
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    userLoading.value = false
  }
}

const roleColor = (role) => {
  const map = {
    'admin': '#F56C6C',
    'operator': '#E6A23C',
    'viewer': '#67C23A'
  }
  return map[role] || '#909399'
}

// --- 用户对话框 ---
const dialogVisible = ref(false)

const userForm = ref({
  username: '',
  password: '',
  email: '',
  role: 'viewer'
})

const resetUserForm = () => {
  userForm.value = { username: '', password: '', email: '', role: 'viewer' }
}

const openAddDialog = () => {
  resetUserForm()
  dialogVisible.value = true
}

const handleSaveUser = async () => {
  try {
    await authAPI.register(userForm.value)
    ElMessage.success('用户添加成功')
    dialogVisible.value = false
    fetchUsers()
  } catch (err) {
    ElMessage.error(err.message || '添加失败')
  }
}

const handleDeleteUser = async (row) => {
  try {
    await adminAPI.deleteUser(row.id)
    ElMessage.success('用户已删除')
    fetchUsers()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ========== 标签页 2：操作日志 ==========
const logList = ref([])
const logTotal = ref(0)
const logLoading = ref(false)
const logDateRange = ref(null)
const logPage = ref(1)
const logPageSize = ref(10)

const fetchLogs = async () => {
  logLoading.value = true
  try {
    const res = await adminAPI.logs({ page: logPage.value, page_size: logPageSize.value })
    logList.value = res.data.list
    logTotal.value = res.data.total
  } catch {
    ElMessage.error('获取日志列表失败')
  } finally {
    logLoading.value = false
  }
}

const logTagType = (type) => {
  const map = {
    'login': 'primary',
    'create': 'success',
    'delete': 'danger',
    'update': 'warning',
    'export': 'info'
  }
  return map[type] || 'info'
}

const handleQueryLogs = () => {
  logPage.value = 1
  fetchLogs()
}

// ========== 标签页 3：系统配置 ==========
const configForm = ref({
  systemName: '全息网络洞察系统',
  retentionDays: 180,
  alertInterval: 5,
  logLevel: 'INFO',
  apiUrl: 'https://api.deepseek.com/v1',
  apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxx',
  emailNotify: true
})

const handleSaveConfig = () => {
  ElMessage.success('配置保存成功')
}

const handleResetConfig = () => {
  configForm.value = {
    systemName: '全息网络洞察系统',
    retentionDays: 180,
    alertInterval: 5,
    logLevel: 'INFO',
    apiUrl: '',
    apiKey: '',
    emailNotify: false
  }
  ElMessage.success('已恢复默认配置')
}

// 初始化加载
onMounted(() => {
  fetchUsers()
  fetchLogs()
})

onActivated(() => {
  fetchUsers()
  fetchLogs()
})
</script>

<style scoped>
.admin-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  margin: 0;
}

.admin-card {
  border-radius: 8px;
}

.tab-header {
  margin-bottom: 16px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.suffix-label {
  margin-left: 8px;
  font-size: 14px;
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

:deep(.el-table th.el-table__cell) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>

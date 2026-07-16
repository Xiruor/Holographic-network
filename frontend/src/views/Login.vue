<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="40" color="#409EFF"><Monitor /></el-icon>
        </div>
        <h1 class="system-title">全息网络洞察系统</h1>
        <p class="system-subtitle">基于AI大模型的智能监控平台</p>
      </div>

      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>

        <div class="register-link">
          <span>还没有账号？</span>
          <el-link type="primary" :underline="'never'">注册账号</el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { authAPI } from '../api'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请填写完整的登录信息')
    return
  }

  loading.value = true
  try {
    const res = await authAPI.login({
      username: loginForm.username,
      password: loginForm.password
    })
    sessionStorage.setItem('token', res.data.token)
    sessionStorage.setItem('userRole', res.data.user.role)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (err) {
    const msg = err.message || err.msg || '登录失败，请检查用户名和密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a2a6c, #2d4373, #4a6fa5);
}

.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.25);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  margin-bottom: 12px;
}

.system-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.system-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
  letter-spacing: 1px;
}

.login-form {
  margin-top: 8px;
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: #909399;
}
</style>

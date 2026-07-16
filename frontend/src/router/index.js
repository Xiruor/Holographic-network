import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Devices from '../views/Devices.vue'
import DataUpload from '../views/DataUpload.vue'
import DataAnalysis from '../views/DataAnalysis.vue'
import AiAnalysis from '../views/AiAnalysis.vue'
import Visualization from '../views/Visualization.vue'
import Alerts from '../views/Alerts.vue'
import Reports from '../views/Reports.vue'
import Admin from '../views/Admin.vue'
import AlertDetail from '../views/AlertDetail.vue'
import DeviceDetail from '../views/DeviceDetail.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: Devices,
        meta: { title: '设备管理', icon: 'Monitor' }
      },
      {
        path: 'data/upload',
        name: 'DataUpload',
        component: DataUpload,
        meta: { title: '数据上传', icon: 'Upload' }
      },
      {
        path: 'analysis',
        name: 'DataAnalysis',
        component: DataAnalysis,
        meta: { title: '数据分析', icon: 'DataAnalysis' }
      },
      {
        path: 'analysis/ai',
        name: 'AiAnalysis',
        component: AiAnalysis,
        meta: { title: 'AI 分析', icon: 'Cpu' }
      },
      {
        path: 'visualization',
        name: 'Visualization',
        component: Visualization,
        meta: { title: '可视化看板', icon: 'DataBoard' }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: Alerts,
        meta: { title: '告警中心', icon: 'WarningFilled' }
      },
      {
        path: 'alerts/:id',
        name: 'AlertDetail',
        component: AlertDetail,
        meta: { title: '告警详情', hidden: true }
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetail',
        component: DeviceDetail,
        meta: { title: '设备详情', hidden: true }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: Reports,
        meta: { title: '报表中心', icon: 'Document' }
      },
      {
        path: 'admin',
        name: 'Admin',
        component: Admin,
        meta: { title: '系统管理', icon: 'Setting', requireAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 简单的登录守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = sessionStorage.getItem('token')
  if (to.meta.requiresAuth && !isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && isLoggedIn) {
    next('/dashboard')
  } else if (to.meta.requireAdmin && sessionStorage.getItem('userRole') !== 'admin') {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

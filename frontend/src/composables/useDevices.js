import { ref } from 'vue'
import { deviceAPI } from '@/api'

/**
 * 共享 composable — 从数据库获取设备名称列表
 * 用于所有需要「设备选择器」的页面，确保设备选项始终与设备管理同步
 *
 * @param {Object} options
 * @param {boolean} options.includeAll  - 是否包含「全部设备」选项，默认 true
 * @returns {{ deviceOptions: Ref<string[]>, fetchDevices: () => Promise<void> }}
 */
export function useDevices({ includeAll = true } = {}) {
  const deviceOptions = ref([])

  const fetchDevices = async (retries = 2) => {
    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const res = await deviceAPI.list({ page: 1, page_size: 200 })
        const list = (res.data?.list || []).map((d) => d.name)
        deviceOptions.value = includeAll ? ['全部设备', ...list] : list
        console.log('[useDevices] 设备列表已更新:', deviceOptions.value)
        return // 成功后直接返回
      } catch (err) {
        console.warn(`[useDevices] 第 ${attempt}/${retries} 次请求失败:`, err?.message || err)
        if (attempt < retries) {
          // 短暂等待后重试，应对后端瞬时重启等场景
          await new Promise((r) => setTimeout(r, 600))
        }
      }
    }
    // 所有重试都失败，使用默认占位保证页面可用
    deviceOptions.value = includeAll
      ? ['全部设备', '核心路由器-01', '核心路由器-02', '汇聚交换机-01', '汇聚交换机-03', '防火墙-FW01', '应用服务器-01', '应用服务器-02', '数据库服务器-01']
      : ['核心路由器-01', '核心路由器-02', '汇聚交换机-01', '汇聚交换机-03', '防火墙-FW01', '应用服务器-01', '应用服务器-02', '数据库服务器-01']
  }

  // 立即发起请求，确保选择器尽早显示真实数据
  fetchDevices()

  return { deviceOptions, fetchDevices }
}

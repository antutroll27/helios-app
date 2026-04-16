import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/pages/HomePage.vue') },
    { path: '/settings', component: () => import('@/pages/SettingsPage.vue') },
    { path: '/biometrics', name: 'biometrics', component: () => import('@/pages/BiometricsPage.vue') },
    { path: '/lab', component: () => import('@/pages/LabPage.vue') },
    { path: '/auth', name: 'auth', component: () => import('@/pages/AuthPage.vue') },
  ]
})

export default router

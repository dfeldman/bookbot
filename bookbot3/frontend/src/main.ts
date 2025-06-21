import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import Welcome from './views/Welcome.vue'
import BookWizard from './views/BookWizard.vue'
import Dashboard from './views/Dashboard.vue'
import BookViewer from './views/BookViewer.vue'
import ChunkEditor from './views/ChunkEditor.vue'
import JobsViewer from './views/JobsViewer.vue'
import JobLogsViewer from './views/JobLogsViewer.vue'
import JobDetailsViewer from './views/JobDetailsViewer.vue'
import EditorDemo from './views/EditorDemo.vue'

import './style.css'

const routes = [
  { path: '/', name: 'Welcome', component: Welcome },
  { path: '/wizard', name: 'BookWizard', component: BookWizard },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard },
  { path: '/books/:bookId', name: 'BookViewer', component: BookViewer },
  { path: '/books/:bookId/chunks/:chunkId/edit', name: 'ChunkEditor', component: ChunkEditor, props: true },
  { path: '/jobs', name: 'JobsViewer', component: JobsViewer },
  { path: '/jobs/:jobId/logs', name: 'JobLogsViewer', component: JobLogsViewer, props: true },
  { path: '/jobs/:jobId', name: 'JobDetailsViewer', component: JobDetailsViewer, props: true },
  { path: '/editor-demo', name: 'EditorDemo', component: EditorDemo }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')

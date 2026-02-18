'use client'

import { useState, useEffect } from 'react'
import { Activity, Cpu, GitBranch, Zap, Terminal, Code2, Users, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface AgentStatus {
  id: string
  name: string
  status: 'active' | 'idle' | 'working'
  tasksCompleted: number
  currentTask?: string
}

interface SystemMetrics {
  epoch: number
  tasksCompleted: number
  activeAgents: number
  health: number
}

export default function MissionControl() {
  const [agents, setAgents] = useState<AgentStatus[]>([
    { id: 'chief_architect', name: 'Chief Architect', status: 'active', tasksCompleted: 12, currentTask: 'Reviewing system architecture' },
    { id: 'frontend_lead', name: 'Frontend Lead', status: 'working', tasksCompleted: 8, currentTask: 'Building dashboard components' },
    { id: 'backend_lead', name: 'Backend Lead', status: 'working', tasksCompleted: 15, currentTask: 'Implementing API endpoints' },
    { id: 'devsecops', name: 'DevSecOps Engineer', status: 'idle', tasksCompleted: 6 },
    { id: 'qa_engineer', name: 'QA Engineer', status: 'active', tasksCompleted: 10, currentTask: 'Running test suite' },
  ])

  const [metrics, setMetrics] = useState<SystemMetrics>({
    epoch: 1,
    tasksCompleted: 51,
    activeAgents: 5,
    health: 98.5,
  })

  const getStatusColor = (status: AgentStatus['status']) => {
    switch (status) {
      case 'active': return 'text-green-500'
      case 'working': return 'text-blue-500'
      case 'idle': return 'text-gray-500'
    }
  }

  const getStatusIcon = (status: AgentStatus['status']) => {
    switch (status) {
      case 'active': return <Activity className="w-4 h-4" />
      case 'working': return <Cpu className="w-4 h-4 animate-pulse" />
      case 'idle': return <Terminal className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                <Zap className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Genesis Mission Control</h1>
                <p className="text-sm text-gray-400">Autonomous Software Factory</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-sm text-gray-400">System Health</div>
                <div className="text-xl font-bold text-green-400">{metrics.health}%</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">Epoch</div>
                <div className="text-xl font-bold">{metrics.epoch}</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-2">
              <Users className="w-8 h-8 text-blue-400" />
              <span className="text-3xl font-bold">{metrics.activeAgents}</span>
            </div>
            <div className="text-sm text-gray-400">Active Agents</div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-2">
              <CheckCircle2 className="w-8 h-8 text-green-400" />
              <span className="text-3xl font-bold">{metrics.tasksCompleted}</span>
            </div>
            <div className="text-sm text-gray-400">Tasks Completed</div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-2">
              <GitBranch className="w-8 h-8 text-purple-400" />
              <span className="text-3xl font-bold">7</span>
            </div>
            <div className="text-sm text-gray-400">Active PRs</div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
          >
            <div className="flex items-center justify-between mb-2">
              <Code2 className="w-8 h-8 text-yellow-400" />
              <span className="text-3xl font-bold">12.5K</span>
            </div>
            <div className="text-sm text-gray-400">Lines Generated</div>
          </motion.div>
        </div>

        {/* Agent Status */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 mb-8">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Users className="w-6 h-6" />
            Agent Status
          </h2>
          <div className="space-y-4">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/5 rounded-lg p-4 border border-white/10 hover:bg-white/10 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`${getStatusColor(agent.status)}`}>
                      {getStatusIcon(agent.status)}
                    </div>
                    <div>
                      <div className="font-semibold">{agent.name}</div>
                      <div className="text-sm text-gray-400">
                        {agent.currentTask || 'Waiting for tasks...'}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Tasks Completed</div>
                    <div className="text-lg font-bold">{agent.tasksCompleted}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Philosophy Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-lg rounded-xl p-6 border border-white/20 text-center"
        >
          <div className="text-sm text-gray-400 mb-2">System Philosophy</div>
          <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Zero Human Hands - Autonomous Recursive Self-Improvement
          </div>
        </motion.div>
      </main>
    </div>
  )
}

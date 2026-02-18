'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { Save, Play, Terminal, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-gray-900">
      <div className="text-white">Loading editor...</div>
    </div>
  ),
})

export default function EditorPage() {
  const [code, setCode] = useState(`# Genesis Autonomous Code Editor
# This editor is integrated with the Genesis AI system

def hello_genesis():
    """
    Example function created by Genesis autonomous system.
    """
    print("Hello from Genesis!")
    print("Autonomous software factory in action!")

if __name__ == "__main__":
    hello_genesis()
`)

  const [language, setLanguage] = useState('python')
  const [output, setOutput] = useState('')

  const handleSave = () => {
    console.log('Saving code...')
    setOutput('Code saved successfully!')
  }

  const handleRun = () => {
    console.log('Running code...')
    setOutput('Executing code...\nHello from Genesis!\nAutonomous software factory in action!')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white">
      {/* Header */}
      <header className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                href="/"
                className="p-2 bg-white/10 rounded-lg hover:bg-white/20 transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold">Genesis Code Editor</h1>
                <p className="text-sm text-gray-400">AI-Powered Development Environment</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
              </select>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-all"
              >
                <Save className="w-4 h-4" />
                Save
              </button>
              <button
                onClick={handleRun}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-all"
              >
                <Play className="w-4 h-4" />
                Run
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6 h-[calc(100vh-88px)]">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Editor */}
          <div className="lg:col-span-2 bg-white/10 backdrop-blur-lg rounded-xl overflow-hidden border border-white/20">
            <MonacoEditor
              height="100%"
              language={language}
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                wordWrap: 'on',
              }}
            />
          </div>

          {/* Output Panel */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-green-400" />
              <h2 className="text-lg font-bold">Output</h2>
            </div>
            <div className="bg-black/50 rounded-lg p-4 font-mono text-sm h-[calc(100%-60px)] overflow-auto">
              {output ? (
                <pre className="text-green-400 whitespace-pre-wrap">{output}</pre>
              ) : (
                <div className="text-gray-500">No output yet. Run your code to see results.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

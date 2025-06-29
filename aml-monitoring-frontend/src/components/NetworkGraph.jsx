import { useState, useEffect, useRef } from 'react'

const NetworkGraph = ({ data, width = 800, height = 600 }) => {
  const svgRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)

  // Простая физическая симуляция для расположения узлов
  const simulateLayout = (nodes, edges) => {
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) / 3

    // Размещаем узлы по кругу с некоторой случайностью
    return nodes.map((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI
      const r = radius + (Math.random() - 0.5) * 100
      
      return {
        ...node,
        x: centerX + Math.cos(angle) * r,
        y: centerY + Math.sin(angle) * r
      }
    })
  }

  const formatAmount = (amount) => {
    if (amount >= 1000000000) {
      return `${(amount / 1000000000).toFixed(1)}B ₸`
    } else if (amount >= 1000000) {
      return `${(amount / 1000000).toFixed(1)}M ₸`
    } else {
      return `${(amount / 1000).toFixed(0)}K ₸`
    }
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Нет данных для отображения</h3>
          <p className="mt-1 text-sm text-gray-500">Попробуйте изменить параметры фильтрации</p>
        </div>
      </div>
    )
  }

  const layoutNodes = simulateLayout(data.nodes, data.edges)

  return (
    <div className="relative">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="border border-gray-200 rounded-lg bg-white"
        viewBox={`0 0 ${width} ${height}`}
      >
        {/* Определения для стрелки */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#6b7280"
            />
          </marker>
          <marker
            id="arrowhead-suspicious"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#ef4444"
            />
          </marker>
        </defs>

        {/* Связи */}
        {data.edges.map((edge, index) => {
          const sourceNode = layoutNodes.find(n => n.id === edge.source)
          const targetNode = layoutNodes.find(n => n.id === edge.target)
          
          if (!sourceNode || !targetNode) return null

          const isSuspicious = edge.is_suspicious
          const strokeColor = isSuspicious ? '#ef4444' : '#6b7280'
          const strokeWidth = Math.max(1, edge.weight || 1)

          return (
            <g key={`edge-${index}`}>
              <line
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                opacity={0.6}
                markerEnd={isSuspicious ? "url(#arrowhead-suspicious)" : "url(#arrowhead)"}
              />
              {/* Подпись связи при наведении */}
              {(hoveredNode === edge.source || hoveredNode === edge.target) && (
                <text
                  x={(sourceNode.x + targetNode.x) / 2}
                  y={(sourceNode.y + targetNode.y) / 2}
                  textAnchor="middle"
                  className="text-xs fill-gray-700"
                  dominantBaseline="central"
                >
                  {formatAmount(edge.total_amount)}
                </text>
              )}
            </g>
          )
        })}

        {/* Узлы */}
        {layoutNodes.map((node) => {
          const isSelected = selectedNode === node.id
          const isHovered = hoveredNode === node.id
          const radius = node.size || 20

          return (
            <g key={`node-${node.id}`}>
              {/* Тень узла */}
              <circle
                cx={node.x + 2}
                cy={node.y + 2}
                r={radius}
                fill="rgba(0,0,0,0.1)"
              />
              
              {/* Основной узел */}
              <circle
                cx={node.x}
                cy={node.y}
                r={radius}
                fill={node.color || '#3b82f6'}
                stroke={isSelected ? '#1f2937' : '#ffffff'}
                strokeWidth={isSelected ? 3 : 2}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => setSelectedNode(isSelected ? null : node.id)}
                className="transition-all duration-200 hover:opacity-80"
              />

              {/* Текст внутри узла */}
              <text
                x={node.x}
                y={node.y}
                textAnchor="middle"
                dominantBaseline="central"
                className="text-xs font-bold fill-white pointer-events-none"
              >
                {node.centrality || ''}
              </text>

              {/* Подпись узла */}
              <text
                x={node.x}
                y={node.y + radius + 15}
                textAnchor="middle"
                className="text-xs fill-gray-700 pointer-events-none"
              >
                {node.name && node.name.length > 15 ? 
                  `${node.name.substring(0, 15)}...` : 
                  node.name || node.id
                }
              </text>

              {/* Детальная информация при наведении */}
              {isHovered && (
                <g>
                  <rect
                    x={node.x + radius + 10}
                    y={node.y - 30}
                    width="200"
                    height="60"
                    fill="white"
                    stroke="#d1d5db"
                    strokeWidth="1"
                    rx="4"
                  />
                  <text x={node.x + radius + 15} y={node.y - 15} className="text-xs font-semibold fill-gray-900">
                    {node.name || node.id}
                  </text>
                  <text x={node.x + radius + 15} y={node.y} className="text-xs fill-gray-600">
                    Транзакций: {formatNumber(node.total_transactions)}
                  </text>
                  <text x={node.x + radius + 15} y={node.y + 12} className="text-xs fill-gray-600">
                    Объем: {formatAmount(node.total_volume)}
                  </text>
                  <text x={node.x + radius + 15} y={node.y + 24} className="text-xs fill-gray-600">
                    Риск: {(node.risk_score || 0).toFixed(1)}
                  </text>
                </g>
              )}
            </g>
          )
        })}
      </svg>

      {/* Легенда */}
      <div className="absolute top-4 right-4 bg-white p-4 rounded-lg shadow-lg border">
        <h4 className="text-sm font-semibold text-gray-900 mb-2">Легенда</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span>Высокий риск (≥7.0)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span>Средний риск (4.0-7.0)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span>Низкий риск (2.0-4.0)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span>Минимальный риск (&lt;2.0)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-6 h-1 bg-red-500"></div>
            <span>Подозрительные связи</span>
          </div>
        </div>
      </div>

      {/* Информация о выбранном узле */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg border max-w-sm">
          {(() => {
            const node = layoutNodes.find(n => n.id === selectedNode)
            if (!node) return null

            const connections = data.edges.filter(e => 
              e.source === selectedNode || e.target === selectedNode
            )

            return (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Детали клиента
                </h4>
                <div className="space-y-1 text-xs text-gray-600">
                  <p><span className="font-medium">ID:</span> {node.id}</p>
                  <p><span className="font-medium">Имя:</span> {node.name}</p>
                  <p><span className="font-medium">Транзакций:</span> {formatNumber(node.total_transactions)}</p>
                  <p><span className="font-medium">Общий объем:</span> {formatAmount(node.total_volume)}</p>
                  <p><span className="font-medium">Риск-скор:</span> {(node.risk_score || 0).toFixed(2)}</p>
                  <p><span className="font-medium">Связей:</span> {connections.length}</p>
                  <p><span className="font-medium">Центральность:</span> {node.centrality}</p>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                >
                  Закрыть
                </button>
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}

export default NetworkGraph
const PieChart = ({ data, size = 200 }) => {
  // Подготавливаем данные
  const total = data.reduce((sum, item) => sum + item.value, 0)
  if (total === 0) return null

  // Рассчитываем углы для каждого сегмента
  let currentAngle = -90 // Начинаем с верха
  const segments = data.map((item) => {
    const percentage = (item.value / total) * 100
    const angle = (percentage / 100) * 360
    const startAngle = currentAngle
    currentAngle += angle
    
    return {
      ...item,
      percentage,
      startAngle,
      endAngle: currentAngle
    }
  })

  const radius = size / 2 - 10
  const centerX = size / 2
  const centerY = size / 2

  // Функция для создания пути сегмента
  const createPath = (segment) => {
    const startAngleRad = (segment.startAngle * Math.PI) / 180
    const endAngleRad = (segment.endAngle * Math.PI) / 180
    
    const x1 = centerX + radius * Math.cos(startAngleRad)
    const y1 = centerY + radius * Math.sin(startAngleRad)
    const x2 = centerX + radius * Math.cos(endAngleRad)
    const y2 = centerY + radius * Math.sin(endAngleRad)
    
    const largeArcFlag = segment.percentage > 50 ? 1 : 0
    
    return `
      M ${centerX} ${centerY}
      L ${x1} ${y1}
      A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
      Z
    `
  }

  return (
    <div className="flex items-center space-x-6">
      {/* Диаграмма */}
      <svg width={size} height={size} className="transform -rotate-0">
        {segments.map((segment, index) => (
          <g key={index}>
            <path
              d={createPath(segment)}
              fill={segment.color}
              stroke="white"
              strokeWidth="2"
              className="hover:opacity-80 transition-opacity cursor-pointer"
            />
            {/* Метка с процентом для больших сегментов */}
            {segment.percentage > 10 && (
              <text
                x={centerX + (radius * 0.7) * Math.cos(((segment.startAngle + segment.endAngle) / 2) * Math.PI / 180)}
                y={centerY + (radius * 0.7) * Math.sin(((segment.startAngle + segment.endAngle) / 2) * Math.PI / 180)}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-white text-sm font-semibold pointer-events-none"
              >
                {segment.percentage.toFixed(0)}%
              </text>
            )}
          </g>
        ))}
      </svg>

      {/* Легенда */}
      <div className="space-y-2">
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-4 h-4 rounded"
              style={{ backgroundColor: segment.color }}
            />
            <span className="text-sm text-gray-700">{segment.label}</span>
            <span className="text-sm text-gray-500">({segment.value})</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default PieChart
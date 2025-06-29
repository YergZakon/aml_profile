const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');

// Цвета для консоли
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

console.log(`${colors.blue}====================================================`);
console.log(`  🚀 АФМ РК - Единый AML Пайплайн`);
console.log(`====================================================${colors.reset}\n`);

// Пути
const backendPath = path.join(__dirname, 'aml-backend');
const frontendPath = path.join(__dirname, 'aml-monitoring-frontend');

function checkProjectStructure() {
  console.log(`${colors.yellow}Проверка структуры проекта...${colors.reset}`);
  
  if (!fs.existsSync(backendPath)) {
    console.error(`${colors.red}❌ Папка aml-backend не найдена!${colors.reset}`);
    process.exit(1);
  }
  
  const unifiedPipelinePath = path.join(backendPath, 'unified_aml_pipeline.py');
  if (!fs.existsSync(unifiedPipelinePath)) {
    console.error(`${colors.red}❌ Файл unified_aml_pipeline.py не найден!${colors.reset}`);
    process.exit(1);
  }
  
  console.log(`${colors.green}✅ Структура проекта корректна!${colors.reset}\n`);
}

function getPythonCommand() {
  let pythonCmd;
  if (os.platform() === 'win32') {
    pythonCmd = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
  } else {
    pythonCmd = path.join(backendPath, 'venv', 'bin', 'python');
  }

  if (!fs.existsSync(pythonCmd)) {
    console.error(`${colors.red}❌ Python не найден в venv!${colors.reset}`);
    console.error(`Создайте виртуальное окружение:`);
    console.error(`  cd aml-backend && python -m venv venv`);
    process.exit(1);
  }

  return pythonCmd;
}

function checkUploadsDirectory() {
  const uploadsPath = path.join(backendPath, 'uploads');
  
  if (!fs.existsSync(uploadsPath)) {
    console.log(`${colors.yellow}⚠️ Папка uploads не найдена, создаем...${colors.reset}`);
    fs.mkdirSync(uploadsPath, { recursive: true });
  }
  
  const jsonFiles = fs.readdirSync(uploadsPath).filter(file => file.endsWith('.json'));
  
  if (jsonFiles.length === 0) {
    console.log(`${colors.yellow}⚠️ JSON файлы не найдены в папке uploads${colors.reset}`);
    console.log(`${colors.cyan}💡 Поместите JSON файлы АФМ в папку aml-backend/uploads/${colors.reset}`);
    return false;
  }
  
  console.log(`${colors.green}✅ Найдено JSON файлов: ${jsonFiles.length}${colors.reset}`);
  jsonFiles.forEach(file => {
    const filePath = path.join(uploadsPath, file);
    const stats = fs.statSync(filePath);
    const sizeMB = (stats.size / (1024 * 1024)).toFixed(1);
    console.log(`   📄 ${file} (${sizeMB} MB)`);
  });
  
  return true;
}

function startBackend(pythonCmd) {
  return new Promise((resolve, reject) => {
    console.log(`${colors.green}🔧 Запуск Backend сервера...${colors.reset}`);
    
    const backend = spawn(pythonCmd, ['app.py'], {
      cwd: backendPath,
      stdio: 'inherit',
      shell: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    backend.on('error', (err) => {
      console.error(`${colors.red}❌ Ошибка Backend:${colors.reset}`, err.message);
      reject(err);
    });

    setTimeout(() => resolve(backend), 3000);
  });
}

function startFrontend() {
  return new Promise((resolve, reject) => {
    const npmCmd = os.platform() === 'win32' ? 'npm.cmd' : 'npm';
    
    console.log(`${colors.green}🎨 Запуск Frontend сервера...${colors.reset}`);
    
    const frontend = spawn(npmCmd, ['run', 'dev'], {
      cwd: frontendPath,
      stdio: 'inherit',
      shell: true
    });

    frontend.on('error', (err) => {
      console.error(`${colors.red}❌ Ошибка Frontend:${colors.reset}`, err.message);
      reject(err);
    });

    setTimeout(() => resolve(frontend), 2000);
  });
}

function runUnifiedPipeline(pythonCmd, workers = require('os').cpus().length) {
  return new Promise((resolve, reject) => {
    console.log(`${colors.magenta}🔍 Запуск единого AML пайплайна...${colors.reset}`);
    console.log(`👥 Воркеров: ${workers}`);
    console.log(`📦 Директория: uploads`);
    console.log(`⚠️ Порог риска: 3.0\n`);
    
    const args = [
      'unified_aml_pipeline.py',
      '--json-dir', 'uploads',
      '--workers', workers.toString(),
      '--batch-size', '1000',
      '--risk-threshold', '3.0'
    ];
    
    const pipeline = spawn(pythonCmd, args, {
      cwd: backendPath,
      stdio: 'inherit',
      shell: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    pipeline.on('error', (err) => {
      console.error(`${colors.red}❌ Ошибка пайплайна:${colors.reset}`, err.message);
      reject(err);
    });

    pipeline.on('exit', (code) => {
      if (code === 0) {
        console.log(`${colors.green}🎉 Единый AML пайплайн завершен успешно!${colors.reset}\n`);
        resolve();
      } else {
        console.error(`${colors.red}❌ Пайплайн завершился с ошибкой (код ${code})${colors.reset}\n`);
        reject(new Error(`Pipeline exited with code ${code}`));
      }
    });
  });
}

function setupCleanup(processes) {
  const cleanup = () => {
    console.log(`\n${colors.yellow}Остановка серверов...${colors.reset}`);
    
    processes.forEach(proc => {
      if (proc && proc.pid) {
        if (os.platform() === 'win32') {
          try {
            spawn('taskkill', ['/pid', proc.pid, '/f', '/t'], { shell: true });
          } catch (e) {
            proc.kill();
          }
        } else {
          try {
            process.kill(-proc.pid, 'SIGTERM');
          } catch (e) {
            proc.kill('SIGTERM');
          }
        }
      }
    });
    
    setTimeout(() => {
      console.log(`${colors.green}✅ Серверы остановлены${colors.reset}`);
      process.exit(0);
    }, 1000);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  
  return cleanup;
}

function showSystemInfo() {
  setTimeout(() => {
    console.log(`\n${colors.blue}====================================================`);
    console.log(`  ${colors.green}✅ Система успешно запущена!${colors.reset}`);
    console.log(`${colors.blue}====================================================${colors.reset}`);
    console.log(`  Backend API:   ${colors.green}http://localhost:8000/api/${colors.reset}`);
    console.log(`  Frontend:      ${colors.green}http://localhost:3000${colors.reset}`);
    console.log(`  Единый пайплайн: ${colors.cyan}Готов к обработке${colors.reset}`);
    console.log(`${colors.blue}====================================================${colors.reset}\n`);
    console.log(`${colors.yellow}Нажмите Ctrl+C для остановки всех серверов${colors.reset}`);
  }, 2000);
}

// Главная функция
async function main() {
  try {
    // Проверки
    checkProjectStructure();
    const pythonCmd = getPythonCommand();
    
    // Проверяем наличие JSON файлов
    const hasJsonFiles = checkUploadsDirectory();
    
    if (!hasJsonFiles) {
      console.log(`${colors.yellow}💡 Запускаем только веб-интерфейс${colors.reset}\n`);
      
      // Запуск только Backend + Frontend
      const backend = await startBackend(pythonCmd);
      const frontend = await startFrontend();
      
      setupCleanup([backend, frontend]);
      showSystemInfo();
      
    } else {
      console.log(`${colors.cyan}🚀 Режим: Полная система + AML анализ${colors.reset}\n`);
      
      // Запуск Backend + Frontend
      const backend = await startBackend(pythonCmd);
      const frontend = await startFrontend();
      
      // Запуск единого пайплайна через 5 секунд
      setTimeout(async () => {
        try {
          await runUnifiedPipeline(pythonCmd);
          console.log(`${colors.green}🎉 Система полностью готова к работе!${colors.reset}\n`);
        } catch (amlErr) {
          console.error(`${colors.yellow}⚠️ Система запущена, но AML анализ не удался: ${amlErr.message}${colors.reset}`);
        }
      }, 5000);
      
      setupCleanup([backend, frontend]);
      showSystemInfo();
    }
    
  } catch (error) {
    console.error(`${colors.red}❌ Критическая ошибка:${colors.reset}`, error.message);
    process.exit(1);
  }
}

// Запуск
main();
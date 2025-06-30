const { spawn } = require('child_process');
const path = require('path');
const os = require('os');
const fs = require('fs');
const readline = require('readline');

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
console.log(`  АФМ РК - Система мониторинга транзакций + AML`);
console.log(`====================================================${colors.reset}\n`);

// Правильные имена папок
const backendPath = path.join(__dirname, 'aml-backend');
const frontendPath = path.join(__dirname, 'aml-monitoring-frontend');

// Функция для создания интерфейса readline
function createInterface() {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

// Функция для отображения меню
function showMenu() {
  console.log(`${colors.cyan}Выберите режим запуска:${colors.reset}`);
  console.log(`${colors.green}1.${colors.reset} 🚀 Полная система (Backend + Frontend)`);
  console.log(`${colors.green}2.${colors.reset} 🔍 Система + AML-анализ (рекомендуется)`);
  console.log(`${colors.green}3.${colors.reset} ⚡ Только AML-анализ (быстрый)`);
  console.log(`${colors.green}4.${colors.reset} 🧪 AML тестирование (100 клиентов)`);
  console.log(`${colors.green}5.${colors.reset} 🎯 AML высокого риска (>5)`);
  console.log(`${colors.green}6.${colors.reset} 📂 JSON файлы АФМ (мультипроцессинг)`);
  console.log(`${colors.green}7.${colors.reset} 🔄 Гибридный анализ (JSON + БД)`);
  console.log(`${colors.green}8.${colors.reset} 🔧 Оптимизация базы данных`);
  console.log(`${colors.green}9.${colors.reset} 📊 Сравнение производительности`);
  console.log();
}

// Функция проверки структуры проекта
function checkProjectStructure() {
  console.log(`${colors.yellow}Проверка структуры проекта...${colors.reset}`);
  console.log(`Текущая директория: ${__dirname}`);
  console.log(`Backend путь: ${backendPath}`);
  console.log(`Frontend путь: ${frontendPath}`);

  // Проверяем наличие папок
  if (!fs.existsSync(backendPath)) {
    console.error(`${colors.red}[ОШИБКА] Папка aml-backend не найдена!${colors.reset}`);
    console.error(`Ожидаемый путь: ${backendPath}`);
    process.exit(1);
  }

  if (!fs.existsSync(frontendPath)) {
    console.error(`${colors.red}[ОШИБКА] Папка aml-monitoring-frontend не найдена!${colors.reset}`);
    console.error(`Ожидаемый путь: ${frontendPath}`);
    process.exit(1);
  }

  // Проверяем наличие файлов
  const appPyPath = path.join(backendPath, 'app.py');
  if (!fs.existsSync(appPyPath)) {
    console.error(`${colors.red}[ОШИБКА] Файл app.py не найден!${colors.reset}`);
    process.exit(1);
  }

  const amlPipelinePath = path.join(backendPath, 'aml_pipeline.py');
  if (!fs.existsSync(amlPipelinePath)) {
    console.error(`${colors.red}[ОШИБКА] Файл aml_pipeline.py не найден!${colors.reset}`);
    console.error(`${colors.yellow}Запустите: npm run aml:optimize для создания файлов${colors.reset}`);
    process.exit(1);
  }

  console.log(`${colors.green}✓ Структура проекта корректна!${colors.reset}\n`);
}

// Функция определения команды Python
function getPythonCommand() {
  let pythonCmd;
  if (os.platform() === 'win32') {
    pythonCmd = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
  } else {
    pythonCmd = path.join(backendPath, 'venv', 'bin', 'python');
  }

  if (!fs.existsSync(pythonCmd)) {
    console.error(`${colors.red}[ОШИБКА] Python не найден в venv!${colors.reset}`);
    console.error(`Создайте виртуальное окружение:`);
    console.error(`  cd aml-backend && python -m venv venv`);
    process.exit(1);
  }

  return pythonCmd;
}

// Функция запуска Backend
function startBackend(pythonCmd) {
  return new Promise((resolve, reject) => {
    console.log(`${colors.green}[1/2] Запуск Backend сервера...${colors.reset}`);
    console.log(`Команда: ${pythonCmd} app.py`);
    console.log(`Директория: ${backendPath}\n`);

    const backend = spawn(pythonCmd, ['app.py'], {
      cwd: backendPath,
      stdio: 'inherit',
      shell: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    backend.on('error', (err) => {
      console.error(`${colors.red}[ОШИБКА] Backend:${colors.reset}`, err.message);
      reject(err);
    });

    // Даем время на запуск
    setTimeout(() => resolve(backend), 3000);
  });
}

// Функция запуска Frontend
function startFrontend() {
  return new Promise((resolve, reject) => {
    const npmCmd = os.platform() === 'win32' ? 'npm.cmd' : 'npm';
    
    console.log(`${colors.green}[2/2] Запуск Frontend сервера...${colors.reset}`);
    console.log(`Команда: ${npmCmd} run dev`);
    console.log(`Директория: ${frontendPath}\n`);
    
    const frontend = spawn(npmCmd, ['run', 'dev'], {
      cwd: frontendPath,
      stdio: 'inherit',
      shell: true
    });

    frontend.on('error', (err) => {
      console.error(`${colors.red}[ОШИБКА] Frontend:${colors.reset}`, err.message);
      reject(err);
    });

    setTimeout(() => resolve(frontend), 2000);
  });
}

// Функция запуска AML-анализа
function runAMLAnalysis(pythonCmd, mode = 'quick') {
  return new Promise((resolve, reject) => {
    let script, args = [], description;
    
    switch(mode) {
      case 'quick':
        script = 'run_aml_analysis.py';
        description = 'Быстрый AML-анализ всех клиентов';
        break;
      case 'test':
        script = 'aml_pipeline.py';
        description = 'Тестовый AML-анализ (100 клиентов)';
        break;
      case 'high-risk':
        script = 'aml_pipeline.py';
        description = 'AML-анализ высокого риска';
        break;
      case 'json-afm':
        script = 'aml_pipeline_enhanced.py';
        args = ['--json-dir', 'uploads', '--workers', '20', '--batch-size', '100'];
        description = 'Обработка JSON файлов АФМ (мультипроцессинг)';
        break;
      case 'hybrid':
        script = 'aml_pipeline.py';
        description = 'Гибридный анализ (JSON файлы + БД)';
        // Для гибридного режима будем использовать интерактивный запуск
        break;
      case 'optimize':
        script = 'optimize_database.py';
        description = 'Оптимизация базы данных';
        break;
      case 'compare':
        script = 'compare_performance.py';
        description = 'Сравнение производительности';
        break;
      default:
        script = 'run_aml_analysis.py';
        description = 'AML-анализ';
    }

    console.log(`${colors.magenta}🔍 ${description}...${colors.reset}`);
    console.log(`Команда: ${pythonCmd} ${script} ${args.join(' ')}`);
    console.log(`Директория: ${backendPath}\n`);

    const aml = spawn(pythonCmd, [script, ...args], {
      cwd: backendPath,
      stdio: 'inherit',
      shell: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    aml.on('error', (err) => {
      console.error(`${colors.red}[ОШИБКА] AML:${colors.reset}`, err.message);
      reject(err);
    });

    aml.on('exit', (code) => {
      if (code === 0) {
        console.log(`${colors.green}✓ AML-анализ завершен успешно!${colors.reset}\n`);
        resolve();
      } else {
        console.error(`${colors.red}✗ AML-анализ завершился с ошибкой (код ${code})${colors.reset}\n`);
        reject(new Error(`AML process exited with code ${code}`));
      }
    });
  });
}

// Функция показа информации о запущенной системе
function showSystemInfo() {
  setTimeout(() => {
    console.log(`\n${colors.blue}====================================================`);
    console.log(`  ${colors.green}✓ Система успешно запущена!${colors.reset}`);
    console.log(`${colors.blue}====================================================${colors.reset}`);
    console.log(`  Backend API:   ${colors.green}http://localhost:8000/api/${colors.reset}`);
    console.log(`  Frontend:      ${colors.green}http://localhost:3000${colors.reset}`);
    console.log(`  AML-команды:   ${colors.cyan}npm run aml:quick${colors.reset}`);
    console.log(`  JSON АФМ:      ${colors.cyan}npm run aml:json-afm${colors.reset}`);
    console.log(`  Гибридный:     ${colors.cyan}npm run aml:hybrid${colors.reset}`);
    console.log(`${colors.blue}====================================================${colors.reset}\n`);
    console.log(`${colors.yellow}Нажмите Ctrl+C для остановки всех серверов${colors.reset}`);
    console.log(`${colors.yellow}Или запустите анализ в новом терминале:${colors.reset}`);
    console.log(`${colors.cyan}  • npm run aml:quick     ${colors.reset}${colors.yellow}(быстрый анализ БД)${colors.reset}`);
    console.log(`${colors.cyan}  • npm run aml:json-afm  ${colors.reset}${colors.yellow}(JSON файлы АФМ)${colors.reset}`);
    console.log(`${colors.cyan}  • npm run aml:hybrid    ${colors.reset}${colors.yellow}(JSON + БД)${colors.reset}\n`);
  }, 2000);
}

// Функция очистки процессов
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
      console.log(`${colors.green}✓ Серверы остановлены${colors.reset}`);
      process.exit(0);
    }, 1000);
  };

  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  
  return cleanup;
}

// Главная функция
async function main() {
  try {
    checkProjectStructure();
    const pythonCmd = getPythonCommand();
    
    showMenu();
    
    const rl = createInterface();
    
    rl.question(`${colors.cyan}Введите номер (1-9): ${colors.reset}`, async (choice) => {
      rl.close();
      
      console.log();
      
      switch(choice.trim()) {
        case '1':
          // Полная система
          try {
            const backend = await startBackend(pythonCmd);
            const frontend = await startFrontend();
            setupCleanup([backend, frontend]);
            showSystemInfo();
          } catch (err) {
            console.error(`${colors.red}Ошибка запуска системы:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '2':
          // Система + AML
          try {
            const backend = await startBackend(pythonCmd);
            const frontend = await startFrontend();
            
            // Запускаем AML-анализ после запуска системы
            setTimeout(async () => {
              try {
                await runAMLAnalysis(pythonCmd, 'quick');
                console.log(`${colors.green}🎉 Система и AML-анализ готовы к работе!${colors.reset}\n`);
              } catch (amlErr) {
                console.error(`${colors.yellow}⚠️ Система запущена, но AML-анализ не удался${colors.reset}`);
              }
            }, 5000);
            
            setupCleanup([backend, frontend]);
            showSystemInfo();
          } catch (err) {
            console.error(`${colors.red}Ошибка запуска:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '3':
          // Только AML быстрый
          try {
            await runAMLAnalysis(pythonCmd, 'quick');
            console.log(`${colors.green}🎉 AML-анализ завершен!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка AML-анализа:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '4':
          // AML тестирование
          try {
            await runAMLAnalysis(pythonCmd, 'test');
            console.log(`${colors.green}🎉 Тестовый анализ завершен!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка тестирования:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '5':
          // AML высокого риска
          try {
            await runAMLAnalysis(pythonCmd, 'high-risk');
            console.log(`${colors.green}🎉 Анализ высокого риска завершен!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка анализа:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '6':
          // JSON файлы АФМ с мультипроцессингом
          try {
            console.log(`${colors.blue}📂 Проверка JSON файлов в папке uploads...${colors.reset}`);
            const uploadsPath = path.join(backendPath, 'uploads');
            if (!fs.existsSync(uploadsPath)) {
              console.log(`${colors.yellow}⚠️ Папка uploads не найдена, создаем...${colors.reset}`);
              fs.mkdirSync(uploadsPath, { recursive: true });
            }
            
            const jsonFiles = fs.readdirSync(uploadsPath).filter(file => file.endsWith('.json'));
            if (jsonFiles.length === 0) {
              console.log(`${colors.yellow}⚠️ JSON файлы не найдены в папке uploads${colors.reset}`);
              console.log(`${colors.cyan}💡 Поместите JSON файлы АФМ в папку aml-backend/uploads/${colors.reset}`);
              process.exit(0);
            }
            
            console.log(`${colors.green}✓ Найдено ${jsonFiles.length} JSON файлов:${colors.reset}`);
            jsonFiles.forEach(file => console.log(`   • ${file}`));
            console.log();
            
            await runAMLAnalysis(pythonCmd, 'json-afm');
            console.log(`${colors.green}🎉 Обработка JSON файлов завершена!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка обработки JSON:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '7':
          // Гибридный анализ
          try {
            console.log(`${colors.blue}🔄 Запуск гибридного анализа...${colors.reset}`);
            console.log(`${colors.cyan}Будет выполнен анализ JSON файлов + клиентов из БД${colors.reset}\n`);
            
            // Запускаем интерактивный режим с выбором гибридного анализа
            const hybridProcess = spawn(pythonCmd, ['aml_pipeline.py'], {
              cwd: backendPath,
              stdio: ['pipe', 'inherit', 'inherit'],
              shell: true,
              env: { ...process.env, PYTHONUNBUFFERED: '1' }
            });
            
            // Автоматически выбираем опцию 5 (гибридный анализ)
            setTimeout(() => {
              hybridProcess.stdin.write('5\n');
            }, 1000);
            
            hybridProcess.on('exit', (code) => {
              if (code === 0) {
                console.log(`${colors.green}🎉 Гибридный анализ завершен!${colors.reset}`);
              } else {
                console.error(`${colors.red}Ошибка гибридного анализа (код ${code})${colors.reset}`);
              }
              process.exit(code);
            });
            
          } catch (err) {
            console.error(`${colors.red}Ошибка гибридного анализа:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '8':
          // Оптимизация
          try {
            await runAMLAnalysis(pythonCmd, 'optimize');
            console.log(`${colors.green}🎉 Оптимизация завершена!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка оптимизации:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        case '9':
          // Сравнение
          try {
            await runAMLAnalysis(pythonCmd, 'compare');
            console.log(`${colors.green}🎉 Сравнение завершено!${colors.reset}`);
            process.exit(0);
          } catch (err) {
            console.error(`${colors.red}Ошибка сравнения:${colors.reset}`, err.message);
            process.exit(1);
          }
          break;
          
        default:
          console.log(`${colors.red}❌ Неверный выбор! Запускаем стандартную систему...${colors.reset}\n`);
          try {
            const backend = await startBackend(pythonCmd);
            const frontend = await startFrontend();
            setupCleanup([backend, frontend]);
            showSystemInfo();
          } catch (err) {
            console.error(`${colors.red}Ошибка:${colors.reset}`, err.message);
            process.exit(1);
          }
      }
    });
    
  } catch (error) {
    console.error(`${colors.red}Критическая ошибка:${colors.reset}`, error.message);
    process.exit(1);
  }
}

// Запуск
main(); 
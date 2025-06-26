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
};

console.log(`${colors.blue}====================================================`);
console.log(`  АФМ РК - Запуск системы мониторинга транзакций`);
console.log(`====================================================${colors.reset}\n`);

// Правильные имена папок
const backendPath = path.join(__dirname, 'aml-backend');
const frontendPath = path.join(__dirname, 'aml-monitoring-frontend');

console.log(`${colors.yellow}Проверка структуры проекта...${colors.reset}`);
console.log(`Текущая директория: ${__dirname}`);
console.log(`Backend путь: ${backendPath}`);
console.log(`Frontend путь: ${frontendPath}`);

// Проверяем наличие папок
if (!fs.existsSync(backendPath)) {
  console.error(`${colors.red}[ОШИБКА] Папка aml-backend не найдена!${colors.reset}`);
  console.error(`Ожидаемый путь: ${backendPath}`);
  console.error(`\nУбедитесь, что структура проекта следующая:`);
  console.error(`  profile/`);
  console.error(`    ├── aml-backend/`);
  console.error(`    ├── aml-monitoring-frontend/`);
  console.error(`    └── run-dev.js (этот файл)`);
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
  console.error(`${colors.red}[ОШИБКА] Файл app.py не найден в папке aml-backend!${colors.reset}`);
  console.error(`Ожидаемый путь: ${appPyPath}`);
  process.exit(1);
}

const packageJsonPath = path.join(frontendPath, 'package.json');
if (!fs.existsSync(packageJsonPath)) {
  console.error(`${colors.red}[ОШИБКА] Файл package.json не найден в папке aml-monitoring-frontend!${colors.reset}`);
  console.error(`Ожидаемый путь: ${packageJsonPath}`);
  process.exit(1);
}

console.log(`${colors.green}✓ Структура проекта корректна!${colors.reset}\n`);

// Определяем команду Python для разных ОС, теперь с учетом venv
let pythonCmd;
if (os.platform() === 'win32') {
  pythonCmd = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
} else {
  pythonCmd = path.join(backendPath, 'venv', 'bin', 'python');
}

// Проверяем, существует ли python в venv
if (!fs.existsSync(pythonCmd)) {
    console.error(`${colors.red}[ОШИБКА] Исполняемый файл Python не найден в виртуальном окружении!${colors.reset}`);
    console.error(`Ожидаемый путь: ${pythonCmd}`);
    console.error(`\nПожалуйста, убедитесь, что виртуальное окружение создано в папке aml-backend.`);
    console.error(`Если нет, создайте его:`);
    console.error(`  cd aml-backend`);
    console.error(`  python -m venv venv`);
    console.error(`  .\\venv\\Scripts\\activate`);
    console.error(`  pip install -r requirements.txt`);
    process.exit(1);
}

const npmCmd = os.platform() === 'win32' ? 'npm.cmd' : 'npm';

// Небольшая задержка, чтобы дать файловой системе "догнать"
setTimeout(() => {
    // Запускаем Backend
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
      console.error(`${colors.red}[ОШИБКА] Не удалось запустить Backend:${colors.reset}`);
      console.error(err.message);
      if (err.code === 'ENOENT') {
        console.error(`\n${colors.yellow}Похоже, Python не установлен или не добавлен в PATH.${colors.reset}`);
        console.error(`Установите Python 3.8+ с https://www.python.org/`);
      }
      process.exit(1);
    });

    // Ждем запуска бэкенда перед запуском фронтенда
    setTimeout(() => {
      console.log(`${colors.green}[2/2] Запуск Frontend сервера...${colors.reset}`);
      console.log(`Команда: ${npmCmd} run dev`);
      console.log(`Директория: ${frontendPath}\n`);
      
      const frontend = spawn(npmCmd, ['run', 'dev'], {
        cwd: frontendPath,
        stdio: 'inherit',
        shell: true
      });

      frontend.on('error', (err) => {
        console.error(`${colors.red}[ОШИБКА] Не удалось запустить Frontend:${colors.reset}`);
        console.error(err.message);
        if (err.code === 'ENOENT') {
          console.error(`\n${colors.yellow}Похоже, Node.js не установлен или не добавлен в PATH.${colors.reset}`);
          console.error(`Установите Node.js 16+ с https://nodejs.org/`);
        }
        backend.kill();
        process.exit(1);
      });

      // Показываем информацию о запущенной системе
      setTimeout(() => {
        console.log(`\n${colors.blue}====================================================`);
        console.log(`  ${colors.green}✓ Система успешно запущена!${colors.reset}`);
        console.log(`${colors.blue}====================================================${colors.reset}`);
        console.log(`  Backend API:  ${colors.green}http://localhost:8000/api/${colors.reset}`);
        console.log(`  Frontend:     ${colors.green}http://localhost:3000${colors.reset}`);
        console.log(`${colors.blue}====================================================${colors.reset}\n`);
        console.log(`${colors.yellow}Нажмите Ctrl+C для остановки всех серверов${colors.reset}\n`);
      }, 2000);

      // Обработка завершения процессов
      const cleanup = () => {
        console.log(`\n${colors.yellow}Остановка серверов...${colors.reset}`);
        
        // Для Windows используем taskkill
        if (os.platform() === 'win32') {
          try {
            spawn('taskkill', ['/pid', backend.pid, '/f', '/t'], { shell: true });
            spawn('taskkill', ['/pid', frontend.pid, '/f', '/t'], { shell: true });
          } catch (e) {
            // Fallback
            backend.kill();
            frontend.kill();
          }
        } else {
          // Для Unix-систем
          try {
            process.kill(-backend.pid, 'SIGTERM');
            process.kill(-frontend.pid, 'SIGTERM');
          } catch (e) {
            backend.kill('SIGTERM');
            frontend.kill('SIGTERM');
          }
        }
        
        setTimeout(() => {
          console.log(`${colors.green}✓ Серверы остановлены${colors.reset}`);
          process.exit(0);
        }, 1000);
      };

      // Регистрируем обработчики
      process.on('SIGINT', cleanup);
      process.on('SIGTERM', cleanup);
      
      // Если один из процессов завершился
      frontend.on('exit', (code) => {
        if (code !== null) {
          console.log(`\n${colors.red}Frontend завершился с кодом ${code}${colors.reset}`);
          cleanup();
        }
      });

    }, 3000);

    backend.on('exit', (code) => {
      if (code !== null) {
        console.log(`\n${colors.red}Backend завершился с кодом ${code}${colors.reset}`);
        process.exit(code);
      }
    });
}, 500); // 500 мс задержка
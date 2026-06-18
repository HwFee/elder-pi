const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const path = require('path');

const backendDir = path.resolve(__dirname, '..', '..', 'signaling-server');
const frontendDir = path.resolve(__dirname, '..');
const dbFile = path.join(backendDir, 'signaling-test.db');

if (fs.existsSync(dbFile)) {
  fs.unlinkSync(dbFile);
}

const sharedEnv = {
  ...process.env,
  SECRET_KEY: 'test-secret',
  DATABASE_URL: 'sqlite+aiosqlite:///./signaling-test.db',
};

const setupCode = `import asyncio
from app.db import async_engine, Base
from app.models import User, Device, Contact, CallSession
async def main():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(main())
`;

const children = [];

function cleanup() {
  children.forEach((child) => {
    child.kill();
  });
}

process.on('exit', cleanup);
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

const setup = spawn('python', ['-'], {
  cwd: backendDir,
  stdio: ['pipe', 'inherit', 'inherit'],
  env: sharedEnv,
});
children.push(setup);

setup.stdin.write(setupCode);
setup.stdin.end();

setup.on('exit', (code) => {
  if (code !== 0) {
    process.exit(code ?? 1);
  }

  const backend = spawn('python', ['-m', 'uvicorn', 'app.main:socket_app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: backendDir,
    stdio: 'inherit',
    env: sharedEnv,
  });
  children.push(backend);

  backend.on('exit', (exitCode) => {
    process.exit(exitCode ?? 0);
  });

  waitForBackend(() => {
    const frontend = spawn('node', [path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js'), '--host', '127.0.0.1'], {
      cwd: frontendDir,
      stdio: 'inherit',
      env: process.env,
    });
    children.push(frontend);

    frontend.on('exit', (exitCode) => {
      process.exit(exitCode ?? 0);
    });
  });
});

function waitForBackend(callback) {
  const url = 'http://127.0.0.1:8000/health';
  let attempts = 0;
  const maxAttempts = 150;

  function poll() {
    attempts += 1;
    if (attempts > maxAttempts) {
      console.error('Backend did not become ready in time');
      process.exit(1);
    }

    http.get(url, (res) => {
      if (res.statusCode === 200) {
        callback();
      } else {
        setTimeout(poll, 200);
      }
    }).on('error', () => {
      setTimeout(poll, 200);
    });
  }

  poll();
}

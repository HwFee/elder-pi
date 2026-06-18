import { initLogin, requireAuth } from './auth.js';
import { initDashboard } from './api.js';
import { initCall } from './webrtc.js';

function bootstrap() {
  const page = document.body.dataset.page;
  if (page === 'login') {
    initLogin();
  } else if (page === 'dashboard') {
    requireAuth();
    initDashboard().catch((err) => {
      console.error(err);
      window.location.href = '/index.html';
    });
  } else if (page === 'call') {
    requireAuth();
    initCall();
  }
}

bootstrap();

/**
 * SecureVote – Client-side form validation
 * NOTE: Server-side validation is the real security layer.
 *       This is purely for UX feedback.
 */

document.addEventListener('DOMContentLoaded', function () {

  // ── Password strength meter ──────────────────────────────────────────────
  const pwdInput    = document.getElementById('password');
  const strengthBar = document.getElementById('strengthBar');
  const strengthTxt = document.getElementById('strengthText');

  if (pwdInput && strengthBar) {
    pwdInput.addEventListener('input', function () {
      const val = this.value;
      let score = 0;
      if (val.length >= 8)                    score++;
      if (/[A-Z]/.test(val))                  score++;
      if (/[a-z]/.test(val))                  score++;
      if (/\d/.test(val))                     score++;
      if (/[@$!%*?&_\-#]/.test(val))          score++;

      const levels = [
        { pct: 0,   cls: '',          label: '' },
        { pct: 20,  cls: 'bg-danger', label: 'Very Weak' },
        { pct: 40,  cls: 'bg-warning',label: 'Weak' },
        { pct: 60,  cls: 'bg-info',   label: 'Fair' },
        { pct: 80,  cls: 'bg-primary',label: 'Strong' },
        { pct: 100, cls: 'bg-success',label: 'Very Strong' },
      ];

      const level = levels[score];
      strengthBar.style.width = level.pct + '%';
      strengthBar.className   = 'progress-bar ' + level.cls;
      if (strengthTxt) {
        strengthTxt.textContent = level.label;
        strengthTxt.className   = 'form-text ' + (score >= 4 ? 'text-success' : 'text-warning');
      }
    });
  }

  // ── Password match indicator ─────────────────────────────────────────────
  const confirmInput = document.getElementById('confirm_password');
  const matchMsg     = document.getElementById('matchMsg');

  if (confirmInput && matchMsg) {
    confirmInput.addEventListener('input', function () {
      if (!pwdInput) return;
      if (this.value === pwdInput.value) {
        matchMsg.textContent = '✓ Passwords match';
        matchMsg.className   = 'form-text text-success';
      } else {
        matchMsg.textContent = '✗ Passwords do not match';
        matchMsg.className   = 'form-text text-danger';
      }
    });
  }

  // ── Toggle password visibility ───────────────────────────────────────────
  const toggleBtn = document.getElementById('togglePwd');
  if (toggleBtn && pwdInput) {
    toggleBtn.addEventListener('click', function () {
      const icon = this.querySelector('i');
      if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        pwdInput.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  }

  // ── Registration form submit guard ───────────────────────────────────────
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', function (e) {
      const username = document.getElementById('username').value.trim();
      const email    = document.getElementById('email').value.trim();
      const password = pwdInput ? pwdInput.value : '';
      const confirm  = confirmInput ? confirmInput.value : '';

      if (!username || !email || !password || !confirm) {
        e.preventDefault();
        alert('Please fill in all required fields.');
        return;
      }

      if (password !== confirm) {
        e.preventDefault();
        alert('Passwords do not match.');
        return;
      }

      const pwdRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_\-#]).{8,}$/;
      if (!pwdRegex.test(password)) {
        e.preventDefault();
        alert('Password must be at least 8 characters and include uppercase, lowercase, digit, and special character.');
      }
    });
  }
});

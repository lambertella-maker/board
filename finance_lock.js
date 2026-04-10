(function() {
  const SESSION_KEY = 'ella_finance_dash_unlocked';
  const PASSCODE_KEY = 'ella_finance_passcode_hash';
  const RP_ID = window.location.hostname;
  const BIOMETRIC_KEY = `ella_finance_biometric_cred:${RP_ID}`;

  function getNavigationType() {
    const navEntry = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    if (navEntry && navEntry.type) return navEntry.type;
    if (performance.navigation) {
      if (performance.navigation.type === 1) return 'reload';
      if (performance.navigation.type === 2) return 'back_forward';
    }
    return 'navigate';
  }

  function injectLock() {
    if (document.getElementById('finance-lock')) return;
    document.body.insertAdjacentHTML('afterbegin', `
      <div class="finance-lock" id="finance-lock" aria-modal="true" role="dialog" aria-labelledby="finance-lock-title">
        <div class="finance-lock__panel">
          <div class="finance-lock__badge">Private Dashboard</div>
          <h1 class="finance-lock__title" id="finance-lock-title">Ella Finance</h1>
          <p class="finance-lock__subtitle" id="finance-lock-subtitle">Unlock with biometrics or your backup passcode.</p>
          <div class="finance-lock__actions">
            <button type="button" class="finance-lock__button finance-lock__button--primary" id="finance-lock-biometric">Unlock with Face ID / Touch ID</button>
            <button type="button" class="finance-lock__button finance-lock__button--secondary" id="finance-lock-enroll">Set up Face ID / Touch ID</button>
          </div>
          <form class="finance-lock__form" id="finance-lock-form" novalidate>
            <label class="finance-lock__label" for="finance-lock-passcode">Backup passcode</label>
            <input class="finance-lock__input" id="finance-lock-passcode" type="password" inputmode="numeric" autocomplete="current-password" placeholder="Enter passcode">
            <div class="finance-lock__row" id="finance-lock-confirm-row">
              <div>
                <label class="finance-lock__label" for="finance-lock-passcode-confirm">Confirm passcode</label>
                <input class="finance-lock__input" id="finance-lock-passcode-confirm" type="password" inputmode="numeric" autocomplete="new-password" placeholder="Re-enter passcode">
              </div>
            </div>
            <div class="finance-lock__hint" id="finance-lock-hint">Choose a backup passcode so you can still get in when biometrics fail.</div>
            <button type="submit" class="finance-lock__button finance-lock__button--secondary" id="finance-lock-submit">Save backup passcode</button>
            <div class="finance-lock__status" id="finance-lock-status" aria-live="polite"></div>
          </form>
        </div>
      </div>
    `);
  }

  function bytesToBase64(bytes) {
    return btoa(String.fromCharCode(...new Uint8Array(bytes)));
  }

  function base64ToBytes(value) {
    return Uint8Array.from(atob(value), c => c.charCodeAt(0));
  }

  async function sha256(value) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
    return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
  }

  async function createBiometricCredential() {
    const credential = await navigator.credentials.create({
      publicKey: {
        challenge: crypto.getRandomValues(new Uint8Array(32)),
        rp: { name: 'Ella Finance', id: RP_ID },
        user: {
          id: crypto.getRandomValues(new Uint8Array(16)),
          name: 'ella',
          displayName: 'Ella'
        },
        pubKeyCredParams: [
          { type: 'public-key', alg: -7 },
          { type: 'public-key', alg: -257 }
        ],
        authenticatorSelection: {
          authenticatorAttachment: 'platform',
          userVerification: 'required'
        },
        timeout: 60000
      }
    });
    localStorage.setItem(BIOMETRIC_KEY, bytesToBase64(credential.rawId));
  }

  async function authenticateBiometric() {
    const stored = localStorage.getItem(BIOMETRIC_KEY);
    if (!stored) return false;

    await navigator.credentials.get({
      publicKey: {
        challenge: crypto.getRandomValues(new Uint8Array(32)),
        rpId: RP_ID,
        allowCredentials: [{ type: 'public-key', id: base64ToBytes(stored), transports: ['internal'] }],
        userVerification: 'required',
        timeout: 60000
      }
    });
    return true;
  }

  function init() {
    if (!document.body) return;
    if (getNavigationType() !== 'reload') {
      sessionStorage.removeItem(SESSION_KEY);
    }
    if (sessionStorage.getItem(SESSION_KEY) === '1') return;

    injectLock();

    const lock = document.getElementById('finance-lock');
    const subtitle = document.getElementById('finance-lock-subtitle');
    const biometricBtn = document.getElementById('finance-lock-biometric');
    const enrollBtn = document.getElementById('finance-lock-enroll');
    const form = document.getElementById('finance-lock-form');
    const passcodeInput = document.getElementById('finance-lock-passcode');
    const confirmRow = document.getElementById('finance-lock-confirm-row');
    const confirmInput = document.getElementById('finance-lock-passcode-confirm');
    const hint = document.getElementById('finance-lock-hint');
    const submitBtn = document.getElementById('finance-lock-submit');
    const status = document.getElementById('finance-lock-status');
    let fallbackVisible = false;

    const supportsBiometric = Boolean(window.PublicKeyCredential && window.isSecureContext);

    function unlock() {
      sessionStorage.setItem(SESSION_KEY, '1');
      document.body.classList.remove('finance-lock-active');
      lock.classList.add('is-hidden');
    }

    function setStatus(message, tone) {
      status.textContent = message || '';
      status.className = 'finance-lock__status';
      if (tone) status.classList.add(`is-${tone}`);
    }

    function hasPasscode() {
      return Boolean(localStorage.getItem(PASSCODE_KEY));
    }

    function hasBiometric() {
      return Boolean(localStorage.getItem(BIOMETRIC_KEY));
    }

    function setFallbackVisibility(visible) {
      fallbackVisible = visible;
      form.style.display = visible ? 'block' : 'none';
      if (!visible) {
        passcodeInput.value = '';
        confirmInput.value = '';
      }
    }

    function updateMode() {
      const passcodeExists = hasPasscode();
      const biometricExists = hasBiometric();
      const biometricRequired = supportsBiometric && biometricExists;

      document.body.classList.add('finance-lock-active');
      confirmRow.style.display = passcodeExists ? 'none' : 'block';
      confirmInput.required = !passcodeExists;
      passcodeInput.autocomplete = passcodeExists ? 'current-password' : 'new-password';
      passcodeInput.placeholder = passcodeExists ? 'Enter backup passcode' : 'Create backup passcode';
      submitBtn.textContent = passcodeExists ? 'Unlock with passcode' : 'Save backup passcode';
      hint.textContent = passcodeExists
        ? 'Use this when Face ID or Touch ID is unavailable.'
        : 'Pick a passcode you will remember. It works as the fallback on every dashboard.';

      if (!supportsBiometric) {
        biometricBtn.style.display = 'none';
        enrollBtn.style.display = 'none';
        setFallbackVisibility(true);
        subtitle.textContent = passcodeExists
          ? 'This browser can use your backup passcode.'
          : 'Set your backup passcode to protect this dashboard.';
        return;
      }

      biometricBtn.style.display = biometricExists ? 'block' : 'none';
      enrollBtn.style.display = biometricExists ? 'none' : 'block';
      setFallbackVisibility(!biometricRequired);
      subtitle.textContent = biometricExists
        ? 'Biometric unlock is required on this device. Your backup passcode appears only if biometric unlock fails.'
        : 'Set up Face ID or Touch ID for fast unlock, with a backup passcode underneath.';
    }

    async function setBusy(target, busyText) {
      target.dataset.label = target.textContent;
      target.textContent = busyText;
      target.disabled = true;
      biometricBtn.disabled = true;
      enrollBtn.disabled = true;
      submitBtn.disabled = true;
    }

    function clearBusy(target) {
      if (target.dataset.label) target.textContent = target.dataset.label;
      biometricBtn.disabled = false;
      enrollBtn.disabled = false;
      submitBtn.disabled = false;
    }

    biometricBtn.addEventListener('click', async () => {
      try {
        setStatus('Checking Face ID / Touch ID…', 'info');
        await setBusy(biometricBtn, 'Checking…');
        await authenticateBiometric();
        setStatus('Unlocked.', 'success');
        unlock();
      } catch (error) {
        setStatus('Biometric unlock failed. Use your backup passcode below.', 'error');
        setFallbackVisibility(true);
        passcodeInput.focus({ preventScroll: true });
        if (error && error.name !== 'NotAllowedError') console.warn('finance lock biometric unlock failed', error);
      } finally {
        clearBusy(biometricBtn);
      }
    });

    enrollBtn.addEventListener('click', async () => {
      try {
        setStatus('Setting up Face ID / Touch ID…', 'info');
        await setBusy(enrollBtn, 'Setting up…');
        await createBiometricCredential();
        updateMode();
        setStatus('Biometric unlock is ready.', 'success');
        await authenticateBiometric();
        unlock();
      } catch (error) {
        setStatus('Biometric setup failed. Your backup passcode still works.', 'error');
        setFallbackVisibility(true);
        if (error && error.name !== 'NotAllowedError') console.warn('finance lock biometric setup failed', error);
      } finally {
        clearBusy(enrollBtn);
      }
    });

    form.addEventListener('submit', async event => {
      event.preventDefault();
      const passcode = passcodeInput.value.trim();
      const confirm = confirmInput.value.trim();
      const passcodeExists = hasPasscode();

      if (passcode.length < 4) {
        setStatus('Use at least 4 characters for the passcode.', 'error');
        return;
      }

      try {
        await setBusy(submitBtn, passcodeExists ? 'Unlocking…' : 'Saving…');

        if (!passcodeExists) {
          if (passcode !== confirm) {
            setStatus('Passcodes do not match.', 'error');
            return;
          }
          localStorage.setItem(PASSCODE_KEY, await sha256(passcode));
          passcodeInput.value = '';
          confirmInput.value = '';
          updateMode();
          setStatus('Backup passcode saved.', 'success');
          return;
        }

        const storedHash = localStorage.getItem(PASSCODE_KEY);
        const incomingHash = await sha256(passcode);
        if (storedHash !== incomingHash) {
          setStatus('Incorrect passcode.', 'error');
          return;
        }

        setStatus('Unlocked.', 'success');
        passcodeInput.value = '';
        unlock();
      } finally {
        clearBusy(submitBtn);
      }
    });

    updateMode();
    if (supportsBiometric && hasBiometric()) {
      biometricBtn.click();
    } else if (fallbackVisible) {
      passcodeInput.focus({ preventScroll: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

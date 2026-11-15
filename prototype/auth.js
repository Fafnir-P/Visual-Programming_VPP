// ============================================================================
// LOGIN (renderer side)
// ============================================================================
// The account is local to this computer. Passwords and the saved API key are
// handled by the main process (main.js) through window.vpAuth (preload.js).
// This file only draws the login dialog and keeps the key field in sync.
// Not signed in = guest: the key stays in memory only.

const authState = {
    available: false,   // true when running inside the desktop app
    username: null,
    canEncrypt: false,
    keyMessage: ''      // short note shown in the Model tab status line
};

let loginMode = 'signin';

function el(id) {
    return document.getElementById(id);
}

function setLoginMode(mode) {
    loginMode = mode;
    const creating = mode === 'create';
    el('loginTitle').textContent = creating ? 'Create account' : 'Sign in';
    el('loginSubmitBtn').textContent = creating ? 'Create account' : 'Sign in';
    el('loginConfirmGroup').hidden = !creating;
    el('loginPassword').autocomplete = creating ? 'new-password' : 'current-password';
    el('loginTabSignIn').classList.toggle('active', !creating);
    el('loginTabSignIn').setAttribute('aria-selected', String(!creating));
    el('loginTabCreate').classList.toggle('active', creating);
    el('loginTabCreate').setAttribute('aria-selected', String(creating));
    el('loginError').textContent = '';
    el('loginPassword').value = '';
    el('loginConfirm').value = '';
}

function openLoginDialog() {
    const dialog = el('loginDialog');
    setLoginMode('signin');
    el('loginUsername').value = '';
    el('loginPassword').value = '';
    el('loginConfirm').value = '';
    if (!dialog.open) dialog.showModal();
    el('loginUsername').focus();
}

function closeLoginDialog() {
    el('loginPassword').value = '';
    el('loginConfirm').value = '';
    const dialog = el('loginDialog');
    if (dialog.open) dialog.close();
}

function renderAuthToolbar() {
    const label = el('userLabel');
    const btn = el('authBtn');
    btn.hidden = !authState.available;
    if (authState.username) {
        label.textContent = 'Signed in: ' + authState.username;
        btn.textContent = 'Log out';
    } else {
        label.textContent = authState.available ? 'Guest' : '';
        btn.textContent = 'Sign in';
    }
}

// Called once a sign-in or account creation succeeded.
async function applySignedIn(username) {
    authState.username = username;
    authState.keyMessage = '';
    const input = el('bedrockApiKeyInput');
    if (input.value) {
        // A key typed as a guest is kept and saved to this account.
        await persistKey(input.value);
    } else {
        const res = await window.vpAuth.loadKey();
        if (res.ok) {
            input.value = res.key;
            bedrockState.apiKey = res.key;
        } else {
            authState.keyMessage = res.error;
        }
    }
    renderAuthToolbar();
    updateBedrockStatus();
}

async function persistKey(value) {
    const res = value ? await window.vpAuth.saveKey(value) : await window.vpAuth.clearKey();
    authState.keyMessage = res.ok ? '' : res.error;
    updateBedrockStatus();
}

async function signOut() {
    await window.vpAuth.logout();
    authState.username = null;
    authState.keyMessage = '';
    el('bedrockApiKeyInput').value = '';
    bedrockState.apiKey = '';
    renderAuthToolbar();
    updateBedrockStatus();
    openLoginDialog();
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const username = el('loginUsername').value.trim();
    const password = el('loginPassword').value;
    const error = el('loginError');
    error.textContent = '';

    if (!username || !password) {
        error.textContent = 'Enter a username and a password.';
        return;
    }
    if (loginMode === 'create') {
        if (password.length < 8) {
            error.textContent = 'Password must be at least 8 characters.';
            return;
        }
        if (password !== el('loginConfirm').value) {
            error.textContent = 'The two passwords do not match.';
            return;
        }
    }

    const submit = el('loginSubmitBtn');
    submit.disabled = true;
    try {
        const res = loginMode === 'create'
            ? await window.vpAuth.register(username, password)
            : await window.vpAuth.login(username, password);
        if (!res.ok) {
            error.textContent = res.error;
            return;
        }
        closeLoginDialog();
        await applySignedIn(res.username);
    } catch (err) {
        error.textContent = 'Something went wrong. Try again.';
    } finally {
        submit.disabled = false;
    }
}

async function initAuthUI() {
    el('loginTabSignIn').addEventListener('click', () => setLoginMode('signin'));
    el('loginTabCreate').addEventListener('click', () => setLoginMode('create'));
    el('loginForm').addEventListener('submit', handleLoginSubmit);
    el('loginGuestBtn').addEventListener('click', closeLoginDialog);
    // Esc must not leave the dialog half-closed; use the buttons.
    el('loginDialog').addEventListener('cancel', (e) => e.preventDefault());

    el('authBtn').addEventListener('click', () => {
        if (authState.username) signOut();
        else openLoginDialog();
    });

    // Save when the user finishes editing the key (blur or Enter), not on every keystroke.
    el('bedrockApiKeyInput').addEventListener('change', (e) => {
        if (authState.username) persistKey(e.target.value);
    });

    if (!window.vpAuth) {
        // Plain browser: no account storage exists. Guest only.
        renderAuthToolbar();
        return;
    }
    authState.available = true;
    const status = await window.vpAuth.status();
    authState.canEncrypt = !!status.canEncrypt;
    if (status.ok && status.loggedIn) {
        await applySignedIn(status.username);
    } else {
        renderAuthToolbar();
        openLoginDialog();
    }
}

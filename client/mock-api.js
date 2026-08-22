/**
 * mock-api.js — In-browser mock API for testing the GUI
 * Simulates register, login, logout, /me, /files, /files/:id
 * Uses seed-data.json loaded at startup.
 */

let MOCK_USERS = [];
let MOCK_FILES = [];
let mockCurrentUser = null;
let mockRegisteredUsers = [];

// Load seed data on startup
fetch('seed-data.json')
  .then(r => r.json())
  .then(data => {
    MOCK_USERS = data.users || [];
    MOCK_FILES = data.files || [];
    mockRegisteredUsers = [...MOCK_USERS];
    console.log('[Mock API] Seed data loaded:', MOCK_USERS.length, 'users,', MOCK_FILES.length, 'files');
  })
  .catch(() => console.warn('[Mock API] Could not load seed-data.json — mock mode will have no data.'));

/** Mock implementations called by the mode-switching logic in index.html */

function mockRegister(email, password) {
  if (mockRegisteredUsers.find(u => u.email === email)) {
    return { status: 409, body: { error: 'This email is already registered' } };
  }
  const newUser = { id: 'u' + Date.now(), email, password, name: email.split('@')[0] };
  mockRegisteredUsers.push(newUser);
  return { status: 201, body: { message: 'User registered successfully', user_id: newUser.id } };
}

function mockLogin(email, password) {
  const user = mockRegisteredUsers.find(u => u.email === email && u.password === password);
  if (!user) {
    return { status: 401, body: { error: 'Invalid email or password' } };
  }
  mockCurrentUser = user;
  const fakeToken = 'mock-jwt-' + btoa(user.id + ':' + Date.now());
  return { status: 200, body: { message: 'Login successful', token: fakeToken } };
}

function mockLogout() {
  if (!mockCurrentUser) {
    return { status: 401, body: { error: 'Not logged in' } };
  }
  mockCurrentUser = null;
  return { status: 200, body: { message: 'Successfully logged out' } };
}

function mockGetMe() {
  if (!mockCurrentUser) {
    return { status: 401, body: { error: 'Token missing. Please login.' } };
  }
  return { status: 200, body: { id: mockCurrentUser.id, email: mockCurrentUser.email, full_name: mockCurrentUser.name } };
}

function mockGetFiles() {
  if (!mockCurrentUser) {
    return { status: 401, body: { error: 'Token missing. Please login.' } };
  }
  const userFiles = MOCK_FILES.filter(f => f.user_id === mockCurrentUser.id);
  return { status: 200, body: { files: userFiles, count: userFiles.length } };
}

function mockGetFileById(fileId) {
  if (!mockCurrentUser) {
    return { status: 401, body: { error: 'Token missing. Please login.' } };
  }
  const file = MOCK_FILES.find(f => f.id === String(fileId));
  if (!file) {
    return { status: 404, body: { error: 'File not found' } };
  }
  if (file.user_id !== mockCurrentUser.id) {
    return { status: 403, body: { error: 'Access denied — this file does not belong to you' } };
  }
  return { status: 200, body: file };
}

/**
 * appwrite-adapter.js — Appwrite Web SDK adapter
 * Connects the GUI to Appwrite Cloud for authentication and file management.
 * Uses the Appwrite Web SDK (loaded via CDN in index.html).
 */

let appwriteClient = null;
let appwriteAccount = null;
let appwriteDatabases = null;
let appwriteCurrentUserId = null;

/** Initialize (or re-initialize) the Appwrite client with current GUI settings */
function initAppwrite() {
  const endpoint = document.getElementById('awEndpoint').value.trim();
  const projectId = document.getElementById('awProjectId').value.trim();

  appwriteClient = new Appwrite.Client();
  appwriteClient.setEndpoint(endpoint).setProject(projectId);

  appwriteAccount = new Appwrite.Account(appwriteClient);
  appwriteDatabases = new Appwrite.Databases(appwriteClient);
}

/** Helper to get Database and Collection IDs from GUI */
function getAwIds() {
  return {
    databaseId: document.getElementById('awDatabaseId').value.trim(),
    collectionId: document.getElementById('awFilesCollectionId').value.trim(),
    bucketId: document.getElementById('awBucketId').value.trim()
  };
}

/** Register a new user via Appwrite Auth */
async function appwriteRegister(email, password) {
  try {
    initAppwrite();
    const user = await appwriteAccount.create(
      Appwrite.ID.unique(), email, password, email.split('@')[0]
    );
    return { status: 201, body: { message: 'User registered successfully', user_id: user.$id } };
  } catch (e) {
    const code = e.code || 500;
    return { status: code, body: { error: e.message } };
  }
}

/** Login via Appwrite (creates an email/password session) */
async function appwriteLogin(email, password) {
  try {
    initAppwrite();
    const session = await appwriteAccount.createEmailPasswordSession(email, password);
    // Get user details after login
    const user = await appwriteAccount.get();
    appwriteCurrentUserId = user.$id;
    return {
      status: 200,
      body: {
        message: 'Login successful',
        token: session.$id,
        user_id: user.$id,
        email: user.email
      }
    };
  } catch (e) {
    const code = e.code || 401;
    return { status: code, body: { error: e.message || 'Invalid email or password' } };
  }
}

/** Logout — delete current Appwrite session */
async function appwriteLogout() {
  try {
    initAppwrite();
    await appwriteAccount.deleteSession('current');
    appwriteCurrentUserId = null;
    return { status: 200, body: { message: 'Successfully logged out' } };
  } catch (e) {
    return { status: e.code || 401, body: { error: e.message } };
  }
}

/** GET /me — Get current user profile from Appwrite */
async function appwriteGetMe() {
  try {
    initAppwrite();
    const user = await appwriteAccount.get();
    appwriteCurrentUserId = user.$id;
    return {
      status: 200,
      body: {
        id: user.$id,
        email: user.email,
        full_name: user.name || user.email.split('@')[0],
        created_at: user.$createdAt
      }
    };
  } catch (e) {
    return { status: 401, body: { error: 'Not logged in. Please login first.' } };
  }
}

/** GET /files — List current user's files from Appwrite Database */
async function appwriteGetFiles() {
  try {
    initAppwrite();
    // Make sure we have user ID
    if (!appwriteCurrentUserId) {
      const user = await appwriteAccount.get();
      appwriteCurrentUserId = user.$id;
    }
    const { databaseId, collectionId } = getAwIds();
    const response = await appwriteDatabases.listDocuments(
      databaseId,
      collectionId,
      [Appwrite.Query.equal('user_id', appwriteCurrentUserId)]
    );
    const files = response.documents.map(doc => ({
      id: doc.$id,
      filename: doc.filename,
      file_path: doc.file_path,
      file_size: doc.file_size,
      uploaded_at: doc.$createdAt
    }));
    return { status: 200, body: { files: files, count: files.length } };
  } catch (e) {
    return { status: e.code || 500, body: { error: e.message } };
  }
}

/** GET /files/:id — Get a specific file by document ID */
async function appwriteGetFileById(fileId) {
  try {
    initAppwrite();
    if (!appwriteCurrentUserId) {
      const user = await appwriteAccount.get();
      appwriteCurrentUserId = user.$id;
    }
    const { databaseId, collectionId } = getAwIds();
    const doc = await appwriteDatabases.getDocument(databaseId, collectionId, fileId);
    
    // With proper document-level permissions, if user doesn't own the file,
    // Appwrite will throw a 404 (document not found) — this IS proper security.
    // The user simply cannot "see" documents they don't own.
    return {
      status: 200,
      body: {
        id: doc.$id,
        filename: doc.filename,
        file_path: doc.file_path,
        file_size: doc.file_size,
        uploaded_at: doc.$createdAt
      }
    };
  } catch (e) {
    // Appwrite returns 404 for files the user doesn't own (Row Level Security)
    const code = e.code || 404;
    return { status: code, body: { error: e.message || 'File not found or access denied' } };
  }
}

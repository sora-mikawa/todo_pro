<template>
  <div class="container">
    <h1>Todo App (FastAPI + Vue)</h1>

    <!-- 未ログイン時 -->
    <div v-if="!token" class="auth-box">
      <input v-model="email" type="email" placeholder="メールアドレス" />
      <input v-model="password" type="password" placeholder="パスワード" />

      <div class="button-row">
        <button class="btn btn-login" @click="login">ログイン</button>
        <button class="btn btn-register" @click="register">新規登録</button>
      </div>

      <p v-if="message" class="message">{{ message }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <!-- ログイン後 -->
    <div v-else class="todo-area">
      <button class="btn btn-logout" @click="logout">ログアウト</button>
      <Todo :token="token" />
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Todo from "./components/todo.vue";

const email = ref("");
const password = ref("");
const token = ref(localStorage.getItem("access_token") || "");
const error = ref("");
const message = ref("");

async function login() {
  error.value = "";
  message.value = "";
  try {
    const res = await fetch("http://localhost:8000/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.value, password: password.value }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "ログイン失敗");
    }
    const data = await res.json();
    token.value = data.access_token;
    localStorage.setItem("access_token", token.value);
  } catch (e) {
    error.value = e.message;
  }
}

async function register() {
  error.value = "";
  message.value = "";
  try {
    const res = await fetch("http://localhost:8000/users/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.value, password: password.value }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "登録失敗");
    }
    await res.json();
    message.value = "登録が完了しました。続けてログインしてください";
  } catch (e) {
    error.value = e.message;
  }
}

function logout() {
  localStorage.removeItem("access_token");
  token.value = "";
}
</script>

<style>
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  background: url('./images/background.jpg') no-repeat center center fixed;
  background-size: cover;
  font-family: sans-serif;
}

.container {
  max-width: 800px;
  margin: 60px auto;
  padding: 20px;
}
</style>


<style scoped>

.container {
   max-width: 800px;
  margin: 60px auto;
  padding: 20px;
  font-family: sans-serif;
}

h1 {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 20px;
}

.auth-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.auth-box input {
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.auth-box input:focus {
  border-color: #0077cc;
  outline: none;
}

.button-row {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.btn {
  flex: 1;
  padding: 8px 0;
  margin: 0 4px;
  font-size: 0.95rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-login {
  background-color: #007bff;
  color: #fff;
}
.btn-login:hover {
  background-color: #0062cc;
}

.btn-register {
  background-color: #28a745;
  color: #fff;
}
.btn-register:hover {
  background-color: #218838;
}

.btn-logout {
  background-color: #777;
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  margin-bottom: 10px;
}
.btn-logout:hover {
  background-color: #555;
}

.message {
  color: #2e7d32;
  margin-top: 6px;
}

.error {
  color: #c62828;
  margin-top: 6px;
}

.todo-area {
  margin-top: 10px;
}
</style>

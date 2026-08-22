<template>
  <div class="task-container">
    <h2>タスク一覧</h2>

    <!-- タスク追加フォーム -->
    <div class="task-form">
      <input v-model="newTitle" placeholder="タイトル" />
      <input v-model="newDescription" placeholder="説明(任意)" />
      <select v-model="newStatus">
        <option value="todo">未着手</option>
        <option value="in_progress">進行中</option>
        <option value="done">完了</option>
      </select>
      <input type="number" v-model.number="newPriority" placeholder="優先度(1-5)" />
      <input type="date" v-model="newDeadline" />
      <button @click="addTask">追加</button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- タスク表示 -->
    <ul class="task-list">
      <li v-for="task in tasks" :key="task.id">
        <!-- 編集モード -->
        <div v-if="editId === task.id" class="edit-form">
          <input v-model="editTitle" placeholder="タイトル" />
          <input v-model="editDescription" placeholder="説明" />
          <select v-model="editStatus">
            <option value="todo">未着手</option>
            <option value="in_progress">進行中</option>
            <option value="done">完了</option>
          </select>
          <input type="number" v-model.number="editPriority" />
          <input type="date" v-model="editDeadline" />
          <button @click="saveEdit(task.id)">保存</button>
          <button @click="cancelEdit">キャンセル</button>
        </div>

        <!-- 通常表示 -->
        <div v-else>
          <div class="task-title">{{ task.title }}</div>
          <div class="task-meta">
            <span>説明: {{ task.description || 'なし' }}</span>
            <span>状態: {{ task.status }}</span>
            <span>優先度: {{ task.priority }}</span>
            <span>期限: {{ task.deadline || '未設定' }}</span>
          </div>
          <button @click="startEdit(task)" class="edit-btn">編集</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";

const props = defineProps({
  token: { type: String, required: true },
});

const tasks = ref([]);
const newTitle = ref("");
const newDescription = ref("");
const newStatus = ref("todo");
const newPriority = ref(2);
const newDeadline = ref("");
const error = ref("");

// 編集モード関連
const editId = ref(null);
const editTitle = ref("");
const editDescription = ref("");
const editStatus = ref("todo");
const editPriority = ref(2);
const editDeadline = ref("");

async function fetchTasks() {
  error.value = "";
  try {
    const res = await fetch("http://localhost:8000/tasks/", {
      headers: { Authorization: `Bearer ${props.token}` },
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "タスク取得失敗");
    }
    const data = await res.json();
    tasks.value = data.tasks;
  } catch (e) {
    error.value = e.message;
  }
}

async function addTask() {
  if (!newTitle.value.trim()) return;
  try {
    const res = await fetch("http://localhost:8000/tasks/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${props.token}`,
      },
      body: JSON.stringify({
        title: newTitle.value,
        description: newDescription.value,
        status: newStatus.value,
        priority: newPriority.value,
        deadline: newDeadline.value || null,
      }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "タスク登録失敗");
    }
    clearNew();
    fetchTasks();
  } catch (e) {
    error.value = e.message;
  }
}

function clearNew() {
  newTitle.value = "";
  newDescription.value = "";
  newStatus.value = "todo";
  newPriority.value = 2;
  newDeadline.value = "";
}

// 編集モード開始
function startEdit(task) {
  editId.value = task.id;
  editTitle.value = task.title;
  editDescription.value = task.description || "";
  editStatus.value = task.status;
  editPriority.value = task.priority;
  editDeadline.value = task.deadline || "";
}

// 編集キャンセル
function cancelEdit() {
  editId.value = null;
}

// 編集保存
async function saveEdit(taskId) {
  try {
    const res = await fetch(`http://localhost:8000/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${props.token}`,
      },
      body: JSON.stringify({
        title: editTitle.value,
        description: editDescription.value,
        status: editStatus.value,
        priority: editPriority.value,
        deadline: editDeadline.value || null,
      }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "更新失敗");
    }
    editId.value = null;
    fetchTasks();
  } catch (e) {
    error.value = e.message;
  }
}

onMounted(fetchTasks);
watch(() => props.token, fetchTasks);
</script>

<style scoped>
.task-container {
  max-width: 700px;
  margin: 20px auto;
  font-family: sans-serif;
}

h2 {
  font-size: 1.4rem;
  margin-bottom: 10px;
}

.task-form {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 100px 150px auto;
  gap: 6px;
  margin-bottom: 15px;
  align-items: center;
}

.task-form input,
.task-form select {
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.task-form button {
  background-color: #4caf50;
  color: #fff;
  border: none;
  padding: 7px 14px;
  border-radius: 4px;
  cursor: pointer;
}

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.task-list li {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 12px;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  transition: transform 0.15s, box-shadow 0.15s;
}
.task-list li:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.12);
}

.task-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 6px;
}

.task-meta {
  font-size: 0.85rem;
  color: #444;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}

.task-meta span {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.edit-form {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 80px 120px auto auto;
  gap: 6px;
  align-items: center;
}

.edit-form input,
.edit-form select {
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.edit-form button {
  background: #2196f3;
  color: #fff;
  border: none;
  padding: 5px 10px;
  margin-right: 4px;
  cursor: pointer;
  border-radius: 4px;
}
.edit-btn {
  background: #2196f3;
  color: #fff;
  border: none;
  padding: 6px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.edit-btn:hover {
  background: #1976d2;
}
</style>

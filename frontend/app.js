document.addEventListener('DOMContentLoaded', () => {
    const taskForm = document.getElementById('task-form');
    const payloadInput = document.getElementById('payload-input');
    const taskList = document.getElementById('task-list');

    // Fetch and render tasks via API proxy path
    const fetchTasks = async () => {
        try {
            const response = await fetch('/api/tasks');
            if (!response.ok) throw new Error('Network response was not ok');
            const tasks = await response.json();
            renderTasks(tasks);
        } catch (error) {
            console.error('Error fetching tasks:', error);
            if (taskList.children.length === 1 && taskList.children[0].textContent.includes('Loading')) {
                taskList.innerHTML = '<li class="task-item">Error loading tasks. Ensure the backend is running.</li>';
            }
        }
    };

    const renderTasks = (tasks) => {
        taskList.innerHTML = '';
        if (tasks.length === 0) {
            taskList.innerHTML = '<li class="task-item">No tasks found. Submit one above.</li>';
            return;
        }
        
        tasks.forEach(task => {
            const li = document.createElement('li');
            li.className = 'task-item';
            
            const statusClass = task.status === 'done' ? 'status-done' : 'status-pending';
            const created = new Date(task.created_at).toLocaleString();
            
            li.innerHTML = `
                <div>
                    <div class="payload">${escapeHTML(task.payload)}</div>
                    <div class="meta">ID: ${task.id} | Created: ${created}</div>
                </div>
                <div class="status ${statusClass}">${task.status.toUpperCase()}</div>
            `;
            taskList.appendChild(li);
        });
    };

    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = payloadInput.value.trim();
        if (!payload) return;

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload })
            });
            
            if (response.ok) {
                payloadInput.value = '';
                fetchTasks(); // Immediate refresh
            }
        } catch (error) {
            console.error('Error submitting task:', error);
        }
    });

    const escapeHTML = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    // Initial fetch and start polling every 3 seconds
    fetchTasks();
    setInterval(fetchTasks, 3000);
});

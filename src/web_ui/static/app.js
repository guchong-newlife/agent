(function() {
    const messagesEl = document.getElementById("messages");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const statusBar = document.getElementById("statusBar");
    const traceContent = document.getElementById("traceContent");
    const tracePanel = document.getElementById("tracePanel");
    const toggleTrace = document.getElementById("toggleTrace");

    let currentAssistantMsg = null;
    let isProcessing = false;
    let conversationId = null;

    function setStatus(text, cls) {
        statusBar.textContent = text;
        statusBar.className = "status-bar " + (cls || "");
    }

    function addMessage(role, content) {
        const div = document.createElement("div");
        div.className = "message " + role;
        div.innerHTML = content;
        messagesEl.appendChild(div);
        scrollToBottom();
        return div;
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addTraceStep(step) {
        if (traceContent.querySelector(".trace-empty")) {
            traceContent.innerHTML = "";
        }

        const div = document.createElement("div");
        div.className = "trace-step";

        if (step.event_type === "final_answer") {
            div.classList.add("final-step");
        }

        const eventLabel = step.event_type === "tool_call" ? "调用工具" :
                           step.event_type === "tool_result" ? "返回结果" : "完成";

        div.innerHTML = `
            <div class="step-header">
                <span class="step-number">#${step.step_number} ${eventLabel}</span>
                <span class="tool-name tool-${step.event_type === 'tool_call' ? 'call' : 'result'}">${step.tool_name || ''}</span>
            </div>
            ${step.arguments ? `<div class="step-args">${JSON.stringify(step.arguments, null, 2)}</div>` : ''}
            ${step.result_summary ? `<div class="step-detail">${step.result_summary}</div>` : ''}
            ${step.result_count > 0 ? `<span class="result-count">${step.result_count} 条结果</span>` : ''}
        `;
        traceContent.appendChild(div);
        traceContent.scrollTop = traceContent.scrollHeight;
    }

    function streamTraceSteps(trace) {
        traceContent.innerHTML = "";
        for (const step of trace) {
            addTraceStep(step);
        }
    }

    async function sendMessage() {
        const query = userInput.value.trim();
        if (!query || isProcessing) return;

        isProcessing = true;
        sendBtn.disabled = true;
        userInput.value = "";
        setStatus("思考中...", "thinking");

        // Remove welcome message if present
        const welcome = messagesEl.querySelector(".welcome-message");
        if (welcome) welcome.remove();

        addMessage("user", formatContent(query));
        currentAssistantMsg = addMessage("assistant", '<span class="status-bar thinking">分析问题中...</span>');
        traceContent.innerHTML = '<div class="trace-empty">搜索进行中...</div>';

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, conversation_id: conversationId }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let assistantContent = "";
            let isAnswering = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                let eventType = "";
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith("data: ")) {
                        const data = line.slice(6);
                        handleSSEEvent(eventType, data);
                    }
                }
            }

            function handleSSEEvent(type, data) {
                try {
                    const payload = JSON.parse(data);
                    switch (type) {
                        case "conversation_id":
                            conversationId = payload.conversation_id;
                            break;

                        case "tool_call":
                            setStatus(`正在搜索: ${payload.tool_name}...`, "searching");
                            addTraceStep({
                                event_type: "tool_call",
                                step_number: payload.iteration,
                                tool_name: payload.tool_name,
                                arguments: payload.arguments,
                            });
                            if (!isAnswering && currentAssistantMsg) {
                                currentAssistantMsg.innerHTML = `<span class="status-bar searching">正在调用 ${payload.tool_name} 获取信息...</span>`;
                            }
                            break;

                        case "tool_result":
                            setStatus(`获取结果: ${payload.result_summary}`, "searching");
                            addTraceStep({
                                event_type: "tool_result",
                                step_number: payload.iteration,
                                tool_name: payload.tool_name,
                                result_summary: payload.result_summary,
                                result_count: payload.result_count,
                            });
                            break;

                        case "final_answer":
                            isAnswering = true;
                            setStatus("生成回答中...", "answering");
                            assistantContent = payload.content;
                            if (currentAssistantMsg) {
                                currentAssistantMsg.innerHTML = formatContent(assistantContent) + formatSources(payload.trace);
                            }
                            setStatus(`完成 (共 ${payload.iterations} 轮搜索)`, "");
                            // Re-render trace with final state
                            if (payload.trace) {
                                streamTraceSteps(payload.trace);
                            }
                            break;

                        case "error":
                            if (currentAssistantMsg) {
                                currentAssistantMsg.innerHTML = `<span class="status-bar" style="color:var(--error)">错误: ${payload.message}</span>`;
                            }
                            setStatus("出错", "error");
                            break;
                    }
                } catch (e) {
                    // Ignore parse errors for non-JSON data
                }
            }

            if (!assistantContent && currentAssistantMsg) {
                currentAssistantMsg.innerHTML = '<span style="color:var(--text2)">未能获取有效回答，请重试。</span>';
            }
        } catch (error) {
            if (currentAssistantMsg) {
                currentAssistantMsg.innerHTML = `<span style="color:var(--error)">连接错误: ${error.message}</span>`;
            }
            setStatus("连接失败", "error");
        } finally {
            isProcessing = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    function formatContent(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\n/g, "<br>")
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<span class="source-tag" title="$2">$1</span>')
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/`([^`]+)`/g, "<code>$1</code>");
    }

    function formatSources(trace) {
        if (!trace || trace.length === 0) return "";
        const sources = new Set();
        for (const step of trace) {
            if (step.tool_name && step.event_type === "tool_call") {
                const nameMap = {
                    "search_relational_db": "关系数据库",
                    "search_vector_store": "向量搜索",
                    "search_keywords": "关键词搜索",
                    "search_logs": "日志系统",
                    "search_code": "代码仓库",
                    "hr_search_employees": "HR系统",
                    "hr_get_org_chart": "HR系统",
                    "hr_get_direct_reports": "HR系统",
                    "hr_get_department_employees": "HR系统",
                    "crm_search_customers": "CRM系统",
                    "crm_get_customer_orders": "CRM系统",
                    "crm_search_products": "CRM系统",
                    "doc_search_documents": "文档管理",
                    "doc_get_documents_by_type": "文档管理",
                    "pm_search_projects": "项目管理",
                    "pm_get_project_tasks": "项目管理",
                    "pm_get_team_workload": "项目管理",
                };
                sources.add(nameMap[step.tool_name] || step.tool_name);
            }
        }
        if (sources.size === 0) return "";
        return '<div style="margin-top:8px;font-size:12px;color:var(--text2)">数据来源: ' +
            Array.from(sources).map(s => `<span class="source-tag">${s}</span>`).join(" ") +
            '</div>';
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    toggleTrace.addEventListener("click", function() {
        tracePanel.classList.toggle("hidden");
        this.textContent = tracePanel.classList.contains("hidden") ? "追踪面板" : "隐藏追踪";
    });
})();

<template>
  <div class="chat-placeholder" aria-label="Helios chat loading">
    <div class="chat-header">
      <span class="chat-badge">HELIOS / COPILOT</span>
      <span class="chat-state">Connecting</span>
    </div>

    <div class="chat-panel">
      <div class="bubble bubble-user">
        Ask about recovery, sleep, or the next best step.
      </div>
      <div class="bubble bubble-assistant">
        Loading your biological context and the supporting signals.
      </div>
    </div>

    <div class="chat-footer">
      <span class="pulse" />
      <span class="footer-copy">Chat unlocks as you near this section.</span>
    </div>
  </div>
</template>

<style scoped>
.chat-placeholder {
  width: 100%;
  min-height: 24rem;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  background:
    radial-gradient(circle at top right, rgba(0, 212, 170, 0.14), transparent 34%),
    radial-gradient(circle at bottom left, rgba(0, 180, 216, 0.12), transparent 32%),
    linear-gradient(180deg, rgba(10, 15, 28, 0.95), rgba(6, 11, 22, 0.98));
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
}

.chat-header,
.chat-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.chat-badge,
.chat-state,
.footer-copy {
  font-size: 0.56rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.chat-badge {
  color: #d8f8ff;
}

.chat-state {
  color: rgba(196, 225, 232, 0.64);
}

.chat-panel {
  display: grid;
  gap: 0.75rem;
  padding: 1.1rem 0;
}

.bubble {
  max-width: 85%;
  padding: 0.85rem 0.95rem;
  border-radius: 16px;
  font-size: 0.82rem;
  line-height: 1.45;
}

.bubble-user {
  margin-left: auto;
  color: #03131a;
  background: linear-gradient(135deg, #d6fffb, #7cefd7);
  border-bottom-right-radius: 5px;
}

.bubble-assistant {
  color: #eaf7fb;
  background: rgba(11, 28, 41, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-bottom-left-radius: 5px;
}

.chat-footer {
  justify-content: flex-start;
  color: rgba(196, 225, 232, 0.68);
}

.pulse {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: #00d4aa;
  box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.45);
  animation: pulse 1.8s infinite;
}

.footer-copy {
  color: rgba(196, 225, 232, 0.68);
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(0, 212, 170, 0.45);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(0, 212, 170, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(0, 212, 170, 0);
  }
}
</style>

<template>
  <div class="globe-placeholder" aria-label="Helios globe loading">
    <div class="globe-placeholder__panel">
      <div class="globe-placeholder__topline font-mono">
        <span>HELIOS / CALIBRATION</span>
        <span>COBE INIT</span>
      </div>

      <div class="globe-placeholder__scope" aria-hidden="true">
        <div class="globe-placeholder__grid" />
        <div class="globe-placeholder__arc globe-placeholder__arc--outer" />
        <div class="globe-placeholder__arc globe-placeholder__arc--inner" />
        <div class="globe-placeholder__trace" />
        <div class="globe-placeholder__pulse globe-placeholder__pulse--a" />
        <div class="globe-placeholder__pulse globe-placeholder__pulse--b" />
      </div>

      <div class="globe-placeholder__copy">
        <p class="globe-placeholder__eyebrow font-mono">Planetary model boot</p>
        <h1 class="globe-placeholder__title">Loading orbital frame</h1>
        <p class="globe-placeholder__body">
          Calibrating destination offsets, solar timing, and local space-weather context.
        </p>
      </div>

      <div class="globe-placeholder__progress" aria-hidden="true">
        <span class="globe-placeholder__progress-label font-mono">SYNC</span>
        <div class="globe-placeholder__progress-bar">
          <span />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.globe-placeholder {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: grid;
  place-items: center;
  overflow: hidden;
  padding: 1rem;
  background:
    radial-gradient(circle at 50% 34%, rgba(73, 193, 255, 0.14), transparent 30%),
    radial-gradient(circle at 64% 22%, rgba(94, 234, 212, 0.1), transparent 18%),
    linear-gradient(180deg, rgba(3, 8, 18, 0.72), rgba(2, 6, 18, 0.9));
}

.globe-placeholder::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 24%, rgba(255, 255, 255, 0.55) 0 0.08rem, transparent 0.11rem),
    radial-gradient(circle at 28% 38%, rgba(167, 231, 255, 0.46) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 48% 18%, rgba(255, 255, 255, 0.62) 0 0.08rem, transparent 0.11rem),
    radial-gradient(circle at 71% 28%, rgba(177, 232, 255, 0.48) 0 0.06rem, transparent 0.08rem),
    radial-gradient(circle at 82% 42%, rgba(255, 255, 255, 0.44) 0 0.06rem, transparent 0.08rem);
  opacity: 0.68;
  pointer-events: none;
}

.globe-placeholder__panel {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 1rem;
  width: min(48rem, calc(100% - 2rem));
  padding: 1rem 1rem 1.1rem;
  border-radius: 1.35rem;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    linear-gradient(180deg, rgba(7, 14, 27, 0.92), rgba(7, 14, 27, 0.76)),
    radial-gradient(circle at top right, rgba(94, 234, 212, 0.08), transparent 42%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 24px 52px rgba(2, 8, 20, 0.3);
  backdrop-filter: blur(16px);
}

.globe-placeholder__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  font-size: 0.58rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.82);
}

.globe-placeholder__scope {
  position: relative;
  min-height: 18rem;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background:
    radial-gradient(circle at 50% 16%, rgba(73, 193, 255, 0.12), transparent 20%),
    linear-gradient(180deg, rgba(3, 10, 22, 0.66), rgba(2, 7, 18, 0.86));
}

.globe-placeholder__grid,
.globe-placeholder__arc,
.globe-placeholder__trace,
.globe-placeholder__pulse {
  position: absolute;
}

.globe-placeholder__grid {
  inset: 0;
  background:
    repeating-linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.04) 0,
      rgba(255, 255, 255, 0.04) 1px,
      transparent 1px,
      transparent 40px
    ),
    repeating-linear-gradient(
      rgba(255, 255, 255, 0.035) 0,
      rgba(255, 255, 255, 0.035) 1px,
      transparent 1px,
      transparent 40px
    );
  mask-image: radial-gradient(circle at center, black 34%, transparent 86%);
  opacity: 0.52;
}

.globe-placeholder__arc {
  left: 50%;
  border-radius: 50%;
  transform: translateX(-50%);
}

.globe-placeholder__arc--outer {
  bottom: -18%;
  width: min(78vw, 34rem);
  height: min(78vw, 34rem);
  border: 1px solid rgba(111, 216, 255, 0.26);
  box-shadow: 0 0 30px rgba(73, 193, 255, 0.08);
}

.globe-placeholder__arc--inner {
  bottom: 12%;
  width: min(34vw, 15rem);
  height: min(34vw, 15rem);
  border: 1px solid rgba(255, 189, 118, 0.28);
}

.globe-placeholder__trace {
  left: 12%;
  right: 12%;
  bottom: 28%;
  height: 2px;
  background:
    linear-gradient(
      90deg,
      transparent 0%,
      rgba(111, 216, 255, 0.5) 18%,
      rgba(255, 189, 118, 0.88) 48%,
      rgba(94, 234, 212, 0.56) 76%,
      transparent 100%
    );
  opacity: 0.92;
}

.globe-placeholder__pulse {
  width: 0.7rem;
  height: 0.7rem;
  border-radius: 999px;
  box-shadow: 0 0 0 0 rgba(94, 234, 212, 0.2);
}

.globe-placeholder__pulse--a {
  top: 26%;
  left: 24%;
  background: rgba(94, 234, 212, 0.84);
}

.globe-placeholder__pulse--b {
  top: 36%;
  right: 20%;
  background: rgba(255, 189, 118, 0.9);
}

.globe-placeholder__copy {
  display: grid;
  gap: 0.42rem;
  max-width: 26rem;
}

.globe-placeholder__eyebrow {
  margin: 0;
  font-size: 0.56rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(210, 237, 245, 0.68);
}

.globe-placeholder__title {
  margin: 0;
  font-size: clamp(1.45rem, 2vw, 2.1rem);
  line-height: 1.04;
  letter-spacing: 0.04em;
  color: rgba(242, 251, 255, 0.96);
}

.globe-placeholder__body {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: rgba(220, 238, 244, 0.76);
}

.globe-placeholder__progress {
  display: grid;
  gap: 0.42rem;
}

.globe-placeholder__progress-label {
  font-size: 0.54rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.78);
}

.globe-placeholder__progress-bar {
  height: 0.44rem;
  overflow: hidden;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(4, 10, 21, 0.76);
}

.globe-placeholder__progress-bar > span {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 189, 118, 0.92), rgba(94, 234, 212, 0.82));
}

@media (max-width: 640px) {
  .globe-placeholder {
    min-height: 340px;
    padding: 0.75rem;
  }

  .globe-placeholder__panel {
    width: min(100%, calc(100% - 0.5rem));
    padding: 0.9rem 0.9rem 1rem;
    border-radius: 1.15rem;
  }

  .globe-placeholder__scope {
    min-height: 14rem;
  }

  .globe-placeholder__topline {
    font-size: 0.52rem;
    letter-spacing: 0.14em;
  }

  .globe-placeholder__body {
    font-size: 0.74rem;
  }
}
</style>

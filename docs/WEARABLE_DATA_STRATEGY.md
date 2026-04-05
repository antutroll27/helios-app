# HELIOS — Wearable Data Strategy

## The Insight

Every major wearable platform lets users export their own health data. HELIOS doesn't need corporate API partnerships to deliver personalized circadian intelligence. Users own their data — we give them a reason to bring it to us.

---

## Platform Compatibility

| Platform | Export Format | Sleep-Only Size | Integration Difficulty | Key Biometrics Available |
|---|---|---|---|---|
| **Oura Ring** | JSON | ~5 MB/year | Trivial — maps 1:1 to our data model | Sleep stages, HRV (rMSSD), skin temp, respiratory rate, readiness score |
| **Whoop** | CSV | ~5 MB/year | Easy — clean columns, well-labeled | Sleep stages, HRV (rMSSD), skin temp, respiratory rate, recovery score |
| **Fitbit / Google Fit** | JSON (Google Takeout) | ~10-30 MB/year | Easy — filter sleep records from Takeout | Sleep stages, HRV (rMSSD + SDNN), skin temp deviation, resting HR |
| **Samsung Health** | CSV | ~5-10 MB/year | Easy — standard CSV | Sleep stages, HR, stress score, SpO2 |
| **Garmin Connect** | FIT binary | ~5-20 MB/year | Medium — needs FIT parser library | Sleep stages, HRV, stress, Body Battery, resting HR |
| **Apple Health** | XML | 500 MB-2 GB total | Hard — monolithic XML, streaming parse | ALL synced device data — universal import for iOS users |

### The Apple Health Multiplier

iOS users who sync Oura, Garmin, Fitbit, or Whoop to Apple Health can export **everything in one file**. One upload = their entire wearable history across all devices. This makes Apple Health export a universal import path.

---

## How It Works

### User Experience

```
1. User exports data from their wearable app
   (Oura: Settings → Download My Data)
   (Fitbit: Google Takeout → Select Fitbit)
   (Apple Health: Settings → Health → Export All Health Data)

2. User drags the file onto HELIOS
   (drag-and-drop zone in the app, or paste into chat)

3. HELIOS auto-detects the platform and parses the data
   (no manual selection needed — format detection is automatic)

4. Within seconds, the user gets personalized insights:
   "Based on 14 nights of Oura data, you're a Moderate Late
    chronotype (MSFsc 05:15). Your HRV drops 18% on nights
    after afternoon caffeine. Adjusting your protocol..."
```

### No OAuth. No Partnerships. No Waiting.

The user owns their data and brings it to us. This approach:
- **Ships immediately** — no business development timelines
- **Works globally** — no geographic API restrictions
- **Respects privacy** — user controls what they share
- **Covers every platform** — if it exports, we can parse it
- **GDPR-friendly** — user-initiated data transfer

---

## Technical Architecture

### Data Model

Our existing `SleepLog` dataclass already has every field we need:

```python
@dataclass
class SleepLog:
    date: str
    sleep_onset: datetime
    wake_time: datetime
    total_sleep_min: int
    deep_sleep_min: Optional[int] = None
    rem_sleep_min: Optional[int] = None
    hrv_avg: Optional[float] = None        # rMSSD from wearable
    skin_temp_delta: Optional[float] = None # deviation from baseline
    resting_hr: Optional[float] = None
    sleep_score: Optional[int] = None
    source: str = "manual"                  # "oura" | "fitbit" | "garmin" | etc.
```

### Parser Adapter Pattern

Each platform gets a parser that normalizes into our data model:

```python
class WearableParser(Protocol):
    def parse(self, file_content: bytes, filename: str) -> list[SleepLog]: ...

class OuraParser(WearableParser): ...      # JSON → SleepLog
class WhoopParser(WearableParser): ...     # CSV → SleepLog
class FitbitParser(WearableParser): ...    # JSON → SleepLog
class GarminParser(WearableParser): ...    # FIT binary → SleepLog
class AppleHealthParser(WearableParser): ... # XML streaming → SleepLog
class SamsungParser(WearableParser): ...   # CSV → SleepLog
```

### Auto-Detection

HELIOS identifies the platform automatically from the file:

```python
def detect_platform(filename: str, content_sample: bytes) -> str:
    if filename.endswith('.fit'):
        return 'garmin'
    if b'bedtime_start' in content_sample:
        return 'oura'
    if b'HKQuantityTypeIdentifier' in content_sample:
        return 'apple_health'
    if b'Sleep Start' in content_sample and b'HRV' in content_sample:
        return 'whoop'
    if b'sleep-' in content_sample and b'levels' in content_sample:
        return 'fitbit'
    # ... fallback detection
```

### Data Flow

```
File Upload → Auto-Detect Platform → Route to Parser
    → Extract SleepLog + Biometric entries
    → Store in Supabase (per-user, structured tables)
    → ChronotypeEngine assesses chronotype from sleep logs
    → CaffeineModel correlates with caffeine intake
    → SpaceWeatherBioModel correlates with Kp/HRV patterns
    → Hermes Agent distills insights into user memory
    → Next conversation is deeply personalized
```

---

## What We Extract — Beyond Sleep

HELIOS doesn't just track when you sleep. We extract the full biometric picture to enable ISS-grade circadian analysis:

| Metric | What It Tells Us | Scientific Basis |
|---|---|---|
| **HRV (rMSSD)** | Parasympathetic tone, circadian phase marker, geomagnetic storm impact | Alabdali 2022 (n=809), Woelders 2023 |
| **HRV (SDNN)** | Overall autonomic variability, recovery quality | McCraty 2018 |
| **Resting HR** | Circadian rhythm marker — HR acrophase estimates circadian phase | Kolbe 2024 |
| **Skin/Wrist Temperature** | Core body temp proxy (skin max ≈ core min), sleep readiness signal | Cuesta 2017, Martinez-Nicolas 2019 |
| **Sleep Stages** | Deep/REM/light architecture for protocol effectiveness scoring | — |
| **Respiratory Rate** | Sleep quality indicator, illness early warning | — |
| **SpO2** | Sleep apnea screening, altitude adaptation effects | — |

### The Unique Advantage: Space Weather × Personal Biometrics

No other product combines **real-time NASA/NOAA space weather data** with **personal HRV measurements**. HELIOS can show users:

> "Your HRV dropped 22% last Tuesday. That correlates with a Kp 5 geomagnetic storm that hit 18 hours earlier (Alabdali 2022). This isn't random — your autonomic nervous system responds to space weather. We've adjusted tonight's wind-down to start 30 minutes earlier."

This is the kind of insight that turns users into believers and investors into backers.

---

## Supabase Schema

```sql
-- Core user data
users              -- auth, profile, encrypted LLM API keys
chat_sessions      -- full conversation logs
chat_messages      -- individual messages (role, content, timestamp)
memories           -- Mem0 distilled insights (semantic/episodic/procedural)

-- Wearable data pipeline
data_imports       -- uploaded files (source platform, date range, status, row count)
sleep_logs         -- nightly sleep data (maps to SleepLog dataclass)
biometric_logs     -- HR, HRV, skin temp, respiratory rate, SpO2 time series

-- Protocol tracking
protocol_logs      -- daily recommended vs actual protocol adherence
caffeine_logs      -- intake events for CaffeineModel
```

---

## Roadmap

### v1: File Upload (Now)
- User exports data from wearable app
- Drags file onto HELIOS
- Parsers extract and store data
- Hermes Agent learns from accumulated data
- **No API partnerships needed**

### v2: Live API Sync (Future)
- OAuth integration with Garmin Connect, Oura API v2, Fitbit Web API
- Automatic daily sync — no manual export
- Real-time notifications ("Your HRV is trending down, start wind-down early tonight")
- **Requires partnership agreements**

### v3: Custom Wearable Hardware (Long-term)
- Affordable, stylish, sleep-specific wearable
- Optimized sensors: wrist temperature, PPG (HRV), accelerometer
- Direct BLE sync to HELIOS — no third-party app needed
- The full stack: hardware + software + circadian science
- **HELIOS software is the foundation the hardware plugs into**

---

## Competitive Moat

| Feature | HELIOS | Sleep Trackers (Oura, Whoop) | Sleep Apps (Sleep Cycle, etc.) |
|---|---|---|---|
| Peer-reviewed circadian science | 28 papers, quantitative models | Basic sleep scoring | None |
| Space weather correlation | NASA/NOAA real-time data | No | No |
| Personalized caffeine model | CYP1A2/ADORA2A profiling | No | No |
| Learning agent | Hermes + Mem0, evolves per user | Static algorithms | No |
| Multi-platform data import | 6 platforms, file upload | Own device only | Phone sensors only |
| Open scientific knowledge base | Exact citations in every response | Proprietary algorithms | None |

---

*HELIOS — Circadian Intelligence Engine*
*Hackathon Winner, Da Nang Digital Nomad Fest 2026*
*Investor inquiries: [contact info]*

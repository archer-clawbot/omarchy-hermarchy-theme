.pragma library

var SIGNAL_FOR_STATE = {
  idle: "muted",
  executing: "cyan",
  waiting: "amber",
  completed: "green",
  failed: "red",
  unavailable: "muted",
  unknown: "muted"
}

function fallback() {
  return {
    schemaVersion: 1,
    observedAt: "",
    state: "unknown",
    signal: "muted",
    node: "—",
    gateway: { state: "unknown" },
    agent: { id: "agent", name: "Hermes", available: false },
    activity: {
      sessionId: null,
      task: null,
      detail: null,
      lastActivityAt: null,
      lastActivity: null,
      endReason: null,
      activeWorkers: 0
    },
    runtime: { model: null, provider: null },
    source: { adapter: "unknown", confidence: "unknown" }
  }
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value)
}

function contains(values, value) {
  for (var index = 0; index < values.length; index++) {
    if (values[index] === value) return true
  }
  return false
}

function hasExactKeys(value, expected) {
  if (!isObject(value)) return false
  var actual = Object.keys(value).sort()
  var wanted = expected.slice().sort()
  if (actual.length !== wanted.length) return false
  for (var index = 0; index < wanted.length; index++) {
    if (actual[index] !== wanted[index]) return false
  }
  return true
}

function isNullableString(value) {
  return value === null || typeof value === "string"
}

function isDateTime(value) {
  if (typeof value !== "string") return false
  var match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-](\d{2}):(\d{2}))$/)
  if (!match) return false
  var year = Number(match[1])
  var month = Number(match[2])
  var day = Number(match[3])
  var hour = Number(match[4])
  var minute = Number(match[5])
  var second = Number(match[6])
  var offsetHour = match[7] === undefined ? 0 : Number(match[7])
  var offsetMinute = match[8] === undefined ? 0 : Number(match[8])
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return false
  if (offsetHour > 23 || offsetMinute > 59) return false
  var leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  var days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  return day >= 1 && day <= days[month - 1]
}

function accept(value) {
  var topKeys = ["schemaVersion", "observedAt", "state", "signal", "node", "gateway", "agent", "activity", "runtime", "source"]
  if (!hasExactKeys(value, topKeys) || value.schemaVersion !== 1) return fallback()
  if (!isDateTime(value.observedAt)) return fallback()
  if (typeof value.state !== "string" || SIGNAL_FOR_STATE[value.state] === undefined) return fallback()
  if (value.signal !== SIGNAL_FOR_STATE[value.state]) return fallback()
  if (typeof value.node !== "string" || value.node.length === 0) return fallback()

  if (!hasExactKeys(value.gateway, ["state"])) return fallback()
  if (!contains(["active", "inactive", "activating", "deactivating", "failed", "unknown"], value.gateway.state)) return fallback()

  if (!hasExactKeys(value.agent, ["id", "name", "available"])) return fallback()
  if (typeof value.agent.id !== "string" || value.agent.id.length === 0) return fallback()
  if (typeof value.agent.name !== "string" || value.agent.name.length === 0) return fallback()
  if (typeof value.agent.available !== "boolean") return fallback()

  var activityKeys = ["sessionId", "task", "detail", "lastActivityAt", "lastActivity", "endReason", "activeWorkers"]
  if (!hasExactKeys(value.activity, activityKeys)) return fallback()
  var nullableActivity = ["sessionId", "task", "detail", "lastActivityAt", "lastActivity", "endReason"]
  for (var index = 0; index < nullableActivity.length; index++) {
    if (!isNullableString(value.activity[nullableActivity[index]])) return fallback()
  }
  if (value.activity.lastActivityAt !== null && !isDateTime(value.activity.lastActivityAt)) return fallback()
  var workers = value.activity.activeWorkers
  if (typeof workers !== "number" || !isFinite(workers) || workers < 0 || Math.floor(workers) !== workers) return fallback()

  var successReasons = ["complete", "completed", "finished", "success", "succeeded", "task_completed"]
  var failureReasons = ["error", "exception", "failed", "failure", "task_failed", "tool_error"]
  if (value.state === "completed" && !contains(successReasons, value.activity.endReason)) return fallback()
  if (value.state === "failed" && !contains(failureReasons, value.activity.endReason)) return fallback()

  if (!hasExactKeys(value.runtime, ["model", "provider"])) return fallback()
  if (!isNullableString(value.runtime.model) || !isNullableString(value.runtime.provider)) return fallback()

  if (!hasExactKeys(value.source, ["adapter", "confidence"])) return fallback()
  if (typeof value.source.adapter !== "string" || value.source.adapter.length === 0) return fallback()
  if (!contains(["observed", "inferred", "explicit", "unknown"], value.source.confidence)) return fallback()
  return value
}

function indicator(value) {
  var state = accept(value)
  var suffixes = {
    idle: "·",
    executing: "●",
    waiting: "● INPUT",
    completed: "● DONE",
    failed: "● FAILED",
    unavailable: "·",
    unknown: "·"
  }
  return { label: "HERMES", suffix: suffixes[state.state], signal: state.signal }
}

function display(value, fallbackValue) {
  if (value === undefined || value === null) return fallbackValue
  var text = String(value).trim()
  return text === "" ? fallbackValue : text
}

function modelName(value) {
  var text = display(value, "—")
  var match = text.match(/^([A-Za-z]+)-([0-9][^-]*)(?:-(.*))?$/)
  if (!match) return text.replace(/-/g, " ").toUpperCase()
  return (match[1] + "-" + match[2] + (match[3] ? " " + match[3].replace(/-/g, " ") : "")).toUpperCase()
}

function eventTime(value) {
  var text = display(value, "")
  var match = text.match(/^\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}:\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/)
  return match ? match[1] + " " + match[2] : "—"
}

function workerText(value) {
  var count = Math.max(0, Math.floor(Number(value) || 0))
  var padded = count < 10 ? "0" + count : String(count)
  return padded + (count === 1 ? " ACTIVE" : " ACTIVE")
}

function upperWords(value) {
  return display(value, "—").replace(/[-_]/g, " ").toUpperCase()
}

function panel(value) {
  var state = accept(value)
  return {
    agentName: upperWords(state.agent.name),
    state: state.state.toUpperCase(),
    task: display(state.activity.task, "—"),
    detail: display(state.activity.detail, "—"),
    model: modelName(state.runtime.model),
    provider: upperWords(state.runtime.provider),
    workers: workerText(state.activity.activeWorkers),
    node: upperWords(state.node),
    gateway: upperWords(state.gateway.state),
    lastActivity: display(state.activity.lastActivity, "—"),
    lastActivityAt: eventTime(state.activity.lastActivityAt),
    endReason: upperWords(state.activity.endReason)
  }
}

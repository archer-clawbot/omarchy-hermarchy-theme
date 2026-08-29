import QtQuick
import QtTest
import "../../extras/quickshell/StateModel.js" as StateModel

TestCase {
  name: "HermarchyStateModel"

  function baseState() {
    return {
      schemaVersion: 1,
      observedAt: "2033-05-18T03:33:20Z",
      state: "idle",
      signal: "muted",
      node: "workstation",
      gateway: { state: "active" },
      agent: { id: "hermes", name: "Hermes", available: true },
      activity: {
        sessionId: "session-1",
        task: "Provider enrichment",
        detail: "Delegating evidence checks",
        lastActivityAt: "2033-05-18T03:33:07Z",
        lastActivity: "Running workers",
        endReason: null,
        activeWorkers: 2
      },
      runtime: { model: "gpt-5.6-sol", provider: "openai-codex" },
      source: { adapter: "hermes-local", confidence: "observed" }
    }
  }

  function test_indicatorLabelsStayRestrained() {
    var state = baseState()
    compare(StateModel.indicator(state), { label: "HERMES", suffix: "·", signal: "muted" })

    state.state = "executing"; state.signal = "cyan"
    compare(StateModel.indicator(state), { label: "HERMES", suffix: "●", signal: "cyan" })

    state.state = "waiting"; state.signal = "amber"
    compare(StateModel.indicator(state), { label: "HERMES", suffix: "● INPUT", signal: "amber" })

    state.state = "failed"; state.signal = "red"; state.activity.endReason = "task_failed"
    compare(StateModel.indicator(state), { label: "HERMES", suffix: "● FAILED", signal: "red" })
  }

  function test_panelPresentationUsesContractFields() {
    var state = baseState()
    state.state = "executing"
    state.signal = "cyan"

    var panel = StateModel.panel(state)
    compare(panel.agentName, "HERMES")
    compare(panel.state, "EXECUTING")
    compare(panel.task, "Provider enrichment")
    compare(panel.detail, "Delegating evidence checks")
    compare(panel.model, "GPT-5.6 SOL")
    compare(panel.provider, "OPENAI CODEX")
    compare(panel.workers, "02 ACTIVE")
    compare(panel.node, "WORKSTATION")
    compare(panel.gateway, "ACTIVE")
    compare(panel.lastActivity, "Running workers")
    compare(panel.lastActivityAt, "03:33:07 Z")
    compare(panel.endReason, "—")
  }

  function test_invalidOrMismatchedRecordsFailMuted() {
    compare(StateModel.accept(null).state, "unknown")
    compare(StateModel.accept([]).state, "unknown")

    var state = baseState()
    state.signal = "red"
    var accepted = StateModel.accept(state)
    compare(accepted.state, "unknown")
    compare(accepted.signal, "muted")
  }

  function test_malformedNestedRecordsFailMuted() {
    var records = []
    var state

    state = baseState(); state.observedAt = "2033-05-18 03:33:20Z"; records.push(state)
    state = baseState(); state.activity.lastActivityAt = "not-a-date"; records.push(state)
    state = baseState(); state.gateway.state = "online"; records.push(state)
    state = baseState(); state.activity.task = { text: "Provider enrichment" }; records.push(state)
    state = baseState(); state.runtime.model = ["gpt-5.6-sol"]; records.push(state)
    state = baseState(); delete state.agent.id; records.push(state)
    state = baseState(); delete state.source.adapter; records.push(state)
    state = baseState(); state.source.confidence = "certain"; records.push(state)
    state = baseState(); state.activity.activeWorkers = 1.5; records.push(state)
    state = baseState(); state.unexpected = true; records.push(state)
    state = baseState(); state.gateway.unexpected = true; records.push(state)
    state = baseState(); state.state = "completed"; state.signal = "green"; state.activity.endReason = "maybe"; records.push(state)

    for (var index = 0; index < records.length; index++) {
      var accepted = StateModel.accept(records[index])
      compare(accepted.state, "unknown", "malformed record " + index + " was accepted")
      compare(accepted.signal, "muted", "malformed record " + index + " was not muted")
    }
  }

  function test_allSupportedStatesKeepTextAndSignalInSync() {
    var cases = [
      ["idle", "muted", "·", null],
      ["executing", "cyan", "●", null],
      ["waiting", "amber", "● INPUT", null],
      ["completed", "green", "● DONE", "completed"],
      ["failed", "red", "● FAILED", "tool_error"],
      ["unavailable", "muted", "·", null],
      ["unknown", "muted", "·", null]
    ]

    for (var index = 0; index < cases.length; index++) {
      var state = baseState()
      state.state = cases[index][0]
      state.signal = cases[index][1]
      state.activity.endReason = cases[index][3]
      var indicator = StateModel.indicator(state)
      compare(indicator.suffix, cases[index][2], state.state)
      compare(indicator.signal, cases[index][1], state.state)
      compare(StateModel.panel(state).state, state.state.toUpperCase(), state.state)
    }
  }

  function test_missingOptionalFieldsUseQuietFallbacks() {
    var state = baseState()
    state.activity.task = null
    state.activity.detail = null
    state.activity.lastActivityAt = null
    state.activity.lastActivity = null
    state.runtime.model = null
    state.runtime.provider = null

    var panel = StateModel.panel(state)
    compare(panel.task, "—")
    compare(panel.detail, "—")
    compare(panel.model, "—")
    compare(panel.provider, "—")
    compare(panel.lastActivity, "—")
    compare(panel.endReason, "—")
    compare(panel.lastActivityAt, "—")
  }

  function test_completedStateHasCompactDoneSuffix() {
    var state = baseState()
    state.state = "completed"
    state.signal = "green"
    state.activity.endReason = "completed"
    compare(StateModel.indicator(state).suffix, "● DONE")
  }
}

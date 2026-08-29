import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "StateModel.js" as StateModel

Panel {
  id: root
  moduleName: "io.github.archer-clawbot.hermarchy-agent"
  ipcTarget: "io.github.archer-clawbot.hermarchy-agent"
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  property var stateRecord: StateModel.fallback()
  property bool refreshing: false
  readonly property var barIdentity: hostWidget || root
  readonly property var indicator: StateModel.indicator(stateRecord)
  readonly property var presentation: StateModel.panel(stateRecord)
  readonly property int refreshSeconds: Math.max(1, Math.min(60, parseInt(setting("refreshIntervalSec", 2), 10) || 2))
  readonly property string readerPath: Quickshell.env("HOME") + "/.config/omarchy/plugins/io.github.archer-clawbot.hermarchy-agent/scripts/hermarchy-state-read"
  readonly property color foreground: bar ? bar.foreground : Color.foreground
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property color mutedColor: "#606468"
  readonly property color cyanColor: "#61D6FF"
  readonly property color amberColor: "#E2C275"
  readonly property color greenColor: "#86D993"
  readonly property color redColor: "#E46E6E"
  readonly property color signalColor: colorForSignal(stateRecord.signal)

  function colorForSignal(signal) {
    if (signal === "cyan") return cyanColor
    if (signal === "amber") return amberColor
    if (signal === "green") return greenColor
    if (signal === "red") return redColor
    return mutedColor
  }

  function refresh() {
    if (!stateProcess.running) {
      refreshing = true
      stateProcess.running = true
    }
  }

  function acceptOutput(raw) {
    try {
      stateRecord = StateModel.accept(JSON.parse(String(raw || "")))
    } catch (error) {
      stateRecord = StateModel.fallback()
    }
  }

  function open() {
    root.controller.show()
    refresh()
  }

  function close() { root.controller.hide() }
  function toggle() { root.opened ? close() : open() }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function")
      return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  Process {
    id: stateProcess
    command: [root.readerPath]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.acceptOutput(text)
    }
    onExited: function(exitCode) {
      root.refreshing = false
      if (exitCode !== 0) root.stateRecord = StateModel.fallback()
    }
  }

  Timer {
    interval: root.refreshSeconds * 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  IpcHandler {
    target: root.ipcTarget
    function open(): void { root.open() }
    function close(): void { root.close() }
    function show(): void { root.open() }
    function hide(): void { root.close() }
    function toggle(): void { root.toggle() }
    function refresh(): string { root.refresh(); return "ok" }
    function state(): string { return root.stateRecord.state }
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(420))
    contentHeight: panel.fittedContentHeight(content.implicitHeight, Style.space(440))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Column {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: Style.space(13)

        Text {
          text: "01 // AGENT"
          color: root.mutedColor
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
          font.letterSpacing: 1.3
        }

        Row {
          width: parent.width
          spacing: Style.space(8)

          Text {
            width: Math.min(implicitWidth, parent.width * 0.52)
            text: root.presentation.agentName
            color: root.foreground
            font.family: root.fontFamily
            font.pixelSize: Style.font.title
            font.bold: true
            font.letterSpacing: 1.1
            elide: Text.ElideRight
          }

          Text {
            anchors.baseline: parent.children[0].baseline
            text: root.indicator.suffix === "·" ? "·" : "●"
            color: root.signalColor
            font.family: root.fontFamily
            font.pixelSize: Style.font.body
          }

          Item { width: Math.max(0, parent.width - parent.children[0].implicitWidth - parent.children[1].implicitWidth - parent.children[3].implicitWidth - parent.spacing * 3); height: 1 }

          Text {
            anchors.baseline: parent.children[0].baseline
            text: root.presentation.state
            color: root.signalColor
            font.family: root.fontFamily
            font.pixelSize: Style.font.bodySmall
            font.bold: true
            font.letterSpacing: 0.8
          }
        }

        PanelSeparator { foreground: root.foreground }

        Column {
          width: parent.width
          spacing: Style.space(9)
          ActivityText { label: "TASK"; value: root.presentation.task }
          ActivityText {
            label: "DETAIL"
            value: root.presentation.detail
            visible: value !== "—"
          }
          InfoRow { label: "MODEL"; value: root.presentation.model }
          InfoRow {
            label: "PROVIDER"
            value: root.presentation.provider
            visible: value !== "—"
          }
          InfoRow { label: "WORKERS"; value: root.presentation.workers }
          InfoRow { label: "NODE"; value: root.presentation.node }
          InfoRow { label: "GATEWAY"; value: root.presentation.gateway }
          ActivityText {
            label: "LAST ACTIVITY"
            value: root.presentation.lastActivity
            visible: value !== "—"
          }
          InfoRow {
            label: "ACTIVITY AT"
            value: root.presentation.lastActivityAt
            visible: value !== "—"
          }
          InfoRow {
            label: "END REASON"
            value: root.presentation.endReason
            visible: value !== "—"
          }
        }
      }
    }
  }

  component ActivityText: Column {
    id: activityText
    property string label: ""
    property string value: ""
    width: parent.width
    spacing: Style.space(3)

    Text {
      text: activityText.label
      color: root.mutedColor
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
      font.letterSpacing: 0.9
    }

    Text {
      width: activityText.width
      text: activityText.value
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Style.font.bodySmall
      font.bold: true
      wrapMode: Text.WrapAnywhere
      maximumLineCount: 2
      elide: Text.ElideRight
    }
  }

  component InfoRow: Row {
    id: infoRow
    property string label: ""
    property string value: ""
    width: parent.width
    spacing: Style.space(8)

    Text {
      text: infoRow.label
      color: root.mutedColor
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
      font.letterSpacing: 0.9
    }

    Item {
      width: Math.max(0, infoRow.width - infoRow.children[0].implicitWidth - infoRow.children[2].implicitWidth - infoRow.spacing * 2)
      height: 1
    }

    Text {
      width: Math.min(implicitWidth, infoRow.width * 0.68)
      text: infoRow.value
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Style.font.bodySmall
      font.bold: true
      horizontalAlignment: Text.AlignRight
      elide: Text.ElideRight
    }
  }
}

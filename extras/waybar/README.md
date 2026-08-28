# Optional Waybar status module

Current Omarchy uses its native Quickshell bar and Agents panel. This directory
is for Waybar users and older Omarchy installations; it is deliberately not
installed automatically.

Add this module to your Waybar configuration:

```jsonc
"custom/hermes": {
  "exec": "/path/to/omarchy-hermes-theme/extras/waybar/hermes-status.sh",
  "return-type": "json",
  "interval": 5
}
```

Then include `custom/hermes` in the desired module list. Suggested CSS:

```css
#custom-hermes {
  color: #61D6FF;
  font-family: "IBM Plex Mono";
  letter-spacing: 0.08em;
}
#custom-hermes.offline { color: #606468; }
```

The module only reports the local `hermes-gateway.service` state. It neither
starts nor modifies the service.

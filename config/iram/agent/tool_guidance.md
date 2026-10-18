# IRAM OS Tool Guidance & Execution Recipes

## Hyprland Window Management
- Switch Workspace: `hyprctl dispatch workspace <1-10>`
- Focus Window by Class: `hyprctl dispatch focuswindow "^(class_name)$"`
- Toggle Floating: `hyprctl dispatch togglefloating`
- Center Window: `hyprctl dispatch centerwindow`
- Move Active to Workspace: `hyprctl dispatch movetoworkspace <N>`
- Close Active Window: `hyprctl dispatch killactive`

## PipeWire Audio Management
- Check Audio Status: `wpctl status`
- Adjust Volume: `wpctl set-volume @DEFAULT_AUDIO_SINK@ <level>%` (e.g. `50%`)
- Toggle Mute: `wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle`
- Toggle Sinks: `~/.local/bin/iram-audio-toggle`

## Desktop & Themes
- Apply Theme: `iram theme set "<theme_name>"` (e.g., `tokyo-storm`, `nord-frost`, `cyberpunk-neon`)
- Synchronize Desktop Styling: `~/.local/bin/iram-theme-sync-all`
- Launch GUI Theme Picker: `~/.local/bin/iram-theme-switch`

## Storytold Craft Suite
- PhotoCraft: `craft-photocraft`
- VectorCraft: `craft-vectorcraft`
- CADCraft: `craft-cadcraft`
- DeckCraft: `craft-deckcraft`
- FilmCraft: `craft-filmcraft`
- WordCraft: `craft-wordcraft`
- GridCraft: `craft-gridcraft`

## Notifications
- Desktop Alert: `notify-send -a "Iram Agent" "<Title>" "<Body>"`

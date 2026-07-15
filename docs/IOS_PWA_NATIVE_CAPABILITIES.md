# iOS and PWA Native Capabilities

## Goal

Make GlucoPlate feel like a high-quality iPhone app while keeping the deployment model simple as a PWA.

## iOS PWA requirements

- Use `viewport-fit=cover`.
- Respect safe-area insets for header, bottom navigation, sticky controls, and modals.
- Provide Apple touch icons and install metadata.
- Keep notification enablement behind a user gesture.
- Explain that iPhone push requires adding the app to the Home Screen.
- Keep service worker scope at `/` for full app navigation.

## Device manager layer

Create a small frontend device manager that centralizes capability checks.

Suggested responsibilities:

- `isIOS()`
- `isStandalone()`
- `supportsNotifications()`
- `supportsShare()`
- `supportsWakeLock()`
- `supportsClipboard()`
- `supportsCamera()`
- `safeAreaInsets()`
- `triggerHaptic(kind)` with graceful no-op fallback

## Native-feeling features

### Phase 1: Shell polish

- Safe-area spacing for Dynamic Island and Home Indicator.
- Better standalone-mode layout.
- App install guidance.
- Status bar and theme color polish.
- Large mobile touch targets.

### Phase 2: Cooking experience

- Screen Wake Lock while Cook Mode is active where supported.
- Swipe or large-button navigation between cooking steps.
- Haptic feedback for save, start cooking, next step, timer complete, and notification enabled.
- Sticky cooking actions above the Home Indicator.

### Phase 3: Sharing and import

- Web Share API for recipe sharing.
- Clipboard import for ingredients.
- Camera capture for ingredient photos.
- File input fallback for unsupported browsers.

### Phase 4: Offline first

- Cache app shell.
- Cache saved recipes.
- Queue save and grocery actions while offline.
- Sync when online.

### Phase 5: Deep links

- Notification click opens the intended recipe, cook mode, grocery list, or reminder screen.
- Add URL patterns for key screens.

## Testing checklist

- Safari on iPhone, browser tab mode.
- Safari on iPhone, Home Screen installed mode.
- Chrome on Android.
- Desktop Safari or Chrome.
- Notification permission denied.
- Notification permission granted.
- Offline startup.
- Cook Mode with screen lock prevention unsupported.

# As-Is Architecture — Medicine Reminder (Flutter)

The original codebase is a **Flutter mobile-first application** with cross-platform
runners (Android, iOS, Web, Linux, macOS, Windows). All data is kept **on the
device** — no backend, no shared database, no user accounts.

## Tech stack (as-is)

| Layer          | Technology                                            |
|----------------|-------------------------------------------------------|
| UI framework   | Flutter 2.x / Dart                                    |
| State mgmt     | RxDart `BehaviorSubject` + `provider` (BLoC pattern)  |
| Local storage  | `shared_preferences` (JSON-encoded medicine list)     |
| Notifications  | `flutter_local_notifications` + `timezone`            |
| Animations     | `flare_flutter`                                       |
| Android build  | Gradle + Kotlin                                       |
| iOS build      | Xcode + Swift + CocoaPods (Ruby)                      |
| Desktop        | C++ runners (Linux, Windows, macOS shells)            |
| Web            | Flutter web (compiled to JS)                          |

## Component diagram

```
+-----------------------------------------------------------------+
|                       USER DEVICE                               |
|                                                                 |
|  +-------------------------------------------------------+      |
|  |                 FLUTTER APP (Dart)                    |      |
|  |                                                       |      |
|  |  +----------------+    +-----------------------+      |      |
|  |  |   main.dart    |--->| GlobalBloc (RxDart)   |      |      |
|  |  +----------------+    +-----------+-----------+      |      |
|  |                                    |                  |      |
|  |  +----------------+  +-------------v-----------+      |      |
|  |  |  HomePage      |  |  NewEntry / Details     |      |      |
|  |  |  (Provider)    |  |  screens                |      |      |
|  |  +----------------+  +-------------------------+      |      |
|  |         |                          |                  |      |
|  |         v                          v                  |      |
|  |  +-------------------------------------------------+  |      |
|  |  |         flutter_local_notifications             |  |      |
|  |  |         (schedules OS-level alarms)             |  |      |
|  |  +-------------------------------------------------+  |      |
|  |                                                       |      |
|  |  +-------------------------------------------------+  |      |
|  |  |    shared_preferences (JSON blob "medicines")   |  |      |
|  |  +-------------------------------------------------+  |      |
|  +-------------------------------------------------------+      |
|                                                                 |
|  +------------------+  +------------------+  +---------------+  |
|  | Android runner   |  | iOS runner       |  | Desktop C++   |  |
|  | (Kotlin/Gradle)  |  | (Swift/Ruby-Pods)|  | (Linux/Win/mac|  |
|  +------------------+  +------------------+  +---------------+  |
+-----------------------------------------------------------------+
```

## Data flow (as-is)

1. User taps **+** on HomePage → `NewEntry` screen.
2. Form fields (name, dosage, type, interval, start time) validated in-widget.
3. `GlobalBloc.updateMedicineList(...)` appends the new `Medicine` to the
   `BehaviorSubject<List<Medicine>>` **and** JSON-encodes it into
   `SharedPreferences` under the `medicines` key.
4. `scheduleNotification(medicine)` computes N repeat slots (24 / interval)
   and calls `flutterLocalNotificationsPlugin.zonedSchedule(...)` for each.
5. Deletion cancels the notifications by their stored IDs and re-writes
   the shared-preferences list.

## Limitations that motivate the rewrite

- **Single-device, single-user** — no accounts, no multi-session support.
- **No backend / no analytics** — an admin dashboard is impossible.
- **No web-first UX** — the "web" target compiles a mobile UI to canvas.
- **No feedback loop, no audit of past/upcoming alerts** across users.
- **Deployment story** is per-OS store publishing, not a service you host.

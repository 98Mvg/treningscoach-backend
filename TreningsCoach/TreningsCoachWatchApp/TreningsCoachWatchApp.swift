import SwiftUI
import HealthKit
import WatchKit

final class WatchWorkoutLaunchDelegate: NSObject, WKApplicationDelegate {
    func handle(_ workoutConfiguration: HKWorkoutConfiguration) {
        Task { @MainActor in
            WatchWCManager.shared.primePendingStartFromSystemLaunch(workoutConfiguration: workoutConfiguration)
        }
    }
}

@main
struct TreningsCoachWatchApp: App {
    @WKApplicationDelegateAdaptor(WatchWorkoutLaunchDelegate.self) private var workoutLaunchDelegate

    var body: some Scene {
        WindowGroup {
            WatchRootView()
        }
    }
}

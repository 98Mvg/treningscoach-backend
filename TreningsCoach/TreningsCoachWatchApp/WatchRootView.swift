import SwiftUI

struct WatchRootView: View {
    @StateObject private var wcManager = WatchWCManager.shared
    @StateObject private var workoutManager = WatchWorkoutManager()

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                Text("Coachi")
                    .font(.headline)

                Text("Waiting for iPhone…")
                    .foregroundStyle(.secondary)

                Text("Coachi opens from iPhone workout start. If it does not, open the app here and allow workout access if prompted.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding()
            .onAppear {
                wcManager.onRemoteStopRequest = { _ in
                    workoutManager.stopWorkout(sendRemoteSignal: false)
                    wcManager.showStartScreen = false
                }
            }
            .navigationDestination(isPresented: $wcManager.showStartScreen) {
                WatchStartWorkoutView(wcManager: wcManager, workoutManager: workoutManager)
            }
        }
    }
}

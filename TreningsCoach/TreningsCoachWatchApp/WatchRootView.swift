import SwiftUI

struct WatchRootView: View {
    @StateObject private var wcManager = WatchWCManager()
    @StateObject private var workoutManager = WatchWorkoutManager()

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                Text("Coachi")
                    .font(.headline)

                Text("Waiting for iPhone…")
                    .foregroundStyle(.secondary)
            }
            .padding()
            .onAppear {
                wcManager.onRemoteStopRequest = { _ in
                    workoutManager.stopWorkout(sendRemoteSignal: false)
                }
            }
            .navigationDestination(isPresented: $wcManager.showStartScreen) {
                WatchStartWorkoutView(wcManager: wcManager, workoutManager: workoutManager)
            }
        }
    }
}

import SwiftUI

struct WatchRootView: View {
    @StateObject private var wcManager = WatchWCManager()
    @StateObject private var workoutManager = WatchWorkoutManager()

    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                Text("TreningsCoach")
                    .font(.headline)

                NavigationLink(
                    destination: WatchStartWorkoutView(wcManager: wcManager, workoutManager: workoutManager),
                    isActive: $wcManager.showStartScreen
                ) {
                    EmptyView()
                }
                .hidden()

                Text("Waiting for iPhone…")
                    .foregroundStyle(.secondary)
            }
            .padding()
            .onAppear {
                wcManager.onRemoteStopRequest = { _ in
                    workoutManager.stopWorkout(sendRemoteSignal: false)
                }
            }
        }
    }
}
